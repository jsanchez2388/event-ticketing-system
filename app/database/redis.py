import functools
import time

import redis

from app.config import get_settings


_client = None
_degraded = False
_last_connect_attempt = 0.0

# Redis holds a cache and a ranking index, never the system of record, so an
# outage must degrade those features rather than fail the request. Both a
# missing client and a dropped connection count as unavailable; command errors
# such as ResponseError are left to raise, since those are bugs, not outages.
UNAVAILABLE_ERRORS = (
    RuntimeError,
    redis.ConnectionError,
    redis.TimeoutError
)

# Without these a partitioned Redis would hang every request instead of
# failing fast into the degraded path.
CONNECT_TIMEOUT_SECONDS = 2
SOCKET_TIMEOUT_SECONDS = 2

RECONNECT_COOLDOWN_SECONDS = 5


def init_client():
    global _client, _degraded

    client = redis.Redis.from_url(
        get_settings().REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=CONNECT_TIMEOUT_SECONDS,
        socket_timeout=SOCKET_TIMEOUT_SECONDS
    )

    # Only publish the client once the ping proves it is usable
    try:
        client.ping()

    except Exception:
        client.close()
        raise

    _client = client
    _degraded = False


def get_redis():
    if _client is None:
        raise RuntimeError(
            "Redis client has not been initialized."
        )

    return _client


def _try_reconnect() -> bool:
    """Attempt one reconnect, at most once per cooldown window.

    Lets the app recover on its own when Redis was unavailable at startup, or
    went away and came back, without restarting the server.
    """
    global _last_connect_attempt

    now = time.monotonic()

    if now - _last_connect_attempt < RECONNECT_COOLDOWN_SECONDS:
        return False

    _last_connect_attempt = now

    try:
        init_client()

    except Exception:
        return False

    return True


def optional(fallback=None):
    """Return `fallback` instead of raising when Redis is unavailable.

    Pass a zero-argument callable for mutable fallbacks, for example
    `@optional(fallback=list)`.
    """
    def decorator(fn):

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            global _degraded

            try:
                result = fn(*args, **kwargs)

            except UNAVAILABLE_ERRORS as error:
                if not _try_reconnect():
                    return _degrade(fn, error, fallback)

                try:
                    result = fn(*args, **kwargs)

                except UNAVAILABLE_ERRORS as retry_error:
                    return _degrade(fn, retry_error, fallback)

            if _degraded:
                _degraded = False
                print("Redis is reachable again.")

            return result

        return wrapper

    return decorator


def _degrade(fn, error, fallback):
    global _degraded

    if not _degraded:
        _degraded = True
        print(f"Redis unavailable, skipping {fn.__name__}: {error}")

    return fallback() if callable(fallback) else fallback


def is_available() -> bool:
    """Best-effort view of whether Redis is currently usable."""
    return _client is not None and not _degraded


def close_client():
    global _client

    if _client is not None:
        _client.close()
        _client = None
