"""
Split a goldenset_compare-style evaluation.json into one CSV per metric.

Each CSV has one row per evaluated sample for that metric only, with
identifiers, both responses, compare scores, and light usage/cost fields.

Also writes **combined_compare_metrics.csv** (configurable name): all metric
rows stacked in sample order (long format; same columns, including metric_name).

Usage (from the oan-evaluation directory):

    python -m data_transformation.export_compare_evaluation_to_metric_csvs
    python -m data_transformation.export_compare_evaluation_to_metric_csvs \\
        --evaluation data/models/goldenset_compare/evaluation.json \\
        --out-dir data/models/goldenset_compare/metric_csvs \\
        --combined-name combined_compare_metrics.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVAL = REPO_ROOT / "data" / "models" / "goldenset_compare" / "evaluation.json"
DEFAULT_OUT = REPO_ROOT / "data" / "models" / "goldenset_compare" / "metric_csvs"

csv.field_size_limit(256 * 1024 * 1024)

FIELDNAMES = (
    "sample_index",
    "row_num",
    "review_category",
    "pipeline",
    "category",
    "question",
    "response_a",
    "response_b",
    "metric_name",
    "score",
    "reason",
    "score_a",
    "reason_a",
    "score_b",
    "reason_b",
    "better_response",
    "better_response_reason",
    "elapsed_seconds",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cost_usd",
)


def _flatten_row(
    sample_index: int,
    original: Dict[str, Any],
    metric: Dict[str, Any],
) -> Dict[str, Any]:
    src = original.get("source") or {}
    meta = metric.get("metadata") or {}
    tu = meta.get("token_usage") or {}
    ce = meta.get("cost_estimate") or {}

    return {
        "sample_index": sample_index,
        "row_num": src.get("row_num", ""),
        "review_category": src.get("review_category", ""),
        "pipeline": src.get("pipeline", ""),
        "category": original.get("category", ""),
        "question": original.get("question", ""),
        "response_a": original.get("response_a", ""),
        "response_b": original.get("response_b", ""),
        "metric_name": metric.get("metric_name", ""),
        "score": metric.get("score"),
        "reason": metric.get("reason", ""),
        "score_a": meta.get("score_a"),
        "reason_a": meta.get("reason_a", ""),
        "score_b": meta.get("score_b"),
        "reason_b": meta.get("reason_b", ""),
        "better_response": meta.get("better_response", ""),
        "better_response_reason": meta.get("better_response_reason", ""),
        "elapsed_seconds": meta.get("elapsed_seconds"),
        "input_tokens": tu.get("input_tokens"),
        "output_tokens": tu.get("output_tokens"),
        "total_tokens": tu.get("total_tokens"),
        "cost_usd": ce.get("cost_usd"),
    }


def export_metric_csvs(
    evaluation_path: Path,
    out_dir: Path,
    *,
    combined_filename: str = "combined_compare_metrics.csv",
) -> Dict[str, Any]:
    if not evaluation_path.exists():
        raise FileNotFoundError(f"evaluation.json not found: {evaluation_path}")

    with evaluation_path.open("r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = json.load(f)

    by_metric: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    combined_rows: List[Dict[str, Any]] = []

    for idx, item in enumerate(data):
        original = item.get("original") or {}
        for m in item.get("metrics") or []:
            name = m.get("metric_name")
            if not name:
                continue
            row = _flatten_row(idx, original, m)
            by_metric[str(name)].append(row)
            combined_rows.append(row)

    out_dir.mkdir(parents=True, exist_ok=True)

    fieldnames = list(FIELDNAMES)
    written: List[str] = []

    for metric_name in sorted(by_metric.keys()):
        rows = by_metric[metric_name]
        safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in metric_name)
        out_path = out_dir / f"{safe}.csv"
        with out_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k, "") for k in fieldnames})
        written.append(str(out_path))

    combined_path = out_dir / combined_filename
    with combined_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in combined_rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})

    return {
        "metrics": sorted(by_metric.keys()),
        "paths": written,
        "combined_path": str(combined_path),
        "combined_rows": len(combined_rows),
        "samples": len(data),
    }


def main() -> None:
    p = argparse.ArgumentParser(
        description="Export compare evaluation.json to one CSV per metric plus one combined CSV."
    )
    p.add_argument("--evaluation", type=str, default=str(DEFAULT_EVAL))
    p.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT))
    p.add_argument(
        "--combined-name",
        type=str,
        default="combined_compare_metrics.csv",
        help="Single stacked CSV filename (written inside --out-dir).",
    )
    args = p.parse_args()

    eval_path = Path(args.evaluation).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    summary = export_metric_csvs(
        eval_path, out_dir, combined_filename=args.combined_name
    )

    print(f"Evaluation: {eval_path}")
    print(f"Samples: {summary['samples']}")
    print(f"Combined ({summary['combined_rows']} rows): {summary['combined_path']}")
    print(f"Metrics ({len(summary['metrics'])}): {', '.join(summary['metrics'])}")
    for path in summary["paths"]:
        print(f"  {path}")


if __name__ == "__main__":
    main()
