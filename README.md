<!--
README.md

PURPOSE
  Quick-start instructions for teammates and graders.
  (PROJECT_GUIDE.md explains the design; this file explains how to run it.)

TO ADD
  # Event Ticketing System
  - One-paragraph project description (FastAPI + PostgreSQL + MongoDB + Redis).

  ## Prerequisites
  - Python version, PostgreSQL, MongoDB, Redis (local installs or Docker).

  ## Setup
  - Clone, create and activate the venv (Windows and macOS/Linux commands),
    pip install -r requirements.txt, copy .env.example to .env.

  ## Database Initialization
  - psql ... -f sql/schema.sql, then sql/seed.sql
  - python -m mongo.seed_event_content, then python -m mongo.indexes

  ## Run the API
  - uvicorn app.main:app --reload
  - Swagger UI at http://127.0.0.1:8000/docs

  ## Demos and Experiments
  - python -m mongo.queries
  - python -m redis_demo.cache_demo and python -m redis_demo.trending_demo
  - python -m experiments.cache_benchmark, then python -m experiments.plot_results

  ## Endpoints
  - Table of routes (see PROJECT_GUIDE.md section 7).

  ## Team
  - Member names and responsibilities.
-->
