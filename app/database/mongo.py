import functools
import time
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar, cast
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure
from app.config import get_settings

P = ParamSpec("P")
R = TypeVar("R")

MongoDocument = dict[str, Any]

_client: MongoClient[MongoDocument] | None = None
_degraded = False
_last_connect_attempt = 0.0

# Specific exceptions that indicate MongoDB is unavailable, which we want to catch and degrade gracefully.
UNAVAILABLE_ERRORS = (
    RuntimeError,
    ConnectionFailure
)

# The timeouts are short because we want to fail fast and degrade gracefully if MongoDB is unavailable.
CONNECT_TIMEOUT_SECONDS = 2
SOCKET_TIMEOUT_SECONDS = 2
SERVER_SELECTION_TIMEOUT_SECONDS = 2

# The cooldown is long enough to avoid spamming the logs with repeated failures when MongoDB is down.
RECONNECT_COOLDOWN_SECONDS = 5

def init_client() -> MongoClient[MongoDocument]:
    """Initialize the MongoDB client."""
    global _client, _degraded

    client: MongoClient[MongoDocument] = MongoClient(
        get_settings().require("MONGO_URI"),
        connectTimeoutMS=CONNECT_TIMEOUT_SECONDS * 1000,
        socketTimeoutMS=SOCKET_TIMEOUT_SECONDS * 1000,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_SECONDS * 1000
    )

    try:
        client.admin.command("ping")
    except Exception:
        client.close()
        raise

    _client = client
    _degraded = False

    return _client

def get_client() -> MongoClient[MongoDocument]:
    """Return the MongoDB client, or raise if it has not been initialized."""
    if _client is None:
        _try_reconnect()

    if _client is None:
        raise RuntimeError(
            "MongoDB client has not been initialized."
        )

    return _client

def _try_reconnect() -> bool:
    """Attempt to reconnect to MongoDB if the cooldown has passed."""
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
    """Decorator to provide a fallback value when MongoDB is unavailable."""
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
                print("MongoDB is reachable again.")

            return result

        return wrapper

    return decorator

def _degrade(fn: Callable[..., Any], error: BaseException, fallback: Any) -> Any:
    """Called when an operation fails while MongoDB is unavailable."""
    global _degraded

    if not _degraded:
        _degraded = True
        print(f"MongoDB unavailable, skipping {fn.__name__}: {error}")

    return fallback() if callable(fallback) else fallback

def is_available() -> bool:
    """Best-effort view of whether MongoDB is currently usable."""
    return _client is not None and not _degraded

def get_database() -> Database[MongoDocument]:
    """Return the MongoDB database, or raise if it has not been initialized."""
    return get_client()[get_settings().require("MONGO_DB")]

def get_event_content_collection() -> Collection[MongoDocument]:
    """Return the event content collection, or raise if it has not been initialized."""
    return get_database()[get_settings().EVENT_CONTENT_COLLECTION]

def test_connection() -> dict[str, Any]:
    """Tests the connection to the MongoDB database."""
    get_client().admin.command("ping")

    return {
        "status": "connected",
        "database": get_settings().MONGO_DB
    }

def close_client() -> None:
    """Close the MongoDB client."""
    global _client

    if _client is not None:
        _client.close()
        _client = None
