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

EVENT_CONTENT_COLLECTION = "event_content"


if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is missing. Add it to the .env file."
    )

if not MONGO_DB:
    raise RuntimeError(
        "MONGO_DB is missing. Add it to the .env file."
    )


_client = None


def init_client():
    global _client

    if _client is None:
        _client = MongoClient(MONGO_URI)


def close_client():
    global _client

    if _client is not None:
        _client.close()
        _client = None


def get_database():
    if _client is None:
        init_client()

    return _client[MONGO_DB]


def get_event_content_collection():
    database = get_database()

    return database[EVENT_CONTENT_COLLECTION]


def test_connection():
    if _client is None:
        init_client()

    _client.admin.command("ping")

    return {
        "status": "connected",
        "database": MONGO_DB
    }