# app/database/mongo.py
#
# PURPOSE
#   Connection setup for MongoDB (pymongo). Connection handling ONLY:
#   no queries or business logic belong here.
#
# NOTES
#   - Documents link to PostgreSQL through the `eventId` field, which must
#     equal events.event_id.

from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.config import get_settings

_client: MongoClient | None = None


def init_client() -> MongoClient:
    global _client

    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.require("MONGO_URI"))

    return _client


def close_client() -> None:
    global _client

    if _client is not None:
        _client.close()
        _client = None


def get_database() -> Database:
    client = init_client()

    return client[get_settings().require("MONGO_DB")]


def get_event_content_collection() -> Collection:
    return get_database()[get_settings().EVENT_CONTENT_COLLECTION]


def test_connection() -> dict[str, Any]:
    client = init_client()

    client.admin.command("ping")

    return {
        "status": "connected",
        "database": get_settings().MONGO_DB
    }