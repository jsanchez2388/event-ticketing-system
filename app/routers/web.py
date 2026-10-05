from app.services.cache_benchmark_service import run_cache_benchmark
from pathlib import Path
from time import perf_counter
from app.services.analytics_service import get_event_inventory
from fastapi.responses import RedirectResponse
from datetime import datetime

from app.services.cache_service import (
    get_ttl_remaining,
    is_event_cache_enabled,
    set_event_cache_enabled,
)


from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request,
    Form,
)
from fastapi.responses import RedirectResponse

from fastapi.templating import Jinja2Templates

from app.security import get_csrf_token, validate_csrf_token

from app.services.web_service import (
    get_event_cards,
    get_event_page_details,
    get_trending_event_cards
)

from app.models.event_content import ReviewCreate
from app.services.content_service import add_review

from app.services.admin_service import (
    get_admin_dashboard_data,
    get_all_venues,
    create_event,
    get_admin_event,
    update_event,
    get_admin_ticket_type,
    update_ticket_type,
    create_ticket_type,
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
# SUBMIT EVENT REVIEW

@router.post("/site/events/{event_id}/reviews")
def website_submit_review(
    request: Request,
    event_id: int,
    rating: int = Form(...),
    comment: str = Form(...),
    csrf_token: str = Form(...)
):
    user_id = request.session.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="You must be logged in to leave a review"
        )

    validate_csrf_token(
        request,
        csrf_token
    )

    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=400,
            detail="Rating must be between 1 and 5"
        )

    comment = comment.strip()

    if not comment:
        raise HTTPException(
            status_code=400,
            detail="Review comment cannot be empty"
        )

    review = ReviewCreate(
        userId=user_id,
        rating=rating,
        comment=comment
    )

    add_review(
        event_id,
        review
    )

    return RedirectResponse(
        url=f"/site/events/{event_id}",
        status_code=303
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

    cache_enabled = is_event_cache_enabled()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            **dashboard,
            "csrf_token": csrf_token,
            "cache_enabled": cache_enabled,
            "benchmark_result": None,
            "benchmark_error": None,
        }
    )


# ============================================================
# ADMIN - TOGGLE EVENT CACHE
# ============================================================

@router.post("/site/admin/cache/toggle")
def website_admin_toggle_cache(
    request: Request,
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    currently_enabled = is_event_cache_enabled()

    set_event_cache_enabled(
        not currently_enabled
    )

    return RedirectResponse(
        url="/site/admin",
        status_code=303
    )




# ============================================================
# ADMIN - CACHE PERFORMANCE BENCHMARK
# ============================================================

@router.post("/site/admin/cache/benchmark")
def website_admin_cache_benchmark(
    request: Request,
    event_id: int = Form(...),
    iterations: int = Form(10),
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    dashboard = get_admin_dashboard_data()

    cache_enabled = is_event_cache_enabled()

    try:
        benchmark_result = run_cache_benchmark(
            event_id=event_id,
            iterations=iterations
        )

        benchmark_error = None

    except Exception as error:
        benchmark_result = None
        benchmark_error = str(error)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            **dashboard,
            "csrf_token": get_csrf_token(request),
            "cache_enabled": cache_enabled,
            "benchmark_result": benchmark_result,
            "benchmark_error": benchmark_error,
        }
    )


# ============================================================
# ADMIN - CREATE EVENT FORM
# ============================================================

