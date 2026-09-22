# mongo/indexes.py
#
# PURPOSE
#   Create indexes on `event_content` and show that they are used.
#   Run from the repo root: python -m mongo.indexes
#
# TO ADD
#   def create_indexes() -> None
#       create_index("eventId", unique=True)   API lookups / link to PostgreSQL
#       create_index("tags")                    multikey index for tag searches
#       create_index("speakers.name")           speaker lookups
#       create_index("genres")                  concert genre filter
#       create_index("reviews.rating")          rating filters
#
#   def list_indexes() -> None
#       Print index_information() for the report.
#
#   def explain_query_example() -> None
#       Run find(...).explain() for a tag query and print whether it used
#       IXSCAN or COLLSCAN (evidence that indexing helps).
#
#   def main() -> None
#   if __name__ == "__main__": main()

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


def show_indexes():
    collection = get_event_content_collection()

    indexes = collection.index_information()

    for name, info in indexes.items():
        print(name)
        print(info)
        print()


if __name__ == "__main__":
    create_indexes()
    show_indexes()