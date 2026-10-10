from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class Speaker(BaseModel):
    """A speaker billed for an event."""
    name: str
    organization: str| None = None
    topics: list[str] = []

class ScheduleItem(BaseModel):
    """A single entry in an event's schedule."""
    time: str
    session: str | None = None
    room: str | None = None
    activity: str | None = None

class Review(BaseModel):
    """A review as stored in MongoDB."""
    userId: int
    rating: int = Field(ge = 1, le = 5)
    comment: str
    createdAt: datetime | None = None

class ReviewCreate(BaseModel):
    """An incoming review submission."""
    userId: int
    rating: int = Field(ge=1, le=5)
    comment: str

class EventContent(BaseModel):
    """Event content held in MongoDB, keyed by event_id.

    Extra keys are allowed so each event type can carry its own fields.
    """
    model_config = ConfigDict(extra="allow")
    eventId: int
    eventType: str
    title: str
    tags: list[str] = []
    reviews: list[Review] = []
    speakers: list[Speaker] | None = None
    schedule: list[ScheduleItem] | None = None
