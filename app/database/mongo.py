import functools
import time
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from app.config import get_settings


_client: MongoClient | None = None
_degraded = False
_last_connect_attempt = 0.0

# Mongo holds optional event content - descriptions, speakers, schedules,
# performers, reviews - while PostgreSQL stays the system of record, so an
# outage must drop those sections rather than fail the request. OperationFailure
# is left to raise, since bad credentials or a malformed query are bugs, not
# outages.
UNAVAILABLE_ERRORS = (
    RuntimeError,
    ConnectionFailure
)

# Without these an unreachable cluster would hang every request for pymongo's
# 30 second server-selection default instead of failing fast into the degraded
# path.
CONNECT_TIMEOUT_SECONDS = 2
SOCKET_TIMEOUT_SECONDS = 2
SERVER_SELECTION_TIMEOUT_SECONDS = 2

RECONNECT_COOLDOWN_SECONDS = 5


def init_client() -> MongoClient:
    global _client, _degraded

    client = MongoClient(
        get_settings().require("MONGO_URI"),
        connectTimeoutMS=CONNECT_TIMEOUT_SECONDS * 1000,
        socketTimeoutMS=SOCKET_TIMEOUT_SECONDS * 1000,
        serverSelectionTimeoutMS=SERVER_SELECTION_TIMEOUT_SECONDS * 1000
    )

    # MongoClient never contacts the cluster on construction, so only a ping
    # proves the connection is usable.
    try:
        client.admin.command("ping")

    except Exception:
        client.close()
        raise

    _client = client
    _degraded = False

    return _client


def get_client() -> MongoClient:
    # Connect on first use so the standalone scripts under mongo/ keep working
    # without an explicit init_client() call. The cooldown inside
    # _try_reconnect stops a down cluster from being retried on every read.
    if _client is None:
        _try_reconnect()

    if _client is None:
        raise RuntimeError(
            "MongoDB client has not been initialized."
        )

    return _client


def _try_reconnect() -> bool:
    """Attempt one reconnect, at most once per cooldown window.

    Lets the app recover on its own when MongoDB was unavailable at startup, or
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
    """Return `fallback` instead of raising when MongoDB is unavailable.

    Pass a zero-argument callable for mutable fallbacks, for example
    `@optional(fallback=dict)`. Use it only on reads that enrich a response;
    writes must keep raising so a failed save is never reported as a success.
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
                print("MongoDB is reachable again.")

            return result

        return wrapper

    return decorator


def _degrade(fn, error, fallback):
    global _degraded

    if not _degraded:
        _degraded = True
        print(f"MongoDB unavailable, skipping {fn.__name__}: {error}")

    return fallback() if callable(fallback) else fallback


def is_available() -> bool:
    """Best-effort view of whether MongoDB is currently usable."""
    return _client is not None and not _degraded


def get_database() -> Database:
    return get_client()[get_settings().require("MONGO_DB")]


def get_event_content_collection() -> Collection:
    return get_database()[get_settings().EVENT_CONTENT_COLLECTION]


def test_connection() -> dict[str, Any]:
    get_client().admin.command("ping")

    return {
        "status": "connected",
        "database": get_settings().MONGO_DB
    }


def close_client() -> None:
    global _client

    if _client is not None:
        _client.close()
        _client = None
