from typing import Any, cast
from app.database import redis as redis_db

TRENDING_KEY = "trending:events"
DEFAULT_TOP_N = 10

def event_member(event_id: int) -> str:
    """Return the sorted-set member for an event, of the form event:{id}."""
    return f"event:{event_id}"

@redis_db.optional()
def record_view(event_id: int) -> float | None:
    """Increment an event's trending score and return the new score."""
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    new_score = redis_client.zincrby(
        TRENDING_KEY,
        1,
        member
    )

    return new_score

# Get the top N trending events, if no limit is provided, it defaults to 10.

@redis_db.optional(fallback=list)
def get_top_trending(limit: int = DEFAULT_TOP_N) -> list[dict[str, Any]]:
    """Return the highest-scoring events with their scores and ranks."""
    redis_client = redis_db.get_redis()

    results = cast(
        "list[tuple[str, float]]",
        redis_client.zrevrange(
            TRENDING_KEY,
            0,
            limit - 1,
            withscores=True
        )
    )

    trending_events = []

    for rank, (member, score) in enumerate(results, start=1):
        event_id = int(member.split(":")[1])

        trending_events.append(
            {
                "rank": rank,
                "event_id": event_id,
                "score": score
            }
        )

    return trending_events

# Get the score of a specific event

@redis_db.optional()
def get_event_score(event_id: int) -> float | None:
    """Return an event's trending score, or None if it has never been viewed."""
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    return redis_client.zscore(
        TRENDING_KEY,
        member
    )

@redis_db.optional()
def remove_event(event_id: int) -> None:
    """Remove an event from the trending set."""
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    redis_client.zrem(
        TRENDING_KEY,
        member
    )

@redis_db.optional()
def reset_trending() -> None:
    """Clear every entry from the trending set."""
    redis_client = redis_db.get_redis()

    redis_client.delete(TRENDING_KEY)
