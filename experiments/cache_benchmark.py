"""Cache performance experiment.

Compares retrieving one event three ways:

    A  database        PostgreSQL + MongoDB, a new Neon connection per call
                       (what the application does today)
    C  database_warm   the same two queries on one already-open connection
    B  redis           a single cached read

A is the required "without Redis" arm and B the required "with Redis" arm.
C is added so the gap can be split into connection setup versus the actual
cost of the datastores.

Run from the repo root:  python -m experiments.cache_benchmark
"""

import argparse
import csv
import sys
from time import perf_counter
from app.database.mongo import (
    init_client as init_mongo,
    close_client as close_mongo,
    test_connection as test_mongo
)
from app.database.postgres import get_connection, test_connection as test_postgres
from app.database.redis import (
    init_client as init_redis,
    close_client as close_redis
)
from app.services.benchmark_service import (
    ARM_DATABASE,
    ARM_DATABASE_WARM,
    ARM_LABELS,
    ARM_REDIS,
    RESULTS_CSV,
    summarize
)
from app.services.cache_service import (
    get_cached_event,
    invalidate_event,
    set_cached_event
)
from app.services.content_service import get_event_content
from app.services.event_service import build_event_detail

DEFAULT_EVENT_ID = 103
DEFAULT_RUNS = 30
QUICK_RUNS = 10
WARMUP_RUNS = 3

BENCHMARK_TTL_SECONDS = 600

def time_call(fn, *args, **kwargs) -> float:
    """Run fn once and return how long it took, in milliseconds."""
    start = perf_counter()
    fn(*args, **kwargs)
    return (perf_counter() - start) * 1000

def measure_database(event_id: int) -> float:
    """Time one cold rebuild of an event from PostgreSQL and MongoDB."""
    return time_call(build_event_detail, event_id)

def measure_database_warm(event_id: int, conn) -> float:
    """Time one rebuild of an event, reusing an already-open connection."""
    return time_call(build_event_detail, event_id, conn=conn)

def measure_redis(event_id: int) -> float:
    """Time one cached read, repopulating the cache on a miss."""
    start = perf_counter()
    cached = get_cached_event(event_id)
    elapsed = (perf_counter() - start) * 1000

    if cached is None:
        raise RuntimeError(
            f"Cache miss during the Redis arm for event {event_id}. "
            "The key expired mid-run, so these timings are not valid."
        )

    return elapsed

def preflight(event_id: int) -> None:
    """Fail early and legibly if a datastore or the event is unavailable."""
    for name, check in [("PostgreSQL", test_postgres), ("MongoDB", test_mongo)]:
        try:
            check()
        except Exception as error:
            sys.exit(f"{name} is not reachable: {error}")

    try:
        init_redis()
    except Exception as error:
        sys.exit(
            f"Redis is not reachable: {error}\n"
            "Start it with: docker compose up -d redis"
        )

    if build_event_detail(event_id) is None:
        sys.exit(f"Event {event_id} was not found. Valid demo events are 101-106.")

    if get_event_content(event_id) is None:
        print(f"Warning: event {event_id} has no MongoDB content document.")

def warm_up(event_id: int, conn) -> None:
    """Discarded runs that absorb DNS, TLS setup and any Neon cold start."""
    for _ in range(WARMUP_RUNS):
        build_event_detail(event_id)
        build_event_detail(event_id, conn=conn)
        get_cached_event(event_id)

def run_experiments(event_id: int, runs: int, include_warm_conn: bool) -> dict[str, list[float]]:
    """Time every arm round-robin so network drift is shared evenly."""
    results: dict[str, list[float]] = {ARM_DATABASE: [], ARM_REDIS: []}

    if include_warm_conn:
        results[ARM_DATABASE_WARM] = []

    conn = get_connection()

    try:
        invalidate_event(event_id)

        event_detail = build_event_detail(event_id)

        if event_detail is None:
            raise ValueError(f"Event {event_id} was not found.")

        set_cached_event(event_id, event_detail, ttl=BENCHMARK_TTL_SECONDS)

        warm_up(event_id, conn)

        for run in range(1, runs + 1):
            results[ARM_DATABASE].append(measure_database(event_id))

            if include_warm_conn:
                results[ARM_DATABASE_WARM].append(measure_database_warm(event_id, conn))

            results[ARM_REDIS].append(measure_redis(event_id))

            print(f"  run {run}/{runs}", end="\r", flush=True)

    finally:
        conn.close()

    print(" " * 30, end="\r")
    return results

