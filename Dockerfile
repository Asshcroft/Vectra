FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV HF_HOME=/home/appuser/.cache/huggingface

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"

ENV HF_HUB_OFFLINE=1

COPY --chown=appuser:appuser . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]