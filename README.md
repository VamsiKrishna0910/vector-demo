# Vector Demo: RAG with Milvus + LangChain Core + Ollama/OpenAI

A production-ready **Retrieval-Augmented Generation (RAG)** pipeline that demonstrates:
- 📄 **PDF Ingestion** → Vector embeddings → Milvus database
- 🔍 **Semantic Search** → Find relevant documents
- 🤖 **LLM Q&A** → LangChain Core + Ollama or OpenAI
- 🏦 **Multi-collection Support** → General QA + Mortgage-specific QA

Perfect for building document-based AI assistants, knowledge bases, and domain-specific chatbots.

---

## ✨ Key Features

✅ **Fast PDF Processing** - Intelligent chunking with overlap for context preservation  
✅ **Vector Search** - Semantic similarity search using `all-MiniLM-L6-v2` embeddings  
✅ **Flexible LLM** - Use Ollama (local) or OpenAI (cloud)  
✅ **Multi-collection** - Separate search contexts (general docs + mortgage docs)  
✅ **RESTful API** - Easy integration with FastAPI  
✅ **Docker Ready** - Milvus + MinIO + Attu pre-configured  

---

## 🏗 Architecture

```
PDFs (pdfs/)
    ↓
milvus_ingest.py (Chunking + Embedding)
    ↓
Milvus Vector DB (pdf_docs, mortgage_docs collections)
    ↓
FastAPI (api_service.py)
    ├─ /search (Vector search only)
    ├─ /qa (RAG: search + LLM answer)
    └─ /qa/mortgage (Mortgage-specific RAG)
```

---

## 📋 Prerequisites

- **Docker & Docker Compose** (for Milvus, MinIO, Attu)
- **Python 3.12+** (for API and ingestion)
- **Git** (for cloning)
- **Optional**: OpenAI API key (if using OpenAI instead of Ollama)

---

## 🚀 Quick Start

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/vector-demo.git
cd vector-demo

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Start Docker Services

```bash
cd ..  # Go to parent directory where docker-compose.yml is
docker compose up -d
```

**What this starts:**
- 🐳 **Milvus** (vector DB) - `localhost:19530`
- 🐳 **MinIO** (object storage) - `localhost:9000`
- 🐳 **Attu** (Milvus UI) - `localhost:8080`

Verify services are running:
```bash
docker compose ps
```

### 3️⃣ Prepare PDFs

Add your PDF files to the `pdfs/` directory:

```bash
cp /path/to/your/documents.pdf vector-demo/pdfs/
```

Example structure:
```
vector-demo/
├── pdfs/
│   ├── document1.pdf
│   ├── document2.pdf
│   └── mortgage/
│       └── mortgage_policy.pdf
```

### 4️⃣ Ingest PDFs into Milvus

```bash
cd vector-demo
python milvus_ingest.py
```

**Output:** Embedding vectors stored in `pdf_docs` collection.

### 5️⃣ Start API Server

```bash
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

**API ready at:** `http://localhost:8000`

---

## 📚 Usage

### Standalone Search (CLI)

Query vectors directly without API:

```bash
python milvus_search.py "What is the minimum down payment?"
```

### API: Vector Search

**POST** `/search`

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "items": [
    {
      "source": "document1.pdf",
      "page": 1,
      "chunk": "...",
      "distance": 0.23
    }
  ]
}
```

### API: RAG Q&A (LLM-powered)

**POST** `/qa`

```bash
curl -X POST http://127.0.0.1:8000/qa \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "top_k": 3
  }'
```

**Response:**
```json
{
  "answer": "Based on the documents, the main topic is...",
  "items": [
    {
      "source": "document1.pdf",
      "page": 1,
      "chunk": "..."
    }
  ],
  "model": "llama2"
}
```

### API: Mortgage QA (Domain-specific)

**POST** `/qa/mortgage`

```bash
curl -X POST http://127.0.0.1:8000/qa/mortgage \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Can loan be approved with DTI 48%?",
    "top_k": 5
  }'
```

**Response:**
```json
{
  "matched": true,
  "answer": "According to mortgage policy...",
  "items": [...]
}
```

---

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

**Key settings:**

```env
# Milvus Configuration
MILVUS_URI=tcp://localhost:19530
MILVUS_COLLECTION=pdf_docs

# Embedding Model
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE_CHARS=1200
CHUNK_OVERLAP_CHARS=200

# Search
TOP_K=5

# LLM: Ollama (default)
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2

# OR LLM: OpenAI (uncomment to use)
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-3.5-turbo
```

### Using Different LLMs

**Ollama (local, free):**
```env
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama2
```

**OpenAI (cloud, paid):**
```env
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-3.5-turbo
```

---

## 🔧 Advanced Usage

### Ingest Mortgage Docs to Separate Collection

```bash
MILVUS_COLLECTION=mortgage_docs PDF_GLOB='mortgage/*.pdf' python milvus_ingest.py
```

### Filter PDFs During Ingestion

```bash
PDF_GLOB='policy*.pdf' python milvus_ingest.py
```

### Check Ingestion Details

View what was stored in Milvus using **Attu Dashboard:**
- Open: `http://localhost:8080`
- Browse collections, view embeddings, check metadata

---

## 📊 Database Schema

**Fields stored in Milvus:**

