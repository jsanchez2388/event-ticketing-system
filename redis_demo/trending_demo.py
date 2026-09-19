# redis_demo/trending_demo.py
#
# PURPOSE
#   Demonstrate Redis Use Case 2 (trending events via a sorted set).
#   Run from the repo root: python -m redis_demo.trending_demo
#
# TO ADD
#   def simulate_views(view_counts: dict[int, int]) -> None
#       For each event_id, call trending_service.record_view() N times
#       (use uneven counts or random weights so the ranking is interesting).
#
#   def print_top_trending(limit: int = 10) -> None
#       Call trending_service.get_top_trending(limit) and print a table of
#       rank / event:{id} / score (optionally with titles).
#
#   def main() -> None
#       Initialize Redis, call trending_service.reset_trending(), simulate views,
#       print the Top 10, record more views for a lower-ranked event,
#       and print again to show it moving up.
#
#   if __name__ == "__main__": main()
