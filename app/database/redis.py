import redis

from app.config import REDIS_URL


_client = None


def init_client():
    global _client

    _client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
    )

    _client.ping()


def get_redis():
    if _client is None:
        raise RuntimeError(
            "Redis client has not been initialized."
        )

    return _client


def close_client():
    global _client

    if _client is not None:
        _client.close()
        _client = None