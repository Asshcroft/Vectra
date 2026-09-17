import uuid
from pathlib import Path
from database import create_media_asset
from tasks import process_image

def main():
    image_path = Path("images/cat.jpg")

    if not image_path.exists():
        raise FileNotFoundError(
            f"File not found at {image_path}"
        )

    image_id = uuid.uuid4()

    create_media_asset(
        image_id=image_id,
        original_filename=image_path.name,
        stored_path=str(image_path),
        content_type="image/jpeg",
    )

    task = process_image.delay(image_id=str(image_id))

    print(f"Image id: {image_id}")
    print(f"Celery task id: {task.id}")
    print(f"Image was sent for background task")

if __name__ == "__main__":
    main()
