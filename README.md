# Event Ticketing System

A FastAPI event ticketing platform built for COMP 642. It uses three databases,
each for the job it is actually good at: **PostgreSQL** is the system of record
for users, events, inventory, orders and payments, and it enforces the purchase
transaction; **MongoDB** stores the parts of an event whose shape differs by
event type — speakers, schedules, performers, genres, reviews — in a single
`event_content` collection; **Redis** caches assembled event pages and keeps a
sorted set of trending events.

The site is server-rendered with Jinja2 under `/site/...`, and the graded SQL
and MongoDB queries are also exposed as JSON endpoints so they can be read and
run directly.

## Prerequisites

- Python 3.11
- A PostgreSQL database (the project uses [Neon](https://neon.tech))
- A MongoDB database (MongoDB Atlas, or a local server)
- Redis — `docker compose up -d` starts one on `localhost:6379`

## Setup

```bash
git clone https://github.com/jsanchez2388/event-ticketing-system.git
cd event-ticketing-system

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

cp .env.example .env           # then fill in your own values
```

`.env.example` documents every variable and which ones are required.
`POSTGRES_CONNECTION_STRING`, `MONGO_URI`, `MONGO_DB` and `SESSION_SECRET`
have no defaults, and the app refuses to start without `SESSION_SECRET`.

## Database initialization

Run the SQL files in this order, in the Neon SQL editor or with `psql`:

```bash
psql "$POSTGRES_CONNECTION_STRING" -f sql/schema.sql
psql "$POSTGRES_CONNECTION_STRING" -f sql/seed.sql
psql "$POSTGRES_CONNECTION_STRING" -f sql/purchase_tickets.sql
```

`schema.sql` drops every ticketing table before recreating them — check which
database your connection string points at first.

Then load MongoDB:

```bash
python -m mongo.seed_event_content
python -m mongo.indexes
```

`seed.sql` creates events 101–106 and five sign-in-ready accounts; the Mongo
seed creates the matching six `event_content` documents. Credentials for those
accounts are in [setup.md](setup.md).

## Run

```bash
uvicorn app.main:app --reload
```

| URL | What it is |
|-----|------------|
| http://127.0.0.1:8000/site | The website |
| http://127.0.0.1:8000/docs | Swagger UI for the JSON API |
| http://127.0.0.1:8000/health/database | PostgreSQL connectivity check |

## Demos and experiments

```bash
python -m mongo.queries            # the required MongoDB queries, labeled
python -m redis_demo.cache_demo    # MISS -> database -> populate -> HIT
python -m redis_demo.trending_demo # simulates views, prints the Top 10
python -m experiments.cache_benchmark  # cached vs uncached, >= 10 runs each
python -m experiments.plot_results     # writes the comparison chart
```

Results are in `experiments/results.csv` and `experiments/summary.md`.

## Where things are

| Path | Contents |
|------|----------|
| `sql/` | `schema.sql`, `seed.sql`, the 8 required queries, the purchase function, a transaction demo |
| `mongo/` | Seed documents, the required queries, index creation |
| `redis_demo/` | The two Redis use cases |
| `app/routers/` | `web.py` is the site; the others are the JSON API |
| `app/services/` | Business logic — the transaction, the 8 SQL queries, cache and trending helpers |
| `docs/` | The benchmark chart, written by `experiments/plot_results.py` |

The 8 SQL queries in `sql/queries.sql` are generated from the same constants
the application executes (`QUERY_SQL` in `app/services/analytics_service.py`),
so the file and the running code cannot drift. `/site/postgres-demo` displays
each query's SQL next to its live results.

## Documentation

- [setup.md](setup.md) — step-by-step localhost setup, including seeded accounts and troubleshooting
- [experiments/summary.md](experiments/summary.md) — cache benchmark results table
