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
