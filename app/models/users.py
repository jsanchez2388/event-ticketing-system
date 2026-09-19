# app/models/users.py
#
# PURPOSE
#   Pydantic schemas describing user data sent to and returned from the API.
#   (The actual `users` TABLE is defined in sql/schema.sql.)
#
# TO ADD
#   class UserRole(str, Enum)
#       Values: CUSTOMER, ADMIN. Mirrors the `role` column in `users`.
#
#   class UserCreate(BaseModel)
#       Request body for POST /users.
#       Fields: email (EmailStr or str), first_name, last_name, password (or
#       omit auth entirely if the team decides it is out of scope),
#       role (default CUSTOMER).
#
#   class UserResponse(BaseModel)
#       Returned from POST /users and user lookups.
#       Fields: user_id, email, first_name, last_name, role, created_at.
#       Must NOT include a password / password hash.
#
# NOTES
#   - EmailStr requires the `email-validator` package; plain str is fine too.
#   - Order history schemas live in app/models/orders.py.
