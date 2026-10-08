from app.database.mongo import get_event_content_collection


def create_indexes():
    collection = get_event_content_collection()

    collection.create_index(
        "eventId",
        unique=True
    )

    collection.create_index("tags")
    collection.create_index("speakers.name")
    collection.create_index("genres")
    collection.create_index("reviews.rating")

    print("MongoDB indexes created.")


def list_indexes():
    collection = get_event_content_collection()

    indexes = collection.index_information()

    for name, info in indexes.items():
        print(name)
        print(info)
        print()

def explain_tag_query():
    collection = get_event_content_collection()

    explanation = collection.find(
        {"tags": "Tech"}
    ).explain()

    winning_plan = explanation["queryPlanner"]["winningPlan"]

    print("Explain result for tag query:")
    print(winning_plan)


if __name__ == "__main__":
    create_indexes()
    list_indexes()
    explain_tag_query()
