from pathlib import Path
from time import perf_counter
from app.services.cache_service import get_ttl_remaining


from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request
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