# app/services/trending_service.py
#
# PURPOSE
#   Redis Use Case 2: trending events using a sorted set.
#       Key: trending:events   Member: event:{event_id}   Score: view count
#
# TO ADD
#   Constants
#       TRENDING_KEY = "trending:events"
#       DEFAULT_TOP_N = 10
#
#   def record_view(event_id: int) -> float
#       ZINCRBY the event's score by 1 and return the new score.
#       Called on EVERY event view, including cache hits.
#
#   def get_top_trending(limit: int = DEFAULT_TOP_N) -> list[dict]
#       ZREVRANGE 0..limit-1 WITHSCORES; return
#       [{"rank": int, "event_id": int, "score": float}, ...].
#       Optionally enrich with event titles (from the cache or PostgreSQL).
#
#   def get_event_score(event_id: int) -> float | None
#       ZSCORE; used to include popularity_score in the event detail response.
#
#   def remove_event(event_id: int) -> None
#       ZREM; used when an event is deleted.
#
#   def reset_trending() -> None
#       DEL the sorted set. For demos and tests only.
#
# NOTES
#   - Optional enhancement: time-windowed trending (e.g. one key per day,
#     combined with ZUNIONSTORE) if the team wants to discuss it.
