# PURPOSE
#   Demonstrate Redis Use Case 1 (event cache) for the report.
#   Must visibly show: CACHE MISS -> DATABASE RETRIEVAL -> CACHE POPULATION -> CACHE HIT.
#   Run from the repo root: python -m redis_demo.cache_demo

from time import perf_counter, sleep

from app.database.mongo import init_client as init_mongo, close_client as close_mongo
from app.database.redis import init_client as init_redis, close_client as close_redis
from app.services.cache_service import invalidate_event, get_ttl_remaining, set_cached_event
from app.services.event_service import get_event_detail


def setup() -> None:
    """Initialize the database clients needed by the cache demo."""
    init_mongo()
    init_redis()


def demo_cache_flow(event_id: int) -> None:
    """Show a Redis cache miss followed by a cache hit for one event."""

    print(f"\n--- Redis Cache Demo: Event {event_id} ---")

    # Start from a clean state so the first request is a cache miss.
    invalidate_event(event_id)

    # First request: Redis miss -> PostgreSQL + MongoDB -> Redis populated.
    print("\n1. First request")

    start = perf_counter()
    first_result = get_event_detail(event_id)
    first_elapsed_ms = (perf_counter() - start) * 1000

    if first_result is None:
        print(f"Event {event_id} was not found.")
        return

    print(f"First request time: {first_elapsed_ms:.3f} ms")
    print(f"Cache hit: {first_result['cache_hit']}")

    # Show that the event now exists in Redis and has a TTL.
    print(f"Redis key: event:{event_id}")

    # Show Redis automatically counting down the TTL.
    for check in range(6):
        ttl = get_ttl_remaining(event_id)
        print(f"TTL remaining: {ttl} seconds")

        if check < 5:
            sleep(1)

    # Second request: should come from Redis.
    print("\n2. Second request")

    start = perf_counter()
    second_result = get_event_detail(event_id)
    second_elapsed_ms = (perf_counter() - start) * 1000

    print(f"Second request time: {second_elapsed_ms:.3f} ms")
    print(f"Cache hit: {second_result['cache_hit']}")
    print(f"Popularity score: {second_result['popularity_score']}")
    print(f"TTL remaining: {ttl} seconds")


    print("\n--- Demo Complete ---")


def demo_ttl_expiry(event_id: int) -> None:
    print("\n--- TTL Expiration Demo ---")

    # Get the event normally first.
    event = get_event_detail(event_id)

    # Re-cache it with a short TTL just for this demo.
    set_cached_event(event_id, event, ttl=5)

    while True:
        ttl = get_ttl_remaining(event_id)

        if ttl == -2:
            print("TTL: EXPIRED - Redis key no longer exists")
            break

        print(f"TTL remaining: {ttl} seconds")
        sleep(1)

    print("\nRequesting the event again after expiration...")

    result = get_event_detail(event_id)

    print(f"Cache hit: {result['cache_hit']}")


def main() -> None:
    setup()

    try:
        demo_cache_flow(103)
        demo_ttl_expiry(103)
    finally:
        close_mongo()
        close_redis()

if __name__ == "__main__":
    main()