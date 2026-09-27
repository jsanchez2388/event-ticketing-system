from app.database import redis as redis_db


TRENDING_KEY = "trending:events"
DEFAULT_TOP_N = 10

# Naming convention: event:{event_id}
def event_member(event_id: int) -> str:
    return f"event:{event_id}"



def record_view(event_id: int) -> float:
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    # Increments the score of the event by 1
    new_score = redis_client.zincrby(
        TRENDING_KEY,
        1,
        member
    )

    return new_score


# Get the top N trending events, if no limit is provided, it defaults to 10. 
def get_top_trending(limit: int = DEFAULT_TOP_N) -> list[dict]:
    redis_client = redis_db.get_redis()

    # Get the top N events from the sorted set, along with their scores in reverse order
    results = redis_client.zrevrange(
        TRENDING_KEY,
        0,
        limit - 1,
        withscores=True
    )

    trending_events = []

    # Adds the ranking and returns a list of dictionaries with event_id, score, and rank in a cleaner format
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
def get_event_score(event_id: int) -> float | None:
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    return redis_client.zscore(
        TRENDING_KEY,
        member
    )


# Remove an event from the trending list. This is useful if an event is deleted or no longer relevant.
def remove_event(event_id: int) -> None:
    redis_client = redis_db.get_redis()
    member = event_member(event_id)

    redis_client.zrem(
        TRENDING_KEY,
        member
    )


# Reset the trending list, for the demo
def reset_trending() -> None:
    redis_client = redis_db.get_redis()

    redis_client.delete(TRENDING_KEY)