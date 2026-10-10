import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast
import redis
from app.config import get_settings

P = ParamSpec("P")
R = TypeVar("R")

_client: redis.Redis | None = None
_degraded = False
_last_connect_attempt = 0.0

# Specific exceptions that indicate Redis is unavailable, which we want to catch and degrade gracefully.
UNAVAILABLE_ERRORS = (
    RuntimeError,
    redis.ConnectionError,
    redis.TimeoutError
)

# The timeouts are short because we want to fail fast and degrade gracefully if Redis is unavailable.
CONNECT_TIMEOUT_SECONDS = 2
SOCKET_TIMEOUT_SECONDS = 2

RECONNECT_COOLDOWN_SECONDS = 5

def init_client() -> None:
    """Initialize the Redis client."""
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

def get_redis() -> redis.Redis:
    """Return the Redis client, or raise if it has not been initialized."""
    if _client is None:
        raise RuntimeError(
            "Redis client has not been initialized."
        )

    return _client

def _try_reconnect() -> bool:
    """
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

def optional(
    fallback: Any = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to provide a fallback value when Redis is unavailable."""
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            global _degraded

            try:
                result = fn(*args, **kwargs)

            except UNAVAILABLE_ERRORS as error:
                if not _try_reconnect():
                    return cast(R, _degrade(fn, error, fallback))

                try:
                    result = fn(*args, **kwargs)

                except UNAVAILABLE_ERRORS as retry_error:
                    return cast(R, _degrade(fn, retry_error, fallback))

            if _degraded:
                _degraded = False
                print("Redis is reachable again.")

            return result

        return wrapper

    return decorator

def _degrade( fn: Callable[..., Any], error: BaseException, fallback: Any) -> Any:
    """Called when an operation fails while Redis is unavailable."""
    global _degraded

    if not _degraded:
        _degraded = True
        print(f"Redis unavailable, skipping {fn.__name__}: {error}")

    return fallback() if callable(fallback) else fallback

def is_available() -> bool:
    """Best-effort view of whether Redis is currently usable."""
    return _client is not None and not _degraded

def close_client() -> None:
    """Close the Redis client."""
    global _client

    if _client is not None:
        _client.close()
        _client = None