def save_results(results: dict[str, list[float]], path=RESULTS_CSV) -> None:
    """Write the per-run timings to the results CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run", "experiment", "ms"])

        for arm, timings in results.items():
            for run, ms in enumerate(timings, start=1):
                writer.writerow([run, arm, f"{ms:.4f}"])

def build_table(results: dict[str, list[float]]) -> list[list[str]]:
    """Build the summary table rows for whichever arms produced results."""
    arms = [a for a in (ARM_DATABASE, ARM_REDIS, ARM_DATABASE_WARM) if results.get(a)]
    summaries = {arm: summarize(results[arm]) for arm in arms}

    rows = [["Metric"] + [ARM_LABELS[arm] for arm in arms]]

    for label, key in [
        ("Minimum", "minimum"),
        ("Maximum", "maximum"),
        ("Average", "average"),
        ("Median", "median"),
        ("Std dev", "stdev")
    ]:
        rows.append([label] + [f"{summaries[arm][key]:.3f} ms" for arm in arms])

    return rows

def print_table(rows: list[list[str]]) -> None:
    """Print a table with box-drawing borders."""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]

    def rule(char: str) -> str:
        """Return a horizontal border built from the given character."""
        return "+" + "+".join(char * (w + 2) for w in widths) + "+"

    def render(row: list[str]) -> str:
        """Return one row padded to the column widths."""
        return "| " + " | ".join(v.ljust(widths[i]) for i, v in enumerate(row)) + " |"

    print(rule("="))
    print(render(rows[0]))
    print(rule("="))

    for row in rows[1:]:
        print(render(row))

    print(rule("-"))

def write_markdown(rows: list[list[str]], event_id: int, runs: int) -> None:
    """Write the report-ready table so the numbers never need retyping."""
    path = RESULTS_CSV.parent / "summary.md"

    lines = [
        "# Cache Benchmark Results",
        "",
        f"Event {event_id}, {runs} timed runs per arm, measured with time.perf_counter().",
        "",
        "| " + " | ".join(rows[0]) + " |",
        "|" + "|".join("---" for _ in rows[0]) + "|"
    ]

    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {path}")

def main() -> None:
    """Run the benchmark from the command line."""
    parser = argparse.ArgumentParser(description="Cache performance experiment.")
    parser.add_argument("--event-id", type=int, default=DEFAULT_EVENT_ID)
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS)
    parser.add_argument("--quick", action="store_true", help=f"use {QUICK_RUNS} runs")
    parser.add_argument("--skip-warm-conn", action="store_true", help="drop the open-connection arm")
    args = parser.parse_args()

    runs = QUICK_RUNS if args.quick else args.runs

    if runs < 10:
        sys.exit("The project requires at least 10 runs per experiment.")

    init_mongo()

    try:
        preflight(args.event_id)

        print(f"Benchmarking event {args.event_id}, {runs} runs per arm...")
        results = run_experiments(args.event_id, runs, not args.skip_warm_conn)

        save_results(results)
        print(f"Wrote {RESULTS_CSV}\n")

        rows = build_table(results)
        print_table(rows)
        write_markdown(rows, args.event_id, runs)

        print("\nNext: python -m experiments.plot_results")

    finally:
        # Cleanup must not mask an earlier failure, and Redis may never have
        # come up at all.
        try:
            invalidate_event(args.event_id)
        except Exception:
            pass

        close_mongo()
        close_redis()

if __name__ == "__main__":
    main()
