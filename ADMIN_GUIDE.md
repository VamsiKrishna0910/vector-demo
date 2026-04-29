# Milvus Stack - Administrator Guide

## Overview

This guide covers administrative procedures for the organization-wide Milvus deployment at `/opt/milvus-stack/`. It's designed to help admins manage the infrastructure, handover procedures, and emergency scenarios.

## Directory Ownership & Permissions

### Current Setup

```bash
# View ownership
ls -ld /opt/milvus-stack/

# Expected output:
# drwxrwxr-x root docker /opt/milvus-stack/
```

### Permission Model

- **Owner**: `root` (system administrator)
- **Group**: `docker` (managed users)
- **Permissions**: `775` (read, write, execute for group members)
- **Volumes**: Same permissions - ensures data persistence access

## Docker Group Management

### Adding Users to Docker Group

```bash
# Add user to docker group
sudo usermod -aG docker <username>

# Verify (user must log out and back in, or use newgrp)
groups <username>

# Current members (expected)
# vamsi
# raghavender
```

### Verifying Group Access

```bash
# As the new user, verify docker access
docker ps

# Should see running containers without sudo
```

### Removing Users from Docker Group

```bash
# Remove user from docker group
sudo delgroup <username> docker

# Verify removal
groups <username>
```

## Starting & Stopping Services

### Standard Start

```bash
cd /opt/milvus-stack
docker compose up -d
```

### Start with Logs Display

```bash
cd /opt/milvus-stack
docker compose up        # Press Ctrl+C to detach after startup
```

### Graceful Shutdown

```bash
cd /opt/milvus-stack
docker compose down
```

### Emergency Stop (kill containers)

```bash
cd /opt/milvus-stack
docker compose kill
```

### Complete Shutdown (remove volumes)

```bash
cd /opt/milvus-stack
docker compose down -v
```

⚠️ **WARNING**: `down -v` removes persistent data!

## Monitoring & Health Checks

### Container Status

```bash
cd /opt/milvus-stack
docker compose ps
```

### View Container Logs

```bash
# All services
docker compose logs

# Specific service
docker compose logs milvus
docker compose logs attu
docker compose logs minio

# Last N lines with follow
docker compose logs --tail=50 -f milvus
```

### Resource Usage

```bash
# Docker resource usage
docker stats

# Disk usage
du -sh /opt/milvus-stack/volumes/
du -sh /opt/milvus-stack/volumes/milvus_db/
du -sh /opt/milvus-stack/volumes/minio_data/
```

### Port Verification

```bash
# Check if ports are listening
lsof -i -P -n | grep LISTEN

# Specific ports
netstat -tuln | grep -E ':(8080|19530|19121|9000)'
```

## Backup & Recovery

### Full System Backup

```bash
cd /opt/milvus-stack
BACKUP_DIR="/backup/milvus/$(date +%Y%m%d_%H%M%S)"

# Create backup directory
sudo mkdir -p "$BACKUP_DIR"

# Backup volumes
sudo tar -czf "$BACKUP_DIR/volumes.tar.gz" volumes/

# Backup configuration
sudo tar -czf "$BACKUP_DIR/config.tar.gz" docker-compose.yml milvus_conf/

# List backup
ls -lh "$BACKUP_DIR/"
```

### Backup Only Database (Milvus)

```bash
cd /opt/milvus-stack/volumes
tar -czf milvus_backup_$(date +%Y%m%d_%H%M%S).tar.gz milvus_db/
ls -lh *.tar.gz
```

### Restore from Backup

```bash
# Stop services first
cd /opt/milvus-stack
docker compose down

# Restore volumes
sudo rm -rf volumes/
sudo tar -xzf /path/to/volumes.tar.gz

# Restart
docker compose up -d
```

### Scheduled Backups

Create `/etc/cron.d/milvus-backup`:

```bash
# Backup Milvus daily at 2 AM
0 2 * * * root cd /opt/milvus-stack/volumes && tar -czf milvus_backup_$(date +\%Y\%m\%d).tar.gz milvus_db/ && find . -name "milvus_backup_*.tar.gz" -mtime +30 -delete
```

## Handover Procedures

### Transition to New Admin

**Current Admin** runs:

```bash
# Document current state
cd /opt/milvus-stack
docker compose ps > handover_status.txt
du -sh volumes/ > handover_sizes.txt

# Create full backup
BACKUP_DIR="/backup/milvus/handover_$(date +%Y%m%d_%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo tar -czf "$BACKUP_DIR/volumes.tar.gz" volumes/
sudo tar -czf "$BACKUP_DIR/config.tar.gz" docker-compose.yml milvus_conf/

echo "Handover backup created at: $BACKUP_DIR"
```

**New Admin** does:

```bash
# Verify access
groups $USER
sudo usermod -aG docker $USER    # If needed
newgrp docker                    # Activate immediately

# Test docker access
cd /opt/milvus-stack
docker compose ps

# Review backup documentation
cat /backup/milvus/handover_*/config.tar.gz | tar -tzf - | head -20
```

### Verify Handover Success

```bash
# Test all services
cd /opt/milvus-stack
docker compose down && sleep 5 && docker compose up -d

# Wait for services to start (30-60 seconds)
sleep 30

# Verify all containers running
docker compose ps | grep "Up"

# Test connectivity
curl -X GET http://localhost:8080/ 2>/dev/null | head -c 50
```

