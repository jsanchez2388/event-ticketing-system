from app.database.mongo import get_event_content_collection

def query1_events_with_tag(tag: str):
    """Query 1: find events carrying a tag (array match with projection)."""
    collection = get_event_content_collection()

    results = collection.find(
        {"tags": tag},
        {
            "_id": 0,
            "eventId": 1,
            "title": 1,
            "tags": 1
        }
    )

    return list(results)

def query2_events_with_speaker(name: str):
    """Query 2: find events featuring a speaker (dot notation into nested documents)."""
    collection = get_event_content_collection()

    results = collection.find(
        {"speakers.name": name},
        {"_id": 0}
    )

    return list(results)

def query3_reviews_above_rating(min_rating: int):
    """Query 3: find reviews rated above a threshold ($gt)."""
    collection = get_event_content_collection()

    results = collection.find(
        {
            "reviews.rating": {
                "$gt": min_rating
            }
        },
        {
            "_id": 0,
            "eventId": 1,
            "title": 1,
            "reviews": 1
        }
    )

    return list(results)

def query4_speaker_org_and_topic(
    organization: str,
    topic: str
):
    """Query 4: find speakers matching an organization and topic ($elemMatch)."""
    collection = get_event_content_collection()

    results = collection.find(
        {
            "speakers": {
                "$elemMatch": {
                    "organization": organization,
                    "topics": topic
                }
            }
        },
        {"_id": 0}
    )

    return list(results)

def query5_concerts_by_genre(genre: str):
    """Query 5: find concerts in a genre (array match)."""
    collection = get_event_content_collection()

    results = collection.find(
        {
            "eventType": "Concert",
            "genres": genre
        },
        {
            "_id": 0,
            "eventId": 1,
            "title": 1,
            "genres": 1
        }
    )

    return list(results)

def query6_age_restricted_or_tagged(
    min_age: int,
    tag: str
):
    """Query 6: find events restricted above a minimum age or carrying a tag ($or)."""
    collection = get_event_content_collection()

    results = collection.find(
        {
            "$or": [
                {
                    "ageRestriction": {
                        "$gte": min_age
                    }
                },
                {
                    "tags": tag
                }
            ]
        },
        {
            "_id": 0,
            "eventId": 1,
            "title": 1,
            "ageRestriction": 1,
            "tags": 1
        }
    )

    return list(results)

def query7_sessions_in_room(room: str):
    """Query 7: find conference sessions held in a room ($elemMatch with projection)."""
    collection = get_event_content_collection()

    results = collection.find(
        {
            "schedule.room": room
        },
        {
            "_id": 0,
            "eventId": 1,
            "title": 1,
            "schedule": {
                "$elemMatch": {
                    "room": room
                }
            }
        }
    )

    return list(results)

def query8_add_review(
    event_id: int,
    review: dict
):
    """Query 8: append a review to an event's reviews array ($push)."""
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$push": {
                "reviews": review
            }
        }
    )

    return {
        "matched": result.matched_count,
        "modified": result.modified_count
    }

def cleanup_query8_review():
    """Remove the review added by query 8 so the demo can be re-run ($pull)."""
    collection = get_event_content_collection()

    collection.update_one(
        {"eventId": 101},
        {
            "$pull": {
                "reviews": {
                    "userId": 402,
                    "rating": 5,
                    "comment": "Amazing concert!"
                }
            }
        }
    )

def query9_add_tag(
    event_id: int,
    tag: str
):
    """Query 9: add a tag to an event without duplicating it ($addToSet)."""
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$addToSet": {
                "tags": tag
            }
        }
    )

    return {
        "matched": result.matched_count,
        "modified": result.modified_count
    }

def query10_delete_low_reviews(
    event_id: int,
    max_rating: int
):
    """Query 10: remove an event's reviews at or below a rating ($pull with $lte)."""
    collection = get_event_content_collection()

    result = collection.update_one(
        {"eventId": event_id},
        {
            "$pull": {
                "reviews": {
                    "rating": {
                        "$lte": max_rating
                    }
                }
            }
        }
    )

    return {
        "matched": result.matched_count,
        "modified": result.modified_count
    }

if __name__ == "__main__":
    print("\nQUERY 1 - Events with tag 'Tech'")
    print(
        query1_events_with_tag("Tech")
    )

    print("\nQUERY 2 - Events with speaker Dr. John Doe")
    print(
        query2_events_with_speaker(
            "Dr. John Doe"
        )
    )

    print("\nQUERY 3 - Reviews above rating 4")
    print(
        query3_reviews_above_rating(4)
    )

    print("\nQUERY 4 - Speaker organization and topic")
    print(
        query4_speaker_org_and_topic(
            "TechAI",
            "Feature Engineering"
        )
    )

    print("\nQUERY 5 - Concerts by genre")
    print(
        query5_concerts_by_genre(
            "Pop"
        )
    )

    print("\nQUERY 6 - Age restricted OR tagged")
    print(
        query6_age_restricted_or_tagged(
            18,
            "Outdoors"
        )
    )

    print("\nQUERY 7 - Sessions in Main Hall")
    print(
        query7_sessions_in_room(
            "Main Hall"
        )
    )

    print("\nQUERY 8 - Add review")
    print(
        query8_add_review(
            101,
            {
                "userId": 402,
                "rating": 5,
                "comment": "Amazing concert!"
            }
        )
    )

    print("\nQUERY 9 - Add tag")
    print(
        query9_add_tag(
            101,
            "Featured"
        )
    )

    print("\nQUERY 10 - Delete reviews rated 4 or lower for event 105")
    print(
        query10_delete_low_reviews(105, 4)
    )

    cleanup_query8_review()
