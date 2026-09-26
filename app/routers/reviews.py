# app/routers/reviews.py
#
# PURPOSE
#   Endpoints for reviewing events (stored in MongoDB `event_content`).

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
    created = add_review(event_id, payload)

    if created is None:
        raise HTTPException(
            status_code=404,
            detail = "Event content not found"
        )

    return created

@router.get("/{event_id}/reviews")
def list_reviews(event_id: int, min_rating: int | None = Query(default = None, ge = 1, le = 5)):
    reviews = get_reviews(event_id, min_rating)

    if reviews is None:
        raise HTTPException(
            status_code = 404,
            detail = "Event content not found"
        )

    return reviews

@router.delete("/{event_id}/reviews/{user_id}")
def remove_review(event_id: int, user_id: int):
    success = delete_review(event_id, user_id)

    if not success:
        raise HTTPException(
            status_code = 404,
            detail = "Review not found"
        )

    return {"message": "Review deleted successfully"}