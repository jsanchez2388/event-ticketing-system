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
