# Event Ticketing System — Project Guide

This guide maps every project requirement to a location in the repository, so each team member knows **what to build and where to put it**. It describes responsibilities and expected contents only; implementation is left to the team.

---

## 1. Architecture at a Glance

```
                Client (Swagger UI at /docs, curl, Postman)
                                |
                                v
                  FastAPI application (app/)
                                |
         +----------------------+----------------------+
         |                      |                      |
         v                      v                      v
    PostgreSQL               MongoDB                 Redis
  (system of record)    (flexible content)      (speed layer)
  users, events,        event_content:          event cache (TTL),
  venues, ticket        tags, speakers,         trending sorted set
  types, orders,        schedules, performers,
  order items,          genres, reviews
  payments
```

**Rule of thumb for deciding where data lives:**

| If the data is...                                               | Store it in    |
|-----------------------------------------------------------------|----------------|
| Structured, related, needs constraints or transactions (money, inventory, accounts) | PostgreSQL |
| Varies in shape by event type, nested, or list-heavy (speakers, schedules, reviews) | MongoDB |
| Derived, temporary, or needs sub-millisecond access (cached summaries, popularity scores) | Redis |

> **SQL choice:** The skeleton uses **PostgreSQL** (`psycopg2-binary`). If the team switches to MySQL, swap the driver to `pymysql` and adjust the DDL syntax (e.g. `SERIAL` → `AUTO_INCREMENT`).

---

## 2. Target Directory Layout

Files marked ✅ already exist. Everything else is to be created.

```
event-ticketing-system/
├── .env.example                 # Template for connection settings (no real secrets)
├── .gitignore                   ✅
├── requirements.txt             ✅
├── README.md                    # How to install, seed, and run
├── PROJECT_GUIDE.md             ✅ (this file)
│
├── app/                         # ── Application / API layer ──
│   ├── __init__.py              ✅
│   ├── main.py                  ✅ FastAPI instance; register routers here
│   ├── config.py                # Reads connection settings from environment
│   │
│   ├── database/                # Connection setup ONLY (no business logic)
│   │   ├── __init__.py          ✅
│   │   ├── postgres.py          # PostgreSQL connection / connection pool
│   │   ├── mongo.py             # MongoClient + handle to `event_content`
│   │   └── redis.py             # Redis client (import as `from app.database import redis as redis_db`)
│   │
│   ├── models/                  # Data shapes
│   │   ├── __init__.py          ✅
│   │   ├── users.py             # Pydantic request/response schemas
│   │   ├── events.py
│   │   ├── orders.py
│   │   └── event_content.py     # Pydantic schemas for Mongo documents & reviews
│   │
│   ├── services/                # Business logic that routers call
│   │   ├── __init__.py
│   │   ├── purchase_service.py  # The ticket-purchase TRANSACTION
│   │   ├── event_service.py     # Cross-database GET /events/{id} flow + event/ticket type mgmt
│   │   ├── content_service.py   # MongoDB event content + reviews
│   │   ├── user_service.py      # Accounts + order history (Query 2)
│   │   ├── sales_service.py     # Admin sales/analytics (Queries 3-8)
│   │   ├── cache_service.py     # Redis cache-aside helpers + TTL
│   │   └── trending_service.py  # Redis sorted-set helpers
│   │
│   └── routers/                 # HTTP endpoints (thin: validate → call service → return)
│       ├── __init__.py          ✅
│       ├── users.py             # /users
│       ├── events.py            # /events, /events/{id}, /events/{id}/content
│       ├── orders.py            # /orders
│       ├── reviews.py           # /events/{id}/reviews
│       ├── trending.py          # /trending
│       └── admin.py             # /admin/... (event mgmt, inventory, sales, analytics)
│
├── sql/                         # ── Part A: Relational ──
│   ├── schema.sql               # CREATE TABLE statements, constraints, indexes
│   ├── seed.sql                 # Sample data
│   ├── queries.sql              # The 8+ required queries, labeled Query 1–8
│   └── transaction_demo.sql     # (Optional) standalone BEGIN/COMMIT/ROLLBACK demo
│
├── mongo/                       # ── Part B: MongoDB ──
│   ├── seed_event_content.py    # insertOne / insertMany sample documents
│   ├── queries.py               # The 8+ required queries, labeled
│   └── indexes.py               # createIndex calls
│
├── redis_demo/                  # ── Part C: Redis ──
│   ├── cache_demo.py            # Shows MISS → DB → populate → HIT
│   └── trending_demo.py         # Simulates views, prints Top 10
│
├── experiments/                 # ── Performance experiment ──
│   ├── cache_benchmark.py       # Runs A (no cache) and B (cache) ≥ 10 times each
│   ├── results.csv              # Raw timings
│   └── plot_results.py          # Produces the comparison chart
│
└── docs/                        # ── Report deliverables ──
    ├── architecture_diagram.png # Your OWN diagram (required)
    ├── er_diagram.png           # Complete relational model (required)
    ├── cache_benchmark.png      # Visualization output
    └── report.md                # Final report: analysis + answers to Q1–Q6
```

