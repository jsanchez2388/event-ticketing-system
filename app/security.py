import hmac
import secrets

from fastapi import Request


CSRF_SESSION_KEY = "_csrf_token"


def get_csrf_token(request: Request) -> str:
    """
    Get the current CSRF token.

    If the session does not have one yet,
    create a cryptographically secure token.
    """

    token = request.session.get(CSRF_SESSION_KEY)

    if not token:
        token = secrets.token_urlsafe(32)

        request.session[CSRF_SESSION_KEY] = token

    return token


def rotate_csrf_token(request: Request) -> str:
    """
    Generate a new CSRF token.

    Useful after login/signup because the
    authentication state has changed.
    """

    token = secrets.token_urlsafe(32)

    request.session[CSRF_SESSION_KEY] = token

    return token


def validate_csrf_token(
    request: Request,
    submitted_token: str
) -> bool:
    """
    Compare the submitted form token with
    the token stored in the user's session.
    """

    session_token = request.session.get(
        CSRF_SESSION_KEY
    )

    if not session_token:
        return False

    if not submitted_token:
        return False

    return hmac.compare_digest(
        session_token,
        submitted_token
    )