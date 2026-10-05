# EventHub — Presentation Outline

**Format:** 17–18 minutes, 4 presenters, live demo with screenshot fallback.
**Target:** 16:30 of content, 1:30 reserve. Plan to finish early; you will not.

---

## The one-sentence thesis

> We did not use three databases because the assignment said so. We used three because a ticketing system has three genuinely different data problems: money that must be correct, content that has no fixed shape, and reads that happen constantly.

Every segment should land back on this. If a grader remembers one thing, it is this sentence.

---

## Where your margin is

Every group is building the same system against the same requirements. That means the baseline — three databases, 8 SQL queries, 8+ Mongo queries, a cache, a sorted set — is table stakes and scores nothing on its own. Assume the grader has already seen it several times.

The margin is in four things no one else is likely to have:

1. **The three-arm benchmark.** Others will show "cache fast, database slow." You can decompose *why*, and defend it.
2. **Results published inside the app.** Most groups will have a matplotlib PNG pasted into a report. Yours is a live page in the product.
3. **Cache invalidation demoed live.** Showing that a write invalidates the key proves you understood that caching creates a correctness problem, not just a speed win.
4. **Instrumentation in the UI.** Your event page already prints request time and TTL on screen. That's the system explaining itself while you talk.

Spend time proportional to distinctiveness. Move fast through the parts everyone has.

## The five things to highlight

Rank order. If you are running out of time, protect these from the top down.

1. **The cross-database event detail page.** One request (`GET /events/{id}`) touches PostgreSQL, MongoDB and Redis and returns a single merged object. This is the only thing that proves *polyglot persistence* rather than *three separate assignments stapled together*. It is the centerpiece of the demo.
2. **The three-arm benchmark result.** Most teams will show "cache fast, database slow." You can show *why*: of the 433× speedup, 3.6× is connection reuse and 122× is avoiding network round trips. That decomposition is the single most defensible thing in the project.
3. **Varied MongoDB document shapes.** A Concert document and a Conference document have different fields. This justifies choosing a document store instead of just asserting it.
4. **The purchase transaction.** COMMIT/ROLLBACK against real inventory, demoed live. Required deliverable and a satisfying moment on screen.
5. **Cache invalidation on writes.** Purchases and reviews invalidate the cached event. Shows you understood that caching creates a correctness problem, not just a speed win.

---

## Minute-by-minute

### 0:00 – 3:00 · Opening & Architecture — **Presenter A**

| Time | Beat |
|---|---|
| 0:00 | **Hook, not a title slide.** "A ticketing site has to do three things at once: never sell the same seat twice, show wildly different content for a concert versus a conference, and survive a traffic spike when tickets drop. Those are three different database problems." |
| 0:30 | The system in one line: FastAPI event ticketing platform, three datastores, one web UI. |
| 0:45 | **Request-flow diagram** (not a box inventory). Trace one request, `GET /events/{id}`: browser → check Redis → miss → PostgreSQL join + MongoDB fetch → merge → populate cache → increment trending → return. Then: "Every number in our experiment later is this path, with and without step 2." This diagram sets up D's demo *and* the benchmark. |
| 2:00 | **ER diagram — 20 seconds, one claim.** Do not walk the tables. Put it up and name the decisions: "`available_quantity` lives on `ticket_types` so we check inventory without scanning orders; `payments` is split from `orders` so a failed payment doesn't destroy the order record. The rest is what you'd expect." Move on. |
| 2:20 | Roadmap + handoff: "I'll hand to [B] for the relational layer." |

> **Why the ER diagram gets 20 seconds.** Every group is building this project with the same architecture, so their ER diagrams will look like yours. The grader will have seen several before yours and the marginal information is near zero. Keep it on screen because it is a required deliverable and the rubric may list it — but spend the time on the request flow, which is specific to your system.

> **Gap warning:** both diagrams are missing from `docs/`. The request-flow diagram is now the higher-value one: a generic three-box architecture diagram is as commodity as the ER diagram, but a sequence showing the cache-aside path through all three stores is yours alone. ~20 minutes in draw.io and it carries a third of this segment.

---

### 3:00 – 7:00 · PostgreSQL — **Presenter B**

| Time | Beat |
|---|---|
| 3:00 | **Why relational here.** Money and inventory. Constraints, foreign keys and ACID transactions are the entire reason this layer exists. One sentence, then prove it. |
| 3:30 | **Schema decisions worth defending** (pick 2, not all): `available_quantity` on `ticket_types` so inventory is checked without scanning orders; `order_items` as a junction table so one order can hold multiple ticket types; `payments` separate from `orders` so payment state and order state can diverge. |
| 4:15 | **Queries — show 3, not 8.** Open `sql/queries.sql`. Pick the ones with teeth: the **5-table join** (user ticket history), the **window function** (`SUM(...) OVER (PARTITION BY ...)` for inventory), and the **FILTER + correlated EXISTS** revenue query. Say what question each answers in business terms *before* showing SQL. |
| 5:30 | **LIVE: the purchase transaction.** This is your moment. Log in → open an event → note the remaining inventory → buy a ticket → show inventory decremented and the order in the account page. Then say the important part: *"That ran as one transaction. If the payment insert failed, the inventory would roll back — we are never left having charged someone for a seat we did not reserve."* |
| 6:45 | Handoff to [C]. |

