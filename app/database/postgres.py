from typing import Any, cast
import psycopg2
from psycopg2.extras import RealDictConnection, RealDictCursor

from app.config import get_settings

def get_connection() -> RealDictConnection:
      """Returns a connection to the PostgreSQL database."""
      settings = get_settings()

      return cast(
          RealDictConnection,
          psycopg2.connect(
              settings.require("POSTGRES_CONNECTION_STRING"),
              cursor_factory=RealDictCursor
          )
      )

def test_connection() -> dict[str, Any]:
    """Tests the connection to the PostgreSQL database."""
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

        result = cursor.fetchone()

        cursor.close()

        if result is None:
            raise RuntimeError(
                "Health-check query returned no rows."
            )

        return result

    finally:
        conn.close()
