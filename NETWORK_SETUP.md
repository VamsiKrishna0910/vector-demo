# 🌐 Network Setup & Multi-User Access Guide

This guide explains how to expose Docker, Milvus, and Attu to your host network so other users and projects can access them.

---

## 📡 What's Now Exposed to Your Network

After the updates, your services are accessible on all network interfaces:

| Service | Port | URL for Network Users |
|---------|------|----------------------|
| **Milvus gRPC** | 19530 | `<your-server-ip>:19530` |
| **Milvus HTTP** | 19121 | `<your-server-ip>:19121` |
| **Attu UI** | 8080 | `http://<your-server-ip>:8080` |
| **MinIO** | 9000 | `http://<your-server-ip>:9000` |
| **FastAPI** | 8000 | `http://<your-server-ip>:8000` (if running) |

---

## 🔍 Find Your Server's IP Address

### On Your Server (Linux)

```bash
hostname -I
```

**Output example:** `192.168.1.100 10.0.0.50`

Pick the IP on your internal network (usually `192.168.x.x` or `10.x.x.x`)

### On Other Machines

**Linux/Mac:**
```bash
ping <hostname-of-your-server>
nslookup <hostname-of-your-server>
```

**Windows:**
```cmd
ping <hostname-of-your-server>
```

---

## 🚀 Restart Services to Apply Changes

Since `docker-compose.yml` has been updated, restart the services:

```bash
cd /home/vamsi

# Stop current services
docker compose down

# Start with new network bindings
docker compose up -d

# Verify all services are running
docker compose ps
```

---

## 👥 For Other Users on Your Network

### Step 1: Find Your Server's IP

Ask you or find it using:
```bash
ping <your-server-name>
```

Example: `192.168.1.100`

### Step 2: Test Connection to Milvus

```bash
# Test gRPC port
nc -zv 192.168.1.100 19530

# Test HTTP port
curl -X GET http://192.168.1.100:19121/api/v1/health/live
```

### Step 3: Update Their Connection String

In their Python code or `.env` file:

```env
# Instead of localhost
MILVUS_URI=tcp://192.168.1.100:19530

# Or for HTTP
MILVUS_HTTP_URI=http://192.168.1.100:19121
```

### Step 4: Use Your Vector Demo API

Other users can now call your FastAPI endpoints:

**Start FastAPI on your server:**
```bash
cd /home/vamsi/Vector_demo
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

**From another machine:**
```bash
curl -X POST http://192.168.1.100:8000/qa \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the main topic?",
    "top_k": 3
  }'
```

---

## 💻 Python Example for Remote Users

Other users can use your Milvus like this:

```python
from pymilvus import connections, Collection

# Connect to remote Milvus
connections.connect(
    host="192.168.1.100",  # Your server IP
    port=19530
)

# Access collections
collection = Collection("pdf_docs")

# Search
results = collection.search(
    data=[your_embedding],
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=5
)
```

---

## 🔌 Docker Access for Other Users

### Option 1: Add Users to Docker Group

If other users have accounts on your server:

```bash
# Add user to docker group
sudo usermod -aG docker username

# User must log out and log back in
# Then they can run:
docker ps
docker compose ps
```

### Option 2: Share Docker Commands (No Direct Access)

Users don't have direct Docker access, but can:
1. Clone your project
2. Use pre-made scripts you provide
3. Call your API endpoints (doesn't require Docker knowledge)

---

## 🌐 Attu Web UI for Network Users

Other users can access the Milvus dashboard directly:

1. Open browser on their machine
2. Go to: `http://<your-server-ip>:8080`
3. Browse collections and data

**Example:** `http://192.168.1.100:8080`

---

## 🔐 Security Considerations

### Open Network = Security Risk

Since services are now exposed to the network, consider:

#### 1. **Firewall Rules** (Recommended)

Only allow specific IPs:

