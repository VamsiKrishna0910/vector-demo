import os
import sys
import json
import numpy as np

from dotenv import load_dotenv
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from pymilvus import Collection, connections


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible embedding wrapper around SentenceTransformers."""

    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()


load_dotenv()

MILVUS_URI = os.getenv("MILVUS_URI", "tcp://localhost:19530")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "pdf_docs")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
TOP_K = int(os.getenv("TOP_K", "5"))


def connect_milvus():
    """Connect to Milvus using optional token."""
    if MILVUS_TOKEN and MILVUS_TOKEN.strip():
        connections.connect(alias="default", uri=MILVUS_URI, token=MILVUS_TOKEN)
    else:
        connections.connect(alias="default", uri=MILVUS_URI)



def main():
    raw = False
    json_out = False
    args = sys.argv[1:]
    if not args:
        print('Usage: python milvus_search.py [--raw|--json] "your question here"')
        raise SystemExit(1)

    if args[0] in ("--raw", "-r"):
        raw = True
        args = args[1:]
    elif args[0] in ("--json", "-j"):
        json_out = True
        args = args[1:]

    query = " ".join(args).strip()
    if not query:
        print('Usage: python milvus_search.py [--raw|--json] "your question here"')
        raise SystemExit(1)

    connect_milvus()

    model = SentenceTransformerEmbeddings(EMBED_MODEL_NAME)
    q_vec = model.embed_query(query)
    col = Collection(COLLECTION_NAME)
    col.load()

    results = col.search(
        data=[q_vec],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=TOP_K,
        output_fields=["source", "page", "chunk_index", "chunk"],
    )[0]

    out = []
    for rank, hit in enumerate(results, start=1):
        ent = getattr(hit, "entity", None) or {}
        src = ent.get("source")
        page = ent.get("page")
        chunk_idx = ent.get("chunk_index")
        txt = ent.get("chunk") or ""
        item = {
            "rank": rank,
            "score": float(hit.score),
            "source": src,
            "page": page,
            "chunk_index": chunk_idx,
            "text": txt,
        }
        out.append(item)

        if raw:
            # print full chunk text
            print(txt)
        elif json_out:
            # will print later as full JSON
            pass
        else:
            print(f"{rank}. score={hit.score:.4f} | {src} | page {page} | chunk {chunk_idx}")
            if txt:
                print(f" {txt}\n")

    if json_out:
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
	main()