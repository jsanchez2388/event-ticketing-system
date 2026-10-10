"""Chart the cache benchmark results.

Reads experiments/results.csv and writes the comparison chart to both
docs/cache_benchmark.png (the report deliverable) and
app/static/img/cache_benchmark.png (served by the /site/benchmark page).

Run from the repo root:  python -m experiments.plot_results
"""

import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from app.services.benchmark_service import (
    ARM_LABELS,
    CHART_FILE,
    DOCS_CHART_FILE,
    RESULTS_CSV,
    load_results,
    summarize_all
)

METRICS = [
    ("minimum", "Minimum"),
    ("maximum", "Maximum"),
    ("average", "Average"),
    ("median", "Median")
]

BAR_COLORS = {
    "database": "#c0392b",
    "database_warm": "#e67e22",
    "redis": "#27ae60"
}

def plot_summary_bars(summaries: dict[str, dict], path) -> None:
    """Draw the grouped bar chart comparing the benchmark arms."""
    arms = list(summaries)
    width = 0.8 / len(arms)
    positions = range(len(METRICS))

    figure, axes = plt.subplots(figsize=(11, 6.5))

    for index, arm in enumerate(arms):
        offset = (index - (len(arms) - 1) / 2) * width
        values = [summaries[arm][key] for key, _ in METRICS]
        bars = axes.bar(
            [p + offset for p in positions],
            values,
            width,
            label=ARM_LABELS[arm],
            color=BAR_COLORS.get(arm, "#34495e")
        )

        for bar, value in zip(bars, values):
            axes.annotate(
                f"{value:.2f}",
                (bar.get_x() + bar.get_width() / 2, value),
                textcoords="offset points",
                xytext=(0, 4),
                ha="center",
                fontsize=9
            )

    # The arms differ by two or three orders of magnitude; on a linear axis the
    # Redis bars would be invisible.
    axes.set_yscale("log")
    axes.set_xticks(list(positions))
    axes.set_xticklabels([label for _, label in METRICS], fontsize=12)
    axes.set_ylabel("Latency in milliseconds (log scale)", fontsize=12)
    axes.set_title(
        "Event retrieval latency: PostgreSQL + MongoDB vs Redis cache",
        fontsize=15,
        pad=14
    )
    axes.legend(fontsize=11)
    axes.grid(axis="y", linestyle=":", alpha=0.6)
    axes.set_axisbelow(True)

    figure.tight_layout()

    for destination in path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(destination, dpi=160)
        print(f"Wrote {destination}")

    plt.close(figure)

def main() -> None:
    """Render the benchmark chart from the results CSV."""
    results = load_results()

    if not results:
        sys.exit(
            f"No results found at {RESULTS_CSV}.\n"
            "Run the benchmark first: python -m experiments.cache_benchmark"
        )

    summaries = summarize_all(results)
    plot_summary_bars(summaries, [DOCS_CHART_FILE, CHART_FILE])

if __name__ == "__main__":
    main()