```bash
# Example: Allow only 192.168.1.0/24 subnet
sudo ufw allow from 192.168.1.0/24 to any port 19530
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

#### 2. **API Authentication**

Add authentication to your FastAPI:

```python
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

app = FastAPI()
security = HTTPBasic()

@app.post("/qa")
async def qa(query: str, credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "user" or credentials.password != "pass":
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Your code here
```

#### 3. **Network Isolation**

Restrict port access at the router level if possible.

#### 4. **Monitoring**

Log all API requests:

```bash
# View FastAPI logs
tail -f fastapi.log

# Check which IPs connected
docker compose logs attu | grep "connection"
```

---

## 📝 Create a Network Guide for Users

Create a file `NETWORK_SETUP.md` in your GitHub to share with other users:

```markdown
# Connecting to Shared Milvus

## Server Details

- **Server IP**: 192.168.1.100 (ask your admin)
- **Milvus gRPC**: 192.168.1.100:19530
- **Milvus HTTP**: 192.168.1.100:19121
- **Attu Dashboard**: http://192.168.1.100:8080
- **API Endpoints**: http://192.168.1.100:8000/qa

## Quick Start

### Python Connection

```python
from pymilvus import connections
connections.connect(host="192.168.1.100", port=19530)
```

### API Usage

```bash
curl -X POST http://192.168.1.100:8000/qa \
  -d '{"query": "Your question", "top_k": 3}'
```
```

---

## ✅ Verification Checklist

After exposing services:

- [ ] Restarted Docker services (`docker compose up -d`)
- [ ] Found server's IP address
- [ ] Tested connectivity from another machine (`nc` or `curl`)
- [ ] Updated documentation with IP address
- [ ] Tested network connection from Python client
- [ ] Tested Attu UI access from another machine
- [ ] (Optional) Configured firewall rules
- [ ] (Optional) Added API authentication

---

## 🧪 Test from Another Machine

```bash
# Test Milvus gRPC
python3 << EOF
from pymilvus import connections
try:
    connections.connect(host="192.168.1.100", port=19530)
    print("✅ Milvus connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
EOF

# Test Attu UI
curl -s http://192.168.1.100:8080 | head -20

# Test FastAPI (if running)
curl http://192.168.1.100:8000/docs
```

---

## 🆘 Troubleshooting

### "Connection refused" error

1. Verify services are running: `docker compose ps`
2. Check firewall: `sudo ufw status`
3. Verify correct IP: `hostname -I`
4. Test port connectivity: `nc -zv 192.168.1.100 19530`

### Port already in use

```bash
# Check what's using the port
lsof -i :19530

# Kill process if needed
kill <PID>
```

### Network unreachable

1. Check if machines are on same network: `ping <server-ip>`
2. Check router configuration
3. Disable VPN if applicable
4. Ask network admin for permission

---

## 📊 Example Network Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Local Network                        │
│              (192.168.1.0/24)                        │
│                                                      │
│  Your Server                    Other Users          │
│  192.168.1.100                  192.168.1.x          │
│  ┌──────────────────┐                                │
│  │ Docker Compose   │◄──────────────────────────────►│
│  │ ┌──────────────┐ │                                │
│  │ │ Milvus:19530 │ │                                │
│  │ │ HTTP:19121   │ │                                │
│  │ │ Attu:8080    │ │                                │
│  │ │ MinIO:9000   │ │                                │
│  │ │ FastAPI:8000 │ │                                │
│  │ └──────────────┘ │                                │
│  └──────────────────┘                                │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Next Steps

1. **Update GitHub** with new network details
2. **Create NETWORK_SETUP.md** for users
3. **Share server IP** with your team
4. **Monitor usage** and logs
5. **(Optional) Add authentication** for security

---

## 📞 Support

For network issues, check:
- Server IP: `hostname -I`
- Services running: `docker compose ps`
- Firewall: `sudo ufw status`
- Logs: `docker compose logs -f`

---

**Your Milvus is now shared! 🎉**
