from fastapi import APIRouter, HTTPException, Query

from app.services.analytics_service import (
    get_events_by_venue,
    get_user_tickets,
    get_tickets_sold,
    get_event_inventory,
    get_event_revenue,
    get_top_customers,
    get_events_over_threshold,
    get_monthly_revenue
)


router = APIRouter(
    tags=["SQL Queries"]
)


# QUERY 1
@router.get("/venues/{venue_id}/events")
def events_at_venue(venue_id: int):
    return get_events_by_venue(venue_id)


# QUERY 2
@router.get("/users/{user_id}/tickets")
def tickets_for_user(user_id: int):
    return get_user_tickets(user_id)


# QUERY 3
@router.get("/analytics/tickets-sold")
def tickets_sold():
    return get_tickets_sold()


# QUERY 4
@router.get("/events/{event_id}/inventory")
def event_inventory(event_id: int):
    results = get_event_inventory(event_id)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Event inventory not found"
        )

    return results


# QUERY 5
@router.get("/analytics/revenue")
def event_revenue():
    return get_event_revenue()


# QUERY 6
@router.get("/analytics/top-customers")
def top_customers(
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    )
):
    return get_top_customers(limit)


# QUERY 7
@router.get("/analytics/events-over-threshold")
def events_over_threshold(
    threshold: float = Query(
        default=500.00,
        ge=0
    )
):
    return get_events_over_threshold(threshold)


# QUERY 8
@router.get("/analytics/monthly-revenue")
def monthly_revenue():
    return get_monthly_revenue()