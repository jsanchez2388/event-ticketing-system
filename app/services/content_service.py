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

from datetime import datetime, timezone
from app.database.mongo import get_event_content_collection
from app.models.event_content import ReviewCreate

def get_event_content(event_id: int):
    collection = get_event_content_collection()

    document = collection.find_one(
        {"eventId": event_id},
        {"_id": 0}
    )

    return document

def add_review(event_id: int, review: ReviewCreate):
    collection = get_event_content_collection()

    review_data = review.model_dump()
    review_data["createdAt"] = datetime.now(timezone.utc)

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$push": {
                "reviews": review_data
            }
        }
    )

    return result.modified_count > 0

def get_reviews(event_id: int, min_rating: int | None = None):
    collection = get_event_content_collection()

    document = collection.find_one(
        {"eventId": event_id},
        {"_id": 0, "reviews": 1}
    )

    if document is None:
        return []

    reviews = document.get("reviews", [])

    if min_rating is not None:
        reviews = [
            review
            for review in reviews
            if review.get("rating", 0) >= min_rating
        ]

    return reviews

def delete_review(event_id: int, user_id: int):
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$pull": {
                "reviews": {
                    "userId": user_id
                }
            }
        }
    )

    return result.modified_count > 0

def create_event_content(document: dict):
    collection = get_event_content_collection()

    result = collection.insert_one(document)

    return result.inserted_id is not None


def update_event_content(event_id: int, updates: dict):
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$set": updates
        }
    )

    return result.modified_count > 0


def delete_event_content(event_id: int):
    collection = get_event_content_collection()

    result = collection.delete_one(
        {"eventId": event_id}
    )

    return result.deleted_count > 0

def get_average_rating(event_id: int):
    collection = get_event_content_collection()

    pipeline = [
        {
            "$match": {
                "eventId": event_id
            }
        },
        {
            "$unwind": "$reviews"
        },
        {
            "$group": {
                "_id": "$eventId",
                "averageRating": {
                    "$avg": "$reviews.rating"
                }
            }
        }
    ]

    result = list(
        collection.aggregate(pipeline)
    )

    if not result:
        return None

    return round(result[0]["averageRating"],2)