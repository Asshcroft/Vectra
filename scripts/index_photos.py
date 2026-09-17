from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from PIL import Image
from pathlib import Path

# Initialization of model, collection_name, and client
model = SentenceTransformer('clip-ViT-B-32')
client = QdrantClient(url="http://localhost:6333")
COLLECTION_NAME = "my_photos"

# Checking whether collection already exists, if not then creating it
if not client.collection_exists(COLLECTION_NAME):
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=512, distance=Distance.COSINE),
    )

# Image indexing
image_dir = Path("images")
points = []

# Going over images' paths and indexing them
for idx, file_path in enumerate(image_dir.glob("*.*")):
    if file_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        # getting vector for the image
        image = Image.open(file_path)
        vector = model.encode(image).tolist()

        # creating a point with payloads for VDB
        point = PointStruct(
            id=idx,
            vector=vector,
            payload={"path": str(file_path)} # Metadata: Path to the image
        )
        points.append(point)
if points:
    client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"Successfully indexed images in collection {COLLECTION_NAME}, {len(points)} points")
else:
    print("No images found")







