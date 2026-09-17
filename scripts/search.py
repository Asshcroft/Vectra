from idlelib import query, search

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialization
client = QdrantClient("http://localhost:6333")
model = SentenceTransformer('clip-ViT-B-32')
COLLECTION_NAME = "my_photos"

query_text = input("Enter a search query in english (for example: 'red car'): ")
query_vector = model.encode(query_text) # Converting text into vector

# Search in qdrant VDB
search_results = client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vector,
    limit=5
)

print("\nSearch results:")
for hit in search_results.points:
    path = hit.payload.get("path", "Unknown")
    score = hit.score
    print(f"File: {path} | Correspondence (Score): {score:.4f}")