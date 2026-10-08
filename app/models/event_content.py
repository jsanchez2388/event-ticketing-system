from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class Speaker(BaseModel):
    name: str
    organization: str| None = None
    topics: list[str] = []

class ScheduleItem(BaseModel):
    time: str
    session: str | None = None
    room: str | None = None
    activity: str | None = None

class Review(BaseModel):
    userId: int
    rating: int = Field(
        ge = 1,
        le = 5
    )
    comment: str
    createdAt: datetime | None = None

class ReviewCreate(BaseModel):
    userId: int
    rating: int = Field(
        ge=1,
        le=5
    )
    comment: str

class EventContent(BaseModel):
    model_config = ConfigDict(
        extra="allow"
    )

    eventId: int
    eventType: str
    title: str
    tags: list[str] = []
    reviews: list[Review] = []

    speakers: list[Speaker] | None = None
    schedule: list[ScheduleItem] | None = None