> **Why `services/`?** Routers should stay thin. Placing the transaction, cache, and cross-database logic in services makes it reusable: the benchmark script and demos can call it directly without going through HTTP.

> **Why `sql/` and `mongo/` at the top level?** Graders need to see the schema, seed data, and required queries as clearly labeled, standalone artifacts, separate from application code.

---

## 3. Configuration

### `.env.example`
List the variables the app expects, with placeholder values only:
- PostgreSQL host, port, database name, user, password
- MongoDB URI and database name
- Redis host and port
- Cache TTL in seconds

Each developer copies it to `.env` (already in `.gitignore`) and fills in local values.

### `app/config.py`
Reads those variables from the environment in one place. Every other module imports settings from here instead of hard-coding them.

### Possible additions to `requirements.txt`
| Package          | Purpose                                        |
|------------------|------------------------------------------------|
| `python-dotenv`  | Load `.env` automatically                      |
| `pydantic-settings` | Typed settings in `config.py` (optional)    |
| `httpx`          | FastAPI `TestClient` and benchmark HTTP calls  |
| `matplotlib`     | Benchmark visualization                        |

---

## 4. Part A — PostgreSQL

### 4.1 `sql/schema.sql`

**Required tables and suggested responsibilities:**

| Table          | Purpose / key columns to think about                          | Relationships |
|----------------|----------------------------------------------------------------|---------------|
| `users`        | Account info; **UNIQUE email**; a `role` column (customer/admin) | 1–many → orders |
| `venues`       | Name, address, city, capacity                                  | 1–many → events |
| `events`       | Title, event type/category, start datetime, status             | many–1 → venues; 1–many → ticket_types |
| `ticket_types` | Name (GA, VIP…), price, total quantity, **quantity remaining** | many–1 → events |
| `orders`       | Order date, status, total amount                               | many–1 → users; 1–many → order_items; 1–1 → payments |
| `order_items`  | Quantity, unit price *at time of purchase*                     | many–1 → orders; many–1 → ticket_types |
| `payments`     | Amount, method, status, timestamp                              | many–1 (or 1–1) → orders |

**Many-to-many requirement:** `orders` ↔ `ticket_types` through `order_items` already qualifies. A second, clearer example could be something like:
- `categories` + `event_categories` junction table (an event can be both "University" and "Workshop"), or
- `event_organizers` linking admin users to the events they manage.

**The schema must visibly demonstrate:**
- [ ] Primary keys on every table
- [ ] Foreign keys with referential integrity (decide on `ON DELETE` behavior deliberately)
- [ ] Appropriate data types (`NUMERIC` for money, never floats; `TIMESTAMP` for dates)
- [ ] `NOT NULL` on required columns
- [ ] `UNIQUE` where appropriate (user email, composite unique on junction tables, one ticket type name per event)
- [ ] `CHECK` constraints are a bonus (price ≥ 0, quantity remaining ≥ 0)
- [ ] One-to-many relationships
- [ ] At least one many-to-many relationship
- [ ] Indexes on foreign keys and frequently filtered columns (e.g. `events.venue_id`, `events.start_time`, `orders.user_id`)

### 4.2 `sql/seed.sql`
Enough data to make every query return interesting results:
- Several venues and users (including at least one admin)
- Events covering **all six types**: concerts, conferences, sporting events, university events, workshops, community events
- Multiple ticket types per event
- Orders spread across **several months** (Query 8 needs this)
- Some users buying far more than others (Query 6 needs this)
- Some events selling above and below the threshold (Query 7 needs this)

