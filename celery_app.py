from celery import Celery
from config import REDIS_URL

celery_app = Celery("vectra", broker=REDIS_URL, include=["tasks"],)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],  # Ignore other content
    result_serializer="json",
    timezone="UTC",
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)