**Cut first if long:** drop to 2 queries, keep the live purchase.

> **Gap note:** `sql/schema.sql` and `sql/seed.sql` are comment-only stubs — the real DDL lives only inside Neon. Nobody will catch this during the talk, but it is a submission risk. Exporting the live schema (`pg_dump --schema-only`) into `schema.sql` is a 5-minute job.

---

### 7:00 – 10:30 · MongoDB — **Presenter C**

| Time | Beat |
|---|---|
| 7:00 | **Why a document store.** Frame it as a problem the relational model handles badly: "A concert has performers and genres. A conference has speakers, each with topics and a schedule of rooms. A workshop has an instructor and a materials list. In SQL that's either a dozen sparse nullable columns or an EAV table nobody wants to query." |
| 7:40 | **Show two documents side by side** — a Concert and a Conference from `event_content`. Different fields, same collection. *This is the justification slide.* Let it sit for a beat. |
| 8:30 | **LIVE: `/mongo` demo page.** Run 2–3 queries. Best picks: tag search (multikey index), `$elemMatch` on speakers by organization *and* topic (shows why `$elemMatch` differs from two separate conditions), and a `$push` write that adds a review. |
| 9:40 | **Indexes + `explain()`.** Run `mongo/indexes.py` or show saved output: IXSCAN versus COLLSCAN on the tag query. This is concrete evidence, not a claim — graders like it. |
| 10:15 | Mention embedded reviews as a design tradeoff: fast to read with the event, but the document rewrites on every `$push`. Handoff to [D]. |

**Cut first if long:** drop to 2 queries; keep the side-by-side documents and the explain output.

---

### 10:30 – 15:30 · Redis & the Experiment — **Presenter D**

This is the strongest segment. Give it room.

| Time | Beat |
|---|---|
| 10:30 | **Two use cases, stated up front:** (1) cache the assembled event detail, (2) a sorted set that ranks trending events. Name them so the audience can follow. |
| 10:50 | **LIVE: the cache-aside flow.** Open an event detail page. First load = cache miss, note the request time shown on the page. Reload = cache hit, note the time drop and the TTL counting down. This page already surfaces `request_time_ms` and `ttl_remaining` — use them, they are doing your narration for you. |
| 12:00 | **LIVE: cache invalidation.** Buy a ticket or post a review on that event, reload, show the cache was invalidated and inventory is correct. Say: *"Caching inventory is dangerous. A stale cache sells seats that no longer exist. That's why writes invalidate rather than waiting for the TTL."* |
| 12:45 | **LIVE: trending page.** Sorted set, `ZINCRBY` on every view, `ZREVRANGE` to read. One line on why this is a good fit: ranking is maintained continuously instead of recomputed per request. |
| 13:30 | **The experiment — `/site/benchmark`.** Walk the three bars: 404 ms new connection / 114 ms open connection / 0.93 ms cache. |
| 14:00 | **The honest finding — do not skip this.** *"433× total. But we added a third arm to find out why. 3.6× of it is just reusing the database connection — our app opens a fresh TLS connection to Neon on every request. The remaining 122× is avoiding two network round trips. We are not claiming the Redis engine beats PostgreSQL at equal distance; we're measuring what our architecture actually does."* This pre-empts the hardest question you will get. |
| 14:45 | What the experiment taught you: the biggest win available is connection pooling, which is a change to PostgreSQL usage, not more caching. Handoff to [A]. |

**Protect this segment.** If you are running long, cut from PostgreSQL and MongoDB, not here.

---

### 15:30 – 16:30 · Analysis & Close — **Presenter A**

Bookend the opening. Do not summarize what was just said; say what you learned.

| Time | Beat |
|---|---|
| 15:30 | **The cost of three databases.** Be candid — this scores better than pretending it was free: no cross-database transactions, cache invalidation is now application logic, event IDs must be kept consistent across stores by hand, three sets of credentials and failure modes. |
| 16:00 | **If limited to one database, which?** Have a real answer. PostgreSQL — it can do JSONB for the flexible content and materialized views for ranking; you would lose latency and simplicity, not capability. |
| 16:20 | Close on the thesis sentence. Then: "Questions." |

---

## Demo runbook

Exact click paths, so nobody improvises on stage.

| # | Demo | Path | Owner |
|---|---|---|---|
| 1 | Purchase transaction | `/site/login` → `/site` → event → Buy → `/site/account` | B |
| 2 | Mongo queries | `/mongo` → run tag search, `$elemMatch`, `$push` review | C |
| 3 | Cache miss → hit | `/site/events/103`, load twice, watch `request_time_ms` + TTL | D |
| 4 | Invalidation | post review on 103 → reload `/site/events/103` | D |
| 5 | Trending | `/site/trending` | D |
| 6 | Benchmark | `/site/benchmark` | D |
| 7 | *(optional)* Resilience | `docker compose stop redis` → reload `/site/events/103` → `docker compose start redis` → reload | D |

