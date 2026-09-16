import psycopg
from psycopg.rows import dict_row
from config import DATABASE_URL


CREATE_MEDIA_ASSETS_TABLE = """
CREATE TABLE IF NOT EXISTS media_assets (
    id UUID PRIMARY KEY,
    original_filename VARCHAR(255) NOT NULL,
    stored_path TEXT NOT NULL,
    content_type VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    qdrant_point_id UUID,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_media_asset_status
        CHECK (status IN ('processing', 'completed', 'failed'))
);       
"""


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def initialize_database():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_MEDIA_ASSETS_TABLE)


def create_media_asset(image_id, original_filename, stored_path, content_type):
    query = """
    INSERT INTO media_assets (
        id,
        original_filename,
        stored_path,
        content_type,
        status
    )
    VALUES (%s, %s, %s, %s, 'processing')
    RETURNING *;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (image_id, original_filename, stored_path, content_type))
            return cur.fetchone()


def get_media_asset(image_id):
    query = """
    SELECT *
    FROM media_assets
    WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (image_id,))
            return cur.fetchone()


def update_media_asset_status(image_id, new_status, qdrant_point_id=None, error=None):
    query = """
    UPDATE media_assets
    SET
        status = %s,
        qdrant_point_id = %s,
        error = %s,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = %s
    RETURNING *;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (new_status, qdrant_point_id, error, image_id))
            return cur.fetchone()


def delete_media_asset(image_id):
    query = """
    DELETE FROM media_assets
    WHERE id = %s;
    """

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (image_id,))

if __name__ == "__main__":
    initialize_database()
    print("Database initialized")