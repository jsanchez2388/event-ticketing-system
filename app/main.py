import os

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database.postgres import test_connection
from app.database.mongo import init_client, close_client
from app.routers.events import router as events_router
from app.routers.analytics import router as analytics_router
from app.routers.web import router as web_router
from app.routers.auth import router as auth_router
from app.routers.account import router as account_router
from app.routers.reviews import router as reviews_router

app = FastAPI(
    title="Event Ticketing System",
    description="COMP 642 Event Ticketing API",
    version="1.0.0"
)

# MongoDB connection lifecycle
@app.on_event("startup")
def startup_event():
    init_client()


@app.on_event("shutdown")
def shutdown_event():
    close_client()

# Login session support
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv(
        "SESSION_SECRET",
        "development-secret-change-me"
    ),
    same_site="lax",
    https_only=False
)


# API routes
app.include_router(events_router)
app.include_router(analytics_router)
app.include_router(reviews_router)

# Website routes
app.include_router(web_router)

# Login / signup routes
app.include_router(auth_router)

app.include_router(account_router)

# CSS
app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Event Ticketing System",
        "website": "/site",
        "signup": "/site/signup",
        "login": "/site/login",
        "docs": "/docs"
    }


@app.get("/health/database")
def database_health():
    try:
        result = test_connection()

        return {
            "status": "ok",
            "postgresql": "connected",
            "database": result["database_name"],
            "user": result["database_user"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"PostgreSQL connection failed: {str(e)}"
        )