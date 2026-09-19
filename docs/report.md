<!--
docs/report.md

PURPOSE
  Final project report. Images referenced below also go in docs/.

TO ADD (sections)
  1. Introduction
     - Application scenario and goals.

  2. System Architecture
     - Your OWN architecture diagram: docs/architecture_diagram.png
     - What each database stores and why.

  3. Part A: Relational Database
     - ER diagram: docs/er_diagram.png
     - Table descriptions; PKs, FKs, NOT NULL, UNIQUE, indexes, many-to-many.
     - Queries 1-8: SQL plus sample output (mark the 3+ table joins).
     - Transaction: steps, COMMIT/ROLLBACK demo output, and WHY transaction
       support matters for purchasing tickets.

  4. Part B: MongoDB
     - event_content design, with example documents of different shapes.
     - 8+ queries with output; a table mapping queries to required operations.
     - Indexes and explain() evidence.

  5. Part C: Redis
     - Use Case 1: cache flow, key design, TTL, invalidation; demo output
       showing miss -> DB retrieval -> cache population -> hit.
     - Use Case 2: sorted set design; Top 10 output.

  6. Application Integration
     - Endpoint list; cross-database GET /events/{id} flow with an example response.

  7. Performance Experiment
     - Method (number of runs, what was timed).
     - Results table: Min / Max / Average / Median for Database vs Redis.
     - Visualization: docs/cache_benchmark.png
     - Why performance differs; when caching is useful; when caching causes
       problems; the chosen TTL and why.

  8. Architecture Analysis
     - Q1 Why PostgreSQL/MySQL for transactional data?
     - Q2 Why MongoDB for the event content?
     - Q3 Why these two Redis use cases?
     - Q4 Why Redis should not be the authoritative system of record.
     - Q5 What complexity three databases add.
     - Q6 Which single database you would choose, and why.

  9. Conclusion and Team Contributions
-->
