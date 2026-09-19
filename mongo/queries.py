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
