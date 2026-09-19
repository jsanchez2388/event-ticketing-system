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
