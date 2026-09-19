from app.database.postgres import get_connection


def get_account(user_id: int):

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


        cursor.execute(
            """
            SELECT
                o.order_id,
                o.order_date,
                o.status AS order_status,

                e.event_id,
                e.title,

                tt.ticket_name,

                oi.quantity,
                oi.unit_price,

                o.total_amount,

                p.payment_method,
                p.payment_status

            FROM orders AS o

            JOIN order_items AS oi
                ON o.order_id = oi.order_id

            JOIN ticket_types AS tt
                ON oi.ticket_type_id =
                   tt.ticket_type_id

            JOIN events AS e
                ON tt.event_id = e.event_id

            JOIN payments AS p
                ON o.order_id = p.order_id

            WHERE o.user_id = %s

            ORDER BY o.order_date DESC;
            """,
            (user_id,)
        )

        orders = cursor.fetchall()

        cursor.close()

        return {
            "user": user,
            "orders": orders
        }

    finally:
        conn.close()