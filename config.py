import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured")

if not REDIS_URL:
    raise RuntimeError("REDIS_URL is not configured")

if not QDRANT_URL:
    raise RuntimeError("QDRANT_URL is not configured")

if not QDRANT_COLLECTION:
    raise RuntimeError("QDRANT_COLLECTION is not configured")