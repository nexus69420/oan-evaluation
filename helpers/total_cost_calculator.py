from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_total_cost(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_cost = 0.0
    metric_entries = 0
    costed_entries = 0
    missing_cost_entries = 0

    for row in rows:
        metrics = row.get("metrics", [])
        if not isinstance(metrics, list):
            continue

        for metric in metrics:
            metric_entries += 1
            metadata = metric.get("metadata", {}) if isinstance(metric, dict) else {}
            cost_estimate = (
                metadata.get("cost_estimate", {}) if isinstance(metadata, dict) else {}
            )
            cost_usd = (
                cost_estimate.get("cost_usd")
                if isinstance(cost_estimate, dict)
                else None
            )
            parsed_cost = _safe_float(cost_usd)

            if parsed_cost is None:
                missing_cost_entries += 1
                continue

            total_cost += parsed_cost
            costed_entries += 1

    return {
        "total_cost_usd": total_cost,
        "rows": len(rows),
        "metric_entries": metric_entries,
        "costed_entries": costed_entries,
        "missing_cost_entries": missing_cost_entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate total LLM evaluation cost from evaluation JSON."
    )
    parser.add_argument(
        "json_file",
        type=str,
        help="Path to evaluation JSON file (for example: data/models/.../evaluation.json)",
    )
    args = parser.parse_args()

    json_path = Path(args.json_file).expanduser().resolve()
    if not json_path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if not isinstance(payload, list):
        raise ValueError("Expected top-level JSON array of evaluation rows.")

    summary = calculate_total_cost(payload)

    print(f"File: {json_path}")
    print(f"Rows scanned: {summary['rows']}")
    print(f"Metric entries scanned: {summary['metric_entries']}")
    print(f"Entries with cost: {summary['costed_entries']}")
    print(f"Entries missing cost: {summary['missing_cost_entries']}")
    print(f"Total cost (USD): ${summary['total_cost_usd']:.6f}")


if __name__ == "__main__":
    main()
