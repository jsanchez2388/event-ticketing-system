from time import perf_counter
from statistics import median
from typing import Any
from app.services.event_service import build_event_detail
from app.services.cache_service import (
    get_cached_event,
    set_cached_event,
    invalidate_event,
)

def run_cache_benchmark(
    event_id: int,
    iterations: int = 10,
) -> dict[str, Any]:
    """Time repeated reads of one event with and without the Redis cache.

    Returns the individual timings and medians for both paths.
    """
    if iterations < 1:
        raise ValueError(
            "Iterations must be at least 1."
        )

    if iterations > 100:
        raise ValueError(
            "Iterations cannot exceed 100."
        )

    # Make sure the event exists.
    # This also acts as a warm-up request.

    event = build_event_detail(event_id)

    if event is None:
        raise ValueError("Event not found.")

    # WITHOUT REDIS CACHE
    #
    # Rebuild the event from PostgreSQL + MongoDB each time.

    no_cache_times = []

    for _ in range(iterations):
        start = perf_counter()

        result = build_event_detail(event_id)

        elapsed_ms = (
            perf_counter() - start
        ) * 1000

        if result is None:
            raise ValueError("Event not found.")

        no_cache_times.append(elapsed_ms)

    # WITH REDIS CACHE

    invalidate_event(event_id)

    event = build_event_detail(event_id)

    if event is None:
        raise ValueError("Event not found.")

    set_cached_event(
        event_id,
        event
    )

    cache_times = []

    for _ in range(iterations):
        start = perf_counter()

        result = get_cached_event(event_id)

        elapsed_ms = (
            perf_counter() - start
        ) * 1000

        if result is None:
            raise RuntimeError(
                "Redis cache unexpectedly returned no event."
            )

        cache_times.append(elapsed_ms)

    # Remove the benchmark copy so the test does not
    # change the application's normal cache state.
    invalidate_event(event_id)

    no_cache_average = (
        sum(no_cache_times)
        / len(no_cache_times)
    )

    cache_average = (
        sum(cache_times)
        / len(cache_times)
    )

    if cache_average > 0:
        speedup = (
            no_cache_average
            / cache_average
        )
    else:
        speedup = 0

    return {
        "event_id": event_id,
        "event_title": event["title"],
        "iterations": iterations,

        "without_cache_ms":
            round(no_cache_average, 3),

        "with_cache_ms":
            round(cache_average, 3),

        "speedup":
            round(speedup, 2),

        "without_cache_min_ms":
            round(min(no_cache_times), 3),

        "with_cache_min_ms":
            round(min(cache_times), 3),

        "without_cache_max_ms":
            round(max(no_cache_times), 3),

        "with_cache_max_ms":
            round(max(cache_times), 3),

        "without_cache_median_ms":
            round(median(no_cache_times), 3),

        "with_cache_median_ms":
            round(median(cache_times), 3),
    }
