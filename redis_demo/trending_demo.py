# redis_demo/trending_demo.py

# PURPOSE
#   Demonstrate Redis Use Case 2 (trending events via a sorted set).
#   Run from the repo root: python -m redis_demo.trending_demo

from app.database.redis import init_client, close_client
from app.services.trending_service import (
    record_view,
    get_top_trending,
    reset_trending,
)


def simulate_views(view_counts: dict[int, int]) -> None:
    """Simulate a specified number of views for each event."""

    for event_id, view_count in view_counts.items():
        for _ in range(view_count):
            record_view(event_id)


def print_top_trending(limit: int = 10) -> None:
    """Print the current Redis trending ranking."""

    trending_events = get_top_trending(limit)

    print(f"{'Rank':<6}{'Event':<14}{'Score':<8}")
    print("-" * 28)

    for event in trending_events:
        print(
            f"{event['rank']:<6}"
            f"event:{event['event_id']:<8}"
            f"{event['score']:<8.0f}"
        )


def main() -> None:
    init_client()

    try:
        # Start with an empty sorted set so the demo is repeatable.
        reset_trending()

        initial_views = {
            101: 8,
            102: 15,
            103: 11,
            104: 5,
            105: 3,
            106: 7,
        }

        print("\n--- Initial Trending Events ---")

        simulate_views(initial_views)
        print_top_trending()

        # Event 105 starts near the bottom.
        # Give it enough new views to move up the ranking.
        print("\nAdding 15 more views to event:105...")

        simulate_views({105: 15})

        print("\n--- Updated Trending Events ---")

        print_top_trending()

    finally:
        close_client()


if __name__ == "__main__":
    main()