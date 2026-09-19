-- sql/queries.sql
-- COMP 642 Event Ticketing Platform
-- The 8 required SQL queries
--
-- Notes:
--   * Sample values are hard-coded so these can be run directly in Neon.
--   * In FastAPI/psycopg2, replace sample values with parameters.
--   * Queries 2, 3, 5, 6, 7, and 8 join three or more tables.
--   * Completed-payment checks use EXISTS so multiple payment records
--     do not accidentally duplicate order items.

-- ============================================================
-- QUERY 1
-- Find all events at a particular venue.
-- Sample parameter: venue_id = 1
-- API parameter version: WHERE e.venue_id = %s
-- ============================================================
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
WHERE e.venue_id = 1
ORDER BY e.start_datetime;


-- ============================================================
-- QUERY 2
-- Find all tickets purchased by a particular user.
-- 5-table join: users, orders, order_items, ticket_types, events
-- Sample parameter: user_id = 402
-- API parameter version: WHERE u.user_id = %s
-- ============================================================
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
WHERE u.user_id = 402
ORDER BY o.order_date DESC, o.order_id, e.event_id;


-- ============================================================
-- QUERY 3
-- Calculate total tickets sold for each event.
-- Uses LEFT JOIN so events with zero ticket sales still appear.
-- 3-table join: events, ticket_types, order_items
-- ============================================================
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
ORDER BY
    total_tickets_sold DESC,
    e.event_id;


-- ============================================================
-- QUERY 4
-- Determine remaining ticket inventory for an event.
-- Shows remaining inventory by ticket type and event total.
-- Sample parameter: event_id = 101
-- API parameter version: WHERE e.event_id = %s
-- ============================================================
SELECT
    e.event_id,
    e.title,
    tt.ticket_type_id,
    tt.ticket_name,
    tt.total_quantity,
    tt.available_quantity AS remaining_for_ticket_type,
    SUM(tt.available_quantity) OVER (
        PARTITION BY e.event_id
    ) AS total_remaining_for_event
FROM events AS e
JOIN ticket_types AS tt
    ON e.event_id = tt.event_id
WHERE e.event_id = 101
ORDER BY tt.ticket_type_id;


-- ============================================================
-- QUERY 5
-- Calculate total revenue for each event.
-- Only counts order items whose order has a completed payment.
-- 4-table path: events -> ticket_types -> order_items -> orders
-- ============================================================
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
ORDER BY
    total_revenue DESC,
    e.event_id;


-- ============================================================
-- QUERY 6
-- Identify customers who have purchased the most tickets.
-- 3-table join: users, orders, order_items
-- Sample limit: top 10 customers
-- ============================================================
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
ORDER BY
    total_tickets_purchased DESC,
    u.user_id
LIMIT 10;


-- ============================================================
-- QUERY 7
-- Find events whose sales exceed a specified threshold.
-- 4-table path: events -> ticket_types -> order_items -> orders
-- Sample threshold: $500.00
-- ============================================================
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
HAVING SUM(oi.quantity * oi.unit_price) > 500.00
ORDER BY
    ticket_sales DESC,
    e.event_id;


-- ============================================================
-- QUERY 8
-- Calculate monthly ticket revenue.
-- Uses order_date to assign each ticket sale to a month.
-- ============================================================
SELECT
    DATE_TRUNC('month', o.order_date) AS revenue_month,
    SUM(oi.quantity * oi.unit_price) AS monthly_ticket_revenue
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
    DATE_TRUNC('month', o.order_date)
ORDER BY
    revenue_month;


-- ============================================================
-- OPTIONAL ADMIN ANALYTICS
-- ============================================================

-- A. Sales summary by event and ticket type
SELECT
    e.event_id,
    e.title,
    tt.ticket_name,
    tt.total_quantity,
    tt.available_quantity,
    COALESCE(SUM(oi.quantity), 0) AS tickets_sold,
    COALESCE(SUM(oi.quantity * oi.unit_price), 0) AS gross_ticket_sales
FROM events AS e
JOIN ticket_types AS tt
    ON e.event_id = tt.event_id
LEFT JOIN order_items AS oi
    ON tt.ticket_type_id = oi.ticket_type_id
GROUP BY
    e.event_id,
    e.title,
    tt.ticket_type_id,
    tt.ticket_name,
    tt.total_quantity,
    tt.available_quantity
ORDER BY
    e.event_id,
    tt.ticket_type_id;


-- B. Events ordered by percentage of inventory sold
SELECT
    e.event_id,
    e.title,
    SUM(tt.total_quantity) AS total_inventory,
    SUM(tt.total_quantity - tt.available_quantity) AS tickets_sold,
    ROUND(
        100.0 * SUM(tt.total_quantity - tt.available_quantity)
        / NULLIF(SUM(tt.total_quantity), 0),
        2
    ) AS percent_sold
FROM events AS e
JOIN ticket_types AS tt
    ON e.event_id = tt.event_id
GROUP BY
    e.event_id,
    e.title
ORDER BY
    percent_sold DESC,
    e.event_id;
