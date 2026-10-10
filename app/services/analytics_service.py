from collections.abc import Sequence
from typing import Any

from app.database.postgres import get_connection


SQL_EVENTS_BY_VENUE = """
SELECT
    e.event_id,
    e.title,
    e.event_type,
    e.start_datetime,
    e.end_datetime,
    e.status,
    v.venue_name,
    v.city,
    v.state
FROM events AS e
JOIN venues AS v
    ON e.venue_id = v.venue_id
WHERE e.venue_id = %s
ORDER BY e.start_datetime;
"""


SQL_USER_TICKETS = """
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    o.order_id,
    o.order_date,
    e.event_id,
    e.title AS event_title,
    tt.ticket_name AS ticket_type,
    oi.quantity,
    oi.unit_price,
    (oi.quantity * oi.unit_price) AS line_total
FROM users AS u
JOIN orders AS o
    ON u.user_id = o.user_id
JOIN order_items AS oi
    ON o.order_id = oi.order_id
JOIN ticket_types AS tt
    ON oi.ticket_type_id = tt.ticket_type_id
JOIN events AS e
    ON tt.event_id = e.event_id
WHERE u.user_id = %s
ORDER BY o.order_date DESC;
"""


SQL_TICKETS_SOLD = """
SELECT
    e.event_id,
    e.title,
    COALESCE(SUM(oi.quantity), 0) AS total_tickets_sold
FROM events AS e
LEFT JOIN ticket_types AS tt
    ON e.event_id = tt.event_id
LEFT JOIN order_items AS oi
    ON tt.ticket_type_id = oi.ticket_type_id
GROUP BY
    e.event_id,
    e.title
ORDER BY total_tickets_sold DESC;
"""


SQL_EVENT_INVENTORY = """
SELECT
    e.event_id,
    e.title,
    tt.ticket_type_id,
    tt.ticket_name,
    tt.price,
    tt.total_quantity,
    tt.available_quantity AS remaining_for_ticket_type,

    SUM(tt.available_quantity)
        OVER (PARTITION BY e.event_id)
        AS total_remaining_for_event

FROM events AS e

JOIN ticket_types AS tt
    ON e.event_id = tt.event_id

WHERE e.event_id = %s

ORDER BY tt.ticket_type_id;
"""


SQL_EVENT_REVENUE = """
SELECT
    e.event_id,
    e.title,

    COALESCE(
        SUM(oi.quantity * oi.unit_price)
        FILTER (
            WHERE EXISTS (
                SELECT 1
                FROM payments AS p
                WHERE p.order_id = o.order_id
                AND LOWER(p.payment_status) = 'completed'
            )
        ),
        0
    ) AS total_revenue

FROM events AS e

LEFT JOIN ticket_types AS tt
    ON e.event_id = tt.event_id

LEFT JOIN order_items AS oi
    ON tt.ticket_type_id = oi.ticket_type_id

LEFT JOIN orders AS o
    ON oi.order_id = o.order_id

GROUP BY
    e.event_id,
    e.title

ORDER BY total_revenue DESC;
"""


SQL_TOP_CUSTOMERS = """
SELECT
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    SUM(oi.quantity) AS total_tickets_purchased

FROM users AS u

JOIN orders AS o
    ON u.user_id = o.user_id

JOIN order_items AS oi
    ON o.order_id = oi.order_id

WHERE LOWER(o.status) = 'completed'

AND EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.order_id = o.order_id
    AND LOWER(p.payment_status) = 'completed'
)

GROUP BY
    u.user_id,
    u.first_name,
    u.last_name,
    u.email

ORDER BY total_tickets_purchased DESC

LIMIT %s;
"""


SQL_EVENTS_OVER_THRESHOLD = """
SELECT
    e.event_id,
    e.title,
    SUM(oi.quantity * oi.unit_price) AS ticket_sales

FROM events AS e

JOIN ticket_types AS tt
    ON e.event_id = tt.event_id

JOIN order_items AS oi
    ON tt.ticket_type_id = oi.ticket_type_id

JOIN orders AS o
    ON oi.order_id = o.order_id

WHERE LOWER(o.status) = 'completed'

AND EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.order_id = o.order_id
    AND LOWER(p.payment_status) = 'completed'
)

GROUP BY
    e.event_id,
    e.title

HAVING SUM(oi.quantity * oi.unit_price) > %s

ORDER BY ticket_sales DESC;
"""


SQL_MONTHLY_REVENUE = """
SELECT
    DATE_TRUNC(
        'month',
        o.order_date
    ) AS revenue_month,

    SUM(
        oi.quantity * oi.unit_price
    ) AS monthly_ticket_revenue

FROM orders AS o

JOIN order_items AS oi
    ON o.order_id = oi.order_id

WHERE LOWER(o.status) = 'completed'

AND EXISTS (
    SELECT 1
    FROM payments AS p
    WHERE p.order_id = o.order_id
    AND LOWER(p.payment_status) = 'completed'
)

GROUP BY
    DATE_TRUNC(
        'month',
        o.order_date
    )

ORDER BY revenue_month;
"""


QUERY_SQL = {
    "q1": SQL_EVENTS_BY_VENUE,
    "q2": SQL_USER_TICKETS,
    "q3": SQL_TICKETS_SOLD,
    "q4": SQL_EVENT_INVENTORY,
    "q5": SQL_EVENT_REVENUE,
    "q6": SQL_TOP_CUSTOMERS,
    "q7": SQL_EVENTS_OVER_THRESHOLD,
    "q8": SQL_MONTHLY_REVENUE,
}


def get_events_by_venue(venue_id: int) -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_EVENTS_BY_VENUE,
            (venue_id,)
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_user_tickets(user_id: int) -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_USER_TICKETS,
            (user_id,)
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_tickets_sold() -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_TICKETS_SOLD
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_event_inventory(event_id: int) -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_EVENT_INVENTORY,
            (event_id,)
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_event_revenue() -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_EVENT_REVENUE
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_top_customers(limit: int) -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_TOP_CUSTOMERS,
            (limit,)
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_events_over_threshold(threshold: float) -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_EVENTS_OVER_THRESHOLD,
            (threshold,)
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()


def get_monthly_revenue() -> Sequence[dict[str, Any]]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            SQL_MONTHLY_REVENUE
        )

        results = cursor.fetchall()
        cursor.close()

        return results

    finally:
        conn.close()
