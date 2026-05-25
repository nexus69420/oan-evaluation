"""
Standalone transformer for goldenset CSV -> combined dev+prod evaluator-ready JSON.

Each output row contains both answers side by side for comparative evaluation:

    {
      "question": <question_gu>,
      "response_a": <answer_gu_dev>,
      "response_b": <answer_gu_prod>,
      "category": ...,
      "retrieved_sources_a": <search_results_dev>,
      "retrieved_sources_b": <search_results_prod>,
      "source": { ... }
    }

Usage (from the oan-evaluation directory):

    python -m data_transformation.transform_goldenset_compare
    python -m data_transformation.transform_goldenset_compare --csv goldenset_full_review_v5.csv --limit 20
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "goldenset_full_review_v3.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "models" / "goldenset_compare"

csv.field_size_limit(256 * 1024 * 1024)


def transform_row(rec: Dict[str, str]) -> Dict[str, Any] | None:
    question = (rec.get("question_gu") or "").strip()
    response_a = (rec.get("answer_gu_dev") or "").strip()
    response_b = (rec.get("answer_gu_prod") or "").strip()
    if not question or (not response_a and not response_b):
        return None

    category = (
        (rec.get("review_category") or rec.get("pipeline") or "Unknown").strip()
        or "Unknown"
    )

    return {
        "question": question,
        "response_a": response_a,
        "response_b": response_b,
        "category": category,
        "agristack_required": "No",
        "agent_turns": [],
        "retrieved_sources_a": (rec.get("search_results_dev") or "").strip(),
        "retrieved_sources_b": (rec.get("search_results_prod") or "").strip(),
        "source": {
            "row_num": rec.get("row_num"),
            "review_category": rec.get("review_category"),
            "pipeline": rec.get("pipeline"),
        },
    }


def transform_csv(
    csv_path: Path,
    out_dir: Path,
    *,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.json"

    rows: List[Dict[str, Any]] = []
    skipped = 0

    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for rec in reader:
            if limit is not None and len(rows) >= limit:
                break
            transformed = transform_row(rec)
            if transformed is None:
                skipped += 1
                continue
            rows.append(transformed)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    return {
        "output_path": str(out_path),
        "rows_written": len(rows),
        "rows_skipped": skipped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform goldenset CSV into combined dev+prod JSON for comparative eval."
    )
    parser.add_argument("--csv", type=str, default=str(DEFAULT_CSV))
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR))
    parser.add_argument(
        "--limit", type=int, default=None, metavar="N",
        help="Emit at most N valid rows (CSV top to bottom).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    summary = transform_csv(csv_path, out_dir, limit=args.limit)

    print(f"CSV: {csv_path}")
    print(f"Output: {summary['output_path']}")
    print(f"Rows written: {summary['rows_written']}, skipped: {summary['rows_skipped']}")
    if args.limit is not None:
        print(f"Limit: {args.limit}")


if __name__ == "__main__":
    main()
