from pathlib import Path

from fastapi import (
    APIRouter,
    HTTPException,
    Request
)

from fastapi.templating import Jinja2Templates

from app.security import get_csrf_token

from app.services.web_service import (
    get_event_cards,
    get_event_page_details
)


router = APIRouter(
    tags=["Website"]
)


APP_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(APP_DIR / "templates")
)


# ============================================================
# WEBSITE HOME
# ============================================================

@router.get("/site")
def website_home(request: Request):

    events = get_event_cards()

    csrf_token = get_csrf_token(
        request
    )

    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "events": events,
            "csrf_token": csrf_token
        }
    )


# ============================================================
# EVENT DETAILS
# ============================================================

@router.get("/site/events/{event_id}")
def website_event_details(
    request: Request,
    event_id: int
):

    data = get_event_page_details(
        event_id
    )

    if data is None:

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )


    csrf_token = get_csrf_token(
        request
    )


    return templates.TemplateResponse(
        request=request,
        name="event_detail.html",
        context={
            **data,
            "csrf_token": csrf_token
        }
    )