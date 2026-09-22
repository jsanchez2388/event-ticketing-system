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

import os

from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()


MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")


if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is missing. Add it to the .env file."
    )

if not MONGO_DB:
    raise RuntimeError(
        "MONGO_DB is missing. Add it to the .env file."
    )


client = MongoClient(MONGO_URI)

database = client[MONGO_DB]

event_content = database["event_content"]


def get_database():
    return database


def get_event_content_collection():
    return event_content


def test_connection():
    client.admin.command("ping")

    return {
        "status": "connected",
        "database": MONGO_DB
    }