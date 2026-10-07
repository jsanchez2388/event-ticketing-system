from app.services.cache_benchmark_service import run_cache_benchmark
import json
from pathlib import Path
from time import perf_counter
from datetime import datetime

from app.database import redis as redis_db
from app.services.analytics_service import (
    QUERY_SQL,
    get_events_by_venue,
    get_user_tickets,
    get_tickets_sold,
    get_event_inventory,
    get_event_revenue,
    get_top_customers,
    get_events_over_threshold,
    get_monthly_revenue,
)
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

from app.models.event_content import ReviewCreate
from app.services.content_service import (
    add_review,
    get_event_content,
    create_event_content,
    update_event_content,
)

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
            "ttl_remaining": ttl_remaining,
            "cache_available": redis_db.is_available()
        }
    )


# ============================================================
# CACHE BENCHMARK RESULTS
# ============================================================

@router.get("/site/benchmark")
def website_benchmark(request: Request):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

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
# POSTGRESQL QUERY DEMO
# ============================================================


@router.get("/site/postgres-demo")
def website_postgres_demo(request: Request):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    def optional_int(name):
        value = request.query_params.get(name)

        if value is None or value.strip() == "":
            return None

        try:
            return int(value)
        except ValueError:
            return None

    def safe_query(function):
        try:
            return function(), None
        except Exception as error:
            return [], str(error)

    venue_id = optional_int("venue_id")
    user_id = optional_int("user_id")
    event_id = optional_int("event_id")

    try:
        limit = int(
            request.query_params.get(
                "limit",
                "10"
            )
        )
    except ValueError:
        limit = 10

    limit = max(
        1,
        min(limit, 100)
    )

    try:
        threshold = float(
            request.query_params.get(
                "threshold",
                "0"
            )
        )
    except ValueError:
        threshold = 0.0

    # Query 1
    if venue_id is not None:
        q1, q1_error = safe_query(
            lambda: get_events_by_venue(
                venue_id
            )
        )
    else:
        q1 = []
        q1_error = None

    # Query 2
    if user_id is not None:
        q2, q2_error = safe_query(
            lambda: get_user_tickets(
                user_id
            )
        )
    else:
        q2 = []
        q2_error = None

    # Query 3
    q3, q3_error = safe_query(
        get_tickets_sold
    )

    # Query 4
    if event_id is not None:
        q4, q4_error = safe_query(
            lambda: get_event_inventory(
                event_id
            )
        )
    else:
        q4 = []
        q4_error = None

    # Query 5
    q5, q5_error = safe_query(
        get_event_revenue
    )

    # Query 6
    q6, q6_error = safe_query(
        lambda: get_top_customers(
            limit
        )
    )

    # Query 7
    q7, q7_error = safe_query(
        lambda: get_events_over_threshold(
            threshold
        )
    )

    # Query 8
    q8, q8_error = safe_query(
        get_monthly_revenue
    )

    return templates.TemplateResponse(
        request=request,
        name="postgres_demo.html",
        context={
            "csrf_token":
                get_csrf_token(request),

            "query_sql": QUERY_SQL,

            "venue_id": venue_id,
            "user_id": user_id,
            "event_id": event_id,
            "limit": limit,
            "threshold": threshold,

            "q1": q1,
            "q2": q2,
            "q3": q3,
            "q4": q4,
            "q5": q5,
            "q6": q6,
            "q7": q7,
            "q8": q8,

            "errors": {
                "q1": q1_error,
                "q2": q2_error,
                "q3": q3_error,
                "q4": q4_error,
                "q5": q5_error,
                "q6": q6_error,
                "q7": q7_error,
                "q8": q8_error,
            },
        }
    )


# ============================================================
# MONGO QUERIES DEMO
# ============================================================

@router.get("/mongo")
@router.get("/site/mongo-demo")
def website_mongo_demo(request: Request):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="mongo_demo.html",
        context={
            "csrf_token": csrf_token
        }
    )

# ============================================================
# POSTGRES QUERIES DEMO
# ============================================================

