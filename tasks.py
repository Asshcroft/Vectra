import uuid

import qdrant_client
from PIL import Image
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
from celery_app import celery_app
from config import QDRANT_COLLECTION, QDRANT_URL
from database import get_media_asset, update_media_asset_status

model = SentenceTransformer('clip-ViT-B-32')
client = QdrantClient(url=QDRANT_URL)

@celery_app.task(name="task.process_image")
def process_image(image_id: str):
    asset_id = (
    image_id
    if isinstance(image_id, uuid.UUID)
    else uuid.UUID(image_id)
    )

    try:
        asset = get_media_asset(asset_id)

        if asset is None:
            raise ValueError(f"Media asset with id={image_id} was not found. ")
        stored_path = asset["stored_path"]

        with Image.open(stored_path) as img:
            rgb_image = img.convert("RGB")
            vector = model.encode(rgb_image).tolist()

        point = PointStruct(
            id=image_id,
            vector=vector,
            payload={
                "path": stored_path,
                "media_asset_id": image_id,
                "original_filename": asset["original_filename"],
            },
        )

        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[point],
        )

        update_media_asset_status(
            image_id=asset_id,
            new_status="completed",
            qdrant_point_id=asset_id,
        )

        return {
            "status": "completed",
            "image_id": image_id,
        }
    except Exception as e:
        update_media_asset_status(
            image_id=asset_id,
            new_status="failed",
            error=str(e),
        )

        raise
