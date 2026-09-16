import time
from celery_app import celery_app

@celery_app.task(name="tasks.test_task")
def test_task(message: str):
    print(f"Task started: {message}")

    time.sleep(5)

    print(f"Task completed: {message}")

    return {
        "status": "Completed",
        "message": message,
    }
