import bcrypt

from app.database.postgres import get_connection


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str
) -> bool:

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def get_user_by_email(email: str):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # SAFE FROM SQL INJECTION:
        # email is passed separately using %s.
        cursor.execute(
            """
            SELECT
                user_id,
                first_name,
                last_name,
                email,
                password_hash,
                account_status,
                role,
                wallet_balance
            FROM users
            WHERE LOWER(email) = LOWER(%s);
            """,
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()

        return user

    finally:
        conn.close()


def create_user(
    first_name: str,
    last_name: str,
    email: str,
    password: str,
    role: str
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        password_hash = hash_password(password)

        if role == "admin":
            starting_balance = 1000.00
        else:
            starting_balance = 500.00

        # SAFE FROM SQL INJECTION:
        # Never insert user values directly into the SQL string.
        cursor.execute(
            """
            INSERT INTO users (
                first_name,
                last_name,
                email,
                password_hash,
                account_status,
                role,
                wallet_balance
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                'active',
                %s,
                %s
            )
            RETURNING
                user_id,
                first_name,
                last_name,
                email,
                role,
                wallet_balance;
            """,
            (
                first_name,
                last_name,
                email,
                password_hash,
                role,
                starting_balance
            )
        )

        user = cursor.fetchone()

        conn.commit()
        cursor.close()

        return user

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()