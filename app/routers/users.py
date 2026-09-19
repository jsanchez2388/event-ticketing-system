# app/routers/users.py
#
# PURPOSE
#   HTTP endpoints for user accounts and order history.
#   Keep thin: validate input -> call app/services/user_service.py -> return.
#
# TO ADD
#   router = APIRouter(prefix="/users", tags=["users"])
#
#   POST /users
#       def create_user(payload: UserCreate) -> UserResponse
#       status_code=201. Return 409 on DuplicateEmailError.
#
#   GET /users/{user_id}
#       def get_user(user_id: int) -> UserResponse
#       404 if not found.
#
#   GET /users/{user_id}/orders
#       def get_user_orders(user_id: int) -> list[OrderResponse]
#       Previous orders with items and payment. 404 if the user does not exist.
#
#   GET /users/{user_id}/tickets   (optional)
#       def get_user_tickets(user_id: int) -> list[OrderItemResponse]
#       Exposes Query 2.
#
# REGISTER
#   app.include_router(users.router) in app/main.py
