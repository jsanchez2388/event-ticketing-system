# app/services/admin_service.py

from app.services.analytics_service import (
    get_tickets_sold,
    get_event_inventory,
    get_event_revenue,
    get_top_customers,
    get_monthly_revenue,
)

from app.services.trending_service import get_event_score
from app.services.content_service import get_average_rating


def get_admin_dashboard_data():

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
