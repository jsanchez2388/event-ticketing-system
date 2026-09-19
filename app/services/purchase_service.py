# app/services/purchase_service.py
#
# PURPOSE
#   The required relational DATABASE TRANSACTION: purchasing tickets.
#   Called by POST /orders (app/routers/orders.py).
#
# TO ADD
#   class PurchaseError(Exception)
#       Base class for purchase failures.
#
#   class InsufficientInventoryError(PurchaseError)
#       Raised when a ticket type has fewer tickets remaining than requested.
#
#   class PaymentFailedError(PurchaseError)
#       Raised when payment fails (or simulate_payment_failure=True).
#
#   def purchase_tickets(user_id, items, payment_method,
#                        simulate_payment_failure=False) -> dict
#       Public entry point. Using ONE connection from
#       app.database.postgres.get_connection():
#         1. BEGIN
#         2. _lock_ticket_types(): read and lock the requested ticket_types rows
#         3. _create_order(): INSERT into orders, get order_id
#         4. _create_order_items(): INSERT one order_items row per item,
#            storing unit_price at time of purchase
#         5. _decrement_inventory(): UPDATE ticket_types.quantity_remaining;
#            raise InsufficientInventoryError if not enough remain
#         6. _create_payment(): INSERT into payments; raise PaymentFailedError
#            on a simulated failure
#         7. COMMIT
#       On ANY exception: ROLLBACK, then re-raise so the router can return an
#       appropriate HTTP error (e.g. 409 for inventory, 402 for payment).
#       After a successful COMMIT: call cache_service.invalidate_event(event_id)
#       for each affected event so cached availability is not stale.
#       Returns the new order (shape of OrderResponse).
#
#   Private helpers (each receives the open cursor; none of them commit):
#       def _lock_ticket_types(cur, ticket_type_ids) -> dict
#           SELECT ... FOR UPDATE so concurrent buyers cannot oversell.
#       def _create_order(cur, user_id, total_amount) -> int
#       def _create_order_items(cur, order_id, items, prices) -> list
#       def _decrement_inventory(cur, items) -> None
#       def _create_payment(cur, order_id, amount, method, simulate_failure) -> dict
#
# NOTES
#   - Helpers must never call commit(); only purchase_tickets() commits.
#   - The report must explain why atomicity matters here (no order without
#     payment, no inventory decremented for a failed order, no overselling).
