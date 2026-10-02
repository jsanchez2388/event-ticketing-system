from fastapi import APIRouter, Query

from app.services.trending_service import get_top_trending
from app.services.event_service import get_events_by_ids


router = APIRouter(
    prefix="/trending",
    tags=["trending"],
)

# Gets ranking from Redis to get the top event IDs and fetches their info from Postgres
@router.get("")
def get_trending(
    limit: int = Query(default=10, ge=1, le=50)
) -> list[dict]:
    """
    Return the highest ranked trending events.

    Events are ranked by their popularity score stored
    in the Redis trending sorted set.
    """
    trending = get_top_trending(limit)

    if not trending:
        return []

    event_ids = [item["event_id"] for item in trending]
    events = get_events_by_ids(event_ids)

    events_by_id = {
        event["event_id"]: event
        for event in events
    }

    results = []

    for item in trending:
        event = events_by_id.get(item["event_id"])

        if event is None:
            continue

        results.append({
            "rank": item["rank"],
            "event_id": item["event_id"],
            "score": item["score"],
            "title": event["title"],
            "event_type": event["event_type"],
            "start_datetime": event["start_datetime"],
            "end_datetime": event["end_datetime"],
            "status": event["status"],
            "venue_id": event["venue_id"],
            "venue_name": event["venue_name"],
            "city": event["city"],
            "state": event["state"],
        })

    return results