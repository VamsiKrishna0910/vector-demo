#!/usr/bin/env python3
"""
Network Test Suite for Remote Milvus Access
Run this script to verify you can access the shared Milvus server
"""

import sys
import socket
from urllib.request import urlopen
from urllib.error import URLError

# ============================================
# Configuration
# ============================================

SERVER_IP = "89.167.64.207"
PORTS = {
    "Milvus gRPC": 19530,
    "Milvus HTTP": 19121,
    "Attu Dashboard": 8080,
    "MinIO": 9000,
}

# ============================================
# Test Functions
# ============================================

def test_port_connectivity(host, port, service_name):
    """Test if a port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ {service_name} ({host}:{port}) - OPEN")
            return True
        else:
            print(f"❌ {service_name} ({host}:{port}) - CLOSED")
            return False
    except Exception as e:
        print(f"❌ {service_name} - ERROR: {e}")
        return False

def test_milvus_http(host, port):
    """Test Milvus HTTP health endpoint"""
    try:
        url = f"http://{host}:{port}/api/v1/health/live"
        response = urlopen(url, timeout=2)
        print(f"✅ Milvus HTTP Health Check - OK")
        return True
    except Exception as e:
        print(f"❌ Milvus HTTP Health Check - ERROR: {e}")
        return False

def test_pymilvus_connection(host, port):
    """Test PyMilvus connection"""
    try:
        from pymilvus import connections, list_collections
        
        connections.connect(host=host, port=port)
        collections = list_collections()
        connections.disconnect()
        
        print(f"✅ PyMilvus Connection - OK")
        print(f"   Collections available: {collections if collections else 'None (empty)'}")
        return True
    except Exception as e:
        print(f"❌ PyMilvus Connection - ERROR: {e}")
        return False

# ============================================
# Main Test Suite
# ============================================

print("=" * 60)
print(f"🧪 Testing Remote Milvus Access")
print(f"   Server: {SERVER_IP}")
print("=" * 60)

results = []

# Test 1: Port Connectivity
print("\n1️⃣  Port Connectivity Tests")
print("-" * 60)
for service, port in PORTS.items():
    results.append(test_port_connectivity(SERVER_IP, port, service))

# Test 2: Milvus HTTP
print("\n2️⃣  Milvus HTTP Health Check")
print("-" * 60)
results.append(test_milvus_http(SERVER_IP, PORTS["Milvus HTTP"]))

# Test 3: PyMilvus Connection
print("\n3️⃣  PyMilvus Connection")
print("-" * 60)
try:
    results.append(test_pymilvus_connection(SERVER_IP, PORTS["Milvus gRPC"]))
except ImportError:
    print("⚠️  PyMilvus not installed. Install with: pip install pymilvus")

# Test Summary
print("\n" + "=" * 60)
print(f"📊 Test Summary")
print("=" * 60)
passed = sum(results)
total = len(results)
percentage = (passed / total * 100) if total > 0 else 0

print(f"Passed: {passed}/{total} ({percentage:.0f}%)")

if passed == total:
    print("\n✅ All tests passed! You can access the remote Milvus server.")
elif passed >= total * 0.75:
    print("\n⚠️  Most tests passed, but there may be connectivity issues.")
else:
    print("\n❌ Tests failed. Check connectivity to the server.")
    print("\nTroubleshooting:")
    print("1. Is the server running? Ask admin to check: docker compose ps")
    print("2. Is firewall blocking ports? Ask network admin")
    print("3. Can you ping the server? ping " + SERVER_IP)

print("\n" + "=" * 60)
print("Next Steps:")
print("  1. Review NETWORK_SETUP.md for detailed setup")
print("  2. Review REMOTE_CONNECTION_EXAMPLE.py for code examples")
print("  3. Modify code to use server IP: " + SERVER_IP + ":19530")
print("=" * 60)
