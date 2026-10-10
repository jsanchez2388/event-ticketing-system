from collections.abc import Sequence
from typing import Any

from app.database.postgres import get_connection
from app.services.event_service import get_event_detail, get_events_by_ids
from app.services.trending_service import get_top_trending
from app.services.content_service import get_event_content_by_ids
from app.services.user_service import get_users_by_ids


def get_event_cards() -> Sequence[dict[str, Any]]:
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

                v.venue_name,
                v.city,
                v.state,

                COALESCE(MIN(tt.price), 0) AS starting_price,
                COALESCE(SUM(tt.available_quantity), 0)
                    AS remaining_inventory

            FROM events AS e

            JOIN venues AS v
                ON e.venue_id = v.venue_id

            LEFT JOIN ticket_types AS tt
                ON e.event_id = tt.event_id

            GROUP BY
                e.event_id,
                e.title,
                e.event_type,
                e.start_datetime,
                e.end_datetime,
                e.status,
                v.venue_name,
                v.city,
                v.state

            ORDER BY e.start_datetime;
            """
        )

        events = cursor.fetchall()
        cursor.close()

        event_ids = [
            event["event_id"]
            for event in events
        ]

        mongo_content = get_event_content_by_ids(event_ids)

        for event in events:
            content = mongo_content.get(event["event_id"], {})
            event["tags"] = content.get("tags", [])

        return events

    finally:
        conn.close()


def get_trending_event_cards(limit: int = 10) -> list[dict[str, Any]]:
    trending = get_top_trending(limit)

    if not trending:
        return []

    event_ids = [
        item["event_id"]
        for item in trending
    ]

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
            "score": item["score"],
            **event
        })

    return results


def get_event_page_details(event_id: int) -> dict[str, Any] | None:

    event = get_event_detail(event_id)
    
    if event is None:
        return None
    
    conn = get_connection()

    try:
        cursor = conn.cursor()

        

        # Ticket types
        cursor.execute(
            """
            SELECT
                ticket_type_id,
                ticket_name,
                price,
                total_quantity,
                available_quantity,
                minimum_purchase,
                maximum_purchase,
                status

            FROM ticket_types

            WHERE event_id = %s

            ORDER BY price;
            """,
            (event_id,)
        )

        ticket_types = cursor.fetchall()

        # Event categories
        cursor.execute(
            """
            SELECT
                ec.category_name

            FROM event_categories AS ec

            JOIN event_category_map AS ecm
                ON ec.category_id = ecm.category_id

            WHERE ecm.event_id = %s

            ORDER BY ec.category_name;
            """,
            (event_id,)
        )

        category_rows = cursor.fetchall()

        categories = [
            row["category_name"]
            for row in category_rows
        ]

        # Reviews are already included in the MongoDB event document
        reviews = event.get("reviews", [])

        reviewer_ids = list({
            review["userId"]
            for review in reviews
            if review.get("userId") is not None
        })

        users_by_id = get_users_by_ids(reviewer_ids)

        for review in reviews:
            user = users_by_id.get(review.get("userId"))

            if user is not None:
                review["reviewer_name"] = (
                    f'{user["first_name"]} {user["last_name"]}'
                )
            else:
                review["reviewer_name"] = "Unknown User"

        if reviews:
            average_rating = sum(
                review.get("rating", 0)
                for review in reviews
            ) / len(reviews)
        else:
            average_rating = None

        cursor.close()

        return {
        "event": event,
        "ticket_types": ticket_types,
        "categories": categories,
        "reviews": reviews,
        "average_rating": average_rating,
        "review_count": len(reviews)
        }

    finally:
        conn.close()