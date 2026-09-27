# mongo/queries.py
#
# PURPOSE
#   The 8+ required MongoDB queries, each in its own labeled function that
#   prints its results for the report.
#   Run from the repo root: python -m mongo.queries
#
# REQUIRED OPERATION COVERAGE (note which function covers each)
#   find(), projection, comparison operators, boolean operators,
#   nested documents, arrays, dot notation, $elemMatch, updates, deletes.
#   (insertOne/insertMany: seed_event_content.py; indexing: indexes.py)
#
# TO ADD
#   def query1_events_with_tag(tag: str)
#       find({"tags": tag}) with a projection of title and tags, excluding _id.
#       [find, arrays, projection]
#
#   def query2_events_with_speaker(name: str)
#       find({"speakers.name": name}).
#       [dot notation, nested documents]
#
#   def query3_events_with_review_rating_above(min_rating: int)
#       find({"reviews.rating": {"$gt": min_rating}}).
#       [comparison operators, arrays]
#
#   def query4_speaker_org_and_topic(organization: str, topic: str)
#       find({"speakers": {"$elemMatch": {"organization": ..., "topics": ...}}}).
#       [$elemMatch, nested documents]
#
#   def query5_concerts_by_genre(genre: str)
#       find({"genres": genre}).
#       [arrays]
#
#   def query6_age_restricted_or_tagged(min_age: int, tag: str)
#       find({"$or": [{"ageRestriction": {"$gte": min_age}}, {"tags": tag}]}).
#       [boolean operators, comparison operators]
#
#   def query7_conference_sessions_in_room(room: str)
#       find on "schedule.room", projecting only the matching schedule entries.
#       [dot notation, projection]
#
#   def query8_add_review(event_id: int, review: dict)
#       update_one({"eventId": ...}, {"$push": {"reviews": review}}).
#       [updates, arrays]
#
#   def query9_update_tags(event_id: int, tag: str)
#       update_one with $addToSet or $set.
#       [updates]
#
#   def query10_delete_low_reviews(event_id: int, max_rating: int)
#       update_one with $pull, and/or delete_one for a whole document.
#       [deletes]
#
#   def main() -> None
#       Initialize the client, run each query with sample arguments, print results.
#
#   if __name__ == "__main__": main()


from app.database.mongo import get_event_content_collection

# Query 1
def query1_events_with_tag(tag: str):
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

# Query 2
def query2_events_with_speaker(name: str):
    collection = get_event_content_collection()

    results = collection.find(
        {"speakers.name": name},
        {"_id": 0}
    )

    return list(results)

# Query 3
def query3_reviews_above_rating(min_rating: int):
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

# Query 4
def query4_speaker_org_and_topic(
    organization: str,
    topic: str
):
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

# Query 5
def query5_concerts_by_genre(genre: str):
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

# Query 6
def query6_age_restricted_or_tagged(
    min_age: int,
    tag: str
):
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

# Query 7
def query7_sessions_in_room(room: str):
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
                "elemMatch": {
                    "room": room
                }
            }
        }
    )

    return list(results)

# Query 8
def query8_add_review(
    event_id: int,
    review: dict
):
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

# Query 9
def query9_add_tag(
    event_id: int,
    tag: str
):
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

# Query 10
def query10_delete_low_reviews():
        collection = get_event_content_collection()

        test_document = {
            "eventId": 999,
            "eventType": "Test",
            "title": "Temporary Delete Test",
            "tags": ["Test"]

        }

        collection.insert_one(test_document)

        result = collection.delete_one(
            {"eventId": 999}
        )

        return {
            "deleted": result.deleted_count
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

    print("\nQUERY 10 - Delete temporary test document")
    print(
        query10_delete_low_reviews()
    )

    cleanup_query8_review()
