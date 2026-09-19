# app/services/sales_service.py
#
# PURPOSE
#   Admin reporting and analytics queries. Each function runs one of the
#   required SQL queries (keep the SQL identical to sql/queries.sql).
#
# TO ADD
#   def get_tickets_sold_per_event() -> list[dict]
#       Query 3: total tickets sold for each event.
#
#   def get_remaining_inventory(event_id: int) -> dict
#       Query 4: remaining inventory per ticket type, plus event totals.
#
#   def get_revenue_per_event() -> list[dict]
#       Query 5: total revenue for each event.
#
#   def get_top_customers(limit: int = 10) -> list[dict]
#       Query 6: customers who purchased the most tickets.
#
#   def get_events_above_sales_threshold(threshold) -> list[dict]
#       Query 7: events whose sales exceed a threshold (GROUP BY ... HAVING).
#       Decide whether the threshold is tickets sold or revenue, and document it.
#
#   def get_monthly_revenue() -> list[dict]
#       Query 8: monthly ticket revenue (DATE_TRUNC on the order date).
#
#   def get_event_activity() -> list[dict]
#       Admin "analyze event activity": combine sales numbers (PostgreSQL),
#       trending scores (trending_service), and average ratings
#       (content_service) into one summary per event.
