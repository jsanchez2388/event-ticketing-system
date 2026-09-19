# app/routers/orders.py
#
# PURPOSE
#   Ticket purchasing endpoint (runs the SQL transaction).
#
# TO ADD
#   router = APIRouter(prefix="/orders", tags=["orders"])
#
#   POST /orders
#       def create_order(payload: OrderCreate) -> OrderResponse
#       status_code=201. Calls purchase_service.purchase_tickets.
#       Error mapping:
#         InsufficientInventoryError -> 409 Conflict
#         PaymentFailedError         -> 402 Payment Required
#         unknown user / ticket type -> 404 Not Found
#       Error responses should confirm that the transaction was rolled back.
#
#   GET /orders/{order_id}   (optional)
#       def get_order(order_id: int) -> OrderResponse
