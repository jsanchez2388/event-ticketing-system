# app/services/content_service.py
#
# PURPOSE
#   MongoDB `event_content` operations used by the API
#   (descriptions, speakers, schedules, performers, reviews).

from datetime import datetime, timezone
from app.database.mongo import get_event_content_collection
from app.models.event_content import ReviewCreate

def get_event_content(event_id: int) -> dict | None:
    """
    Return the content document for the given event, or None if not found.
    Args:
        event_id (int): The ID of the event to retrieve content for.

    Returns:
        dict | None: The content document if found, otherwise None.
    """
    collection = get_event_content_collection()

    document = collection.find_one(
        {"eventId": event_id},
        {"_id": 0}
    )

    return document

def add_review(event_id: int, review: ReviewCreate) -> dict | None:
    """
    Add a review to the given event's content document.
    Args:
        event_id (int): The ID of the event to add the review for.
        review (ReviewCreate): The review data to add.

    Returns:
        dict | None: The added review data if successful, otherwise None.
    """
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

    if result.matched_count == 0:
        return None

    return review_data

def get_reviews(event_id: int, min_rating: int | None = None) -> list[dict] | None:
    """
    Return the reviews for the given event, optionally filtered by minimum rating.
    Args:
        event_id (int): The ID of the event to retrieve reviews for.
        min_rating (int | None): The minimum rating to include in the results.

    Returns:
        list[dict] | None: A list of review documents if found, otherwise None.
    """
    collection = get_event_content_collection()

    document = collection.find_one(
        {"eventId": event_id},
        {"_id": 0, "reviews": 1}
    )

    if document is None:
        return None

    reviews = document.get("reviews", [])

    if min_rating is not None:
        reviews = [
            review
            for review in reviews
            if review.get("rating", 0) >= min_rating
        ]

    return reviews

def delete_review(event_id: int, user_id: int) -> bool:
    """
    Delete a review from the given event's content document.
    Args:
        event_id (int): The ID of the event to delete the review for.
        user_id (int): The ID of the user whose review should be deleted.

    Returns:
        bool: True if the review was successfully deleted, otherwise False.
    """
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

def create_event_content(document: dict) -> bool:
    """
    Create a new content document for the given event.
    Args:
        document (dict): The content document to create.

    Returns:
        bool: True if the content was successfully created, otherwise False.
    """
    collection = get_event_content_collection()

    result = collection.insert_one(document)

    return result.inserted_id is not None


def update_event_content(event_id: int, updates: dict) -> bool:
    """
    Update the content document for the given event.
    Args:
        event_id (int): The ID of the event to update the content for.
        updates (dict): The updates to apply to the content document.

    Returns:
        bool: True if the content was successfully updated, otherwise False.
    """
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$set": updates
        }
    )

    return result.matched_count > 0


def delete_event_content(event_id: int) -> bool:
    """
    Delete the content document for the given event.
    Args:
        event_id (int): The ID of the event to delete the content for.

    Returns:
        bool: True if the content was successfully deleted, otherwise False.
    """
    collection = get_event_content_collection()

    result = collection.delete_one(
        {"eventId": event_id}
    )

    return result.deleted_count > 0

def get_average_rating(event_id: int) -> float | None:
    """
    Calculate the average rating for the given event.
    Args:
        event_id (int): The ID of the event to calculate the average rating for.

    Returns:
        float | None: The average rating if found, otherwise None.
    """
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