# app/models/orders.py
#
# PURPOSE
#   Pydantic schemas for purchasing tickets and viewing past orders.
#   (Tables orders, order_items, payments are defined in sql/schema.sql.)
#
# TO ADD
#   class PaymentMethod(str, Enum)
#       e.g. CREDIT_CARD, DEBIT_CARD, PAYPAL.
#
#   class OrderItemRequest(BaseModel)
#       One line in a purchase: ticket_type_id, quantity (must be > 0).
#
#   class OrderCreate(BaseModel)
#       Request body for POST /orders.
#       Fields: user_id, items (list[OrderItemRequest], non-empty),
#       payment_method, simulate_payment_failure (bool, default False; used
#       only to demonstrate ROLLBACK).
#
#   class OrderItemResponse(BaseModel)
#       order_item_id, ticket_type_id, ticket_type_name, event_id,
#       event_title, quantity, unit_price, line_total.
#
#   class PaymentResponse(BaseModel)
#       payment_id, amount, method, status, paid_at.
#
#   class OrderResponse(BaseModel)
#       order_id, user_id, order_date, status, total_amount,
#       items (list[OrderItemResponse]), payment (PaymentResponse).
#       Returned by POST /orders and each entry of GET /users/{id}/orders.
