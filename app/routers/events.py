# app/routers/events.py
#
# PURPOSE
#   Public event browsing endpoints, including the cross-database detail route.
#
# TO ADD
#   router = APIRouter(prefix="/events", tags=["events"])
#
#   GET /events
#       def list_events(event_type: EventType | None = None,
#                       city: str | None = None,
#                       limit: int = 50, offset: int = 0) -> list[EventSummary]
#       Calls event_service.list_events.
#
#   GET /events/{event_id}
#       def get_event(event_id: int) -> EventDetail
#       REQUIRED CROSS-DATABASE FEATURE: calls event_service.get_event_detail,
#       which uses Redis (cache + trending), PostgreSQL, and MongoDB.
#       404 if the event does not exist.
#
#   GET /events/{event_id}/content
#       def get_event_content(event_id: int) -> dict (or EventContent)
#       MongoDB only; calls content_service.get_event_content. 404 if missing.
#
#   GET /events/venue/{venue_id}   (or /venues/{venue_id}/events)
#       def list_events_by_venue(venue_id: int) -> list[EventSummary]
#       Exposes Query 1.
#
# NOTES
#   - Define /events/venue/{venue_id} BEFORE /events/{event_id}, or use a
#     separate venues router, to avoid route conflicts.
#   - Reviews are handled in routers/reviews.py.
from fastapi import APIRouter, HTTPException

from app.services.event_service import (
    get_all_events,
    get_event_by_id
)

from app.services.content_service import get_event_content

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.get("")
def list_events():
    return get_all_events()

@router.get("/{event_id}/content")
def event_content(event_id: int):
    content = get_event_content(event_id)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Event content not found"
        )

    return content

@router.get("/{event_id}")
def event_details(event_id: int):
    event = get_event_by_id(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event

