"""
Pivot the stacked compare-metrics CSV into one row per (row_num, pipeline).

Input (default):
    data/models/goldenset_compare/metric_csvs/combined_compare_metrics.csv
        - One row per (sample, metric_name)
        - Columns: question, response_a, response_b, metric_name, score_a, score_b,
          better_response, better_response_reason, etc.

Output (default):
    data/models/goldenset_compare/metric_csvs/pivot_compare_metrics.csv
        - One row per unique (row_num, pipeline)
        - Base columns:
              row_num, pipeline, review_category, category,
              question, response_a, response_b
        - For each metric_name M (e.g. accuracy_completeness_compare):
              M__score_a          (score for source A / dev)
              M__score_b          (score for source B / prod)
              M__score_diff_ab    (score_a - score_b)
              M__better_response  ("response_a" / "response_b" / "both")
              M__reason           (better_response_reason)

Usage (from oan-evaluation root):

    python -m data_transformation.pivot_compare_metrics

You can override input/output paths:

    python -m data_transformation.pivot_compare_metrics ^
        --input data/models/goldenset_compare/metric_csvs/combined_compare_metrics.csv ^
        --output data/models/goldenset_compare/metric_csvs/pivot_compare_metrics.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict, OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_IN = (
    REPO_ROOT
    / "data"
    / "models"
    / "goldenset_compare"
    / "metric_csvs"
    / "combined_compare_metrics.csv"
)
DEFAULT_OUT = (
    REPO_ROOT
    / "data"
    / "models"
    / "goldenset_compare"
    / "metric_csvs"
    / "pivot_compare_metrics.csv"
)


Key = Tuple[str, str]  # (row_num, pipeline)


def _short_metric_name(metric_name: str) -> str:
    """Optionally shorten metric column prefixes."""
    # Strip the common suffix for readability, keep the core name stable.
    if metric_name.endswith("_compare"):
        return metric_name[: -len("_compare")]
    return metric_name


def pivot_compare_metrics(input_path: Path, output_path: Path) -> Dict[str, Any]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    # Group rows by (row_num, pipeline)
    groups: Dict[Key, Dict[str, Any]] = {}
    metrics_seen: List[str] = []

    with input_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_num = str(row.get("row_num") or "").strip()
            pipeline = str(row.get("pipeline") or "").strip()
            if not row_num and not pipeline:
                # Skip malformed lines
                continue

            key: Key = (row_num, pipeline)
            metric_name = str(row.get("metric_name") or "").strip()
            if not metric_name:
                continue

            if metric_name not in metrics_seen:
                metrics_seen.append(metric_name)

            # Create / fetch per-question row.
            if key not in groups:
                base: Dict[str, Any] = OrderedDict()
                base["row_num"] = row_num
                base["pipeline"] = pipeline
                base["review_category"] = row.get("review_category", "")
                base["category"] = row.get("category", "")
                base["question"] = row.get("question", "")
                base["response_a"] = row.get("response_a", "")
                base["response_b"] = row.get("response_b", "")
                groups[key] = base

            out_row = groups[key]

            short = _short_metric_name(metric_name)
            prefix = short  # e.g. "accuracy_completeness"

            # Metric-specific fields
            score_a = row.get("score_a")
            score_b = row.get("score_b")

            try:
                score_a_val = float(score_a) if score_a not in (None, "",) else None
            except ValueError:
                score_a_val = None
            try:
                score_b_val = float(score_b) if score_b not in (None, "",) else None
            except ValueError:
                score_b_val = None

            diff = None
            if score_a_val is not None and score_b_val is not None:
                diff = score_a_val - score_b_val

            out_row[f"{prefix}__score_a"] = score_a_val
            out_row[f"{prefix}__score_b"] = score_b_val
            out_row[f"{prefix}__score_diff_ab"] = diff
            out_row[f"{prefix}__better_response"] = row.get("better_response", "")
            # Use better_response_reason as the per-metric reason column.
            out_row[f"{prefix}__reason"] = row.get("better_response_reason", "") or row.get(
                "reason", ""
            )

    # Build column order: base columns, then metrics alphabetically.
    base_cols = [
        "row_num",
        "pipeline",
        "review_category",
        "category",
        "question",
        "response_a",
        "response_b",
    ]

    metric_cols: List[str] = []
    for metric_name in sorted(metrics_seen):
        short = _short_metric_name(metric_name)
        prefix = short
        metric_cols.extend(
            [
                f"{prefix}__score_a",
                f"{prefix}__score_b",
                f"{prefix}__score_diff_ab",
                f"{prefix}__better_response",
                f"{prefix}__reason",
            ]
        )

    fieldnames = base_cols + metric_cols

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        # Sort by row_num then pipeline for stability.
        for (row_num, pipeline) in sorted(groups.keys(), key=lambda k: (int(k[0]), k[1])):
            row = groups[(row_num, pipeline)]
            writer.writerow({col: row.get(col, "") for col in fieldnames})

    return {
        "input": str(input_path),
        "output": str(output_path),
        "rows": len(groups),
        "metrics": sorted(metrics_seen),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pivot combined compare-metrics CSV to one row per (row_num, pipeline)."
    )
    parser.add_argument("--input", type=str, default=str(DEFAULT_IN))
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args()

    summary = pivot_compare_metrics(Path(args.input).resolve(), Path(args.output).resolve())

    print(f"Input:  {summary['input']}")
    print(f"Output: {summary['output']}")
    print(f"Rows:   {summary['rows']}")
    print(f"Metrics ({len(summary['metrics'])}): {', '.join(summary['metrics'])}")


if __name__ == "__main__":
    main()

