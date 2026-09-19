from pathlib import Path

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request
)

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.security import (
    get_csrf_token,
    validate_csrf_token
)

from app.services.account_service import (
    get_account
)

from app.services.purchase_service import (
    purchase_ticket
)


router = APIRouter(
    prefix="/site",
    tags=["Account"]
)


APP_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)


# ============================================================
# MY ACCOUNT
# ============================================================

@router.get("/account")
def account_page(request: Request):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:

        return RedirectResponse(
            url="/site/login",
            status_code=303
        )


    data = get_account(
        user_id
    )


    if not data["user"]:

        request.session.clear()

        return RedirectResponse(
            url="/site/login",
            status_code=303
        )


    message = request.session.pop(
        "message",
        None
    )

    error = request.session.pop(
        "error",
        None
    )


    csrf_token = get_csrf_token(
        request
    )


    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "user": data["user"],
            "orders": data["orders"],
            "message": message,
            "error": error,
            "csrf_token": csrf_token
        }
    )


# ============================================================
# BUY TICKET
# ============================================================

@router.post("/buy/{ticket_type_id}")
def buy_ticket(
    request: Request,
    ticket_type_id: int,
    quantity: int = Form(...),
    csrf_token: str = Form(...)
):

    user_id = request.session.get(
        "user_id"
    )


    # User must be logged in
    if not user_id:

        return RedirectResponse(
            url="/site/login",
            status_code=303
        )


    # --------------------------------------------------------
    # CSRF CHECK
    # --------------------------------------------------------

    if not validate_csrf_token(
        request,
        csrf_token
    ):

        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token."
        )


    # --------------------------------------------------------
    # BASIC QUANTITY CHECK
    # --------------------------------------------------------

    if quantity <= 0:

        request.session["error"] = (
            "Ticket quantity must be "
            "greater than zero."
        )

        return RedirectResponse(
            url="/site/account",
            status_code=303
        )


    # --------------------------------------------------------
    # PURCHASE
    # --------------------------------------------------------

    try:

        result = purchase_ticket(
            user_id=user_id,
            ticket_type_id=ticket_type_id,
            quantity=quantity
        )


        request.session["message"] = (
            f"Purchase successful. "
            f"Order #{result['new_order_id']} "
            f"was created."
        )


    except Exception as e:

        request.session["error"] = str(e)


    return RedirectResponse(
        url="/site/account",
        status_code=303
    )