> Keep the event IDs consistent with the `eventId` values used in MongoDB.

### 4.3 `sql/queries.sql`
Label each query with a comment matching the requirement number.

| #  | Question                                          | Tables likely involved                       |
|----|---------------------------------------------------|----------------------------------------------|
| 1  | All events at a particular venue                  | events, venues                               |
| 2  | All tickets purchased by a particular user        | users, orders, order_items, ticket_types, events |
| 3  | Total tickets sold per event                      | events, ticket_types, order_items            |
| 4  | Remaining ticket inventory for an event           | ticket_types (and events)                    |
| 5  | Total revenue per event                           | events, ticket_types, order_items            |
| 6  | Customers who purchased the most tickets          | users, orders, order_items                   |
| 7  | Events whose sales exceed a threshold             | events, ticket_types, order_items (+ HAVING) |
| 8  | Monthly ticket revenue                            | orders/payments, order_items (+ date grouping) |

- [ ] At least **two** queries join **three or more** tables (Queries 2, 3, 5, 6 are natural candidates)
- [ ] You may add extra queries for the admin features (sales review, activity analysis)

The API should run the **same queries** (parameterized, never string-formatted) from the service or router layer.

### 4.4 Transaction — `app/services/purchase_service.py`
This is where the ticket-purchase transaction lives. Required sequence:

1. Begin transaction
2. Create the `orders` row
3. Create `order_items` rows
4. Decrement `ticket_types` remaining quantity, failing if insufficient
5. Create the `payments` row
6. **COMMIT**; on any failure, **ROLLBACK**

Design points to address:
- How to prevent two buyers from taking the last ticket (row locking such as `SELECT ... FOR UPDATE`, or a conditional `UPDATE ... WHERE remaining >= qty`)
- How the failure case is demonstrated (e.g. requesting more tickets than remain, or a simulated payment failure) and shown to leave no partial rows behind

Called by `POST /orders`. The report must explain **why** atomicity matters here.

---

## 5. Part B — MongoDB

### 5.1 Collection: `event_content`
Each document is linked to PostgreSQL by `eventId`, which matches `events.event_id`.

Deliberately vary document shapes by event type to show off the flexible model:

| Event type   | Fields unique to that type (examples)                        |
|--------------|--------------------------------------------------------------|
| Conference   | `speakers[]` (nested, with `topics[]`), `schedule[]`, `tracks` |
| Concert      | `performers[]`, `genres[]`, `ageRestriction`, `setlist`      |
| Sporting     | `teams[]`, `league`, `season`                                |
| University   | `department`, `openToPublic`, `credits`                      |
| Workshop     | `instructor{}`, `prerequisites[]`, `materialsProvided`       |
| Community    | `organizer{}`, `accessibility[]`, `familyFriendly`           |

Fields shared by most documents: `eventId`, `title`, `description`, `tags[]`, `reviews[]` (each with `userId`, `rating`, `comment`, `createdAt`).

> `reviews[].userId` references `users.user_id` in PostgreSQL. Decide whether reviews are embedded (as in the example) or kept in a separate collection, and justify the choice in the report.

### 5.2 `mongo/seed_event_content.py`
Uses `insertOne` / `insertMany` (`insert_one` / `insert_many` in PyMongo) to load one document per seeded event.

### 5.3 `mongo/queries.py` — Required operation coverage checklist
Label each of the 8+ queries and note which required operations it demonstrates.

- [ ] `insertOne()` and/or `insertMany()`
- [ ] `find()`
- [ ] Projection
- [ ] Comparison operators (`$gt`, `$gte`, `$lt`, `$in`, …)
- [ ] Boolean operators (`$and`, `$or`, `$not`, `$nor`)
- [ ] Nested documents
- [ ] Arrays
- [ ] Dot notation (e.g. `speakers.name`)
- [ ] `$elemMatch`
- [ ] Updates (`$set`, `$push`, …)
- [ ] Deletes
- [ ] Indexing (in `mongo/indexes.py`)

