# mongo/seed_event_content.py
#
# PURPOSE
#   Load sample documents into the MongoDB `event_content` collection.
#   Run from the repo root: python -m mongo.seed_event_content
#
# TO ADD
#   Constant SAMPLE_DOCUMENTS: list[dict]
#       One document per event in sql/seed.sql (eventId must match event_id).
#       Intentionally vary the structure by event type to show schema flexibility:
#         conference: tags, speakers[{name, organization, topics[]}],
#                     schedule[{time, session, room}], reviews[]
#         concert:    performers[], genres[], ageRestriction, reviews[]
#         sporting:   teams[], league, season
#         university: department, openToPublic, credits
#         workshop:   instructor{name, bio}, prerequisites[], materialsProvided
#         community:  organizer{name, contact}, accessibility[], familyFriendly
#       Include reviews with a range of ratings for the rating queries.
#
#   def clear_collection() -> None
#       delete_many({}) so the script can be re-run cleanly.
#
#   def seed_single_document() -> None
#       Demonstrate insert_one() with one document.
#
#   def seed_many_documents() -> None
#       Demonstrate insert_many() with the rest.
#
#   def main() -> None
#       Initialize the Mongo client (app.database.mongo), clear, seed, print counts.
#
#   if __name__ == "__main__": main()

from app.database.mongo import get_event_content_collection


SAMPLE_DOCUMENTS = [
    {
        "eventId": 101,
        "eventType": "Concert",
        "title": "Bruno Mars",
        "tags": ["Live Music", "Pop"],
        "genres": ["Pop", "R&B", "Funk"],
        "performers": ["Bruno Mars", "Anderson .Paak"],
        "ageRestriction": 18,
        "vip_packages": ["VIP Lounge Access"],
        "reviews": [
            {
                "userId": 402,
                "rating": 5,
                "comment": "Incredible stage energy!"
            }
        ]
    },
    {
        "eventId": 102,
        "eventType": "Conference",
        "title": "West Coast Data Science & AI Summit",
        "tags": ["Tech", "Machine Learning", "Data Mining"],
        "speakers": [
            {
                "name": "Dr. John Doe",
                "organization": "TechAI",
                "topics": [
                    "Predictive Modeling with XGBoost",
                    "Feature Engineering"
                ]
            }
        ],
        "schedule": [
            {
                "time": "09:00",
                "session": "Data Pipelines in Python",
                "room": "Main Hall"
            },
            {
                "time": "11:00",
                "session": "Scikit-learn Best Practices",
                "room": "Room B"
            }
        ],
        "reviews": []
    },
    {
        "eventId": 103,
        "eventType": "Sporting Event",
        "title": "Los Angeles Dodgers vs. San Diego Padres",
        "tags": ["Baseball", "MLB", "Live Sports"],
        "teams": {
            "home": "Los Angeles Dodgers",
            "away": "San Diego Padres"
        },
        "promotions": ["Dodger Bobblehead Night"],
        "stadium_rules": {
            "tailgateAllowed": False,
            "clearBagPolicy": True
        },
        "reviews": []
    },
    {
        "eventId": 104,
        "eventType": "University Event",
        "title": "CSUN Master of Science in Data Science Mixer",
        "tags": ["Networking", "Graduate", "CSUN"],
        "department": "Computer Science",
        "targetAudience": [
            "Current Students",
            "Alumni",
            "Faculty"
        ],
        "agenda": [
            {
                "time": "17:00",
                "activity": "Welcome Speech"
            },
            {
                "time": "17:30",
                "activity": "Faculty Introductions"
            },
            {
                "time": "18:00",
                "activity": "Catered Dinner"
            }
        ],
        "reviews": []
    },
    {
        "eventId": 105,
        "eventType": "Workshop",
        "title": "Urban Container Gardening & Propagation",
        "tags": ["Gardening", "Sustainability", "Hands-on"],
        "instructor": "Holly Jones",
        "skillLevel": "Beginner to Intermediate",
        "materialsProvided": [
            "Potting Soil",
            "Seedlings",
            "Containers"
        ],
        "topics": [
            "Growing Tomatoes and Basil",
            "Venus Flytrap Care",
            "Raised-bed Planning"
        ],
        "reviews": [
            {
                "userId": 815,
                "rating": 4,
                "comment": "Great tips on soil selection."
            }
        ]
    },
    {
        "eventId": 106,
        "eventType": "Community Event",
        "title": "Trail Cleanup & Hike",
        "tags": ["Volunteer", "Hiking", "Outdoors"],
        "kidFriendly": True,
        "accessibility": "South trails, unpaved",
        "schedule": [
            {
                "time": "08:00",
                "activity": "Gather and equipment handout"
            },
            {
                "time": "08:30",
                "activity": "Trail cleanup begins"
            },
            {
                "time": "12:00",
                "activity": "Group picnic"
            }
        ],
        "reviews": []
    }
]


def clear_collection():
    collection = get_event_content_collection()

    collection.delete_many({})

    print("Existing event content cleared.")


def seed_single_document():
    collection = get_event_content_collection()

    result = collection.insert_one(
        SAMPLE_DOCUMENTS[0]
    )

    print(
        f"Inserted one document: {result.inserted_id}"
    )


def seed_many_documents():
    collection = get_event_content_collection()

    result = collection.insert_many(
        SAMPLE_DOCUMENTS[1:]
    )

    print(
        f"Inserted {len(result.inserted_ids)} additional documents."
    )


def main():
    clear_collection()

    seed_single_document()

    seed_many_documents()

    collection = get_event_content_collection()

    print(
        f"Total documents: {collection.count_documents({})}"
    )


if __name__ == "__main__":
    main()