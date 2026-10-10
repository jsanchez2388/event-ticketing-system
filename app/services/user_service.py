from typing import Any
from app.database.postgres import get_connection

def get_user(user_id: int) -> dict[str, Any] | None:
    """Return a single user from PostgreSQL by user_id, or None if not found."""
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                first_name,
                last_name,
                email,
                role,
                account_status,
                wallet_balance
            FROM users
            WHERE user_id = %s;
            """,
            (user_id,)
        )

        user = cursor.fetchone()
        cursor.close()

        return user

    finally:
        conn.close()

def get_users_by_ids(user_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Return multiple users from PostgreSQL keyed by user_id.

    Used to resolve the reviewers shown on an event's detail page.
    """
    if not user_ids:
        return {}

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                user_id,
                first_name,
                last_name
            FROM users
            WHERE user_id = ANY(%s);
            """,
            (user_ids,)
        )

        users = cursor.fetchall()
        cursor.close()

        return {
            user["user_id"]: user
            for user in users
        }

    finally:
        conn.close()
