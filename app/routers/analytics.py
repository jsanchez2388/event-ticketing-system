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

@router.get("/venues/{venue_id}/events")
def events_at_venue(venue_id: int):
    """Query 1: events scheduled at a venue."""
    return get_events_by_venue(venue_id)

@router.get("/users/{user_id}/tickets")
def tickets_for_user(user_id: int):
    """Query 2: tickets belonging to a user."""
    return get_user_tickets(user_id)

@router.get("/analytics/tickets-sold")
def tickets_sold():
    """Query 3: tickets sold per event."""
    return get_tickets_sold()

@router.get("/events/{event_id}/inventory")
def event_inventory(event_id: int):
    """Query 4: remaining inventory for an event's ticket types."""
    results = get_event_inventory(event_id)

    if not results:
        raise HTTPException(
            status_code=404,
            detail="Event inventory not found"
        )

    return results

@router.get("/analytics/revenue")
def event_revenue():
    """Query 5: revenue per event."""
    return get_event_revenue()

@router.get("/analytics/top-customers")
def top_customers(
    limit: int = Query(
        default=10,
        ge=1,
        le=100
    )
):
    """Query 6: customers ranked by total spend."""
    return get_top_customers(limit)

@router.get("/analytics/events-over-threshold")
def events_over_threshold(
    threshold: float = Query(
        default=500.00,
        ge=0
    )
):
    """Query 7: events whose revenue exceeds a threshold."""
    return get_events_over_threshold(threshold)

@router.get("/analytics/monthly-revenue")
def monthly_revenue():
    """Query 8: revenue grouped by month."""
    return get_monthly_revenue()