| Field | Type | Description |
|-------|------|-------------|
| `pk` | Integer (Primary Key) | Unique record ID |
| `source` | String | PDF filename |
| `page` | Integer | Page number |
| `chunk_index` | Integer | Chunk within page |
| `chunk` | String | Text content |
| `embedding` | Vector | 384-dim embedding |

---

## 🚦 Monitoring & Debugging

### Check Services

```bash
# Docker status
docker compose ps

# FastAPI health
curl http://localhost:8000/docs

# Milvus connection
python -c "from pymilvus import connections; connections.connect(host='localhost', port=19530); print('Connected!')"
```

### View Logs

```bash
# FastAPI logs
tail -f fastapi.log

# Docker logs
docker compose logs -f milvus
docker compose logs -f attu
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Milvus not reachable | Ensure `docker compose up -d` ran successfully |
| No PDFs ingested | Check `pdfs/` folder exists and contains `.pdf` files |
| LLM errors | Verify `OLLAMA_URL` or `OPENAI_API_KEY` |
| Port conflicts | Change `API_PORT` in `.env` or use different port |

---

## 📁 Project Structure

```
vector-demo/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Template environment variables
├── .gitignore                   # Git ignore rules
├── docker-compose.yml           # Docker services (Milvus, MinIO, Attu)
├── milvus_conf/
│   └── milvus.yaml             # Milvus configuration
├── api_service.py              # FastAPI server
├── milvus_ingest.py            # PDF ingestion script
├── milvus_search.py            # Standalone search CLI
├── pdfs/                        # Your PDF documents
│   ├── document1.pdf
│   ├── document2.pdf
│   └── mortgage/
│       └── mortgage_policy.pdf
└── .venv/                       # Virtual environment (ignored)
```

---

## 🔌 Integration Examples

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/qa",
    json={
        "query": "What is the return policy?",
        "top_k": 3
    }
)

answer = response.json()["answer"]
print(answer)
```

### JavaScript/Node.js

```javascript
const response = await fetch("http://localhost:8000/qa", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: "What is the return policy?",
    top_k: 3
  })
});

const data = await response.json();
console.log(data.answer);
```

---

## 🔐 Security Notes

⚠️ **Before deploying to production:**

1. **Never commit `.env`** - Use `.env.example` as template
2. **Protect API keys** - Store `OPENAI_API_KEY` securely (use environment variables or secrets manager)
3. **Enable authentication** - Add API key validation to `api_service.py`
4. **Rate limiting** - Add FastAPI middleware for rate limiting
5. **HTTPS** - Deploy behind reverse proxy (nginx, Caddy)
6. **Docker security** - Use non-root user in Dockerfile

---

## 🧩 Tech Stack

| Component | Purpose |
|-----------|---------|
| **Milvus** | Vector database |
| **MinIO** | Object storage (Milvus backend) |
| **Attu** | Milvus web UI |
| **FastAPI** | REST API framework |
| **LangChain Core** | LLM orchestration |
| **Ollama** / **OpenAI** | LLM providers |
| **Sentence Transformers** | Embedding model |
| **PyPDF2** / **LangChain** | PDF processing |
| **Docker Compose** | Containerization |

---

## 📦 Installation Details

### System Requirements

- **RAM**: Minimum 4GB (8GB+ recommended)
- **Disk**: At least 2GB free space for Milvus + MinIO data
- **CPU**: 2+ cores

### Dependencies (from requirements.txt)

- `pymilvus` - Milvus Python client
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `langchain-core` - LLM orchestration
- `sentence-transformers` - Embeddings
- `pymupdf` / `pypdf` - PDF processing
- `pydantic` - Data validation

---

## 🤝 Contributing

Contributions are welcome! 

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 Ingestion Notes

The ingestion process:

1. **Read PDFs** from `pdfs/` directory
2. **Extract text** from each page
3. **Split into chunks** (default: 1200 chars with 200 char overlap)
4. **Generate embeddings** using `all-MiniLM-L6-v2`
5. **Store in Milvus** with metadata (filename, page, chunk index)

⚡ **Performance**: ~10-50 PDFs/min (depends on size and hardware)

---

## 🆘 Troubleshooting

### FAQ

**Q: How do I use my own embedding model?**  
A: Set `EMBED_MODEL=your-model-name` in `.env`

**Q: Can I query multiple collections?**  
A: Yes, create multiple collections and set `MILVUS_COLLECTION` accordingly

**Q: How do I update existing documents?**  
A: Re-ingest the PDF - Milvus will replace old embeddings based on `pk`

**Q: What LLM should I use?**  
A: For testing: Ollama (free, local). For production: OpenAI or similar (faster, more capable)

---

## 📖 Further Resources

- [Milvus Documentation](https://milvusdb.com/docs)
- [Attu User Guide](https://attu.io/)
- [LangChain Documentation](https://python.langchain.com/)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Ollama Models](https://ollama.com/library)
- [OpenAI API Reference](https://platform.openai.com/docs)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- 📧 **Issues**: Open a GitHub issue
- 💬 **Discussions**: Use GitHub Discussions
- 📚 **Wiki**: Check project wiki for advanced topics

---

## ⭐ Show Your Support

If this project helped you, please give it a star! ⭐

---

**Happy Building! 🚀**
