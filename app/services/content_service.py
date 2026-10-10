from datetime import datetime, timezone
from typing import Any
from app.database.mongo import get_event_content_collection, optional
from app.models.event_content import ReviewCreate
from app.services.cache_service import invalidate_event

@optional(fallback=None)
def get_event_content(event_id: int) -> dict[str, Any] | None:
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


@optional(fallback=dict)
def get_event_content_by_ids(event_ids: list[int]) -> dict[int, dict[str, Any]]:
    """
    Return content documents for multiple events in a single MongoDB query.

    Args:
        event_ids (list[int]): The event IDs to retrieve content for.

    Returns:
        dict[int, dict]: Content documents keyed by event ID.
    """
    if not event_ids:
        return {}

    collection = get_event_content_collection()

    documents = collection.find(
        {
            "eventId": {
                "$in": event_ids
            }
        },
        {
            "_id": 0
        }
    )

    return {
        document["eventId"]: document
        for document in documents
    }


def add_review(event_id: int, review: ReviewCreate) -> dict[str, Any] | None:
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

    invalidate_event(event_id)

    return review_data

def get_reviews(
    event_id: int,
    min_rating: int | None = None
) -> list[dict[str, Any]] | None:
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

    reviews: list[dict[str, Any]] = document.get("reviews", [])

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

    if result.modified_count > 0:
        invalidate_event(event_id)
        return True

    return False

def create_event_content(document: dict[str, Any]) -> bool:
    """
    Create a new content document for the given event.
    Verifies that the event exists in PostgreSQL before creating.

    Args:
        document (dict): The content document to create.

    Returns:
        bool: True if the content was successfully created, otherwise False.
    """
    from app.services.event_service import get_event_by_id

    event_id = document.get("eventId")
    if event_id is None or get_event_by_id(event_id) is None:
        return False

    collection = get_event_content_collection()

    result = collection.insert_one(document)

    return result.inserted_id is not None


def update_event_content(
    event_id: int,
    updates: dict[str, Any],
    replace_flexible: bool = False
) -> bool:
    """
    Update MongoDB event content.

    When replace_flexible is True, Mongo fields that no longer
    apply to the selected event type are removed.

    Customer reviews are not removed here.
    """

    collection = get_event_content_collection()

    update_operation = {
        "$set": updates
    }

    if replace_flexible:

        flexible_fields = [
            "description",
            "tags",
            "speakers",
            "schedule",
            "performers",
            "genres",
            "ageRestriction",
            "metadata",
        ]

        fields_to_remove = {}

        for field in flexible_fields:

            if field not in updates:
                fields_to_remove[field] = ""

        if fields_to_remove:
            update_operation["$unset"] = fields_to_remove

    result = collection.update_one(
        {
            "eventId": event_id
        },
        update_operation
    )

    if result.matched_count > 0:

        invalidate_event(event_id)

        return True

    return False


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

    if result.deleted_count > 0:
        invalidate_event(event_id)
        return True

    return False

@optional(fallback=None)
def get_average_rating(event_id: int) -> float | None:
    """
    Calculate the average rating for the given event.
    Args:
        event_id (int): The ID of the event to calculate the average rating for.

    Returns:
        float | None: The average rating if found, otherwise None.
    """
    collection = get_event_content_collection()

    pipeline: list[dict[str, Any]] = [
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

    return round(float(result[0]["averageRating"]), 2)
