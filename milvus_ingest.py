import os
import glob
import hashlib
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from pymilvus import (
 connections, utility,
 FieldSchema, CollectionSchema, DataType,
 Collection
)
load_dotenv()


class SentenceTransformerEmbeddings(Embeddings):
    """LangChain-compatible embedding wrapper around SentenceTransformers."""

    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()
MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN", "")
COLLECTION_NAME = os.getenv("MILVUS_COLLECTION", "pdf_docs")
EMBED_MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
PDF_DIR = "pdfs"
PDF_GLOB = os.getenv("PDF_GLOB", "*.pdf")
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "1200"))
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))
# Standard metadata policy
# - primary key is stable (same PDF text -> same pk) so re-ingest is deterministic
# - source/page used for traceability
def connect_milvus():
    if MILVUS_TOKEN and MILVUS_TOKEN.strip():
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT, token=MILVUS_TOKEN)
    else:
        connections.connect(alias="default", host=MILVUS_HOST, port=MILVUS_PORT)
def read_pdf_pages(pdf_path: str):
    reader = PdfReader(pdf_path)
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = " ".join(text.split())
        yield os.path.basename(pdf_path), i + 1, text
def chunk_text(text: str, chunk_size: int, overlap: int):
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)
    return chunks

def stable_pk(source: str, page: int, chunk_index: int, chunk_text: str) -> str:
    raw = f"{source}|{page}|{chunk_index}|{chunk_text[:200]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()
def get_or_create_collection(dim: int) -> Collection:
    if utility.has_collection(COLLECTION_NAME):
        col = Collection(COLLECTION_NAME)
        col.load()
        return col

    fields = [
        FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
        FieldSchema(name="source", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="page", dtype=DataType.INT64),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="chunk", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]

    schema = CollectionSchema(fields, description="PDF chunks + embeddings (standard baseline)")
    col = Collection(COLLECTION_NAME, schema=schema)
    # Index standard (small dataset safe; production-friendly)
    col.create_index(
        field_name="embedding",
        index_params={
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 200},
        },
    )
    col.load()
    return col
def main():
    if not os.path.exists(PDF_DIR):
        raise SystemExit(f"Folder '{PDF_DIR}' not found. Create it and put PDFs inside.")

    pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, PDF_GLOB)))
    if not pdf_files:
        raise SystemExit(
            f"No PDFs found in '{PDF_DIR}' with pattern '{PDF_GLOB}'. "
            "Add PDFs and/or set PDF_GLOB (example: PDF_GLOB='*mortgage*.pdf')."
        )

    print(f"Milvus host: {MILVUS_HOST}:{MILVUS_PORT}")
    connect_milvus()

    print(f"Embedding model: {EMBED_MODEL_NAME}")
    model = SentenceTransformerEmbeddings(EMBED_MODEL_NAME)
    # sentence-transformers embeddings are typically 384/768 dims; we need a sample
    sample_vec = model.embed_query("test")
    dim = len(sample_vec)
    col = get_or_create_collection(dim)

    pks, sources, pages, idxs, chunks, vecs = [], [], [], [], [], []
    total_pages = 0

    for pdf_path in pdf_files:
        for source, page_no, page_text in read_pdf_pages(pdf_path):
            total_pages += 1

            page_chunks = chunk_text(page_text, CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS)
            if not page_chunks:
                continue

            embeddings = model.embed_documents(page_chunks)
            embeddings = np.asarray(embeddings, dtype=np.float32)

            for i, ch in enumerate(page_chunks):
                pks.append(stable_pk(source, page_no, i, ch))
                sources.append(source)
                pages.append(page_no)
                idxs.append(i)
                chunks.append(ch)
                vecs.append(embeddings[i].tolist())

    if not pks:
        raise SystemExit("No extractable text found. Scanned PDFs require OCR(out of scope for baseline).")

    print(f"Pages scanned: {total_pages}")
    print(f"Chunks to insert: {len(pks)}")

    # Insert is idempotent only if the same PK is not re-inserted.
    # For true idempotency, use upsert strategy or delete-by-source before re-ingest.
    col.insert([pks, sources, pages, idxs, chunks, vecs])
    col.flush()
    col.load()
    print("Ingestion complete.")
if __name__ == "__main__":
 main()