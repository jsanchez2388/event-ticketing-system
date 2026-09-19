# app/database/redis.py
#
# PURPOSE
#   Connection setup for Redis (redis-py). Connection handling ONLY:
#   cache and trending logic live in app/services/.
#
# TO ADD
#   Module-level variable
#       _client   A single redis.Redis instance (it pools connections internally).
#
#   def init_client() -> None
#       Create redis.Redis(host=..., port=..., db=..., decode_responses=True)
#       from settings. decode_responses=True returns str instead of bytes.
#       Optionally call ping() to fail fast if Redis is not running.
#
#   def close_client() -> None
#       Close the client. Called at shutdown.
#
#   def get_redis() -> "redis.Redis"
#       Return the shared client. Used by cache_service and trending_service.
#
# NOTES
#   - This file is named redis.py, the same as the `redis` library. Inside it,
#     `import redis` still resolves to the installed library (absolute imports),
#     but elsewhere import it with an alias to avoid confusion, e.g.
#         from app.database import redis as redis_db
#   - Do NOT run this file directly from inside app/database/, or it will
#     shadow the real library.
