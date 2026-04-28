# 🧪 Network Access Test Guide for Other Users

Your server (Vamsi's) is now running Milvus, MinIO, and Attu on the network!

---

## 📍 Server Information

**Server IP:** `89.167.64.207`

| Service | Port | URL | Protocol |
|---------|------|-----|----------|
| **Milvus gRPC** | 19530 | `89.167.64.207:19530` | TCP |
| **Milvus HTTP** | 19121 | `http://89.167.64.207:19121` | HTTP |
| **Attu Dashboard** | 8080 | `http://89.167.64.207:8080` | HTTP |
| **MinIO** | 9000 | `http://89.167.64.207:9000` | HTTP |

---

## ✅ Test 1: Check Network Connectivity

Run this on **your machine** (not the server):

### Option A: Using `ping`
```bash
ping 89.167.64.207
```

Expected: You should see replies.

### Option B: Using `nc` (netcat)
```bash
nc -zv 89.167.64.207 19530
nc -zv 89.167.64.207 8080
```

Expected output:
```
Connection to 89.167.64.207 port 19530 [tcp/*] succeeded!
Connection to 89.167.64.207 port 8080 [tcp/*] succeeded!
```

---

## ✅ Test 2: Test Attu Dashboard (Browser)

From your machine, open browser and go to:

**URL:** `http://89.167.64.207:8080`

You should see the **Attu Dashboard** loaded with Milvus connection already configured!

---

## ✅ Test 3: Test Milvus HTTP API

```bash
curl -X GET http://89.167.64.207:19121/api/v1/health/live
```

Expected response:
```json
{"ok":true}
```

---

## ✅ Test 4: Connect with Python (PyMilvus)

Create a test script `test_milvus_connection.py`:

```python
#!/usr/bin/env python3
"""Test remote Milvus connection"""

from pymilvus import connections, list_collections

print("🔗 Connecting to remote Milvus...")
print("   Server: 89.167.64.207:19530")

try:
    connections.connect(
        host="89.167.64.207",
        port=19530,
        alias="default"
    )
    print("✅ Connected successfully!")
    
    # List collections
    collections = list_collections()
    print(f"\n📚 Collections on server: {collections}")
    
    if collections:
        print("\n✅ Ready to use Milvus!")
    else:
        print("\n⚠️  No collections yet. Ask Vamsi to ingest PDFs.")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Is server IP correct?")
    print("2. Is port 19530 open?")
    print("3. Check firewall settings")
```

Run it:
```bash
python test_milvus_connection.py
```

Expected output:
```
🔗 Connecting to remote Milvus...
   Server: 89.167.64.207:19530
✅ Connected successfully!

📚 Collections on server: ['pdf_docs', 'mortgage_docs']

✅ Ready to use Milvus!
```

---

## ✅ Test 5: Test MinIO Connection

```bash
curl -X GET http://89.167.64.207:9000/minio/bootstrap.html
```

Or open in browser: `http://89.167.64.207:9000`

Default credentials:
- Username: `minioadmin`
- Password: `minioadmin`

---

## 🐍 Test 6: Full Python Vector Search Example

Create `test_remote_search.py`:

```python
#!/usr/bin/env python3
"""Test full vector search on remote Milvus"""

from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

# Connect to remote Milvus
print("Connecting to Milvus...")
connections.connect(host="89.167.64.207", port=19530)

# Load collection
collection = Collection("pdf_docs")
collection.load()

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Your query
query_text = "What is the main topic?"
query_embedding = model.encode(query_text).tolist()

# Search
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=3,
    output_fields=["source", "page", "chunk"]
)

print(f"\n🔍 Search results for: '{query_text}'\n")
for hit in results[0]:
    print(f"📄 {hit.entity.get('source')} (Page {hit.entity.get('page')})")
    print(f"   Score: {hit.score:.4f}")
    print(f"   Text: {hit.entity.get('chunk')[:80]}...\n")
```

---

## 🚀 Test 7: Use API Endpoints (FastAPI)

**First, ask Vamsi to start FastAPI:**
```bash
cd /home/vamsi/Vector_demo
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

Then from your machine:

### Test `/qa` endpoint
```bash
curl -X POST http://89.167.64.207:8000/qa \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "top_k": 3
  }'
```

### Test `/qa/mortgage` endpoint
```bash
curl -X POST http://89.167.64.207:8000/qa/mortgage \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the minimum down payment?",
    "top_k": 3
  }'
```

---

## 📋 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` | Check if server is running: `docker compose ps` |
| `No route to host` | Firewall blocking port - ask network admin |
| `Name or service not known` | Hostname/IP wrong - verify server IP |
| `Timeout` | Server might be overloaded or network slow |
| Collections empty | Ask Vamsi to ingest PDFs first |

---

## 🔧 Diagnostic Commands

### Check port connectivity
```bash
# Linux/Mac
nc -zv 89.167.64.207 19530
telnet 89.167.64.207 19530

# Windows (PowerShell)
Test-NetConnection 89.167.64.207 -Port 19530
```

### Check all ports
```bash
for port in 19530 19121 8080 9000 8000; do
  nc -zv 89.167.64.207 $port 2>&1 | grep -E "succeeded|failed"
done
```

### DNS/Network test
```bash
ping 89.167.64.207
traceroute 89.167.64.207
nslookup 89.167.64.207
```

---

## 📞 Need Help?

1. **Check server logs**: Ask Vamsi to run `docker compose logs -f`
2. **Check firewall**: Is port open on server? `sudo ufw status`
3. **Network issue?** Ask your network admin
4. **Python errors?** Check if `pymilvus` is installed: `pip install pymilvus`

---

## ✨ Success Checklist

- [ ] Can ping server IP
- [ ] Attu dashboard loads in browser
- [ ] Can connect with Python
- [ ] Can list collections
- [ ] Can search vectors
- [ ] Can call API endpoints

---

## 📝 After Tests Pass

Once tests pass, you can:
1. Use Milvus in your own projects
2. Point your code to `89.167.64.207:19530`
3. Call FastAPI endpoints from your apps
4. Access Attu for data browsing

---

**Ready to test? Start with Test 1! 🚀**
