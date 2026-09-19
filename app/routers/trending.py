# app/routers/trending.py
#
# PURPOSE
#   Trending events from the Redis sorted set.
#
# TO ADD
#   router = APIRouter(prefix="/trending", tags=["trending"])
#
#   GET /trending
#       def get_trending(limit: int = 10) -> list[dict]
#       Calls trending_service.get_top_trending(limit).
#       Response items: rank, event_id, score, and optionally title.
#       Cap limit (e.g. le=50) with Query validation.
