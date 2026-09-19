# app/services/cache_service.py
#
# PURPOSE
#   Redis Use Case 1: event cache using the cache-aside pattern.
#       Request -> check Redis -> HIT: return
#                              -> MISS: query DBs -> store with TTL -> return
#   The orchestration (querying the databases on a miss) happens in
#   event_service.py. This module only reads, writes, and deletes cache entries.
#
# TO ADD
#   Constants
#       EVENT_CACHE_PREFIX = "event:"      (key format: event:{event_id})
#       DEFAULT_TTL_SECONDS                (from settings.cache_ttl_seconds;
#                                           justify the chosen value in the report)
#
#   def event_cache_key(event_id: int) -> str
#       Build the Redis key for an event.
#
#   def get_cached_event(event_id: int) -> dict | None
#       GET the key; return the decoded JSON dict, or None on a cache miss.
#       Log/print "CACHE HIT" or "CACHE MISS" for the demo.
#
#   def set_cached_event(event_id: int, data: dict, ttl: int = DEFAULT_TTL_SECONDS) -> None
#       Serialize to JSON and store with an expiry (SET with ex=ttl).
#       Log/print "CACHE POPULATED".
#
#   def invalidate_event(event_id: int) -> None
#       DEL the key. Call after ticket purchases, admin event or ticket type
#       updates, and new reviews so users do not see stale data.
#
#   def get_ttl_remaining(event_id: int) -> int  (optional, for the demo)
#       Return the TTL of the key to show that expiry is set.
#
# NOTES
#   - Redis is NOT the system of record: everything cached here must be
#     rebuildable from PostgreSQL + MongoDB.
#   - Import the client with an alias: from app.database import redis as redis_db
