import hmac
import os
from pathlib import Path

from email_validator import (
    EmailNotValidError,
    validate_email
)

from fastapi import (
    APIRouter,
    Form,
    Request
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.security import (
    get_csrf_token,
    rotate_csrf_token,
    validate_csrf_token
)

from app.services.auth_service import (
    create_user,
    get_user_by_email,
    verify_password
)


router = APIRouter(
    prefix="/site",
    tags=["Authentication"]
)


APP_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)


def normalize_email(email: str):

    try:

        result = validate_email(
            email.strip(),
            check_deliverability=False
        )

        return result.normalized.lower()

    except EmailNotValidError:

        return None


# ============================================================
# SIGNUP PAGE
# ============================================================

@router.get("/signup")
def signup_page(request: Request):

    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="signup.html",
        context={
            "error": None,
            "csrf_token": csrf_token
        }
    )


# ============================================================
# SIGNUP
# ============================================================

@router.post("/signup")
def signup(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    admin_code: str = Form(""),
    csrf_token: str = Form(...)
):

    # --------------------------------------------------------
    # CSRF CHECK
    # --------------------------------------------------------

    if not validate_csrf_token(
        request,
        csrf_token
    ):

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Security token expired or invalid. "
                    "Please try again.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=403
        )


    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

    first_name = first_name.strip()
    last_name = last_name.strip()
    role = role.strip().lower()


    # --------------------------------------------------------
    # VALIDATE NAMES
    # --------------------------------------------------------

    if (
        len(first_name) < 1
        or len(first_name) > 100
    ):

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "First name must be between "
                    "1 and 100 characters.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    if (
        len(last_name) < 1
        or len(last_name) > 100
    ):

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Last name must be between "
                    "1 and 100 characters.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # VALIDATE EMAIL
    # --------------------------------------------------------

    email = normalize_email(email)

    if email is None:

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Please enter a valid email address.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # VALIDATE ROLE
    # --------------------------------------------------------

    if role not in (
        "user",
        "admin"
    ):

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Invalid account type.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # VALIDATE PASSWORD
    # --------------------------------------------------------

    password_bytes = password.encode("utf-8")

    if len(password_bytes) < 8:

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Password must be at least "
                    "8 characters.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    if len(password_bytes) > 72:

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Password is too long.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # DUPLICATE EMAIL
    # --------------------------------------------------------

    existing_user = get_user_by_email(
        email
    )

    if existing_user:

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "An account with that email "
                    "already exists.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # ADMIN CODE
    # --------------------------------------------------------

    if role == "admin":

        expected_admin_code = os.getenv(
            "ADMIN_SIGNUP_CODE"
        )

        if not expected_admin_code:

            return templates.TemplateResponse(
                request=request,
                name="signup.html",
                context={
                    "error":
                        "Admin registration is "
                        "currently unavailable.",
                    "csrf_token":
                        get_csrf_token(request)
                },
                status_code=500
            )


        if not hmac.compare_digest(
            admin_code,
            expected_admin_code
        ):

            return templates.TemplateResponse(
                request=request,
                name="signup.html",
                context={
                    "error":
                        "Invalid admin signup code.",
                    "csrf_token":
                        get_csrf_token(request)
                },
                status_code=403
            )


    # --------------------------------------------------------
    # CREATE USER
    # --------------------------------------------------------

    try:

        user = create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            role=role
        )

    except Exception:

        return templates.TemplateResponse(
            request=request,
            name="signup.html",
            context={
                "error":
                    "Unable to create account.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=400
        )


    # --------------------------------------------------------
    # CREATE SESSION
    # --------------------------------------------------------

    request.session.clear()

    request.session["user_id"] = (
        user["user_id"]
    )

    request.session["email"] = (
        user["email"]
    )

    request.session["role"] = (
        user["role"]
    )

    request.session["first_name"] = (
        user["first_name"]
    )

    # New token after authentication
    rotate_csrf_token(request)


    return RedirectResponse(
        url="/site/account",
        status_code=303
    )


# ============================================================
# LOGIN PAGE
# ============================================================

@router.get("/login")
def login_page(request: Request):

    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "csrf_token": csrf_token
        }
    )


# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...)
):

    # --------------------------------------------------------
    # CSRF CHECK
    # --------------------------------------------------------

    if not validate_csrf_token(
        request,
        csrf_token
    ):

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    "Security token expired or invalid. "
                    "Please try again.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=403
        )


    # --------------------------------------------------------
    # EMAIL VALIDATION
    # --------------------------------------------------------

    email = normalize_email(email)

    if email is None:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    "Incorrect email or password.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=401
        )


    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    user = get_user_by_email(
        email
    )

    if not user:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    "Incorrect email or password.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=401
        )


    # --------------------------------------------------------
    # CHECK PASSWORD
    # --------------------------------------------------------

    if not verify_password(
        password,
        user["password_hash"]
    ):

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    "Incorrect email or password.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=401
        )


    # --------------------------------------------------------
    # ACCOUNT STATUS
    # --------------------------------------------------------

    if user["account_status"] != "active":

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error":
                    "This account is not active.",
                "csrf_token":
                    get_csrf_token(request)
            },
            status_code=403
        )


    # --------------------------------------------------------
    # LOGIN SESSION
    # --------------------------------------------------------

    request.session.clear()

    request.session["user_id"] = (
        user["user_id"]
    )

    request.session["email"] = (
        user["email"]
    )

    request.session["role"] = (
        user["role"]
    )

    request.session["first_name"] = (
        user["first_name"]
    )


    # Rotate token after successful login
    rotate_csrf_token(request)


    return RedirectResponse(
        url="/site/account",
        status_code=303
    )


# ============================================================
# LOGOUT
# ============================================================

@router.post("/logout")
def logout(
    request: Request,
    csrf_token: str = Form(...)
):

    if not validate_csrf_token(
        request,
        csrf_token
    ):

        return RedirectResponse(
            url="/site",
            status_code=303
        )


    request.session.clear()

    return RedirectResponse(
        url="/site/login",
        status_code=303
    )