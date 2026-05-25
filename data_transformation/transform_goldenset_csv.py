"""
Standalone transformer for goldenset CSV (e.g. v3, v5) -> evaluator-ready JSON.

Uses Gujarati question (`question_gu`) and Gujarati answers (`answer_gu_dev` /
`answer_gu_prod`). Produces two JSON files (one per answer variant).
Each output row contains the minimum fields expected by the evaluator:

    {
      "question": <question_gu>,
      "answer":   <answer_gu_dev | answer_gu_prod>,
      "category": <review_category or 'Unknown'>,
      "agristack_required": "No",
      "agent_turns": [],
      "retrieved_sources": <search_results_dev | search_results_prod when present>,
      "source": { ... }
    }

Usage (from the oan-evaluation directory; default CSV is
goldenset_full_review_v3.csv next to this package's parent folder):

    python -m data_transformation.transform_goldenset_csv
    python -m data_transformation.transform_goldenset_csv --csv goldenset_full_review_v5.csv --limit 20
    python -m data_transformation.transform_goldenset_csv --csv <path> --out-dir <dir> --limit 20
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "goldenset_full_review_v3.csv"

# Goldenset rows can include very large tool/search blobs (default limit is 128 KiB).
csv.field_size_limit(256 * 1024 * 1024)
DEFAULT_OUT_ROOT = REPO_ROOT / "data" / "models"


VARIANTS: List[Tuple[str, str, str]] = [
    ("answer_gu_dev", "goldenset_gu_dev", "Variant using answer_gu_dev"),
    ("answer_gu_prod", "goldenset_gu_prod", "Variant using answer_gu_prod"),
]


def transform_row(rec: Dict[str, str], answer_col: str) -> Dict[str, Any] | None:
    question = (rec.get("question_gu") or "").strip()
    answer = (rec.get(answer_col) or "").strip()
    if not question or not answer:
        return None

    category = (
        (rec.get("review_category") or rec.get("pipeline") or "Unknown").strip()
        or "Unknown"
    )

    search_col = (
        "search_results_dev" if answer_col == "answer_gu_dev" else "search_results_prod"
    )
    retrieved_sources = (rec.get(search_col) or "").strip()

    return {
        "question": question,
        "answer": answer,
        "category": category,
        "agristack_required": "No",
        "agent_turns": [],
        "retrieved_sources": retrieved_sources,
        "source": {
            "row_num": rec.get("row_num"),
            "review_category": rec.get("review_category"),
            "pipeline": rec.get("pipeline"),
            "answer_source": answer_col,
            "search_column": search_col,
        },
    }


def transform_csv(
    csv_path: Path,
    out_root: Path,
    *,
    limit: Optional[int] = None,
) -> Dict[str, Dict[str, Any]]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    summaries: Dict[str, Dict[str, Any]] = {}

    for answer_col, model_dir_name, description in VARIANTS:
        out_dir = out_root / model_dir_name
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "data.json"

        rows: List[Dict[str, Any]] = []
        skipped_empty = 0

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for rec in reader:
                if limit is not None and len(rows) >= limit:
                    break
                transformed = transform_row(rec, answer_col)
                if transformed is None:
                    skipped_empty += 1
                    continue
                rows.append(transformed)

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        summaries[answer_col] = {
            "description": description,
            "output_path": str(out_path),
            "model_dir_name": model_dir_name,
            "rows_written": len(rows),
            "rows_skipped_empty": skipped_empty,
        }

    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform goldenset CSV into evaluator JSONs (dev + prod)."
    )
    parser.add_argument("--csv", type=str, default=str(DEFAULT_CSV))
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_ROOT))
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Emit at most N valid Gujarati Q&A rows per variant (CSV top to bottom).",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    out_root = Path(args.out_dir).expanduser().resolve()

    summaries = transform_csv(csv_path, out_root, limit=args.limit)

    print(f"CSV: {csv_path}")
    print(f"Output root: {out_root}")
    if args.limit is not None:
        print(f"Limit: {args.limit} rows per variant")
    for answer_col, info in summaries.items():
        print(
            f"- {answer_col}: rows={info['rows_written']} "
            f"skipped_empty={info['rows_skipped_empty']} "
            f"-> {info['output_path']}"
        )


if __name__ == "__main__":
    main()