**Suggested query list:**
1. Events containing a particular tag
2. Events featuring a particular speaker (dot notation)
3. Events with any review above a rating (comparison on array field)
4. Speaker with a specific organization **and** topic in the same element (`$elemMatch`)
5. Concerts in a particular genre
6. Concerts with an age restriction ≥ N **or** tagged "family" (boolean operators)
7. Projection returning only title and tags
8. Add a review (update with `$push`)
9. Remove a review or document (delete)

### 5.4 `mongo/indexes.py`
Candidates: unique index on `eventId`, and indexes on `tags`, `speakers.name`, `genres`, `reviews.rating`. Be ready to explain why each one helps.

---

## 6. Part C — Redis

### 6.1 Use Case 1: Event Cache — `app/services/cache_service.py`
Implements **cache-aside**:

```
request event → check Redis → HIT  → return
                            → MISS → query DB → store in Redis (with TTL) → return
```

Decide and document:
- **Key naming** (e.g. `event:{id}`)
- **Value format** (JSON string of the combined event summary)
- **TTL value**, and why it was chosen (report requirement)
- **Invalidation:** when an admin updates an event, ticket inventory changes, or a review is added, delete or refresh the key

`redis_demo/cache_demo.py` must visibly print or log: **cache miss → database retrieval → cache population → cache hit**.

### 6.2 Use Case 2: Trending — `app/services/trending_service.py`
- A single sorted set (e.g. key `trending:events`, members `event:{id}`)
- Every event view increments the member's score (`ZINCRBY`)
- The Top 10 comes from a reverse range (`ZREVRANGE ... WITHSCORES`)
- Optional: enrich the Top 10 with event titles from the cache or PostgreSQL

`redis_demo/trending_demo.py` simulates many views and prints the Top 10.

---

## 7. Application Layer — Endpoints

### 7.1 User-facing endpoints

| Requirement             | Endpoint                         | Router file   | Databases used |
|-------------------------|----------------------------------|---------------|----------------|
| Create accounts         | `POST /users`                    | `users.py`    | PostgreSQL |
| Browse events           | `GET /events`                    | `events.py`   | PostgreSQL |
| View event details      | `GET /events/{id}`               | `events.py`   | **All three** |
| View event content      | `GET /events/{id}/content`       | `events.py`   | MongoDB |
| Purchase tickets        | `POST /orders`                   | `orders.py`   | PostgreSQL (transaction); invalidates Redis cache |
| View previous orders    | `GET /users/{id}/orders`         | `users.py`    | PostgreSQL |
| Review events           | `POST /events/{id}/reviews`      | `reviews.py`  | MongoDB; invalidates Redis cache |
| View trending events    | `GET /trending`                  | `trending.py` | Redis (+ optional lookup) |

### 7.2 Admin endpoints — `app/routers/admin.py`

| Requirement                | Suggested endpoint(s)                                   | Backed by |
|----------------------------|---------------------------------------------------------|-----------|
| Create & manage events     | `POST /admin/events`, `PUT/DELETE /admin/events/{id}`   | PostgreSQL + MongoDB content |
| Manage ticket types        | `POST /admin/events/{id}/ticket-types`, `PUT /admin/ticket-types/{id}` | PostgreSQL |
| Monitor ticket inventory   | `GET /admin/events/{id}/inventory`                      | Query 4 |
| Review ticket sales        | `GET /admin/sales`, `GET /admin/sales/monthly`          | Queries 3, 5, 7, 8 |
| Analyze event activity     | `GET /admin/analytics`                                  | Query 6 + Redis trending + Mongo review ratings |

> Admin authentication is not required by the spec. A simple check of `users.role` is enough to show intent.

### 7.3 `app/main.py`
Keep it minimal: create the app, include each router with `app.include_router(...)`, and keep the health check.

### 7.4 Required cross-database feature — `app/services/event_service.py`
`GET /events/{id}` must follow this flow:

1. Check Redis for `event:{id}`
2. **HIT** → go to step 6
3. **MISS** → query PostgreSQL: event, venue, ticket types, prices, availability
4. Query MongoDB: description, speakers/performers, schedule, reviews, tags
5. Combine into one response and store in Redis with a TTL
6. Increment the trending score in the Redis sorted set
7. Return the result, optionally including the current popularity score

> Increment trending on **every** view, hits included, or the score will only count cache misses.

---

## 8. Performance Experiment — `experiments/`

