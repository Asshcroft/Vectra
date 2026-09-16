import uuid

from database import (
    create_media_asset,
    get_media_asset,
    update_media_asset_status,
    delete_media_asset,
    initialize_database,
)

def main():
    initialize_database()

    image_id = uuid.uuid4()

    print("\n1.Creating media asset...")
    created_asset = create_media_asset(
        image_id=image_id,
        original_filename="test.jpg",
        stored_path="uploads/test.jpg",
        content_type="image/jpeg",
    )
    print(created_asset)

    print("\n2.Reading media asset...")
    media_asset = get_media_asset(image_id=image_id)
    print(media_asset)

    print("\n3.Updating media asset status...")
    updated_asset = update_media_asset_status(
        image_id=image_id,
        new_status="completed",
        qdrant_point_id=image_id,
    )
    print(updated_asset)

    print("\n4.Deleting media asset...")
    deleted_asset = delete_media_asset(image_id=image_id)
    print(deleted_asset)

if __name__ == "__main__":
    main()

