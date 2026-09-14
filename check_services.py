import psycopg
from redis import Redis
from config import REDIS_URL, DATABASE_URL

def check_redis():
    r = Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )
    try:
        response = r.ping()
        print(response)
    finally:
        r.close()

def check_postgres():
    with psycopg.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT current_database(), current_user"
            )
            database, user = cur.fetchone()
            print(database, user)


if __name__ == "__main__":
    check_redis()
    check_postgres()