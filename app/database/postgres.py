# app/database/postgres.py
#
# PURPOSE
#   Connection setup for PostgreSQL (psycopg2). Connection handling ONLY:
#   no SQL queries or business logic belong here.
#
# TO ADD
#   Module-level variable
#       _pool   Connection pool (psycopg2.pool.ThreadedConnectionPool is a good
#               fit because FastAPI runs sync endpoints in a thread pool).
#
#   def init_pool() -> None
#       Create the pool using values from app.config.get_settings().
#       Called once at application startup (see lifespan in app/main.py).
#
#   def close_pool() -> None
#       Close all pooled connections. Called at application shutdown.
#
#   def get_connection()  (context manager, via contextlib.contextmanager)
#       Borrow a connection from the pool and always return it afterward, even
#       on error. Services use this, e.g. `with get_connection() as conn:`.
#       The caller is responsible for commit()/rollback(); this is important
#       for the purchase transaction in app/services/purchase_service.py.
#
#   def get_cursor(conn)  (optional helper)
#       Return a cursor using psycopg2.extras.RealDictCursor so rows come back
#       as dicts (easy to convert to JSON / Pydantic models).
#
# NOTES
#   - Always use parameterized queries (%s placeholders) in the services;
#     never build SQL with f-strings.
#   - Standalone scripts (demos, benchmark) should call init_pool() themselves
#     since they do not run the FastAPI lifespan.

from typing import Any, cast

import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import get_settings

def get_connection():
      settings = get_settings()

      return psycopg2.connect(
          settings.require("POSTGRES_CONNECTION_STRING"),
          cursor_factory=RealDictCursor
      )

def test_connection() -> dict[str, Any]:
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                current_database() AS database_name,
                current_user AS database_user;
            """
        )

        result = cast("dict[str, Any] | None", cursor.fetchone())

        cursor.close()

        if result is None:
            raise RuntimeError(
                "Health-check query returned no rows."
            )

        return result

    finally:
        conn.close()