# experiments/plot_results.py
#
# PURPOSE
#   Visualize the caching experiment. Requires matplotlib (add it to requirements.txt).
#   Run from the repo root after the benchmark: python -m experiments.plot_results
#
# TO ADD
#   def load_results(path: str = "experiments/results.csv") -> dict[str, list[float]]
#       Read timings grouped by experiment ("database" / "redis").
#
#   def plot_summary_bars(results) -> None
#       Grouped bar chart of min / max / average / median for Database vs Redis.
#       Consider a log-scale y-axis if the difference is very large.
#
#   def plot_per_run(results) -> None  (optional)
#       Line or box plot of each run's latency for both experiments.
#
#   def main() -> None
#       Save the figure to docs/cache_benchmark.png (axes labeled in ms, with a title).
#
#   if __name__ == "__main__": main()
