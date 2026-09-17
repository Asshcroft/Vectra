## Getting Started

The entire application runs in Docker Compose. You do not need to start FastAPI, Celery, PostgreSQL, Redis, or Qdrant separately.

## Prerequisites

Install:

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Make sure Docker Desktop is running.

Verify the installation:

```bash
git --version
docker --version
docker compose version
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd Vectra
```

Replace `<repository-url>` with the URL of this GitHub repository.

### 2. Build and start the application

```bash
docker compose up --build -d
```

This command builds the application image and starts:

- FastAPI API
- Celery worker
- PostgreSQL
- Redis
- Qdrant

The first build may take several minutes because Docker downloads the dependencies and CLIP model.

The `-d` option runs the containers in the background.

### 3. Check the services

```bash
docker compose ps
```

The following services should be running:

| Service | Purpose |
|---|---|
| `api` | FastAPI application |
| `worker` | Celery background worker |
| `postgres` | Image metadata and processing statuses |
| `redis` | Celery task queue |
| `qdrant` | Image vectors and similarity search |

If a service failed to start, inspect the logs:

```bash
docker compose logs --tail=100
```

Logs for a particular service can be viewed separately:

```bash
docker compose logs api
docker compose logs worker
docker compose logs postgres
docker compose logs redis
docker compose logs qdrant
```

## Using the Application

### 1. Open Swagger UI

Open the following address:

```text
http://localhost:8000/docs
```

Swagger UI allows you to upload images, check their processing status, and perform searches without a separate frontend.

### 2. Upload an image

In Swagger UI:

1. Open `POST /upload`.
2. Click **Try it out**.
3. Click **Choose Files**.
4. Select one or multiple images.
5. Click **Execute**.

A successful request returns:

```text
202 Accepted
```

Example response:

```json
{
  "status": "accepted",
  "files": [
    {
      "image_id": "0939e28a-db06-4eff-a6c0-1168a4cf4c09",
      "stored_path": "uploads/0939e28a-db06-4eff-a6c0-1168a4cf4c09.jpg",
      "task_id": "fda54704-ceec-4b30-92bc-ed05a4eab872"
    }
  ]
}
```

The `202 Accepted` response means that the image was saved and added to the processing queue. Vector generation continues in the background.

Save the returned `image_id` because it is required to check the processing status.

### 3. Check the image status

In Swagger UI:

1. Open `GET /images/{image_id}/status`.
2. Click **Try it out**.
3. Enter the `image_id` returned by `/upload`.
4. Click **Execute**.

Possible statuses:

| Status | Meaning |
|---|---|
| `processing` | The task is waiting or running |
| `completed` | The image vector was stored successfully |
| `failed` | Processing ended with an error |

Wait until the status becomes `completed` before searching for the image.

### 4. Search for images

In Swagger UI:

1. Open `POST /search`.
2. Click **Try it out**.
3. Enter an English query, such as `red car`.
4. Click **Execute**.

Example response:

```json
[
  {
    "path": "uploads/example.jpg",
    "score": 0.8123
  }
]
```

The `score` represents the semantic similarity between the query and image. A higher score usually indicates a better match.

## Monitoring Background Processing

Follow API and Celery worker logs in real time:

```bash
docker compose logs -f api worker
```

During successful processing, the logs should show:

1. FastAPI accepts the upload.
2. Celery receives the task.
3. CLIP generates the image embedding.
4. The worker sends the vector to Qdrant.
5. The task finishes successfully.

Press `Ctrl+C` to stop following the logs. The containers will continue running.

## Running Diagnostic Scripts

Run diagnostic scripts from the root directory:

```bash
python -m scripts.check_services
python -m scripts.check_database
python -m scripts.check_process_image
```

The older CLI utilities can be run with:

```bash
python -m scripts.index_photos
python -m scripts.search
```

The required Docker services must be running before executing these scripts.

## Running the Integration Test

The integration test verifies the complete application flow:

```text
Upload → PostgreSQL → Redis → Celery → CLIP → Qdrant → Search
```

### 1. Start the Docker services

```bash
docker compose up -d
docker compose ps
```

### 2. Create a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, `(.venv)` should appear before the current terminal path.

### 4. Install development dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

### 5. Run the integration test

```powershell
python -m pytest -v tests/test_integration.py
```

Expected result:

```text
tests/test_integration.py::test_upload_process_and_search PASSED
```

The test:

1. Creates a temporary image in memory.
2. Uploads it to the API.
3. Receives its `image_id`.
4. Waits for background processing.
5. Sends a semantic search request.
6. Checks that the uploaded image appears in the results.

## Managing the Application

### Stop and remove containers

```bash
docker compose down
```

This removes the containers and network but preserves the database volumes.

### Start the application again

```bash
docker compose up -d
```

You do not need `--build` if the source code and dependencies have not changed.

### Rebuild after changing code or dependencies

```bash
docker compose up --build -d
```

Use this command after changing:

- Python source files
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yaml`

### Stop containers without removing them

```bash
docker compose stop
```

Start them again:

```bash
docker compose start
```

### Delete containers and persistent data

```bash
docker compose down -v
```

> Warning: `docker compose down -v` deletes PostgreSQL data, Qdrant vectors, and other data stored in Docker volumes.

## Useful Addresses

| Service | Address |
|---|---|
| FastAPI Swagger UI | http://localhost:8000/docs |
| FastAPI OpenAPI schema | http://localhost:8000/openapi.json |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Qdrant REST API | http://localhost:6333 |