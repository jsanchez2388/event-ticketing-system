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
    """An incoming review posted onto a MongoDB event document."""
    userId: int
    rating: int = Field(ge=1, le=5)
    comment: str

@router.get("/events/by-tag")
def events_by_tag(
    tag: str = Query(default="Tech", description="Tag to filter events by")
):
    """Query 1: find events by tag (arrays, find, projection)."""
    return query1_events_with_tag(tag)

@router.get("/events/by-speaker")
def events_by_speaker(
    name: str = Query(default="Dr. John Doe", description="Speaker name")
):
    """Query 2: find events by speaker (dot notation, nested documents)."""
    return query2_events_with_speaker(name)

@router.get("/reviews/above-rating")
def reviews_above_rating(
    min_rating: int = Query(default=4, ge=1, le=5, description="Minimum rating")
):
    """Query 3: find reviews above a rating (comparison operators on arrays)."""
    return query3_reviews_above_rating(min_rating)

@router.get("/speakers/by-org-and-topic")
def speakers_by_org_and_topic(
    organization: str = Query(default="TechAI", description="Speaker organization"),
    topic: str = Query(default="Feature Engineering", description="Topic")
):
    """Query 4: find speakers by organization and topic ($elemMatch)."""
    return query4_speaker_org_and_topic(organization, topic)

@router.get("/concerts/by-genre")
def concerts_by_genre(
    genre: str = Query(default="Pop", description="Concert genre")
):
    """Query 5: find concerts by genre (array filtering)."""
    return query5_concerts_by_genre(genre)

@router.get("/events/age-restricted-or-tagged")
def age_restricted_or_tagged(
    min_age: int = Query(default=18, ge=0, description="Minimum age restriction"),
    tag: str = Query(default="Live Music", description="Tag")
):
    """Query 6: age-restricted or tagged events ($or boolean operator)."""
    return query6_age_restricted_or_tagged(min_age, tag)

@router.get("/sessions/in-room")
def sessions_in_room(
    room: str = Query(default="Main Hall", description="Room name")
):
    """Query 7: conference sessions in a room (dot notation, projection)."""
    return query7_sessions_in_room(room)

@router.post("/events/{event_id}/reviews")
def add_event_review(
    event_id: int,
    payload: MongoReviewPayload
):
    """Query 8: add a review to an event ($push onto the reviews array)."""
    review_dict = payload.model_dump()
    result = query8_add_review(event_id, review_dict)
    if result["matched"] == 0:
        raise HTTPException(status_code=404, detail="Event content not found in MongoDB")
    invalidate_event(event_id)
    return {"status": "success", "result": result}

@router.post("/events/{event_id}/tags")
def add_event_tag(
    event_id: int,
    tag: str = Query(..., description="Tag to add")
):
    """Query 9: add a tag to an event ($addToSet)."""
    result = query9_add_tag(event_id, tag)
    if result["matched"] == 0:
        raise HTTPException(status_code=404, detail="Event content not found in MongoDB")
    invalidate_event(event_id)
    return {"status": "success", "result": result}

@router.post("/test-delete")
def test_delete_query(
    event_id: int = Query(default=101, description="Event ID"),
    max_rating: int = Query(default=2, ge=1, le=5, description="Max rating to delete")
):
    """Query 10: delete an event's low-rated reviews."""
    result = query10_delete_low_reviews(event_id, max_rating)
    if result.get("modified", 0) > 0:
        invalidate_event(event_id)
    return {"status": "success", "result": result}
