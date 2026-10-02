# app/routers/mongo_queries.py
#
# PURPOSE
#   API endpoints exposing the MongoDB queries (matching the structure of app/routers/analytics.py for SQL).
#   Provides query endpoints for easy demoing and testing.

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from mongo.queries import (
    query1_events_with_tag,
    query2_events_with_speaker,
    query3_reviews_above_rating,
    query4_speaker_org_and_topic,
    query5_concerts_by_genre,
    query6_age_restricted_or_tagged,
    query7_sessions_in_room,
    query8_add_review,
    query9_add_tag,
    query10_delete_low_reviews
)
from app.services.cache_service import invalidate_event

router = APIRouter(
    prefix="/mongo",
    tags=["MongoDB Queries"]
)


class MongoReviewPayload(BaseModel):
    userId: int
    rating: int = Field(ge=1, le=5)
    comment: str


# ============================================================
# QUERY 1: Find events by tag (arrays, find, projection)
# ============================================================
@router.get("/events/by-tag")
def events_by_tag(
    tag: str = Query(default="Tech", description="Tag to filter events by")
):
    return query1_events_with_tag(tag)


# ============================================================
# QUERY 2: Find events by speaker (dot notation, nested docs)
# ============================================================
@router.get("/events/by-speaker")
def events_by_speaker(
    name: str = Query(default="Dr. John Doe", description="Speaker name")
):
    return query2_events_with_speaker(name)


# ============================================================
# QUERY 3: Find reviews above a rating (comparison, arrays)
# ============================================================
@router.get("/reviews/above-rating")
def reviews_above_rating(
    min_rating: int = Query(default=4, ge=1, le=5, description="Minimum rating")
):
    return query3_reviews_above_rating(min_rating)


# ============================================================
# QUERY 4: Find speakers by organization and topic ($elemMatch)
# ============================================================
@router.get("/speakers/by-org-and-topic")
def speakers_by_org_and_topic(
    organization: str = Query(default="TechAI", description="Speaker organization"),
    topic: str = Query(default="Feature Engineering", description="Topic")
):
    return query4_speaker_org_and_topic(organization, topic)


# ============================================================
# QUERY 5: Find concerts by genre (arrays, filtering)
# ============================================================
@router.get("/concerts/by-genre")
def concerts_by_genre(
    genre: str = Query(default="Pop", description="Concert genre")
):
    return query5_concerts_by_genre(genre)


# ============================================================
# QUERY 6: Age restricted OR tagged ($or boolean operator)
# ============================================================
@router.get("/events/age-restricted-or-tagged")
def age_restricted_or_tagged(
    min_age: int = Query(default=18, ge=0, description="Minimum age restriction"),
    tag: str = Query(default="Live Music", description="Tag")
):
    return query6_age_restricted_or_tagged(min_age, tag)


# ============================================================
# QUERY 7: Conference sessions in a room (dot notation, projection)
# ============================================================
@router.get("/sessions/in-room")
def sessions_in_room(
    room: str = Query(default="Main Hall", description="Room name")
):
    return query7_sessions_in_room(room)


# ============================================================
# QUERY 8: Add review to event ($push onto reviews array)
# ============================================================
@router.post("/events/{event_id}/reviews")
def add_event_review(
    event_id: int,
    payload: MongoReviewPayload
):
    review_dict = payload.model_dump()
    result = query8_add_review(event_id, review_dict)
    if result["matched"] == 0:
        raise HTTPException(status_code=404, detail="Event content not found in MongoDB")
    invalidate_event(event_id)
    return {"status": "success", "result": result}


# ============================================================
# QUERY 9: Add tag to event ($addToSet updates)
# ============================================================
@router.post("/events/{event_id}/tags")
def add_event_tag(
    event_id: int,
    tag: str = Query(..., description="Tag to add")
):
    result = query9_add_tag(event_id, tag)
    if result["matched"] == 0:
        raise HTTPException(status_code=404, detail="Event content not found in MongoDB")
    invalidate_event(event_id)
    return {"status": "success", "result": result}


# ============================================================
# QUERY 10: Delete operation test (delete low reviews)
# ============================================================
@router.post("/test-delete")
def test_delete_query(
    event_id: int = Query(default=101, description="Event ID"),
    max_rating: int = Query(default=2, ge=1, le=5, description="Max rating to delete")
):
    result = query10_delete_low_reviews(event_id, max_rating)
    if result.get("modified", 0) > 0:
        invalidate_event(event_id)
    return {"status": "success", "result": result}
