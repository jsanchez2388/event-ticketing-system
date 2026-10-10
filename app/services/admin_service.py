from collections.abc import Sequence
from datetime import datetime
from typing import Any

from app.services.analytics_service import (
    get_tickets_sold,
    get_event_inventory,
    get_event_revenue,
    get_top_customers,
    get_monthly_revenue,
)

from app.services.trending_service import get_event_score
from app.services.content_service import get_average_rating

from app.services.cache_service import invalidate_event     

def get_admin_dashboard_data() -> dict[str, Any]:

    # ============================================================
    # POSTGRESQL REPORTS
    # ============================================================

    tickets_sold_rows = get_tickets_sold()
    revenue_rows = get_event_revenue()
    top_customer_rows = get_top_customers(10)
    monthly_revenue_rows = get_monthly_revenue()


    # ============================================================
    # REVENUE LOOKUP
    # ============================================================

    revenue_by_event = {
        row["event_id"]: row["total_revenue"]
        for row in revenue_rows
    }


    # ============================================================
    # INVENTORY
    # ============================================================

    inventory = []

    for row in tickets_sold_rows:

        event_id = row["event_id"]

        inventory_rows = get_event_inventory(event_id)

        for inventory_row in inventory_rows:

            inventory.append({
                "event_id":
                    inventory_row["event_id"],

                "title":
                    inventory_row["title"],

                "ticket_type_id":
                    inventory_row["ticket_type_id"],

                "ticket_name":
                    inventory_row["ticket_name"],

                "price":
                    inventory_row["price"],

                "total_quantity":
                    inventory_row["total_quantity"],

                "remaining_quantity":
                    inventory_row["remaining_for_ticket_type"],

                "event_remaining":
                    inventory_row["total_remaining_for_event"],
            })


    # ============================================================
    # EVENT ACTIVITY
    #
    # PostgreSQL:
    #     ticket sales + revenue
    #
    # Redis:
    #     trending score
    #
    # MongoDB:
    #     average rating
    # ============================================================

    activity = []

    for row in tickets_sold_rows:

        event_id = row["event_id"]


        # --------------------------------------------------------
        # REDIS TRENDING SCORE
        # --------------------------------------------------------

        try:
            trending_score = get_event_score(event_id)

            if trending_score is None:
                trending_score = 0

        except Exception as error:

            print(
                f"Redis trending error for event "
                f"{event_id}: {error}"
            )

            trending_score = 0


        # --------------------------------------------------------
        # MONGODB AVERAGE RATING
        # --------------------------------------------------------

        try:
            average_rating = get_average_rating(event_id)

        except Exception as error:

            print(
                f"MongoDB rating error for event "
                f"{event_id}: {error}"
            )

            average_rating = None


        # --------------------------------------------------------
        # ADD EVENT TO ACTIVITY TABLE
        # --------------------------------------------------------

        activity.append({
            "event_id":
                event_id,

            "title":
                row["title"],

            "tickets_sold":
                row["total_tickets_sold"],

            "revenue":
                revenue_by_event.get(
                    event_id,
                    0
                ),

            "trending_score":
                trending_score,

            "average_rating":
                average_rating,
        })


    # ============================================================
    # TOP CUSTOMERS
    # ============================================================

    top_customers = []

    for row in top_customer_rows:

        top_customers.append({
            "user_id":
                row["user_id"],

            "first_name":
                row["first_name"],

            "last_name":
                row["last_name"],

            "email":
                row["email"],

            "tickets_purchased":
                row["total_tickets_purchased"],
        })


    # ============================================================
    # MONTHLY REVENUE
    # ============================================================

    monthly_revenue = []

    for row in monthly_revenue_rows:

        monthly_revenue.append({
            "month":
                row["revenue_month"],

            "revenue":
                row["monthly_ticket_revenue"],
        })


    # ============================================================
    # SUMMARY
    # ============================================================

    total_tickets_sold = sum(
        row["total_tickets_sold"]
        for row in tickets_sold_rows
    )

    total_revenue = sum(
        row["total_revenue"]
        for row in revenue_rows
    )


    # ============================================================
    # RETURN DASHBOARD DATA
    # ============================================================

    return {
        "activity":
            activity,

        "inventory":
            inventory,

        "top_customers":
            top_customers,

        "monthly_revenue":
            monthly_revenue,

        "total_events":
            len(tickets_sold_rows),

        "total_tickets_sold":
            total_tickets_sold,

        "total_revenue":
            total_revenue,
    }


# ============================================================
# ADMIN EVENT MANAGEMENT
# ============================================================

from app.database.postgres import get_connection
from app.services.cache_service import invalidate_event


def get_all_venues() -> Sequence[dict[str, Any]]:
    """
    Return all venues for the Admin event form.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                venue_id,
                venue_name,
                city,
                state
            FROM venues
            ORDER BY venue_name;
            """
        )

        venues = cursor.fetchall()
        cursor.close()

        return venues

    finally:
        conn.close()


