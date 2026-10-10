import json
from datetime import datetime
from typing import Any
from app.config import get_settings
from app.database import redis as redis_db

# Naming convention: event:{event_id}
EVENT_CACHE_PREFIX = "event:"
DEFAULT_TTL_SECONDS = get_settings().CACHE_TTL_SECONDS

def event_cache_key(event_id: int) -> str:
    """Return the Redis key holding an event's cached detail."""
    return f"{EVENT_CACHE_PREFIX}{event_id}"

@redis_db.optional()
def get_cached_event(event_id: int) -> dict[str, Any] | None:
    """Return an event's cached detail, or None on a cache miss."""
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    cached_data = redis_client.get(key)

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

@redis_db.optional()
def set_cached_event(
    event_id: int,
    data: dict[str, Any],
    ttl: int = DEFAULT_TTL_SECONDS
) -> None:
    """Cache an event's detail, defaulting the TTL to the configured value."""
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    redis_client.set(
        key,
        json.dumps(data, default=str),
        ex=ttl
    )

    print(f"CACHE POPULATED: {key} (TTL: {ttl}s)")

@redis_db.optional()
def invalidate_event(event_id: int) -> None:
    """Drop an event's cached detail after a purchase or an admin edit."""
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    redis_client.delete(key)

@redis_db.optional(fallback=-2)
def get_ttl_remaining(event_id: int) -> int:
    """Return the seconds left on an event's cache entry."""
    redis_client = redis_db.get_redis()
    key = event_cache_key(event_id)

    return redis_client.ttl(key)

CACHE_ENABLED_KEY = "admin:event_cache_enabled"

def is_event_cache_enabled() -> bool:
    """Whether the admin cache toggle is on. Caching is on by default."""
    redis_client = redis_db.get_redis()

    value = redis_client.get(CACHE_ENABLED_KEY)

    if value is None:
        return True

    return value == "1"

def clear_event_cache() -> int:
    """Delete every cached event detail and return how many keys were removed."""
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
    """Turn the event cache on or off.

    Turning it off also clears existing event entries, but leaves the Redis
    trending data untouched.
    """
    redis_client = redis_db.get_redis()

    redis_client.set(
        CACHE_ENABLED_KEY,
        "1" if enabled else "0"
    )

    if not enabled:
        clear_event_cache()
