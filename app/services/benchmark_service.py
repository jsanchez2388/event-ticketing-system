"""Shared loading and summarising of the cache benchmark results.

Lives in app/services so that both the experiment script and the web page
read the same numbers from the same place.
"""

import csv
import statistics

from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

RESULTS_CSV = PROJECT_ROOT / "experiments" / "results.csv"
CHART_FILE = PROJECT_ROOT / "app" / "static" / "img" / "cache_benchmark.png"
DOCS_CHART_FILE = PROJECT_ROOT / "docs" / "cache_benchmark.png"

ARM_DATABASE = "database"
ARM_DATABASE_WARM = "database_warm"
ARM_REDIS = "redis"

ARM_LABELS = {
    ARM_DATABASE: "Database (new connection)",
    ARM_DATABASE_WARM: "Database (open connection)",
    ARM_REDIS: "Redis cache"
}

ARM_ORDER = [ARM_DATABASE, ARM_DATABASE_WARM, ARM_REDIS]

def summarize(timings: list[float]) -> dict[str, Any]:
    """Return min / max / average / median (plus stdev and count) in ms."""
    if not timings:
        return {}

    return {
        "count": len(timings),
        "minimum": min(timings),
        "maximum": max(timings),
        "average": statistics.mean(timings),
        "median": statistics.median(timings),
        "stdev": statistics.stdev(timings) if len(timings) > 1 else 0.0
    }

def load_results(path: Path = RESULTS_CSV) -> dict[str, list[float]]:
    """Read results.csv and group the timings by experiment arm."""
    if not Path(path).exists():
        return {}

    results: dict[str, list[float]] = {}

    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            results.setdefault(row["experiment"], []).append(float(row["ms"]))

    return results

def summarize_all(results: dict[str, list[float]]) -> dict[str, dict[str, Any]]:
    """Summarise every arm present, in display order."""
    return {
        arm: summarize(results[arm])
        for arm in ARM_ORDER
        if results.get(arm)
    }

def speedup(results: dict[str, list[float]], baseline: str, compared: str) -> float | None:
    """How many times faster `compared` is than `baseline`, by median."""
    if not results.get(baseline) or not results.get(compared):
        return None

    faster = statistics.median(results[compared])

    if faster == 0:
        return None

    return statistics.median(results[baseline]) / faster

def results_generated_at(path: Path = RESULTS_CSV) -> datetime | None:
    """Timestamp of the last benchmark run, from the results file mtime."""
    path = Path(path)

    if not path.exists():
        return None

    return datetime.fromtimestamp(path.stat().st_mtime)

def chart_available() -> bool:
    """Whether the benchmark chart image has been generated."""
    return CHART_FILE.exists()
