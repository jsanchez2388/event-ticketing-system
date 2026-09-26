# Code Review — MongoDB Integration

Scope: `git diff main...HEAD` (commits `7c275be`, `87812cb`) — 11 files, +867/-6.

## Findings

### 1. High — `mongo/queries.py:193` — projection operator missing `$`

```python
"schedule": {
    "elemMatch": {   # should be "$elemMatch"
        "room": room
    }
}
```

MongoDB rejects unknown projection expressions, so `query7_sessions_in_room("Main Hall")`
raises `OperationFailure` instead of returning matching sessions. In the `__main__` demo
block this crashes at Query 7 and never reaches Queries 8–10 or `cleanup_query8_review()`,
leaving the test review permanently pushed into event 101.

### 2. Medium — `app/database/mongo.py:48` — import-time `RuntimeError` breaks the whole app

`MONGO_URI` / `MONGO_DB` are validated with a module-level `raise RuntimeError`. Because
`app/services/event_service.py:53` now imports `content_service`, which imports this module,
the entire application — including the PostgreSQL-only `web`, `auth`, `account`, and
`analytics` routers — fails to import on any machine or CI job where those two variables are
not set. Previously a missing Mongo config affected nothing.

**Fix:** move the check inside `init_client()` so failure is scoped to actual Mongo usage.

### 3. Medium — `mongo/queries.py:261` — `query10_delete_low_reviews()` does not do what it says

The function takes no arguments and deletes nothing low-rated: it inserts a throwaway
`eventId: 999` document and deletes it again. The delete described in the file header
(`query10_delete_low_reviews(event_id, max_rating)`) is never exercised, and the function
always reports `{"deleted": 1}` regardless of the data.

### 4. Low — `app/config.py:45` — duplicate, unvalidated configuration source

`MONGO_URI` / `MONGO_DB` are added to `config.py` but nothing reads them;
`app/database/mongo.py` calls `load_dotenv()` and `os.getenv` again independently. The file
header states every other module should import settings from here. Two sources of truth will
drift, and the values in `config.py` are silently unvalidated (unlike `DATABASE_URL`).

### 5. Low — `app/services/content_service.py:65` — `modified_count` used as an existence check

`add_review` returns `result.modified_count > 0`, and `create_review` maps a falsy result to
`404 "Event content not found"`. `matched_count` is the correct existence signal; with
`modified_count`, a matched-but-unmodified write (e.g. a retried or duplicate
acknowledgment) reports a spurious 404 even though the event exists.

Same pattern at `app/services/content_service.py:123` — `update_event_content` with a `$set`
writing values identical to the current document returns `False`, which a caller would read
as "not found".

### 6. Low — `app/services/content_service.py:67` — missing event indistinguishable from no reviews

`get_reviews` returns `[]` both when the event content document is absent and when it simply
has no reviews. So `GET /events/999/reviews` returns `200 []` while
`POST /events/999/reviews` returns `404` for the same nonexistent event. Return `None` for a
missing document and let the router raise the 404.

### 7. Low — `mongo/seed_event_content.py:186` — `insert_one` mutates the module-level sample

`collection.insert_one(SAMPLE_DOCUMENTS[0])` adds an `_id` to the shared dict in place.
Calling `main()` twice in the same process (REPL or a test harness) re-inserts the now
`_id`-bearing dict and raises `DuplicateKeyError`, even though `clear_collection()` ran,
because the id is reused. Pass a copy: `dict(SAMPLE_DOCUMENTS[0])`.

## Non-blocking notes

- `mongo/` has no `__init__.py` and its scripts import `app.*`. Running
  `python mongo/queries.py` fails with `ModuleNotFoundError: app` because Python puts
  `mongo/` on `sys.path`, not the repo root. Run them as `python -m mongo.queries` from the
  repo root, or document that.
- `app/main.py:23,28` use `@app.on_event("startup")` / `("shutdown")`, deprecated in current
  FastAPI in favour of a `lifespan` context manager.
- `init_client()` at startup is redundant — `get_database()` already initialises lazily — but
  harmless.
- `app/services/event_service.py:145` `get_event_content_from_mongo` is a pass-through
  wrapper around `content_service.get_event_content` with no callers.
