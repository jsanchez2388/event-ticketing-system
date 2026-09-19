# app/main.py
#
# TO ADD
#   - A lifespan handler (contextlib.asynccontextmanager, passed as
#     FastAPI(lifespan=...)) that on startup calls:
#         app.database.postgres.init_pool()
#         app.database.mongo.init_client()
#         app.database.redis.init_client()
#     and on shutdown calls the matching close functions.
#   - Router registration:
#         app.include_router(users.router)
#         app.include_router(events.router)
#         app.include_router(orders.router)
#         app.include_router(reviews.router)
#         app.include_router(trending.router)
#         app.include_router(admin.router)
#   - Keep the health check below. Optionally extend it to ping all three
#     databases and report each one's status.

from fastapi import FastAPI

app = FastAPI(title="Event Ticketing System")


@app.get("/")
def health_check():
    return {"status": "ok"}