def create_event(
    venue_id: int,
    title: str,
    event_type: str,
    start_datetime: datetime,
    end_datetime: datetime,
    status: str = "scheduled",
) -> dict[str, Any] | None:
    """
    Create a new PostgreSQL event.
    """

    if end_datetime <= start_datetime:
        raise ValueError(
            "Event end time must be after the start time."
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events (
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            RETURNING
                event_id,
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status;
            """,
            (
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status,
            )
        )

        event = cursor.fetchone()

        conn.commit()
        cursor.close()

        return event

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# ============================================================
# ADMIN - CREATE TICKET TYPE
# ============================================================

def create_ticket_type(
    event_id: int,
    ticket_name: str,
    price: float,
    total_quantity: int,
    minimum_purchase: int = 1,
    maximum_purchase: int = 10,
    status: str = "active",
) -> dict[str, Any] | None:
    if price < 0:
        raise ValueError("Ticket price cannot be negative.")

    if total_quantity < 0:
        raise ValueError("Ticket quantity cannot be negative.")

    if minimum_purchase < 1:
        raise ValueError("Minimum purchase must be at least 1.")

    if maximum_purchase < minimum_purchase:
        raise ValueError(
            "Maximum purchase cannot be less than minimum purchase."
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT event_id
            FROM events
            WHERE event_id = %s;
            """,
            (event_id,)
        )

        if cursor.fetchone() is None:
            raise ValueError("Event not found.")

        cursor.execute(
            """
            INSERT INTO ticket_types (
                event_id,
                ticket_name,
                price,
                total_quantity,
                available_quantity,
                minimum_purchase,
                maximum_purchase,
                status
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING
                ticket_type_id,
                event_id,
                ticket_name,
                price,
                total_quantity,
                available_quantity,
                status;
            """,
            (
                event_id,
                ticket_name,
                price,
                total_quantity,
                total_quantity,
                minimum_purchase,
                maximum_purchase,
                status,
            )
        )

        ticket_type = cursor.fetchone()

        conn.commit()
        cursor.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    try:
        invalidate_event(event_id)
    except Exception as error:
        print(
            f"Could not invalidate cache for event "
            f"{event_id}: {error}"
        )

    return ticket_type
# ============================================================
# ADMIN - GET EVENT
# ============================================================

def get_admin_event(event_id: int) -> dict[str, Any] | None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                event_id,
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status
            FROM events
            WHERE event_id = %s;
            """,
            (event_id,)
        )

        event = cursor.fetchone()
        cursor.close()

        return event

    finally:
        conn.close()

# ============================================================
# ADMIN - UPDATE EVENT
# ============================================================

def update_event(
    event_id: int,
    venue_id: int,
    title: str,
    event_type: str,
    start_datetime: datetime,
    end_datetime: datetime,
    status: str,
) -> dict[str, Any] | None:
    if end_datetime <= start_datetime:
        raise ValueError(
            "Event end time must be after the start time."
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE events
            SET
                venue_id = %s,
                title = %s,
                event_type = %s,
                start_datetime = %s,
                end_datetime = %s,
                status = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE event_id = %s
            RETURNING
                event_id,
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status;
            """,
            (
                venue_id,
                title,
                event_type,
                start_datetime,
                end_datetime,
                status,
                event_id,
            )
        )

        event = cursor.fetchone()

        if event is None:
            raise ValueError("Event not found.")

        conn.commit()
        cursor.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    invalidate_event(event_id)

    return event

# ============================================================
# ADMIN - GET TICKET TYPE
# ============================================================


def cancel_event(event_id: int) -> dict[str, Any] | None:
    """
    Cancel an event without deleting its PostgreSQL record,
    MongoDB content, ticket types, orders, or sales history.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE events
            SET status = 'cancelled'
            WHERE event_id = %s
            RETURNING
                event_id,
                title,
                status;
            """,
            (event_id,)
        )

        event = cursor.fetchone()

        if event is None:
            raise ValueError("Event not found.")

        conn.commit()
        cursor.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    invalidate_event(event_id)

    return event


def get_admin_ticket_type(ticket_type_id: int) -> dict[str, Any] | None:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                ticket_type_id,
                event_id,
                ticket_name,
                price,
                total_quantity,
                available_quantity,
                (total_quantity - available_quantity)
                    AS sold_quantity,
                minimum_purchase,
                maximum_purchase,
                status
            FROM ticket_types
            WHERE ticket_type_id = %s;
            """,
            (ticket_type_id,)
        )

        ticket_type = cursor.fetchone()
        cursor.close()

        return ticket_type

    finally:
        conn.close()

# ============================================================
# ADMIN - UPDATE TICKET TYPE
# ============================================================

def update_ticket_type(
    ticket_type_id: int,
    price: float,
    total_quantity: int,
    status: str,
) -> dict[str, Any] | None:
    if price < 0:
        raise ValueError("Ticket price cannot be negative.")

    if total_quantity < 0:
        raise ValueError(
            "Total ticket quantity cannot be negative."
        )

    conn = get_connection()
    event_id = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                event_id,
                total_quantity,
                available_quantity
            FROM ticket_types
            WHERE ticket_type_id = %s
            FOR UPDATE;
            """,
            (ticket_type_id,)
        )

        current = cursor.fetchone()

        if current is None:
            raise ValueError("Ticket type not found.")

        event_id = current["event_id"]

        sold_quantity = (
            current["total_quantity"]
            - current["available_quantity"]
        )

        if total_quantity < sold_quantity:
            raise ValueError(
                f"Cannot reduce quantity below "
                f"{sold_quantity}. Those tickets are already sold."
            )

        new_available = total_quantity - sold_quantity

        cursor.execute(
            """
            UPDATE ticket_types
            SET
                price = %s,
                total_quantity = %s,
                available_quantity = %s,
                status = %s
            WHERE ticket_type_id = %s
            RETURNING *;
            """,
            (
                price,
                total_quantity,
                new_available,
                status,
                ticket_type_id,
            )
        )

        updated = cursor.fetchone()

        conn.commit()
        cursor.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()

    if event_id is not None:
        invalidate_event(event_id)

    return updated
