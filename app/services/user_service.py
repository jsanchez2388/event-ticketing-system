# app/services/user_service.py
#
# PURPOSE
#   PostgreSQL logic for user accounts and order history.
#
# TO ADD
#   class DuplicateEmailError(Exception)
#       Raised when the UNIQUE email constraint is violated
#       (catch psycopg2.errors.UniqueViolation). The router returns 409.
#
#   def create_user(data: UserCreate) -> dict
#       INSERT into users ... RETURNING the new row.
#       Hash the password if the team stores one (never store plain text).
#
#   def get_user(user_id: int) -> dict | None
#       SELECT a single user.
#
#   def get_user_orders(user_id: int) -> list[dict]
#       Orders with their items, ticket types, events, and payment
#       (a 3+ table join). Shape: list[OrderResponse].
#
#   def get_tickets_purchased_by_user(user_id: int) -> list[dict]
#       Query 2: all tickets purchased by a particular user.
