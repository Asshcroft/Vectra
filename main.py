import uuid
from typing import Annotated
from fastapi import FastAPI, Form, UploadFile, File
from contextlib import asynccontextmanager
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from fastapi.responses import HTMLResponse
from pathlib import Path
from PIL import Image
from pydantic import WithJsonSchema

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

# Загрузка картинок
@app.post("/upload")
async def upload(
        files: Annotated[list[BinaryUploadFile], File()]
):
    points = []
    uploaded_paths = []

    for file in files:
        file_path = UPLOAD_DIR / file.filename # Формирует конечный путь сохранения файла на сервере

        contents = await file.read()
        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # Загрузка изображения в объект PIL для передачи в нейросеть
        with Image.open(file_path) as image:
            vector = app.state.model.encode(image).tolist() # 512-мерный вектор изображения из CLIP в список

        point_id = str(uuid.uuid4())

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"path": str(file_path)}
            )
        )

        uploaded_paths.append(str(file_path))

    # Запись полученной точки (PointStruct) с ID, вектором и путем к файлу (payload) в коллекцию Qdrant
    if points:
        app.state.client.upsert(
            collection_name="my_photos",
            points=points
        )

    return {"status": "success", "uploaded_count": len(points), "paths": uploaded_paths}
