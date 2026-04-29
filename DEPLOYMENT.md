# Organization-Wide Milvus Deployment Guide

## Overview

This is the **centralized, organization-wide** Milvus infrastructure located at `/opt/milvus-stack/`. This deployment is designed to be persistent and independent of individual user accounts, ensuring continuity even if key personnel leave the organization.

## Directory Structure

```
/opt/milvus-stack/
├── docker-compose.yml          # Docker service configuration
├── milvus_conf/
│   └── milvus.yaml            # Milvus configuration
├── volumes/
│   ├── milvus_db/             # Persistent Milvus data
│   └── minio_data/            # MinIO object storage
├── DEPLOYMENT.md              # This file
└── ADMIN_GUIDE.md             # Administrator procedures
```

## Key Features

- **Ownership**: `root:docker` (managed by organization admins)
- **Permissions**: `775` (accessible to all users in docker group)
- **Persistence**: Data stored in `/opt/milvus-stack/volumes/` survives container restarts
- **Network Exposed**: All services accessible from any machine on the network

## Quick Start

### 1. Start Services

```bash
cd /opt/milvus-stack
docker compose up -d
```

### 2. Verify Services

```bash
docker compose ps
```

Expected output:
```
CONTAINER ID   IMAGE                    STATUS              PORTS
xxx            milvusdb/milvus:v2.3.1   Up X minutes        0.0.0.0:19530->19530/tcp, 0.0.0.0:19121->19121/tcp
xxx            minio/minio:latest       Up X minutes        0.0.0.0:9000->9000/tcp
xxx            zilliz/attu:latest       Up X minutes        0.0.0.0:8080->3000/tcp
```

### 3. Access Services

| Service | URL/Address | Purpose |
|---------|------------|---------|
| Attu UI | `http://<server-ip>:8080` | Milvus Management Dashboard |
| Milvus gRPC | `<server-ip>:19530` | Python/SDK connections |
| Milvus HTTP | `<server-ip>:19121` | RESTful API access |
| MinIO | `<server-ip>:9000` | Object storage (internal) |

**Example - Replace with your server IP:**
```
http://89.167.64.207:8080    # Attu Dashboard
```

### 4. Stop Services

```bash
cd /opt/milvus-stack
docker compose down
```

### 5. Stop Services and Remove Data

```bash
cd /opt/milvus-stack
docker compose down -v
```

## Database Collections

### Available Collections

| Collection | Purpose | Size (approx) |
|-----------|---------|---------------|
| `pdf_docs` | General document Q&A | Grows with ingested PDFs |
| `mortgage_docs` | Mortgage-specific domain | Domain-specific documents |

### Backup Collections

```bash
# Backup Milvus database
cd /opt/milvus-stack/volumes
tar -czf milvus_backup_$(date +%Y%m%d_%H%M%S).tar.gz milvus_db/

# Backup MinIO storage
tar -czf minio_backup_$(date +%Y%m%d_%H%M%S).tar.gz minio_data/
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 8080
lsof -i :8080

# Or find all containers
docker ps -a
```

### Container Not Starting

```bash
# View logs
docker compose logs milvus
docker compose logs attu
docker compose logs minio

# Rebuild
docker compose up -d --force-recreate
```

### Permission Denied Error

Make sure your user is in the `docker` group:

```bash
groups $USER
```

If not in docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Maintenance

### Regular Checks

```bash
# Check disk usage
du -sh /opt/milvus-stack/volumes/

# Check container health
docker compose ps

# View recent logs
docker compose logs --tail=50 milvus
```

### Updates

To update Milvus or other service versions, edit `docker-compose.yml` and rebuild:

```bash
cd /opt/milvus-stack
docker compose pull
docker compose up -d
```

## Security Considerations

- Services are exposed to the network on all interfaces (`0.0.0.0`)
- MinIO credentials are default (`minioadmin:minioadmin`) - change if internet-facing
- Milvus has no built-in authentication - rely on network firewall
- See `NETWORK_SETUP.md` in the main project for detailed security setup

## User Access

Any user in the `docker` group can:
- View container status: `cd /opt/milvus-stack && docker compose ps`
- View logs: `docker compose logs`
- Start/stop services: `docker compose up/down`

**Users in docker group:** vamsi, raghavender (and others as added by admin)

## Admin Procedures

See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for:
- Adding new docker users
- Managing backups
- Disaster recovery
- Handover procedures
- Emergency shutdown

## Integration Examples

### Python Client Example

```python
from pymilvus import Collection, connections

# Connect to remote Milvus
connections.connect(
    alias="default",
    host="89.167.64.207",      # Replace with your server IP
    port=19530
)

# Access existing collection
collection = Collection("pdf_docs")
print(f"Collection size: {collection.num_entities}")
```

### cURL Query Example

```bash
# Query Milvus HTTP endpoint
curl -X POST http://89.167.64.207:19121/v1/vector/search \
  -H "Content-Type: application/json" \
  -d '{
    "dbName": "default",
    "collectionName": "pdf_docs",
    "vector": [0.1, 0.2, ...],
    "topk": 10
  }'
```

## Documentation Links

- [Main Project README](../README.md) - Full project overview
- [Network Setup Guide](../NETWORK_SETUP.md) - Multi-user networking setup
- [Remote Access Guide](../REMOTE_TEST_GUIDE.md) - Testing remote connectivity
- [Admin Guide](ADMIN_GUIDE.md) - Administrator procedures

## Support

For issues or questions:
1. Check container logs: `docker compose logs`
2. Verify network connectivity: `ping <server-ip>`
3. Confirm ports are open: `telnet <server-ip> 19530`
4. Review this guide's troubleshooting section

---

**Last Updated**: $(date)
**Deployment Location**: `/opt/milvus-stack/`
**Managed By**: Docker group members
