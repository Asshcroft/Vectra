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

if __name__ == "__main__":
    initialize_database()
    print("Database initialized")