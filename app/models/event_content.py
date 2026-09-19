# app/models/event_content.py
#
# PURPOSE
#   Pydantic schemas for MongoDB `event_content` documents and reviews.
#   The document model is intentionally flexible: different event types have
#   different fields.
#
# TO ADD
#   class Speaker(BaseModel)
#       name, organization, topics (list[str]).
#
#   class ScheduleItem(BaseModel)
#       time, session, room.
#
#   class Review(BaseModel)
#       userId (int, references users.user_id in PostgreSQL), rating (1-5),
#       comment, createdAt (datetime).
#
#   class ReviewCreate(BaseModel)
#       Request body for POST /events/{id}/reviews:
#       user_id, rating (validate 1-5), comment.
#
#   class EventContent(BaseModel)
#       Common fields: eventId, title, description, tags (list[str]),
#       reviews (list[Review]).
#       Optional type-specific fields, e.g.:
#         conference: speakers (list[Speaker]), schedule (list[ScheduleItem])
#         concert:    performers (list[str]), genres (list[str]),
#                     ageRestriction (int)
#         sporting:   teams, league, season
#         workshop:   instructor, prerequisites, materialsProvided
#       Configure model_config = ConfigDict(extra="allow") so unknown fields
#       are kept, which preserves the flexible-schema advantage.
#
#   class EventContentCreate / EventContentUpdate(BaseModel)  (optional)
#       Used by admin endpoints to create or edit content documents.
#
# NOTES
#   - Field names use camelCase to match the documents stored in MongoDB.
#   - Exclude Mongo's `_id` (ObjectId) from API responses or convert it to str.
