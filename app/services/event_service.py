# app/services/event_service.py
#
# PURPOSE
#   Event browsing and management logic, plus the REQUIRED CROSS-DATABASE
#   FEATURE used by GET /events/{id}: PostgreSQL + MongoDB + Redis.
#
# TO ADD (cross-database event detail)
#   def get_event_from_postgres(event_id: int) -> dict | None
#       JOIN events + venues + ticket_types: event fields, venue, ticket types,
#       prices, quantity remaining. Return None if the event does not exist.
#
#   def get_event_content_from_mongo(event_id: int) -> dict | None
#       Delegate to content_service.get_event_content(event_id).
#
#   def build_event_detail(event_id: int) -> dict | None
#       Query PostgreSQL + MongoDB and combine into one EventDetail-shaped dict.
#       NO Redis involved. Used on a cache miss AND by Experiment A in
#       experiments/cache_benchmark.py.
#
#   def get_event_detail(event_id: int, use_cache: bool = True) -> dict | None
#       Full flow:
#         1. cache_service.get_cached_event(event_id)
#         2. HIT  -> use the cached data
#            MISS -> build_event_detail(), then cache_service.set_cached_event()
#         3. trending_service.record_view(event_id)   (on hit AND miss)
#         4. add popularity_score and a cache_hit flag to the response
#         5. return
#       use_cache=False skips steps 1-2 (supports the performance experiment).
#
# TO ADD (browsing and admin management)
#   def list_events(event_type=None, city=None, start_after=None,
#                   limit=50, offset=0) -> list[dict]
#       GET /events: browse with optional filters.
#
#   def get_events_by_venue(venue_id: int) -> list[dict]
#       Query 1.
#
#   def create_event(data: EventCreate) -> dict
#       INSERT into events (+ event_categories rows). Optionally create an
#       initial event_content document via content_service.
#
#   def update_event(event_id: int, data: EventUpdate) -> dict
#       UPDATE events, then cache_service.invalidate_event(event_id).
#
#   def delete_event(event_id: int) -> None
#       Delete (or mark cancelled) in PostgreSQL, remove its Mongo document,
#       invalidate the cache, and remove it from the trending sorted set.
#
#   def create_ticket_type(event_id: int, data: TicketTypeCreate) -> dict
#   def update_ticket_type(ticket_type_id: int, data: TicketTypeUpdate) -> dict
#       Admin ticket type management; invalidate the event cache afterward.
from app.database.postgres import get_connection


def get_all_events():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                e.event_id,
                e.title,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.status,
                v.venue_id,
                v.venue_name,
                v.city,
                v.state
            FROM events AS e
            JOIN venues AS v
                ON e.venue_id = v.venue_id
            ORDER BY e.start_datetime;
            """
        )

        events = cursor.fetchall()
        cursor.close()

        return events

    finally:
        conn.close()


def get_event_by_id(event_id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                e.event_id,
                e.title,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.status,
                v.venue_id,
                v.venue_name,
                v.street,
                v.city,
                v.state,
                v.zip_code,
                COALESCE(
                    SUM(tt.available_quantity),
                    0
                ) AS remaining_inventory
            FROM events AS e
            JOIN venues AS v
                ON e.venue_id = v.venue_id
            LEFT JOIN ticket_types AS tt
                ON e.event_id = tt.event_id
            WHERE e.event_id = %s
            GROUP BY
                e.event_id,
                e.title,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.status,
                v.venue_id,
                v.venue_name,
                v.street,
                v.city,
                v.state,
                v.zip_code;
            """,
            (event_id,)
        )

        event = cursor.fetchone()
        cursor.close()

        return event

    finally:
        conn.close()