# app/routers/reviews.py
#
# PURPOSE
#   Endpoints for reviewing events (stored in MongoDB `event_content`).
#
# TO ADD
#   router = APIRouter(prefix="/events", tags=["reviews"])
#
#   POST /events/{event_id}/reviews
#       def create_review(event_id: int, payload: ReviewCreate) -> Review
#       status_code=201. Calls content_service.add_review, which pushes to the
#       reviews array and invalidates the event cache.
#       404 if the event/content or user does not exist; 422 for invalid rating.
#
#   GET /events/{event_id}/reviews   (optional)
#       def list_reviews(event_id: int, min_rating: int | None = None) -> list[Review]
#
#   DELETE /events/{event_id}/reviews/{user_id}   (optional)
#       def delete_review(event_id: int, user_id: int) -> None
#       Demonstrates a Mongo update with $pull.

from fastapi import APIRouter, HTTPException, Query, status

from app.models.event_content import ReviewCreate
from app.services.content_service import (
    add_review,
    get_reviews,
    delete_review
)

router = APIRouter(
    prefix = "/events",
    tags = ["reviews"]
)

@router.post("/{event_id}/reviews", status_code = status.HTTP_201_CREATED)

def create_review(event_id: int, payload: ReviewCreate):
    success = add_review(event_id, payload)

    if not success:
        raise HTTPException(
            status_code=404,
            detail = "Event content not found"
        )

    return {"message": "Review added successfully"}

@router.get("/{event_id}/reviews")

def list_reviews(event_id: int, min_rating: int | None = Query(default = None, ge = 1, le = 5)):
    return get_reviews(event_id, min_rating)

@router.delete("/{event_id}/reviews/{user_id}")

def remove_review(event_id: int, user_id: int):
    success = delete_review(event_id, user_id)

    if not success:
        raise HTTPException(
            status_code = 404,
            detail = "Review not found"
        )

    return {"message": "Review deleted successfully"}