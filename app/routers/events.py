from fastapi import APIRouter, HTTPException
from app.services.event_service import (
    get_all_events,
    get_event_detail
)
from app.services.content_service import get_event_content

router = APIRouter(
    prefix="/events",
    tags=["Events"]
)

@router.get("")
def list_events():
    """Return every event."""
    return get_all_events()

@router.get("/{event_id}/content")
def event_content(event_id: int):
    """Return the MongoDB content document for an event."""
    content = get_event_content(event_id)

    if content is None:
        raise HTTPException(
            status_code=404,
            detail="Event content not found"
        )

    return content

@router.get("/{event_id}")
def event_details(event_id: int):
    """Return an event's full detail, including content and popularity."""
    event = get_event_detail(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event
