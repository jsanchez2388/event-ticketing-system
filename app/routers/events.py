# app/routers/events.py
#
# PURPOSE
#   Public event browsing endpoints, including the cross-database detail route.
#

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
    event = get_event_detail(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return event
