# app/database/mongo.py
#
# PURPOSE
#   Connection setup for MongoDB (pymongo). Connection handling ONLY:
#   no queries or business logic belong here.
#
# TO ADD
#   Module-level variable
#       _client   A single pymongo.MongoClient shared by the whole app
#                 (MongoClient manages its own internal connection pool).
#
#   Constant
#       EVENT_CONTENT_COLLECTION = "event_content"
#
#   def init_client() -> None
#       Create the MongoClient from settings.mongo_uri. Called at startup.
#
#   def close_client() -> None
#       Close the client. Called at shutdown.
#
#   def get_database()
#       Return the pymongo Database named settings.mongo_db.
#
#   def get_event_content_collection()
#       Return the `event_content` Collection. Used by services, the Mongo
#       seed/query/index scripts, and the cross-database event endpoint.
#
# NOTES
#   - Documents link to PostgreSQL through the `eventId` field, which must
#     equal events.event_id.
