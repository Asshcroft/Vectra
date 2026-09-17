import uuid
import aiofiles
from typing import Annotated
from fastapi import FastAPI, Form, UploadFile, File, HTTPException, status
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from fastapi.responses import HTMLResponse
from pathlib import Path
from pydantic import WithJsonSchema
from database import update_media_asset_status, create_media_asset, get_media_asset
from tasks import process_image

BinaryUploadFile = Annotated[
    UploadFile,
    WithJsonSchema({
        "type": "string",
        "format": "binary",
    }),
]

# Менеджер контекста жизненного цикла приложения. Загружаем модель и клиент
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    model = SentenceTransformer('clip-ViT-B-32')
    client = QdrantClient(url="http://localhost:6333")
    app.state.model = model
    app.state.client = client
    yield
    # Закрытие соединения с ВБД
    app.state.client.close()

app = FastAPI(lifespan=lifespan)

# Обратобчик глав страницы с HTML формой
@app.get("/", response_class=HTMLResponse)
async def main():
    return """
    <form action="/search" method="post">
        <input name="query" type="text" placeholder="Введите запрос...">
        <input type="submit" value="Искать">
    </form>
    """

# Извлечение текстового запроса из тела HTML
@app.post("/search")
async def search(
        query: Annotated[str, Form(...)]
):
    model = app.state.model
    client = app.state.client

    vector = model.encode(query).tolist()
    # Векторный поиск с лимитом в выход пяти наиболее похожих изображений
    results = client.query_points(
        collection_name="my_photos",
        query=vector,
        limit=5
    )
    # Извлечение пути к файлу изображения из метаданных (payload), сохраненных на этапе индексации
    return [{"path": hit.payload.get("path"), "score": hit.score} for hit in results.points]

# Directory so save locally
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
CHUNK_SIZE = 1024 * 1024
# Загрузка картинок
@app.post("/upload", status_code=status.HTTP_202_ACCEPTED,)
async def upload(
        files: Annotated[list[BinaryUploadFile], File()]
):
    uploaded_files = []

    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must have a filename",
            )

        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not allowed file type, {suffix}",
            )

        image_id = uuid.uuid4()

        stored_filename = f"{image_id}{suffix}"
        file_path = UPLOAD_DIR / stored_filename

        async with aiofiles.open(file_path, mode="wb") as buffer:
            while chunk := await file.read(CHUNK_SIZE):
                await buffer.write(chunk)

        create_media_asset(
            image_id=image_id,
            original_filename=file.filename,
            stored_path=str(file_path),
            content_type=file.content_type,
        )

        try:
            task = process_image.delay(image_id=image_id)
        except Exception as error:
            update_media_asset_status(
                image_id=image_id,
                new_status="failed",
                error=f"Could not send task to Celery:{error}",
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Background processing task is unavailable",
            ) from error

        uploaded_files.append(
            {
                "image_id": image_id,
                "original_filename": file.filename,
                "stored_path": str(file_path),
                "status": "processing",
                "task_id": task.id,
            }
        )

    return {
        "status": "completed",
        "uploaded_count": len(uploaded_files),
        "files": uploaded_files,
    }

@app.get("/images/{image_id}/status")
def get_status(image_id: uuid.UUID):
    asset = get_media_asset(image_id=image_id)

    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No asset with id {image_id}",
        )

    qdrant_point_id = asset["qdrant_point_id"]

    return {
        "image_id": image_id,
        "original_filename": asset["original_filename"],
        "status": asset["status"],
        "qdrant_point_id": (
            str(qdrant_point_id)
            if qdrant_point_id is not None
            else None
        ),
        "error": asset["error"],
        "created_at": asset["created_at"],
        "updated_at": asset["updated_at"],
    }