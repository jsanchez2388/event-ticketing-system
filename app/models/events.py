# app/models/events.py
#
# PURPOSE
#   Pydantic schemas for events, venues, ticket types, and the combined
#   cross-database event detail response.
#   (Tables are defined in sql/schema.sql.)
#
# TO ADD
#   class EventType(str, Enum)
#       CONCERT, CONFERENCE, SPORTING, UNIVERSITY, WORKSHOP, COMMUNITY.
#
#   class VenueResponse(BaseModel)
#       venue_id, name, address, city, capacity.
#
#   class TicketTypeCreate(BaseModel)
#       Request body for creating a ticket type (admin).
#       Fields: name, price (Decimal), total_quantity.
#
#   class TicketTypeUpdate(BaseModel)
#       Partial update (all fields Optional): name, price, total_quantity.
#
#   class TicketTypeResponse(BaseModel)
#       ticket_type_id, event_id, name, price, total_quantity,
#       quantity_remaining.
#
#   class EventCreate(BaseModel)
#       Request body for POST /admin/events.
#       Fields: title, event_type, venue_id, start_time, end_time,
#       status, optional category ids (for the many-to-many table).
#
#   class EventUpdate(BaseModel)
#       Partial update, all fields Optional.
#
#   class EventSummary(BaseModel)
#       Lightweight row for GET /events (browse list):
#       event_id, title, event_type, start_time, venue_name, city,
#       min_price (optional).
#
#   class EventDetail(BaseModel)
#       Combined response for GET /events/{id} (cross-database feature):
#         From PostgreSQL: event fields, venue (VenueResponse),
#                          ticket_types (list[TicketTypeResponse])
#         From MongoDB:    content (dict or EventContent from event_content.py)
#         From Redis:      popularity_score (float | None), cache_hit (bool)
#
#   class InventoryResponse(BaseModel)
#       Result of Query 4 for GET /admin/events/{id}/inventory:
#       event_id, ticket_types with sold / remaining counts, totals.
#
# NOTES
#   - Use Decimal (not float) for prices to match NUMERIC in PostgreSQL.
#   - EventDetail must be JSON-serializable because it is cached in Redis
#     (model_dump_json / model_validate_json).
