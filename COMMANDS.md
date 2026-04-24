# Project Command Cheat Sheet

This file contains the main commands to run and maintain the Vector Demo project.

---

## 1) Go to the project folder

```bash
cd /home/vamsi/Vector_demo
```

---

## 2) Start Docker, Milvus, MinIO, and Attu

```bash
cd /home/vamsi && docker compose up -d
```

**What this does**
- Starts `milvus-standalone`
- Starts `milvus-minio`
- Starts `milvus-attu`

---

## 3) Check Docker service status

```bash
cd /home/vamsi && docker compose ps
```

---

## 4) Start FastAPI server

```bash
cd /home/vamsi/Vector_demo && .venv/bin/python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

---

## 5) Restart FastAPI cleanly

```bash
pkill -f "uvicorn api_service:app" || true
cd /home/vamsi/Vector_demo && .venv/bin/python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

---

## 6) Start FastAPI in background

```bash
pkill -f "uvicorn api_service:app" || true
cd /home/vamsi/Vector_demo && nohup .venv/bin/python -m uvicorn api_service:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
```

Check logs:

```bash
cd /home/vamsi/Vector_demo && tail -f fastapi.log
```

---

## 7) Ingest all general PDFs into `pdf_docs`

```bash
cd /home/vamsi/Vector_demo && .venv/bin/python milvus_ingest.py
```

---

## 8) Ingest one individual PDF into general collection

```bash
cd /home/vamsi/Vector_demo && PDF_GLOB='yourfile.pdf' .venv/bin/python milvus_ingest.py
```

---

## 9) Ingest one PDF into `mortgage_docs`

```bash
cd /home/vamsi/Vector_demo && MILVUS_COLLECTION=mortgage_docs PDF_GLOB='yourfile.pdf' .venv/bin/python milvus_ingest.py
```

---

## 10) Ingest all PDFs from `pdfs/mortgage/` into `mortgage_docs`

```bash
cd /home/vamsi/Vector_demo && MILVUS_COLLECTION=mortgage_docs PDF_GLOB='mortgage/*.pdf' .venv/bin/python milvus_ingest.py
```

---

## 11) Test general QA endpoint

```bash
curl -X POST http://127.0.0.1:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"query":"What is your full legal name and date of birth?","top_k":3}'
```

---

## 12) Test mortgage QA endpoint

```bash
curl -X POST http://127.0.0.1:8000/qa/mortgage \
  -H "Content-Type: application/json" \
  -d '{"query":"Can loan be approved with DTI 48% and strong reserves?","top_k":5}'
```

---

## 13) Expose API to Pega using Pinggy

```bash
ssh -p 443 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R0:localhost:8000 a.pinggy.io
```

This gives a public HTTPS URL for:
- `/qa`
- `/qa/mortgage`

---

## 14) Expose Attu dashboard using Pinggy

```bash
ssh -p 443 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R0:localhost:8080 a.pinggy.io
```

---

## 15) Open Attu dashboard directly

```text
http://89.167.64.207:8080
```

If blocked by firewall/proxy, use the Pinggy HTTPS URL instead.

---

## 16) Check if FastAPI is running

```bash
lsof -i :8000 -sTCP:LISTEN -P -n
```

---

## 17) Quick API health check

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/qa/mortgage -H "Content-Type: application/json" -d '{"query":"health check","top_k":1}'
```

If healthy, it should return:

```text
200
```

---

## 18) Stop Docker services

```bash
cd /home/vamsi && docker compose down
```

---

## 19) Check FastAPI/Uvicorn installation

```bash
cd /home/vamsi/Vector_demo && .venv/bin/python -m pip show fastapi uvicorn
```

---

## 20) Daily startup order

```bash
cd /home/vamsi && docker compose up -d
cd /home/vamsi/Vector_demo && nohup .venv/bin/python -m uvicorn api_service:app --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
ssh -p 443 -o StrictHostKeyChecking=no -o ServerAliveInterval=30 -R0:localhost:8000 a.pinggy.io
```

---

## 21) Which endpoint to use

- General QA: `POST /qa`
- Mortgage QA: `POST /qa/mortgage`
