from typing import List, Optional, Dict, Any, Callable
import os
import json
import re
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain.embeddings.base import Embeddings
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda, RunnablePassthrough
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible embedding wrapper around SentenceTransformers."""

    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()


class MilvusRetriever(BaseRetriever):
    """LangChain Core retriever backed by a Milvus collection."""

    collection: Collection
    model: SentenceTransformerEmbeddings
    k: int = 5

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        q_vec = self.model.embed_query(query)
        q_vec = np.asarray(q_vec, dtype=np.float32)
        results = self.collection.search(
            data=[q_vec],
            anns_field="embedding",
            param={"metric_type": "COSINE", "params": {"ef": 64}},
            limit=self.k,
            output_fields=["source", "page", "chunk_index", "chunk"],
        )
        hits = results[0] if results else []
        docs: list[Document] = []
        for hit in hits:
            ent = getattr(hit, "entity", None) or {}
            text = ent.get("chunk") or ""
            metadata = {
                "source": ent.get("source"),
                "page": ent.get("page"),
                "chunk_index": ent.get("chunk_index"),
                "score": float(hit.score) if hit.score is not None else None,
            }
            docs.append(Document(page_content=text, metadata=metadata))
        return docs


import openai
import requests

app = FastAPI(title="Milvus Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "pdf_docs")
MORTGAGE_COLLECTION_NAME = os.getenv("MORTGAGE_MILVUS_COLLECTION", "mortgage_docs")
MORTGAGE_MATCH_SCORE_MIN = float(os.getenv("MORTGAGE_MATCH_SCORE_MIN", "0.35"))
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Default Ollama API URL (change if you self-host elsewhere)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://89.167.64.207:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResultItem(BaseModel):
    rank: int
    score: float
    source: Optional[str]
    page: Optional[int]
    chunk_index: Optional[int]
    text: str


@app.on_event("startup")
def startup_event():
    # connect to Milvus and load model into app.state
    try:
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
        app.state.collections = {}
        try:
            base_collection = Collection(COLLECTION_NAME)
            base_collection.load()
            app.state.collections[COLLECTION_NAME] = base_collection
            app.state.collection = base_collection
        except Exception:
            app.state.collection = None

        # Best-effort pre-load for mortgage collection.
        try:
            mortgage_collection = Collection(MORTGAGE_COLLECTION_NAME)
            mortgage_collection.load()
            app.state.collections[MORTGAGE_COLLECTION_NAME] = mortgage_collection
        except Exception:
            pass
    except Exception:
        app.state.collection = None
        app.state.collections = {}
    try:
        app.state.model = SentenceTransformerEmbeddings(EMBED_MODEL_NAME)
    except Exception:
        app.state.model = None


def _get_collection(collection_name: str) -> Optional[Collection]:
    collections = getattr(app.state, "collections", {}) or {}
    cached = collections.get(collection_name)
    if cached is not None:
        return cached

    try:
        col = Collection(collection_name)
        col.load()
        collections[collection_name] = col
        app.state.collections = collections
        return col
    except Exception:
        return None


@app.post("/search", response_model=List[SearchResultItem])
def search(req: SearchRequest):
    if not app.state.collection:
        raise HTTPException(status_code=500, detail="Milvus collection not available")
    q_vec = app.state.model.embed_query(req.query)
    q_vec = np.asarray(q_vec, dtype=np.float32)
    results = app.state.collection.search(
        data=[q_vec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=req.top_k,
        output_fields=["source", "page", "chunk_index", "chunk"],
    )
    hits = results[0] if results else []
    out = []
    for rank, hit in enumerate(hits, start=1):
        ent = getattr(hit, "entity", None) or {}
        out.append(
            SearchResultItem(
                rank=rank,
                score=float(hit.score),
                source=ent.get("source"),
                page=ent.get("page"),
                chunk_index=ent.get("chunk_index"),
                text=ent.get("chunk") or "",
            )
        )
    return out


def _build_context(items, max_chars=3000):
    parts = []
    total = 0
    for i, it in enumerate(items, start=1):
        if isinstance(it, dict):
            text = it.get("text") or ""
            src = it.get("source")
            page = it.get("page")
        else:
            # langchain_core Document
            text = getattr(it, "page_content", "")
            meta = getattr(it, "metadata", {}) or {}
            src = meta.get("source")
            page = meta.get("page")

        header = f"[{i}] {src or 'unknown'} (page {page})\n"
        block = header + (text or "") + "\n\n"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


def _build_rag_chain(use_ollama: bool, prompt_builder: Optional[Callable[[str, list[Document]], str]] = None):
    """Build a LangChain Core runnable chain for QA.

    The chain takes a user query (string) and returns a dict containing the
    LLM response as well as any metadata produced during the run.
    """

    def _retrieve(inputs: dict):
        query = inputs.get("query")
        if query is None:
            raise ValueError("Expected 'query' in chain input")
        retriever = inputs.get("retriever")
        if retriever is None:
            raise ValueError("Expected 'retriever' in chain input")
        return retriever.invoke(query)

    def _format_prompt(inputs: dict):
        query = inputs.get("query")
        docs = inputs.get("docs")
        if query is None or docs is None:
            raise ValueError("Expected 'query' and 'docs' in chain input")
        if prompt_builder is not None:
            return prompt_builder(query, docs)
        context = _build_context(docs, max_chars=3000)
        # Return the raw prompt string (not a dict), so downstream LLM step can
        # safely use it for the API call.
        return f"Context:\n{context}\nQuestion: {query}\nAnswer:"

    def _call_llm(inputs: dict):
        query = inputs.get("query")
        docs = inputs.get("docs")
        prompt = inputs.get("prompt")
        if query is None or docs is None:
            raise ValueError("Expected 'query' and 'docs' in chain input")
        if use_ollama:
            return _synthesize_with_ollama(query, docs, prompt=prompt)
        return _synthesize_with_openai(query, docs, prompt=prompt)

    # Expect the chain input to be a dict containing `query` and `retriever`.
    # The 'retriever' is passed through the chain so that retrieval can be performed
    # inside the chain steps.
    chain = (
        RunnablePassthrough()
        .assign(docs=RunnableLambda(_retrieve))
        .assign(prompt=RunnableLambda(_format_prompt))
        .assign(llm_output=RunnableLambda(_call_llm))
    )

    return chain


class RetrievalQA(Runnable[str, dict]):
    """LangChain Core runnable wrapping retrieval + LLM.

    This class behaves like a standard LangChain `Runnable` and can be invoked
    with a user query to produce an output containing both the LLM response and
    the retrieved documents.
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        use_ollama: bool,
        prompt_builder: Optional[Callable[[str, list[Document]], str]] = None,
    ):
        self.retriever = retriever
        self.chain = _build_rag_chain(use_ollama=use_ollama, prompt_builder=prompt_builder)

    def invoke(
        self, query: str, config: RunnableConfig | None = None, **kwargs: Any
    ) -> dict:
        return self.chain.invoke(
            {"query": query, "retriever": self.retriever}, config=config, **kwargs
        )