@router.get("/site/admin/events/create")
def website_admin_create_event_form(
    request: Request
):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    venues = get_all_venues()

    csrf_token = get_csrf_token(
        request
    )

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
# ADMIN - CREATE EVENT
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

    # Validate CSRF token.
    session_token = request.session.get(
        "csrf_token"
    )

    if (
        not session_token
        or csrf_token != session_token
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    venues = get_all_venues()

    try:

        start_value = datetime.fromisoformat(
            start_datetime
        )

        end_value = datetime.fromisoformat(
            end_datetime
        )

        new_event = create_event(
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
                "csrf_token": get_csrf_token(
                    request
                ),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url=f"/site/admin/events/{new_event['event_id']}/ticket-types/create",
        status_code=303,
    )

# ============================================================
# ADMIN - EDIT EVENT FORM
# ============================================================

@router.get("/site/admin/events/{event_id}/edit")
def website_admin_edit_event_form(
    request: Request,
    event_id: int
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    event = get_admin_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    venues = get_all_venues()

    ticket_types = get_event_inventory(event_id)

    return templates.TemplateResponse(
        request=request,
        name="admin_event_edit.html",
        context={
            "event": event,
            "venues": venues,
            "ticket_types": ticket_types,
            "csrf_token": get_csrf_token(request),
            "error": None,
        }
    )

# ============================================================
# ADMIN - EDIT EVENT SUBMIT
# ============================================================

@router.post("/site/admin/events/{event_id}/edit")
def website_admin_edit_event(
    request: Request,
    event_id: int,
    venue_id: int = Form(...),
    title: str = Form(...),
    event_type: str = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
    status: str = Form(...),
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    try:
        if not title.strip():
            raise ValueError("Event title is required.")

        if not event_type.strip():
            raise ValueError("Event type is required.")

        update_event(
            event_id=event_id,
            venue_id=venue_id,
            title=title.strip(),
            event_type=event_type.strip(),
            start_datetime=datetime.fromisoformat(
                start_datetime
            ),
            end_datetime=datetime.fromisoformat(
                end_datetime
            ),
            status=status,
        )

    except Exception as error:
        event = get_admin_event(event_id)
        ticket_types = get_event_inventory(event_id)
        return templates.TemplateResponse(
            request=request,
            name="admin_event_edit.html",
            context={
                "event": event,
                "ticket_types": ticket_types,
                "csrf_token": get_csrf_token(request),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/site/admin",
        status_code=303
    )


# ============================================================
# ADMIN - EDIT TICKET TYPE FORM
# ============================================================

@router.get(
    "/site/admin/ticket-types/{ticket_type_id}/edit"
)
def website_admin_edit_ticket_type_form(
    request: Request,
    ticket_type_id: int
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    ticket_type = get_admin_ticket_type(
        ticket_type_id
    )

    if ticket_type is None:
        raise HTTPException(
            status_code=404,
            detail="Ticket type not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="admin_ticket_type_edit.html",
        context={
            "ticket_type": ticket_type,
            "csrf_token": get_csrf_token(request),
            "error": None,
        }
    )


# ============================================================
# ADMIN - EDIT TICKET TYPE SUBMIT
# ============================================================

@router.post(
    "/site/admin/ticket-types/{ticket_type_id}/edit"
)
def website_admin_edit_ticket_type(
    request: Request,
    ticket_type_id: int,
    price: float = Form(...),
    total_quantity: int = Form(...),
    status: str = Form(...),
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    try:
        update_ticket_type(
            ticket_type_id=ticket_type_id,
            price=price,
            total_quantity=total_quantity,
            status=status,
        )

    except Exception as error:
        ticket_type = get_admin_ticket_type(
            ticket_type_id
        )

        return templates.TemplateResponse(
            request=request,
            name="admin_ticket_type_edit.html",
            context={
                "ticket_type": ticket_type,
                "csrf_token": get_csrf_token(
                    request
                ),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url="/site/admin",
        status_code=303
    )


# ============================================================
# ADMIN - DELETE EVENT
# ============================================================

@router.post("/site/admin/events/{event_id}/delete")
def website_admin_delete_event(
    request: Request,
    event_id: int,
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    from app.services.admin_service import delete_event

    try:
        delete_event(event_id)

    except ValueError as error:
        event = get_admin_event(event_id)

        if event is None:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        venues = get_all_venues()

        return templates.TemplateResponse(
            request=request,
            name="admin_event_edit.html",
            context={
                "event": event,
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
# ============================================================
# ADMIN - CREATE TICKET TYPE FORM
# ============================================================

@router.get(
    "/site/admin/events/{event_id}/ticket-types/create"
)
def website_admin_create_ticket_type_form(
    request: Request,
    event_id: int
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    event = get_admin_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return templates.TemplateResponse(
        request=request,
        name="admin_ticket_type_create.html",
        context={
            "event": event,
            "csrf_token": get_csrf_token(request),
            "error": None,
        }
    )


# ============================================================
# ADMIN - CREATE TICKET TYPE SUBMIT
# ============================================================

@router.post(
    "/site/admin/events/{event_id}/ticket-types/create"
)
def website_admin_create_ticket_type(
    request: Request,
    event_id: int,
    ticket_name: str = Form(...),
    price: float = Form(...),
    total_quantity: int = Form(...),
    minimum_purchase: int = Form(1),
    maximum_purchase: int = Form(10),
    status: str = Form("active"),
    csrf_token: str = Form(...),
):
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if csrf_token != get_csrf_token(request):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    try:
        create_ticket_type(
            event_id=event_id,
            ticket_name=ticket_name.strip(),
            price=price,
            total_quantity=total_quantity,
            minimum_purchase=minimum_purchase,
            maximum_purchase=maximum_purchase,
            status=status,
        )

    except Exception as error:
        event = get_admin_event(event_id)

        return templates.TemplateResponse(
            request=request,
            name="admin_ticket_type_create.html",
            context={
                "event": event,
                "csrf_token": get_csrf_token(request),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url=f"/site/admin/events/{event_id}/edit",
        status_code=303
    )