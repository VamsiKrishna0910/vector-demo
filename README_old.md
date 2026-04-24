# Vector Demo (Milvus + LangChain Core + Ollama/OpenAI)

This project demonstrates a minimal pipeline for:

1. **Ingesting PDFs** into a vector database (Milvus).
2. **Searching** for relevant chunks via semantic similarity.
3. **Running a LangChain Core retrieval chain** to answer questions using an LLM (Ollama or OpenAI).

---

## ✅ Architecture Overview

1. **PDF ingestion** (`milvus_ingest.py`) reads PDFs from `pdfs/`, splits into chunks, embeds them and stores vectors + metadata into Milvus.
2. **Vector search** (`milvus_search.py` / `/search` API) queries Milvus for nearest neighbors.
3. **RAG QA** (`/qa` API) uses a LangChain Core runnable chain:
   - Retriever (Milvus) -> fetch docs
   - Build prompt from context
   - Call an LLM (Ollama or OpenAI)

---

## 📦 Prerequisites

- Docker & Docker Compose
- Python 3.12 (recommended)
- (Optional) An OpenAI API key if you want to use OpenAI instead of Ollama

---

## 🔧 Setup

### 1) Install Python deps

```bash
cd Vector_demo
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Start Milvus + MinIO

```bash
docker-compose up -d
```

Milvus will be reachable at `localhost:19530` (gRPC) and `localhost:19121` (HTTP). MinIO will be at `localhost:9000`.

### 3) Prepare PDFs

Put your PDF files under:

```
Vector_demo/pdfs/
```

Example:

```
Vector_demo/pdfs/mydoc.pdf
```

---

## 🧠 Ingestion (PDF → Milvus)

Run the ingestion script to parse the PDFs, chunk them, embed them, and store them in Milvus:

```bash
python milvus_ingest.py
```

### Ingestion notes
- By default it uses the `sentence-transformers/all-MiniLM-L6-v2` embedding model.
- It stores the following fields in Milvus:
  - `pk` (stable primary key)
  - `source` (PDF file name)
  - `page` (page number)
  - `chunk_index` (chunk within that page)
  - `chunk` (chunk text)
  - `embedding` (vector)

---

## 🔍 Vector Search (Standalone)

Search directly with `milvus_search.py`:

```bash
python milvus_search.py "What is this document about?"
```

This runs a semantic search on Milvus and prints the top results.

---

## 🚀 API: `/search` and `/qa`

### Start the API server

```bash
.venv/bin/python -m uvicorn api_service:app --reload --host 0.0.0.0 --port 8000
```

### 1) Search endpoint

**POST** `/search`

Request body:

```json
{
  "query": "Your question here",
  "top_k": 5
}
```

Sample curl:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query":"What is this document about?","top_k":3}'
```

### 2) QA endpoint (RAG)

**POST** `/qa`

Request body is the same as `/search`.

Sample curl:

```bash
curl -X POST http://127.0.0.1:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"query":"What is this document about?","top_k":3}'
```

This endpoint runs a LangChain Core retrieval chain and returns a response like:

- `answer`: the LLM-generated answer
- `items`: retrieved chunks used as context
- `model`: which LLM was called (e.g., `llama3`)

### 3) Mortgage-only QA endpoint (for separate Pega REST Connect)

**POST** `/qa/mortgage`

This endpoint is separate from `/qa` and is intended for mortgage policy questions.
It searches a dedicated Milvus collection (`mortgage_docs` by default) and returns:

- `matched: true` when top similarity score is above threshold
- `matched: false` with `answer: Not found in mortgage policy context.` when no strong match is found

Unlike `/qa`, this endpoint **does not return `purpose` and `example`**. It uses a mortgage-specific prompt and returns a policy-focused answer format.

Sample curl:

```bash
curl -X POST http://127.0.0.1:8000/qa/mortgage \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the minimum down payment?","top_k":3}'
```

---

## 🏦 Ingest only mortgage PDFs into a separate collection

Use environment overrides when running ingestion:

```bash
MILVUS_COLLECTION=mortgage_docs PDF_GLOB='*mortgage*.pdf' python milvus_ingest.py
```

Notes:
- `MILVUS_COLLECTION` selects the target collection.
- `PDF_GLOB` filters PDFs inside `pdfs/` (default is `*.pdf`).
- Keep your general documents in `pdf_docs` and mortgage documents in `mortgage_docs`.

---

## 🔑 Configuration / Environment Variables

Copy `.env` if you want to override defaults.

### Milvus / embedding settings

- `MILVUS_HOST` (default: `localhost`)
- `MILVUS_PORT` (default: `19530`)
- `MILVUS_COLLECTION` (default: `pdf_docs`)
- `MORTGAGE_MILVUS_COLLECTION` (default: `mortgage_docs`)
- `MORTGAGE_MATCH_SCORE_MIN` (default: `0.35`)
- `EMBED_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `PDF_GLOB` (ingest filter, default: `*.pdf`)

### LLM configuration

- Use **Ollama (default)**:
  - `OLLAMA_URL` (default: `http://89.167.64.207:11434/api/generate`)
  - `OLLAMA_MODEL` (default: `llama3`)

- Use **OpenAI** (if you set this, it runs instead of Ollama):
  - `OPENAI_API_KEY`
  - `OPENAI_MODEL` (default: `gpt-3.5-turbo`)

---

## 🧩 How it all fits together

1. **Ingestion**: PDF → text → chunks → embeddings → Milvus
2. **Search**: query → embedding → Milvus similarity search → chunk results
3. **QA** (LangChain Core): query + retrieved chunks → prompt → LLM → answer

---

## 🛠 Troubleshooting

- **Milvus not reachable**: check `docker-compose ps` and ensure `milvus-standalone` is running.
- **No PDFs found**: add PDFs to `pdfs/` and rerun `milvus_ingest.py`.
- **LLM errors**: check `OLLAMA_URL`, `OPENAI_API_KEY`, and make sure the model endpoint is reachable.

---

## 🚀 Next steps (optional)

If you want, I can help you add:

- A simple web UI for `/qa`
- Streaming responses from the LLM
- LangChain-compatible prompt templates and output parsers
- A memory layer or user session tracking

Just say the word!