def _extract_purpose_example(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract purpose/example lines from text.

    This function attempts to keep the parsed values separate even when the
    source text has "Example" embedded inside the Purpose section.
    """

    purpose = None
    example = None
    text = text or ""
    # Capture Purpose up to Example label (preferred), next newline, or end of text.
    pm = re.search(
        r'purpose\s*[:\-]\s*(.*?)(?=\s+example\s*[:\-]|\n|$)',
        text,
        flags=re.I | re.S,
    )
    # Capture Example up to next newline/end, a new Purpose label, or the next
    # numbered question marker (e.g., "2. What is...").
    em = re.search(
        r'example\s*[:\-]\s*(.*?)(?=\n|$|\s+purpose\s*[:\-]|\s+\d+\s*\.\s+[A-Za-z])',
        text,
        flags=re.I | re.S,
    )
    if pm:
        purpose = pm.group(1).strip().strip('"').strip('*')
    if em:
        example = em.group(1).strip().strip('"').strip('*')

    if purpose:
        purpose = re.sub(r'\s*example\s*[:\-].*$', '', purpose, flags=re.I | re.S).strip()
    if example:
        example = re.sub(r'\s*purpose\s*[:\-].*$', '', example, flags=re.I | re.S).strip()
        example = re.sub(r'\s+\d+\s*\.\s+[A-Za-z].*$', '', example, flags=re.S).strip()

    return purpose, example


def _extract_purpose_example_for_query(question: str, text: str) -> tuple[Optional[str], Optional[str]]:
    """Extract purpose/example nearest to the specific question inside text."""

    if not question or not text:
        return None, None

    words = re.findall(r"[a-z0-9]+", question.lower())
    if not words:
        return None, None

    # Build a flexible matcher for the question allowing punctuation/spacing differences.
    question_pattern = r"\b" + r"\W+".join(map(re.escape, words)) + r"\b"
    match = re.search(question_pattern, text, flags=re.I)
    if not match:
        return None, None

    # Search only after the matched question to avoid picking previous question labels.
    segment = text[match.start(): match.start() + 1800]
    return _extract_purpose_example(segment)


def _ollama_generate_text(prompt: str) -> str:
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "max_tokens": 512, "temperature": 0.0}
    r = requests.post(OLLAMA_URL, json=payload, timeout=30)
    r.raise_for_status()

    results = []
    content_type = r.headers.get("Content-Type", "") or ""
    if "ndjson" in content_type or "stream" in content_type:
        for line in r.text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                part = json.loads(line)
                if isinstance(part, dict) and part.get("results"):
                    results.extend(part.get("results"))
                else:
                    results.append(part)
            except Exception:
                continue
    else:
        try:
            data = r.json()
            results = data.get("results") or []
        except Exception:
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    part = json.loads(line)
                    if isinstance(part, dict) and part.get("results"):
                        results.extend(part.get("results"))
                    else:
                        results.append(part)
                except Exception:
                    continue

    out_text = ""
    if not results:
        try:
            matches = re.findall(r'"response"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', (r.text or ""))
            out_text = "".join(matches)
        except Exception:
            out_text = ""
    else:
        for res in results:
            if not isinstance(res, dict):
                continue
            if "response" in res:
                out_text += str(res.get("response") or "")
                continue
            for c in res.get("content", []):
                if c.get("type") == "output_text":
                    out_text += c.get("text", "")

    try:
        cleaned = out_text.encode("utf-8").decode("unicode_escape")
    except Exception:
        cleaned = out_text
    cleaned = cleaned.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"')
    cleaned = re.sub(r'\\\\n', '\n', cleaned)
    return cleaned.strip()


def _openai_generate_text(system_prompt: str, user_prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=512,
        temperature=0.0,
    )
    return resp["choices"][0]["message"]["content"].strip()


def _synthesize_with_openai(question: str, items, prompt: Optional[str] = None) -> Dict[str, Any]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    if prompt is None:
        context = _build_context(items, max_chars=3000)
        system = (
            "You are a concise assistant that answers questions using only the provided context. "
            "If the answer cannot be found in the context, say 'I don't know'. Cite sources by index like [1].\n\n"
            "You must respond with exactly two lines in this format:\n"
            "Purpose: <one or two concise sentences>\n"
            "Example: <one example sentence from the context>\n\n"
            "If there is no clear purpose, respond with 'Purpose: N/A'. "
            "If there is no clear example, respond with 'Example: N/A'."
        )
        user_prompt = f"Context:\n{context}\nQuestion: {question}\nAnswer:"
    else:
        # Preserve the same system instructions as the default prompt.
        system = (
            "You are a concise assistant that answers questions using only the provided context. "
            "If the answer cannot be found in the context, say 'I don't know'. Cite sources by index like [1].\n\n"
            "You must respond with exactly two lines in this format:\n"
            "Purpose: <one or two concise sentences>\n"
            "Example: <one example sentence from the context>\n\n"
            "If there is no clear purpose, respond with 'Purpose: N/A'. "
            "If there is no clear example, respond with 'Example: N/A'."
        )
        user_prompt = prompt

    resp = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user_prompt}],
        max_tokens=512,
        temperature=0.0,
    )
    answer = resp["choices"][0]["message"]["content"].strip()

    purpose, example = _extract_purpose_example(answer)

    # Prefer query-specific extraction from retrieved context to avoid cross-question leakage.
    for item in items or []:
        text = item.get("text") if isinstance(item, dict) else getattr(item, "page_content", "")
        qp, qe = _extract_purpose_example_for_query(question, text)
        if qp:
            purpose = qp
        if qe:
            example = qe
        if qp and qe:
            break

    # If still missing, fall back to generic extraction from context.
    if not purpose or purpose.strip().upper() == "N/A" or not example or example.strip().upper() == "N/A":
        for item in items or []:
            text = item.get("text") if isinstance(item, dict) else getattr(item, "page_content", "")
            if not purpose or purpose.strip().upper() == "N/A":
                p, _ = _extract_purpose_example(text)
                if p:
                    purpose = p
            if not example or example.strip().upper() == "N/A":
                _, e = _extract_purpose_example(text)
                if e:
                    example = e
            if purpose and example:
                break

    if not purpose:
        purpose = "N/A"
    if not example:
        example = "N/A"

    return {"answer": answer, "purpose": purpose, "example": example, "model": OPENAI_MODEL}


def _synthesize_with_ollama(question: str, items, prompt: Optional[str] = None) -> Dict[str, Any]:
    if prompt is None:
        context = _build_context(items, max_chars=3000)
        prompt = (
            "You are a concise assistant that answers questions using only the provided context. "
            "If the answer cannot be found in the context, say 'I don't know'. Cite sources by index like [1].\n\n"
            "You must respond with exactly two lines in this format:\n"
            "Purpose: <one or two concise sentences>\n"
            "Example: <one example sentence from the context>\n\n"
            "If there is no clear purpose, respond with 'Purpose: N/A'. "
            "If there is no clear example, respond with 'Example: N/A'.\n\n"
            f"Context:\n{context}\nQuestion: {question}\nAnswer:"
        )
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "max_tokens": 512, "temperature": 0.0}
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=30)
        r.raise_for_status()
        results = []
        content_type = r.headers.get("Content-Type", "") or ""
        # Parse streaming NDJSON if present
        if "ndjson" in content_type or "stream" in content_type:
            for line in r.text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    part = json.loads(line)
                    if isinstance(part, dict) and part.get("results"):
                        results.extend(part.get("results"))
                    else:
                        results.append(part)
                except Exception:
                    continue
        else:
            try:
                data = r.json()
                results = data.get("results") or []
            except Exception:
                for line in r.text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        part = json.loads(line)
                        if isinstance(part, dict) and part.get("results"):
                            results.extend(part.get("results"))
                        else:
                            results.append(part)
                    except Exception:
                        continue

        out_text = ""
        if not results:
            # Try regex extraction of response fragments as a fallback
            try:
                matches = re.findall(r'"response"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"', (r.text or ""))
                out_text = "".join(matches)
            except Exception:
                out_text = ""
        else:
            for res in results:
                if not isinstance(res, dict):
                    continue
                if "response" in res:
                    out_text += str(res.get("response") or "")
                    continue
                for c in res.get("content", []):
                    if c.get("type") == "output_text":
                        out_text += c.get("text", "")

        # Normalize/unescape escaped sequences without aggressively removing backslashes
        try:
            cleaned = out_text.encode("utf-8").decode("unicode_escape")
        except Exception:
            cleaned = out_text
        # Convert common escaped sequences to actual characters, preserve other backslashes
        cleaned = cleaned.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t').replace('\\"', '"')
        cleaned = re.sub(r'\\\\n', '\n', cleaned)
        cleaned = cleaned.strip()

        # Tolerate markdown asterisks around headings
        cleaned = re.sub(r'^\*+\s*', '', cleaned)
        cleaned = re.sub(r'\s*\*+$', '', cleaned)

        purpose, example = _extract_purpose_example(cleaned)

        # Prefer query-specific extraction from retrieved context to avoid cross-question leakage.
        for item in items or []:
            text = item.get("text") if isinstance(item, dict) else getattr(item, "page_content", "")
            qp, qe = _extract_purpose_example_for_query(question, text)
            if qp:
                purpose = qp
            if qe:
                example = qe
            if qp and qe:
                break

        # If still missing, fall back to generic extraction from context.
        if (not purpose or purpose.strip().upper() == "N/A") or (
            not example or example.strip().upper() == "N/A"
        ):
            for item in items or []:
                text = item.get("text") if isinstance(item, dict) else getattr(item, "page_content", "")
                if not purpose or purpose.strip().upper() == "N/A":
                    p, _ = _extract_purpose_example(text)
                    if p:
                        purpose = p
                if not example or example.strip().upper() == "N/A":
                    _, e = _extract_purpose_example(text)
                    if e:
                        example = e
                if purpose and example:
                    break

        if not purpose:
            purpose = "N/A"
        if not example:
            example = "N/A"

        return {"answer": cleaned, "purpose": purpose, "example": example, "model": OLLAMA_MODEL}
    except Exception as e:
        raise RuntimeError(f"Ollama call failed: {e}")


@app.post("/qa")
def qa(req: SearchRequest):
    if not OPENAI_API_KEY and not OLLAMA_URL:
        raise HTTPException(status_code=500, detail="No LLM configured (set OPENAI_API_KEY or OLLAMA_URL)")

    if not app.state.collection or not app.state.model:
        raise HTTPException(status_code=500, detail="Service not fully initialized")

    retriever = MilvusRetriever(collection=app.state.collection, model=app.state.model, k=req.top_k)

    # Build a LangChain Core RetrievalQA runnable.
    qa_runnable = RetrievalQA(retriever=retriever, use_ollama=bool(OLLAMA_URL))
    try:
        result = qa_runnable.invoke(req.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    docs = result.get("docs") or []
    synth = result.get("llm_output") or {}

    items = []
    for rank, doc in enumerate(docs, start=1):
        meta = getattr(doc, "metadata", {}) or {}
        items.append(
            {
                "rank": rank,
                "score": meta.get("score"),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
                "text": getattr(doc, "page_content", ""),
            }
        )

    return {
        "answer": synth.get("answer"),
        "purpose": synth.get("purpose"),
        "example": synth.get("example"),
        "model": synth.get("model"),
        "items": items,
    }


def _build_mortgage_prompt(query: str, docs: list[Document]) -> str:
    context = _build_context(docs, max_chars=3000)
    return (
        "You are a mortgage-policy assistant. Use only the mortgage policy context below. "
        "If the query is not supported by context, say exactly: Not found in mortgage policy context.\n\n"
        "Return output in this exact format:\n"
        "Decision: <Allowed | Not Allowed | Needs Review | Not Found>\n"
        "Answer: <2-5 concise sentences specific to the asked query>\n"
        "KeyRules:\n"
        "- <rule 1 from context>\n"
        "- <rule 2 from context, if available>\n"
        "Source: [index numbers used]\n\n"
        f"Context:\n{context}\nQuestion: {query}"
    )


@app.post("/qa/mortgage")
def qa_mortgage(req: SearchRequest):
    if not OPENAI_API_KEY and not OLLAMA_URL:
        raise HTTPException(status_code=500, detail="No LLM configured (set OPENAI_API_KEY or OLLAMA_URL)")

    if not app.state.model:
        raise HTTPException(status_code=500, detail="Service not fully initialized")

    mortgage_collection = _get_collection(MORTGAGE_COLLECTION_NAME)
    if not mortgage_collection:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Mortgage collection '{MORTGAGE_COLLECTION_NAME}' not available. "
                "Ingest mortgage PDF data into this collection first."
            ),
        )

    retriever = MilvusRetriever(collection=mortgage_collection, model=app.state.model, k=req.top_k)
    docs = retriever.invoke(req.query)

    items = []
    for rank, doc in enumerate(docs, start=1):
        meta = getattr(doc, "metadata", {}) or {}
        items.append(
            {
                "rank": rank,
                "score": meta.get("score"),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "chunk_index": meta.get("chunk_index"),
                "text": getattr(doc, "page_content", ""),
            }
        )

    top_score = items[0].get("score") if items else None
    if top_score is None or float(top_score) < MORTGAGE_MATCH_SCORE_MIN:
        model_name = OLLAMA_MODEL if OLLAMA_URL else OPENAI_MODEL
        return {
            "matched": False,
            "answer": "Not found in mortgage policy context.",
            "model": model_name,
            "items": items,
        }

    mortgage_prompt = _build_mortgage_prompt(req.query, docs)
    try:
        if OLLAMA_URL:
            answer = _ollama_generate_text(mortgage_prompt)
            model_name = OLLAMA_MODEL
        else:
            system_prompt = (
                "You are a strict mortgage-policy assistant. Use only provided context and follow the required output format."
            )
            answer = _openai_generate_text(system_prompt, mortgage_prompt)
            model_name = OPENAI_MODEL
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    return {
        "matched": True,
        "answer": answer,
        "model": model_name,
        "items": items,
    }