### `cache_benchmark.py`
- **Experiment A:** retrieve the same event while bypassing Redis (call the PostgreSQL + MongoDB path directly, or clear the key before each run), **≥ 10 runs**
- **Experiment B:** retrieve the same event through the cache, warming it once first, **≥ 10 runs**
- Use a high-resolution timer (`time.perf_counter`)
- Write the raw timings to `results.csv`
- Compute min / max / average / median

### `plot_results.py`
Reads `results.csv` and saves `docs/cache_benchmark.png` (bar chart of the four metrics, or a box plot).

### Results table (copy into the report)

| Metric  | Database | Redis |
|---------|----------|-------|
| Minimum | ___ ms   | ___ ms |
| Maximum | ___ ms   | ___ ms |
| Average | ___ ms   | ___ ms |
| Median  | ___ ms   | ___ ms |

Discussion points: why performance differs, when caching helps, when it causes problems (stale inventory!), and the chosen TTL.

---

## 9. Report — `docs/report.md`

| Section                         | Source material in repo                  |
|---------------------------------|------------------------------------------|
| Architecture diagram            | `docs/architecture_diagram.png`          |
| ER diagram                      | `docs/er_diagram.png`                    |
| Schema design decisions         | `sql/schema.sql`                         |
| SQL queries + sample output     | `sql/queries.sql`                        |
| Transaction explanation         | `app/services/purchase_service.py`       |
| MongoDB design + queries        | `mongo/`                                 |
| Redis use cases + demo output   | `redis_demo/`, `app/services/`           |
| Cross-database feature          | `app/services/event_service.py`          |
| Performance experiment          | `experiments/`, `docs/cache_benchmark.png` |
| Architecture Analysis Q1–Q6     | Written discussion                       |

**Architecture Analysis questions to answer:**
1. Why PostgreSQL/MySQL for transactional data?
2. Why MongoDB for the chosen event content?
3. Why these two Redis use cases?
4. Why Redis should not be the authoritative system of record for cached data
5. What additional complexity three databases introduce (consistency, cache invalidation, cross-DB IDs, ops overhead, no cross-DB transactions)
6. Which single database you would choose if limited to one, and why

---

## 10. Suggested Build Order

1. **Infrastructure:** get PostgreSQL, MongoDB, and Redis running locally (Docker is an option); fill in `.env`, `config.py`, and `app/database/*`
2. **Part A:** `schema.sql` → ER diagram → `seed.sql` → `queries.sql`
3. **Part B:** Mongo seed → queries → indexes
4. **API basics:** users, events list, event content routers
5. **Transaction:** `purchase_service.py` + `POST /orders`
6. **Part C:** cache service, trending service, and their demos
7. **Cross-database:** `event_service.py` + `GET /events/{id}`
8. **Admin:** endpoints
9. **Experiment:** benchmark + plot
10. **Report:** diagrams, results, analysis

### Suggested team split (parallel work after step 1)
| Owner | Area |
|-------|------|
| Member 1 | Part A: schema, seed, queries, transaction |
| Member 2 | Part B: MongoDB design, seed, queries, reviews endpoint |
| Member 3 | Part C: Redis cache, trending, performance experiment |
| Everyone | Cross-database endpoint, admin routes, report |

---

## 11. Final Requirements Checklist

**Relational**
- [ ] All 7 required tables, plus at least one many-to-many
- [ ] PK / FK / NOT NULL / UNIQUE / indexes
- [ ] ER diagram
- [ ] Sample data
- [ ] Queries 1–8, with ≥ 2 joining 3+ tables
- [ ] Purchase transaction with COMMIT / ROLLBACK demonstrated

**MongoDB**
- [ ] `event_content` collection with varied document shapes
- [ ] 8+ queries covering all required operations
- [ ] Indexes

**Redis**
- [ ] Cache with TTL, demo showing miss → DB → populate → hit
- [ ] Trending sorted set with Top 10

**Application**
- [ ] REST endpoints for all user and admin features
- [ ] `GET /events/{id}` uses all three databases

**Experiment & Report**
- [ ] ≥ 10 runs each for A and B, results table, visualization
- [ ] Architecture diagram (your own)
- [ ] Caching discussion (differences, usefulness, problems, TTL)
- [ ] Answers to Q1–Q6
