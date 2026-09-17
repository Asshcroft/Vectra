## Getting Started

The entire application runs in Docker Compose. You do not need to start FastAPI, Celery, PostgreSQL, Redis, or Qdrant separately.

## Prerequisites

Install the following programs:

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

Make sure Docker Desktop is running before executing Docker commands.

You can verify the installation with:

```bash
git --version
docker --version
docker compose version
```

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Vectra
```

Replace `<your-repository-url>` with the URL of this GitHub repository.

For example:

```bash
git clone https://github.com/username/Vectra.git
cd Vectra
```

### 2. Build and start the application

```bash
docker compose up --build -d
```

This command:

1. Builds the Docker image for the API and Celery worker.
2. Starts PostgreSQL.
3. Starts Redis.
4. Starts Qdrant.
5. Starts the Celery worker.
6. Starts the FastAPI server.

The first build may take several minutes because Docker must download the Python dependencies and the CLIP model.

The `-d` option starts the containers in the background, so the terminal remains available.

### 3. Check that all services are running

```bash
docker compose ps
```

The output should contain these services:

| Service | Purpose |
|---|---|
| `api` | FastAPI application |
| `worker` | Celery background worker |
| `postgres` | Image metadata and processing statuses |
| `redis` | Celery task queue |
| `qdrant` | Image vectors and similarity search |

All services should have the `running` or `healthy` status.

If a service failed to start, inspect its logs:

```bash
docker compose logs api
docker compose logs worker
docker compose logs postgres
docker compose logs redis
docker compose logs qdrant
```

To display the latest logs from all services:

```bash
docker compose logs --tail=100
```

## Using the Application

### 1. Open Swagger UI

After the containers start, open:

```text
http://localhost:8000/docs
```

Swagger UI allows you to upload images, check their processing status, and perform text searches without creating a separate frontend.

### 2. Upload an image

In Swagger UI:

1. Open `POST /upload`.
2. Click **Try it out**.
3. Click **Choose Files**.
4. Select one or more images.
5. Click **Execute**.

A successful request returns HTTP status:

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

The `202 Accepted` response means that the image was saved and added to the processing queue. It does not mean that vector generation has already finished.

Copy the returned `image_id`. It is required to check the processing status.

### 3. Check the image status

In Swagger UI:

1. Open `GET /images/{image_id}/status`.
2. Click **Try it out**.
3. Paste the `image_id` returned by `/upload`.
4. Click **Execute**.

Possible status values:

| Status | Meaning |
|---|---|
| `processing` | The image is waiting in the queue or is being processed |
| `completed` | The embedding was created and saved in Qdrant |
| `failed` | An error occurred during processing |

Wait until the status becomes `completed` before testing search.

### 4. Search for an image

In Swagger UI:

1. Open `POST /search`.
2. Click **Try it out**.
3. Enter an English search query, for example `red car`.
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

The `score` value represents the similarity between the text query and the image. A higher score usually means a better match.

## Monitoring Background Processing

To follow FastAPI and Celery logs in real time:

```bash
docker compose logs -f api worker
```

During a successful upload, the logs should show:

1. FastAPI accepts the upload.
2. Celery receives the task.
3. CLIP generates the image embedding.
4. The worker sends the vector to Qdrant.
5. The task finishes successfully.

Press `Ctrl+C` to stop following the logs. This only closes the log output; the containers continue running.

## Running the Integration Test

The integration test checks the complete application flow:

```text
Upload → PostgreSQL → Redis → Celery → CLIP → Qdrant → Search
```

### 1. Keep the Docker services running

Verify their state:

```bash
docker compose ps
```

### 2. Create a Python virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
```

### 3. Activate the environment

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should display `(.venv)` before the current path.

### 4. Install test dependencies

```powershell
python -m pip install -r requirements-dev.txt
```

The development requirements include the main application dependencies and Pytest.

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
2. Uploads it to the running API.
3. Receives its `image_id`.
4. Waits until background processing is complete.
5. Sends a semantic search request.
6. Checks that the uploaded image appears in the results.

## Stopping the Application

### Stop all containers

```bash
docker compose down
```

This removes the containers and network but preserves the PostgreSQL, Redis, and Qdrant volumes.

### Start the application again

```bash
docker compose up -d
```

You do not need to use `--build` if the source code and dependencies have not changed.

### Rebuild after changing the code

```bash
docker compose up --build -d
```

Use this command after changing:

- Python source files;
- `requirements.txt`;
- `Dockerfile`;
- Docker Compose configuration.

### Stop containers without removing them

```bash
docker compose stop
```

Start the stopped containers again:

```bash
docker compose start
```

### Delete containers and stored data

```bash
docker compose down -v
```

> Warning: the `-v` option deletes the project volumes, including PostgreSQL records and Qdrant vectors. Use it only when you intentionally want to reset the project.

## Useful Addresses

| Service | Address |
|---|---|
| FastAPI Swagger UI | http://localhost:8000/docs |
| FastAPI OpenAPI schema | http://localhost:8000/openapi.json |
| Qdrant Dashboard | http://localhost:6333/dashboard |
| Qdrant REST API | http://localhost:6333 |