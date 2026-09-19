# app/routers/admin.py
#
# PURPOSE
#   Administrator features: manage events and ticket types, monitor inventory,
#   review sales, analyze activity.
#
# TO ADD
#   router = APIRouter(prefix="/admin", tags=["admin"])
#
#   def require_admin(...)  (dependency, optional)
#       Simple check that the caller's user has role = ADMIN (e.g. user id
#       passed in a header). Full authentication is not required by the spec.
#
#   --- Event management ---
#   POST   /admin/events                     create_event(payload: EventCreate) -> EventSummary   (201)
#   PUT    /admin/events/{event_id}          update_event(event_id, payload: EventUpdate) -> EventSummary
#   DELETE /admin/events/{event_id}          delete_event(event_id) -> None                       (204)
#   PUT    /admin/events/{event_id}/content  update_event_content(event_id, payload: dict) -> dict
#
#   --- Ticket type management ---
#   POST /admin/events/{event_id}/ticket-types      create_ticket_type(event_id, payload: TicketTypeCreate) -> TicketTypeResponse (201)
#   PUT  /admin/ticket-types/{ticket_type_id}       update_ticket_type(ticket_type_id, payload: TicketTypeUpdate) -> TicketTypeResponse
#
#   --- Inventory monitoring ---
#   GET /admin/events/{event_id}/inventory          get_inventory(event_id) -> InventoryResponse          (Query 4)
#
#   --- Sales review ---
#   GET /admin/sales/tickets-sold                   tickets_sold_per_event()                             (Query 3)
#   GET /admin/sales/revenue                        revenue_per_event()                                  (Query 5)
#   GET /admin/sales/top-customers?limit=10         top_customers(limit)                                 (Query 6)
#   GET /admin/sales/above-threshold?threshold=N    events_above_threshold(threshold)                    (Query 7)
#   GET /admin/sales/monthly                        monthly_revenue()                                    (Query 8)
#
#   --- Activity analysis ---
#   GET /admin/analytics                            event_activity()
#       Sales (PostgreSQL) + trending scores (Redis) + average ratings (MongoDB).
#
# NOTES
#   - All mutating routes must invalidate the affected event's Redis cache
#     (handled inside the services).
