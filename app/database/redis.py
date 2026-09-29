import redis

from app.config import get_settings


_client = None


def init_client():
    global _client

    client = redis.Redis.from_url(
        get_settings().REDIS_URL,
        decode_responses=True
    )

    # Only publish the client once the ping proves it is usable
    try:
        client.ping()

    except Exception:
        client.close()
        raise

    _client = client


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