## Emergency Procedures

### Service Crash Recovery

```bash
# View error logs
docker compose logs milvus | tail -50

# Restart failed service
docker compose restart milvus

# Full rebuild if persistent issues
docker compose down
docker compose up -d
```

### Out of Disk Space

```bash
# Check disk usage
df -h /opt/milvus-stack/

# Identify large files
du -sh /opt/milvus-stack/volumes/*

# Stop services if space critical
cd /opt/milvus-stack
docker compose down

# Clean old backups (if applicable)
find /backup/milvus/ -name "*.tar.gz" -mtime +90 -delete
```

### Container Port Conflict

```bash
# Find what's using the port
lsof -i :8080

# Solution A: Kill conflicting process
kill -9 <PID>

# Solution B: Change docker-compose.yml port mapping
# Edit /opt/milvus-stack/docker-compose.yml ports section
# Then rebuild:
docker compose down
docker compose up -d
```

### Data Corruption Recovery

```bash
# Stop services
cd /opt/milvus-stack
docker compose down

# Restore from backup
sudo rm -rf volumes/milvus_db
sudo tar -xzf /backup/milvus/latest_backup/volumes.tar.gz

# Restart
docker compose up -d

# Verify
docker compose logs milvus | grep -i "connected\|ready"
```

## Configuration Changes

### Editing Milvus Configuration

```bash
# Edit configuration
sudo nano /opt/milvus-stack/milvus_conf/milvus.yaml

# Restart to apply changes
cd /opt/milvus-stack
docker compose restart milvus

# Verify changes applied
docker compose logs milvus | grep "config\|parameter"
```

### Changing Docker Compose Settings

```bash
# Edit docker compose file
sudo nano /opt/milvus-stack/docker-compose.yml

# Verify syntax
docker compose config > /dev/null && echo "✅ Config valid"

# Apply changes (no downtime for most changes)
cd /opt/milvus-stack
docker compose up -d

# Full restart if needed
docker compose down && docker compose up -d
```

## Networking & Firewall

### Firewall Rules (Ubuntu UFW)

```bash
# Allow Milvus gRPC
sudo ufw allow 19530/tcp comment "Milvus gRPC"

# Allow Milvus HTTP
sudo ufw allow 19121/tcp comment "Milvus HTTP"

# Allow Attu Dashboard
sudo ufw allow 8080/tcp comment "Attu Dashboard"

# Restrict MinIO to internal only (if needed)
# sudo ufw allow from 192.168.1.0/24 to any port 9000 comment "MinIO Internal"

# Verify rules
sudo ufw status numbered
```

### Testing Connectivity

```bash
# From another machine, test ports
telnet <server-ip> 19530    # Should connect
telnet <server-ip> 8080     # Should connect
telnet <server-ip> 19121    # Should connect

# Or using Python
python3 -c "
import socket
ports = {'Milvus gRPC': 19530, 'Milvus HTTP': 19121, 'Attu': 8080}
for name, port in ports.items():
    try:
        socket.create_connection(('<server-ip>', port), timeout=2)
        print(f'✅ {name} ({port}): OPEN')
    except:
        print(f'❌ {name} ({port}): CLOSED')
"
```

## Updating Services

### Update Milvus Version

```bash
cd /opt/milvus-stack

# Backup before updating
sudo tar -czf volumes/milvus_backup_pre_update_$(date +%Y%m%d).tar.gz volumes/milvus_db/

# Update image and restart
docker compose pull
docker compose up -d --force-recreate

# Verify
docker compose logs milvus | head -20
```

### Verify Services After Update

```bash
# Services should be UP
docker compose ps

# Check logs for errors
docker compose logs | grep -i "error\|fail" | tail -10

# Test connectivity
curl -X GET http://localhost:8080/ 2>/dev/null | head -c 50 && echo "✅ Attu responsive"
```

## Documentation & Runbooks

### Creating Custom Runbooks

```bash
# Document current procedures
cat > /opt/milvus-stack/RUNBOOK_CUSTOM.md << 'EOF'
# Organization-Specific Procedures

## Collections Management
- ...

## Performance Tuning
- ...
EOF
```

### Maintenance Checklist (Monthly)

```bash
# First Monday of each month
- [ ] Check disk space: du -sh /opt/milvus-stack/volumes/
- [ ] Review backup integrity: ls -lh /backup/milvus/
- [ ] Check for updates: docker compose pull && docker images
- [ ] Review logs for errors: docker compose logs | grep -i error
- [ ] Test disaster recovery with backup
- [ ] Document any changes made
```

## Contact & Escalation

When handover occurs, document:

```bash
cat > /opt/milvus-stack/ADMIN_CONTACT.txt << 'EOF'
# Milvus Stack Administration Contact

Primary Admin:     [Name, Email, Phone]
Secondary Admin:   [Name, Email, Phone]
Backup Location:   [Path, Contact]
Last Verified:     [Date]

## Escalation Path
1. First Admin: [Contact]
2. Second Admin: [Contact]
3. IT Department: [Contact]
EOF
```

---

**Last Updated**: [Date]
**Version**: 1.0
**For Issues**: Contact admin team or review /opt/milvus-stack/ logs