@router.get("/postgres")
def website_postgres_demo(request: Request):
    csrf_token = get_csrf_token(request)

    return templates.TemplateResponse(
        request=request,
        name="postgres_demo.html",
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

    if not validate_csrf_token(
        request,
        csrf_token
    ):
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



def _split_form_list(value: str) -> list[str]:

    if not value:
        return []

    value = value.replace("\n", ",")

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def _build_speakers(
    names: list[str] | None,
    organizations: list[str] | None,
    topics: list[str] | None,
) -> list[dict]:

    names = names or []
    organizations = organizations or []
    topics = topics or []

    speakers = []

    count = max(
        len(names),
        len(organizations),
        len(topics),
        0,
    )

    for index in range(count):

        name = (
            names[index].strip()
            if index < len(names)
            else ""
        )

        organization = (
            organizations[index].strip()
            if index < len(organizations)
            else ""
        )

        topic_text = (
            topics[index]
            if index < len(topics)
            else ""
        )

        if (
            not name
            and not organization
            and not topic_text.strip()
        ):
            continue

        speaker = {}

        if name:
            speaker["name"] = name

        if organization:
            speaker["organization"] = organization

        parsed_topics = _split_form_list(
            topic_text
        )

        if parsed_topics:
            speaker["topics"] = parsed_topics

        speakers.append(speaker)

    return speakers


def _build_schedule(
    times: list[str] | None,
    sessions: list[str] | None,
    rooms: list[str] | None,
) -> list[dict]:

    times = times or []
    sessions = sessions or []
    rooms = rooms or []

    schedule = []

    count = max(
        len(times),
        len(sessions),
        len(rooms),
        0,
    )

    for index in range(count):

        time_value = (
            times[index].strip()
            if index < len(times)
            else ""
        )

        session_value = (
            sessions[index].strip()
            if index < len(sessions)
            else ""
        )

        room_value = (
            rooms[index].strip()
            if index < len(rooms)
            else ""
        )

        if (
            not time_value
            and not session_value
            and not room_value
        ):
            continue

        schedule_item = {}

        if time_value:
            schedule_item["time"] = time_value

        if session_value:
            schedule_item["session"] = session_value

        if room_value:
            schedule_item["room"] = room_value

        schedule.append(schedule_item)

    return schedule


def _build_custom_metadata(
    keys: list[str] | None,
    values: list[str] | None,
) -> dict:

    keys = keys or []
    values = values or []

    metadata = {}

    for index, key in enumerate(keys):

        key = key.strip()

        if not key:
            continue

        value = (
            values[index].strip()
            if index < len(values)
            else ""
        )

        if value:
            metadata[key] = value

    return metadata


def _build_mongo_event_content(
    *,
    event_id: int,
    title: str,
    event_type: str,
    description: str,
    tags: str,

    performers: str,
    genres: str,
    age_restriction: str,

    speaker_names: list[str] | None,
    speaker_organizations: list[str] | None,
    speaker_topics: list[str] | None,

    schedule_times: list[str] | None,
    schedule_sessions: list[str] | None,
    schedule_rooms: list[str] | None,

    home_team: str,
    away_team: str,
    sport_name: str,
    league: str,

    department_organization: str,

    skill_level: str,
    materials_needed: str,

    organizer: str,
    community_category: str,

    metadata_keys: list[str] | None,
    metadata_values: list[str] | None,
) -> dict:

    content = {
        "eventId": event_id,
        "title": title.strip(),
        "eventType": event_type.strip(),
    }

    # ========================================================
    # COMMON MONGODB CONTENT
    # ========================================================

    if description.strip():

        content["description"] = (
            description.strip()
        )

    parsed_tags = _split_form_list(tags)

    if parsed_tags:
        content["tags"] = parsed_tags


    event_type_clean = (
        event_type.strip().lower()
    )

    metadata = _build_custom_metadata(
        metadata_keys,
        metadata_values,
    )


    # ========================================================
    # CONCERT
    # ========================================================

    if event_type_clean == "concert":

        parsed_performers = (
            _split_form_list(performers)
        )

        parsed_genres = (
            _split_form_list(genres)
        )

        if parsed_performers:
            content["performers"] = (
                parsed_performers
            )

        if parsed_genres:
            content["genres"] = (
                parsed_genres
            )

        if age_restriction.strip():

            age = int(
                age_restriction
            )

            if age < 0:
                raise ValueError(
                    "Age restriction cannot "
                    "be negative."
                )

            content["ageRestriction"] = age


    # ========================================================
    # SPEAKER-BASED EVENTS
    # ========================================================

    if event_type_clean in {
        "conference",
        "university",
        "workshop",
    }:

        speakers = _build_speakers(
            speaker_names,
            speaker_organizations,
            speaker_topics,
        )

        if speakers:
            content["speakers"] = speakers


    # ========================================================
    # SCHEDULE-BASED EVENTS
    # ========================================================

    if event_type_clean in {
        "conference",
        "university",
        "workshop",
        "community",
    }:

        schedule = _build_schedule(
            schedule_times,
            schedule_sessions,
            schedule_rooms,
        )

        if schedule:
            content["schedule"] = schedule


    # ========================================================
    # SPORT
    # ========================================================

    if event_type_clean == "sport":

        if home_team.strip():
            metadata["homeTeam"] = (
                home_team.strip()
            )

        if away_team.strip():
            metadata["awayTeam"] = (
                away_team.strip()
            )

        if sport_name.strip():
            metadata["sport"] = (
                sport_name.strip()
            )

        if league.strip():
            metadata["league"] = (
                league.strip()
            )


    # ========================================================
    # UNIVERSITY EVENT
    # ========================================================

    if event_type_clean == "university":

        if department_organization.strip():

            metadata[
                "departmentOrganization"
            ] = (
                department_organization.strip()
            )


    # ========================================================
    # WORKSHOP
    # ========================================================

    if event_type_clean == "workshop":

        if skill_level.strip():

            metadata["skillLevel"] = (
                skill_level.strip()
            )

        materials = _split_form_list(
            materials_needed
        )

        if materials:
            metadata[
                "materialsNeeded"
            ] = materials


    # ========================================================
    # COMMUNITY EVENT
    # ========================================================

    if event_type_clean == "community":

        if organizer.strip():

            metadata["organizer"] = (
                organizer.strip()
            )

        if community_category.strip():

            metadata[
                "communityCategory"
            ] = (
                community_category.strip()
            )


    if metadata:
        content["metadata"] = metadata

    return content


# ============================================================
# ADMIN - CREATE EVENT
# ============================================================

def _parse_csv_metadata(value: str) -> list[str]:
    """
    Convert comma-separated form input into a clean list.
    """
    if not value.strip():
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def _parse_json_list_metadata(
    value: str,
    field_name: str,
) -> list:
    """
    Convert JSON textarea input into a Python list.
    """
    if not value.strip():
        return []

    try:
        parsed = json.loads(value)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"{field_name} must contain valid JSON."
        ) from error

    if not isinstance(parsed, list):
        raise ValueError(
            f"{field_name} must be a JSON list."
        )

    return parsed


