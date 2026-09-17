import os
import time
from io import BytesIO
import httpx
import pytest
from PIL import Image

API_URL = os.getenv(
    "TEST_API_URL",
    "http://localhost:8000",
)

PROCESSING_TIMEOUT = 30

def create_test_image() -> bytes:
    image = Image.new(
        mode="RGB",
        size=(128, 128),
        color=(255, 0, 255),
    )

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return buffer.getvalue()


def wait_until_completed(
    client: httpx.Client,
    image_id: str,
) -> dict:
    deadline = time.monotonic() + PROCESSING_TIMEOUT

    while time.monotonic() < deadline:
        response = client.get(
            f"/images/{image_id}/status"
        )

        assert response.status_code == 200, response.text

        asset = response.json()

        if asset["status"] == "completed":
            return asset

        if asset["status"] == "failed":
            pytest.fail(
                f"Image processing failed: {asset['error']}"
            )

        time.sleep(0.5)

    pytest.fail(
        f"Image {image_id} was not processed "
        f"within {PROCESSING_TIMEOUT} seconds"
    )


def test_upload_process_and_search():
    image_bytes = create_test_image()

    with httpx.Client(
            base_url=API_URL,
            timeout=30,
    ) as client:
        upload_response = client.post(
            "/upload",
            files=[
                (
                    "files",
                    (
                        "integration-test-magenta.png",
                        image_bytes,
                        "image/png",
                    ),
                )
            ],
        )

        assert upload_response.status_code == 202, (
            upload_response.text
        )

        upload_data = upload_response.json()

        assert upload_data["status"] == "accepted"
        assert upload_data["uploaded_count"] == 1

        uploaded_file = upload_data["files"][0]

        image_id = uploaded_file["image_id"]
        stored_path = uploaded_file["stored_path"]

        completed_asset = wait_until_completed(
            client=client,
            image_id=image_id,
        )

        assert completed_asset["status"] == "completed"
        assert completed_asset["qdrant_point_id"] == image_id
        assert completed_asset["error"] is None

        search_response = client.post(
            "/search",
            data={
                "query": (
                    "a completely plain bright magenta "
                    "square with no objects"
                )
            },
        )

        assert search_response.status_code == 200, (
            search_response.text
        )

        search_results = search_response.json()

        assert isinstance(search_results, list)
        assert len(search_results) > 0

        result_paths = [
            result["path"]
            for result in search_results
        ]

        assert stored_path in result_paths