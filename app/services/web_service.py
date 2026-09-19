from app.database.postgres import get_connection


def get_event_cards():
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

        return events

    finally:
        conn.close()


def get_event_page_details(event_id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Main event information
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
                v.country

            FROM events AS e

            JOIN venues AS v
                ON e.venue_id = v.venue_id

            WHERE e.event_id = %s;
            """,
            (event_id,)
        )

        event = cursor.fetchone()

        if event is None:
            cursor.close()
            return None

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

        cursor.close()

        return {
            "event": event,
            "ticket_types": ticket_types,
            "categories": categories
        }

    finally:
        conn.close()