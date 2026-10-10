import json
from datetime import datetime
from typing import Any
from app.config import get_settings
from app.database import redis as redis_db

# Naming convention: event:{event_id}
EVENT_CACHE_PREFIX = "event:"
DEFAULT_TTL_SECONDS = get_settings().CACHE_TTL_SECONDS


def event_cache_key(event_id: int) -> str:
    return f"{EVENT_CACHE_PREFIX}{event_id}"

# Reading from the cache
@redis_db.optional()
def get_cached_event(event_id: int) -> dict[str, Any] | None:
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    cached_data = redis_client.get(key)

    # If Redis doesnt have key, returns NONE. If it does, returns the JSON string. We decode it to a dict
    if cached_data is None:
        print(f"CACHE MISS: {key}")
        return None

    data: dict[str, Any] = json.loads(cached_data)
    if data.get("start_datetime"):
        data["start_datetime"] = datetime.fromisoformat(
            data["start_datetime"]
        )

    if data.get("end_datetime"):
        data["end_datetime"] = datetime.fromisoformat(
            data["end_datetime"]
        )

    return data

# We can pass in a custom TTL for the DEMO if needed. If not, it will default to the value in config.py
@redis_db.optional()
def set_cached_event(
    event_id: int,
    data: dict[str, Any],
    ttl: int = DEFAULT_TTL_SECONDS
) -> None:
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    redis_client.set(
        key,
        json.dumps(data, default=str),
        ex=ttl
    )

    print(f"CACHE POPULATED: {key} (TTL: {ttl}s)")


# Invalidate the cache for an event. This will be called after ticket purchases, admin event or ticket type updates.
@redis_db.optional()
def invalidate_event(event_id: int) -> None:
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    redis_client.delete(key)


# Return the TTL of the key to show that expiry is set. This is just for the demo.
@redis_db.optional(fallback=-2)
def get_ttl_remaining(event_id: int) -> int:
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    return redis_client.ttl(key)

# ============================================================
# ADMIN CACHE CONTROL
# ============================================================

CACHE_ENABLED_KEY = "admin:event_cache_enabled"


def is_event_cache_enabled() -> bool:
    redis_client = redis_db.get_redis()

    value = redis_client.get(CACHE_ENABLED_KEY)

    # Cache is ON by default.
    if value is None:
        return True

    return value == "1"


def clear_event_cache() -> int:
    redis_client = redis_db.get_redis()

    keys = list(
        redis_client.scan_iter(
            match=f"{EVENT_CACHE_PREFIX}*"
        )
    )

    if keys:
        redis_client.delete(*keys)

    return len(keys)


def set_event_cache_enabled(enabled: bool) -> None:
    redis_client = redis_db.get_redis()

    redis_client.set(
        CACHE_ENABLED_KEY,
        "1" if enabled else "0"
    )

    # When turning caching off, remove old event cache entries.
    # This does NOT remove Redis trending data.
    if not enabled:
        clear_event_cache()