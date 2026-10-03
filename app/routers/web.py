from pathlib import Path
from time import perf_counter
from app.services.cache_service import get_ttl_remaining

from fastapi.responses import RedirectResponse
from datetime import datetime


from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Form,
)

from fastapi.templating import Jinja2Templates

from app.security import get_csrf_token

from app.services.web_service import (
    get_event_cards,
    get_event_page_details,
    get_trending_event_cards
)

from app.services.admin_service import (
    get_admin_dashboard_data,
    get_all_venues,
    create_event,
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
# TRENDING EVENTS
# ============================================================

@router.get("/site/trending")
def website_trending(request: Request):

    events = get_trending_event_cards()

    csrf_token = get_csrf_token(
        request
    )

    return templates.TemplateResponse(
        request=request,
        name="trending.html",
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
    start = perf_counter()

    data = get_event_page_details(
        event_id
    )

    request_time_ms = (perf_counter() - start) * 1000

    if data is None:

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    ttl_remaining = get_ttl_remaining(event_id)

    csrf_token = get_csrf_token(
        request
    )

    return templates.TemplateResponse(
        request=request,
        name="event_detail.html",
        context={
            **data,
            "csrf_token": csrf_token,
            "request_time_ms": request_time_ms,
            "ttl_remaining": ttl_remaining
        }
    )


# ============================================================
# MONGO QUERIES DEMO
# ============================================================

@router.get("/mongo")
@router.get("/site/mongo-demo")
def website_mongo_demo(request: Request):
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="mongo_demo.html",
        context={
            "csrf_token": csrf_token
        }
    )
# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/site/admin")
def website_admin_dashboard(
    request: Request
):

    # Only administrator accounts may access this page.
    if request.session.get("role") != "admin":

        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )


    dashboard = get_admin_dashboard_data()

    csrf_token = get_csrf_token(
        request
    )


    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            **dashboard,
            "csrf_token": csrf_token
        }
    )

# ============================================================
# ADMIN - CREATE EVENT FORM
# ============================================================

@router.get("/site/admin/events/create")
def website_admin_create_event_form(request: Request):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    venues = get_all_venues()
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="admin_event_create.html",
        context={
            "venues": venues,
            "csrf_token": csrf_token,
            "error": None,
        }
    )


# ============================================================
# ADMIN - CREATE EVENT SUBMIT
# ============================================================

@router.post("/site/admin/events/create")
def website_admin_create_event(
    request: Request,
    venue_id: int = Form(...),
    title: str = Form(...),
    event_type: str = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
    status: str = Form("scheduled"),
    csrf_token: str = Form(...),
):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    expected_csrf_token = get_csrf_token(request)

    if csrf_token != expected_csrf_token:
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    venues = get_all_venues()

    try:
        start_value = datetime.fromisoformat(start_datetime)
        end_value = datetime.fromisoformat(end_datetime)

        if not title.strip():
            raise ValueError("Event title is required.")

        if not event_type.strip():
            raise ValueError("Event type is required.")

        create_event(
            venue_id=venue_id,
            title=title.strip(),
            event_type=event_type.strip(),
            start_datetime=start_value,
            end_datetime=end_value,
            status=status,
        )

    except Exception as error:
        return templates.TemplateResponse(
            request=request,
            name="admin_event_create.html",
            context={
                "venues": venues,
                "csrf_token": get_csrf_token(request),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/site/admin",
        status_code=303
    )
