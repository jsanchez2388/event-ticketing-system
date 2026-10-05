
from app.database.postgres import get_connection
from app.services.content_service import get_event_content


from app.services.cache_service import (
    get_cached_event,
    set_cached_event,
    is_event_cache_enabled,
)
from app.services.trending_service import (record_view, get_event_score)


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


# Will be used to collect all the event details for the trending page
def get_events_by_ids(event_ids: list[int]):
    if not event_ids:
        return []

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
            WHERE e.event_id = ANY(%s);
            """,
            (event_ids,)
        )

        events = cursor.fetchall()
        cursor.close()

        return events

    finally:
        conn.close()



def get_event_content_from_mongo(event_id: int):
    return get_event_content(event_id)


# Builds a complete event detail by combining PostgreSQL + MongoDB data. NO Redis involved. Redis will cache the result of this function.
def build_event_detail(event_id: int):
    event = get_event_by_id(event_id)

    if event is None:
        return None

    event_detail = dict(event)

    content = get_event_content_from_mongo(event_id)

    if content is not None:
        mongo_content = dict(content)

        # PostgreSQL is authoritative for these shared fields.
        mongo_content.pop("eventId", None)
        mongo_content.pop("eventType", None)
        mongo_content.pop("title", None)

        event_detail.update(mongo_content)

    return event_detail


# Combines PostgreSQL + MongoDB + Redis to return a complete event detail, with popularity score and cache hit flag. 
def get_event_detail(event_id: int, use_cache: bool = True):
    event_detail = None
    cache_hit = False
    use_cache = (
        use_cache
        and is_event_cache_enabled()
    )
    # Check the cache first
    if use_cache:
        event_detail = get_cached_event(event_id)

        if event_detail is not None:
            cache_hit = True

    #If the event is not in the cache, builds it from PostgreSQL + MongoDB using the build_event_detail function and then cache it.
    if event_detail is None:
        event_detail = build_event_detail(event_id)

        if event_detail is None:
            return None

        if use_cache:
            set_cached_event(event_id, event_detail)

    record_view(event_id)

    popularity_score = get_event_score(event_id)

    event_detail["popularity_score"] = popularity_score
    event_detail["cache_hit"] = cache_hit

    return event_detail