def _parse_age_restriction(value: str):
    """
    Convert optional age restriction into an integer.
    """
    if not value.strip():
        return None

    try:
        age = int(value)

    except ValueError as error:
        raise ValueError(
            "Age restriction must be a number."
        ) from error

    if age < 0:
        raise ValueError(
            "Age restriction cannot be negative."
        )

    return age

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

    # MongoDB common fields
    description: str = Form(""),
    tags: str = Form(""),

    # Concert
    performers: str = Form(""),
    genres: str = Form(""),
    age_restriction: str = Form(""),

    # Speakers
    speaker_name: list[str] | None = Form(None),
    speaker_organization: list[str] | None = Form(None),
    speaker_topics: list[str] | None = Form(None),

    # Schedule
    schedule_time: list[str] | None = Form(None),
    schedule_session: list[str] | None = Form(None),
    schedule_room: list[str] | None = Form(None),

    # Sport
    home_team: str = Form(""),
    away_team: str = Form(""),
    sport_name: str = Form(""),
    league: str = Form(""),

    # University
    department_organization: str = Form(""),

    # Workshop
    skill_level: str = Form(""),
    materials_needed: str = Form(""),

    # Community
    organizer: str = Form(""),
    community_category: str = Form(""),

    # Extra flexible metadata
    metadata_key: list[str] | None = Form(None),
    metadata_value: list[str] | None = Form(None),
):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if not validate_csrf_token(
        request,
        csrf_token
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    venues = get_all_venues()

    try:

        if not title.strip():
            raise ValueError(
                "Event title is required."
            )

        if not event_type.strip():
            raise ValueError(
                "Event type is required."
            )

        start_value = datetime.fromisoformat(
            start_datetime
        )

        end_value = datetime.fromisoformat(
            end_datetime
        )

        if end_value <= start_value:
            raise ValueError(
                "End date must be after start date."
            )

        # --------------------------------------------------
        # CREATE POSTGRESQL EVENT
        # --------------------------------------------------

        new_event = create_event(
            venue_id=venue_id,
            title=title.strip(),
            event_type=event_type.strip(),
            start_datetime=start_value,
            end_datetime=end_value,
            status=status,
        )

        event_id = new_event["event_id"]

        # --------------------------------------------------
        # BUILD FLEXIBLE MONGODB DOCUMENT
        # --------------------------------------------------

        mongo_content = _build_mongo_event_content(
            event_id=event_id,
            title=title,
            event_type=event_type,
            description=description,
            tags=tags,

            performers=performers,
            genres=genres,
            age_restriction=age_restriction,

            speaker_names=speaker_name,
            speaker_organizations=speaker_organization,
            speaker_topics=speaker_topics,

            schedule_times=schedule_time,
            schedule_sessions=schedule_session,
            schedule_rooms=schedule_room,

            home_team=home_team,
            away_team=away_team,
            sport_name=sport_name,
            league=league,

            department_organization=(
                department_organization
            ),

            skill_level=skill_level,
            materials_needed=materials_needed,

            organizer=organizer,
            community_category=(
                community_category
            ),

            metadata_keys=metadata_key,
            metadata_values=metadata_value,
        )

        # Reviews belong to customers.
        mongo_content["reviews"] = []

        create_event_content(
            mongo_content
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
                "mongo_content": {},
            },
            status_code=400,
        )

    return RedirectResponse(
        url=(
            f"/site/admin/events/"
            f"{event_id}/ticket-types/create"
        ),
        status_code=303,
    )

