from pathlib import Path
from time import perf_counter
from app.database import redis as redis_db
from app.services.cache_service import get_ttl_remaining


from fastapi import (
    APIRouter,
    HTTPException,
    Request
)

from fastapi.templating import Jinja2Templates

from app.security import get_csrf_token

from app.services.web_service import (
    get_event_cards,
    get_event_page_details,
    get_trending_event_cards
)

from app.services.benchmark_service import (
    ARM_DATABASE,
    ARM_DATABASE_WARM,
    ARM_LABELS,
    ARM_REDIS,
    chart_available,
    load_results,
    results_generated_at,
    speedup,
    summarize_all
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
            "ttl_remaining": ttl_remaining,
            "cache_available": redis_db.is_available()
        }
    )


# ============================================================
# CACHE BENCHMARK RESULTS
# ============================================================

@router.get("/site/benchmark")
def website_benchmark(request: Request):

    results = load_results()

    summaries = summarize_all(results)

    metrics = [
        ("Minimum", "minimum"),
        ("Maximum", "maximum"),
        ("Average", "average"),
        ("Median", "median"),
        ("Std dev", "stdev")
    ]

    csrf_token = get_csrf_token(
        request
    )

    return templates.TemplateResponse(
        request=request,
        name="benchmark.html",
        context={
            "csrf_token": csrf_token,
            "arms": list(summaries),
            "arm_labels": ARM_LABELS,
            "summaries": summaries,
            "metrics": metrics,
            "run_count": len(results.get(ARM_REDIS, [])),
            "cache_speedup": speedup(results, ARM_DATABASE, ARM_REDIS),
            "connection_speedup": speedup(results, ARM_DATABASE, ARM_DATABASE_WARM),
            "datastore_speedup": speedup(results, ARM_DATABASE_WARM, ARM_REDIS),
            "chart_available": chart_available(),
            "generated_at": results_generated_at()
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