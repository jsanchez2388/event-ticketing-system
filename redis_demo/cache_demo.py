# redis_demo/cache_demo.py
#
# PURPOSE
#   Demonstrate Redis Use Case 1 (event cache) for the report.
#   Must visibly show: CACHE MISS -> DATABASE RETRIEVAL -> CACHE POPULATION -> CACHE HIT.
#   Run from the repo root: python -m redis_demo.cache_demo
#
# TO ADD
#   def setup() -> None
#       Initialize the PostgreSQL pool, Mongo client, and Redis client (app.database.*).
#
#   def demo_cache_flow(event_id: int) -> None
#       1. cache_service.invalidate_event(event_id)     start from a clean state
#       2. event_service.get_event_detail(event_id)     prints MISS, DB retrieval, POPULATED
#       3. show that the key exists and its TTL (cache_service.get_ttl_remaining)
#       4. event_service.get_event_detail(event_id)     prints HIT
#       Print the timing of each call.
#
#   def demo_ttl_expiry(event_id: int) -> None  (optional)
#       Set a very short TTL, wait past it, and show the next request is a MISS again.
#
#   def main() -> None
#   if __name__ == "__main__": main()