# ============================================================
# ADMIN - EDIT EVENT FORM
# ============================================================

@router.get("/site/admin/events/{event_id}/edit")
def website_admin_edit_event_form(
    request: Request,
    event_id: int,
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

    ticket_types = get_event_inventory(
        event_id
    )

    mongo_content = (
        get_event_content(event_id)
        or {}
    )

    return templates.TemplateResponse(
        request=request,
        name="admin_event_edit.html",
        context={
            "event": event,
            "venues": venues,
            "ticket_types": ticket_types,
            "mongo_content": mongo_content,
            "csrf_token": get_csrf_token(
                request
            ),
            "error": None,
        }
    )


# ============================================================
# ADMIN - EDIT EVENT SUBMIT
# ============================================================

@router.post(
    "/site/admin/events/{event_id}/edit"
)
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

    # MongoDB common fields
    description: str = Form(""),
    tags: str = Form(""),

    # Concert
    performers: str = Form(""),
    genres: str = Form(""),
    age_restriction: str = Form(""),

    # Speakers
    speaker_name: list[str] | None = Form(None),
    speaker_organization: list[str] | None = Form(None),
    speaker_topics: list[str] | None = Form(None),

    # Schedule
    schedule_time: list[str] | None = Form(None),
    schedule_session: list[str] | None = Form(None),
    schedule_room: list[str] | None = Form(None),

    # Sport
    home_team: str = Form(""),
    away_team: str = Form(""),
    sport_name: str = Form(""),
    league: str = Form(""),

    # University
    department_organization: str = Form(""),

    # Workshop
    skill_level: str = Form(""),
    materials_needed: str = Form(""),

    # Community
    organizer: str = Form(""),
    community_category: str = Form(""),

    # Additional metadata
    metadata_key: list[str] | None = Form(None),
    metadata_value: list[str] | None = Form(None),
):

    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access required"
        )

    if not validate_csrf_token(
        request,
        csrf_token
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token"
        )

    try:

        if not title.strip():
            raise ValueError(
                "Event title is required."
            )

        if not event_type.strip():
            raise ValueError(
                "Event type is required."
            )

        start_value = datetime.fromisoformat(
            start_datetime
        )

        end_value = datetime.fromisoformat(
            end_datetime
        )

        if end_value <= start_value:
            raise ValueError(
                "End date must be after start date."
            )

        # --------------------------------------------------
        # UPDATE POSTGRESQL
        # --------------------------------------------------

        update_event(
            event_id=event_id,
            venue_id=venue_id,
            title=title.strip(),
            event_type=event_type.strip(),
            start_datetime=start_value,
            end_datetime=end_value,
            status=status,
        )

        # --------------------------------------------------
        # BUILD CURRENT FLEXIBLE MONGO CONTENT
        # --------------------------------------------------

        mongo_content = _build_mongo_event_content(
            event_id=event_id,
            title=title,
            event_type=event_type,
            description=description,
            tags=tags,

            performers=performers,
            genres=genres,
            age_restriction=age_restriction,

            speaker_names=speaker_name,
            speaker_organizations=(
                speaker_organization
            ),
            speaker_topics=speaker_topics,

            schedule_times=schedule_time,
            schedule_sessions=(
                schedule_session
            ),
            schedule_rooms=schedule_room,

            home_team=home_team,
            away_team=away_team,
            sport_name=sport_name,
            league=league,

            department_organization=(
                department_organization
            ),

            skill_level=skill_level,
            materials_needed=(
                materials_needed
            ),

            organizer=organizer,
            community_category=(
                community_category
            ),

            metadata_keys=metadata_key,
            metadata_values=metadata_value,
        )

        existing_content = get_event_content(
            event_id
        )

        if existing_content is None:

            mongo_content["reviews"] = []

            create_event_content(
                mongo_content
            )

        else:

            update_event_content(
                event_id,
                mongo_content,
                replace_flexible=True,
            )

    except Exception as error:

        event = get_admin_event(
            event_id
        )

        venues = get_all_venues()

        ticket_types = get_event_inventory(
            event_id
        )

        mongo_content = (
            get_event_content(event_id)
            or {}
        )

        return templates.TemplateResponse(
            request=request,
            name="admin_event_edit.html",
            context={
                "event": event,
                "venues": venues,
                "ticket_types": ticket_types,
                "mongo_content": mongo_content,
                "csrf_token": get_csrf_token(
                    request
                ),
                "error": str(error),
            },
            status_code=400,
        )

    return RedirectResponse(
        url=(
            f"/site/admin/events/"
            f"{event_id}/edit"
        ),
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