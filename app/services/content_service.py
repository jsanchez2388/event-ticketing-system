# app/services/content_service.py
#
# PURPOSE
#   MongoDB `event_content` operations used by the API
#   (descriptions, speakers, schedules, performers, reviews).
#
# TO ADD
#   def get_event_content(event_id: int) -> dict | None
#       find_one by eventId with a projection that excludes _id.
#       Used by GET /events/{id}/content and event_service.
#
#   def create_event_content(document: dict) -> None
#       insert_one a new content document (admin event creation).
#
#   def update_event_content(event_id: int, updates: dict) -> bool
#       update_one with $set; invalidate the event cache afterward.
#
#   def delete_event_content(event_id: int) -> bool
#       delete_one by eventId.
#
#   def add_review(event_id: int, review: ReviewCreate) -> dict
#       update_one with $push onto `reviews` (add a createdAt timestamp).
#       Check that the user exists in PostgreSQL (user_service.get_user) and,
#       optionally, that the user bought a ticket to this event.
#       Invalidate the event cache afterward.
#
#   def get_reviews(event_id: int, min_rating: int | None = None) -> list[dict]
#       Return an event's reviews, optionally filtered by rating.
#
#   def delete_review(event_id: int, user_id: int) -> bool
#       update_one with $pull; invalidate the event cache afterward.
#
#   def get_average_rating(event_id: int) -> float | None  (optional)
#       Aggregation over reviews.rating; useful for admin analytics.
