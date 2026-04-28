"""
Example: How to Connect to Shared Milvus from Another Machine

Replace SERVER_IP with the actual IP address of the server
(e.g., 192.168.1.100)
"""

from pymilvus import connections, Collection
import os

# ============================================
# Configuration
# ============================================

SERVER_IP = "192.168.1.100"  # Replace with your server IP
MILVUS_PORT = 19530
COLLECTION_NAME = "pdf_docs"  # or "mortgage_docs"

# ============================================
# Connect to Remote Milvus
# ============================================

print(f"Connecting to Milvus at {SERVER_IP}:{MILVUS_PORT}...")

connections.connect(
    host=SERVER_IP,
    port=MILVUS_PORT,
    alias="default"
)

print("✅ Connected to Milvus!")

# ============================================
# List Available Collections
# ============================================

from pymilvus import list_collections

collections = list_collections()
print(f"\n📚 Available collections: {collections}")

# ============================================
# Access a Collection
# ============================================

try:
    collection = Collection(COLLECTION_NAME)
    print(f"\n✅ Loaded collection: {COLLECTION_NAME}")
    
    # Get collection info
    print(f"   Total documents: {collection.num_entities}")
    print(f"   Schema: {collection.schema}")
    
except Exception as e:
    print(f"❌ Error loading collection: {e}")

# ============================================
# Example: Vector Search
# ============================================

from sentence_transformers import SentenceTransformer

# Initialize embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Your query
query_text = "What is the main topic?"

# Generate embedding
query_embedding = model.encode(query_text, normalize_embeddings=True).tolist()

print(f"\n🔍 Searching for: '{query_text}'")

# Search in Milvus
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=5,
    output_fields=["source", "page", "chunk"]
)

print(f"\n✅ Found {len(results[0])} results:")
for i, hit in enumerate(results[0], 1):
    print(f"\n{i}. Score: {hit.score:.4f}")
    print(f"   Source: {hit.entity.get('source')}")
    print(f"   Page: {hit.entity.get('page')}")
    print(f"   Text: {hit.entity.get('chunk')[:100]}...")

# ============================================
# Close Connection
# ============================================

connections.disconnect(alias="default")
print("\n✅ Disconnected from Milvus")