**Demo 7 is your closer if time allows.** Kill Redis on stage, reload the page, and show it still renders from PostgreSQL and MongoDB with the cache card reading `UNAVAILABLE`. Bring Redis back, reload twice, show `HIT` return — no restart. It takes about 40 seconds and proves the architectural claim that Redis is disposable. Only run it if you are at or ahead of schedule at 14:45.

**Do not run the terminal demos live.** `redis_demo/cache_demo.py` contains ~11 seconds of `sleep()` calls to show the TTL counting down. That is dead air. The web app shows the same thing instantly. Keep the terminal scripts as backup only.

---

## Pre-flight checklist (run 15 minutes before)

- [ ] Docker Desktop running; `docker compose up -d redis`
- [ ] `.env` present and correct
- [ ] **Warm up Neon.** It cold-starts. Load `/site` and an event page twice before presenting — the first request measured 1423 ms versus a 404 ms median. Do not let a cold start be the first number the room sees.
- [ ] Server up: `uvicorn app.main:app`
- [ ] Walk every demo path once, end to end
- [ ] Log in once so the purchase demo does not start at a login form
- [ ] Confirm the demo account has wallet balance and the demo event has inventory
- [ ] Browser zoom at ~125%, tabs pre-opened in demo order, notifications silenced
- [ ] Screenshot folder open in a second window

---

## If something breaks

| Failure | What happens | Do this |
|---|---|---|
| **Redis goes down** | Nothing breaks. Pages serve from PostgreSQL + MongoDB, the cache card reads `UNAVAILABLE`, trending shows its empty state | Keep going. If it happens live, *say so out loud* — an unplanned outage that the system absorbs is the best demo you could ask for |
| Neon slow or unreachable | Pages hang | Screenshots; mention the cold-start behavior you measured |
| Benchmark page empty | `results.csv` missing | Chart is committed at `docs/cache_benchmark.png` — show the file |
| Live purchase fails | Inventory or wallet exhausted | Have a second account and a second event ready |
| Running long at 14:00 | — | Skip trending (12:45 beat), go straight to the benchmark |

Screenshot every demo path the night before. Not optional.

---

## Q&A preparation

These map to the required Architecture Analysis questions, which is almost certainly where the questions come from.

**"Isn't your speedup just network latency?"**
Yes, largely — and we measured exactly how much. Third arm: 3.6× from connection reuse, 122× from avoiding round trips. *You are the only team that will have this answer.*

**"What happens when Redis goes down?"**
The site keeps working. Every cache and trending call degrades to a safe fallback — a cache read returns a miss and falls through to PostgreSQL and MongoDB, trending returns empty, invalidation becomes a no-op. The page says `UNAVAILABLE` instead of pretending it was a cache miss. It also reconnects on its own within a few seconds of Redis coming back, with no restart.

**This is worth demoing live** — see the optional demo below. It is the strongest possible answer to "is Redis load-bearing?" because you show rather than claim.

**"Why isn't Redis your source of truth?"**
Keys expire, data can be evicted under memory pressure, and durability is configurable rather than guaranteed. It holds a disposable copy. Losing Redis should cost latency, never data.

**"How do you prevent selling stale inventory?"**
Writes invalidate the key rather than waiting for expiry, and TTL is 60 s as a backstop.

**"Why 60 seconds?"**
Long enough to absorb a traffic spike on a popular event, short enough that any invalidation we missed self-corrects within a minute.

**"Why not JSONB in PostgreSQL instead of MongoDB?"**
Legitimate — we'd say so. The honest reason is demonstrating a document store; the honest tradeoff is one less system to operate.

**"What would you do next?"**
Connection pooling, from our own benchmark. It is the largest measured win available and it has nothing to do with caching.

---

## Open items before presentation day

Ranked by presentation impact, not by effort.

| Item | Impact | Note |
|---|---|---|
| **Request-flow diagram** | **High** — carries 1:15 of segment 1 | Missing. Highest-value unfinished item. Sequence for `GET /events/{id}`, not a three-box inventory |
| **ER diagram** | **Low** — 20 seconds | You already have one. Do not redraw or polish it; every group has a near-identical one. Just know the two decisions you'll point at |
| Screenshots of all 6 demo paths | High | Your only real insurance |
| Rehearse once with a timer | High | 17 min is tighter than it reads |
| `schema.sql` / `seed.sql` | Low for talk, real for submission | `pg_dump --schema-only` |
| `docs/report.md` | None for talk | But its Q1–Q6 answers *are* your Q&A prep |
| Admin / orders / users routers | None | Stubs; do not mention or demo |

---

## Timing summary

| Segment | Presenter | Length |
|---|---|---|
| Opening & Architecture | A | 3:00 |
| PostgreSQL | B | 4:00 |
| MongoDB | C | 3:30 |
| Redis & Experiment | D | 5:00 |
| Analysis & Close | A | 1:00 |
| **Content total** | | **16:30** |
| Reserve / Q&A | all | 1:30+ |

Rehearse to 15:30. Live demos always run long, and the only segment you cannot afford to rush is the last one.
