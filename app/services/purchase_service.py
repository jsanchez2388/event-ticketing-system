from typing import Any
import psycopg2.errors
from app.database.postgres import get_connection
from app.services.cache_service import invalidate_event

def purchase_ticket(
    user_id: int,
    ticket_type_id: int,
    quantity: int
) -> dict[str, Any] | None:
    """Buy tickets for a ticket type and invalidate the event's cached detail.

    The purchase runs as one transaction and is rolled back if any step fails.
    """
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Find the event_id for this ticket type so we can invalidate its cache after purchase
        cursor.execute(
            """
            SELECT event_id
            FROM ticket_types
            WHERE ticket_type_id = %s;
            """,
            (ticket_type_id,)
        )
        row = cursor.fetchone()
        event_id = row["event_id"] if row else None

        cursor.execute(
            """
            SELECT *
            FROM purchase_tickets(
                %s,
                %s,
                %s,
                'Wallet'
            );
            """,
            (
                user_id,
                ticket_type_id,
                quantity
            )
        )

        result = cursor.fetchone()

        conn.commit()
        cursor.close()

        if event_id is not None:
            invalidate_event(event_id)

        return result

    except psycopg2.errors.RaiseException as error:
        conn.rollback()

        message = (error.diag.message_primary or "").strip()

        raise ValueError(
            message or "The purchase could not be completed."
        ) from error

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
