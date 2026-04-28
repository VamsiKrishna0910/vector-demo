# 🚀 Quick Network Access Reference

## For Your Server

### Find Your IP
```bash
hostname -I
```
**Note it down** - this is what other users need.

### Restart Services with Network Exposure
```bash
cd /home/vamsi
docker compose down
docker compose up -d
docker compose ps
```

### Start FastAPI (Optional)
```bash
cd /home/vamsi/Vector_demo
python -m uvicorn api_service:app --host 0.0.0.0 --port 8000
```

---

## For Other Users on Your Network

### 1. Test Connection
Replace `SERVER_IP` with the actual IP:
```bash
nc -zv SERVER_IP 19530
```

### 2. Python Connection
```python
from pymilvus import connections
connections.connect(host="SERVER_IP", port=19530)
```

### 3. Access Attu Dashboard
```
http://SERVER_IP:8080
```

### 4. Use Your API
```bash
curl -X POST http://SERVER_IP:8000/qa \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question","top_k":3}'
```

---

## Network Ports

| Service | Port | Protocol |
|---------|------|----------|
| Milvus gRPC | 19530 | TCP |
| Milvus HTTP | 19121 | HTTP |
| Attu UI | 8080 | HTTP |
| MinIO | 9000 | HTTP |
| FastAPI | 8000 | HTTP |

---

## Files to Share with Users

1. **NETWORK_SETUP.md** - Full setup guide
2. **REMOTE_CONNECTION_EXAMPLE.py** - Python example code
3. **COMMANDS.md** - Available API endpoints

---

## Example Commands for Users

**Python script:**
```bash
# Copy and modify REMOTE_CONNECTION_EXAMPLE.py
cp REMOTE_CONNECTION_EXAMPLE.py my_milvus_client.py
nano my_milvus_client.py  # Change SERVER_IP
python my_milvus_client.py
```

**Direct API call:**
```bash
curl -X GET http://SERVER_IP:8080/api/v1/health/live
```

---

## Security Quick Checklist

- [ ] Know your server IP: `hostname -I`
- [ ] Firewall configured (if needed): `sudo ufw status`
- [ ] Only trusted users on network
- [ ] Consider adding API authentication
- [ ] Monitor logs: `docker compose logs -f`
