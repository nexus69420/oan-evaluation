"""
run_eval_from_file.py
---------------------
Run the language-quality evaluation judge over one or more
`eval_agrinet-model_*.json` files produced by the agrinet pipeline.

Usage:
    python run_eval_from_file.py <file1.json> [file2.json ...]
    python run_eval_from_file.py <file1.json> [file2.json ...] --concurrency 4

Each input file must follow the schema:
    {
        "metadata": { ... },
        "results": [
            {
                "question_id": "...",
                "question":    "...",
                "answer":      "...",
                "error":       null | "...",   # entries with errors are skipped
                ...
            },
            ...
        ]
    }

For every input file `eval_agrinet-model_<ts>.json` the script writes a
companion file `eval_agrinet-model_<ts>__lang_eval.json` in the *same*
directory.  Already-evaluated question_ids are skipped so the run is
idempotent / resumable.
"""

import sys
import os

# Convert relative paths in CLI arguments to absolute paths before any imports change the CWD.
for _i in range(1, len(sys.argv)):
    _arg = sys.argv[_i]
    if not _arg.startswith("-") and (_i == 1 or sys.argv[_i-1] not in ("-c", "--concurrency")):
        sys.argv[_i] = os.path.abspath(_arg)

import json
import asyncio
import argparse
import warnings
warnings.filterwarnings("ignore")

from tqdm.asyncio import tqdm
from dotenv import load_dotenv
from evaluator import EvalDeps, evaluation_agent, format_agent_record

load_dotenv()

# ── Concurrency ────────────────────────────────────────────────────────────────
CONCURRENCY = int(os.getenv("EVAL_CONCURRENCY", "8"))


# ── I/O helpers ───────────────────────────────────────────────────────────────

def output_path_for(input_path: str) -> str:
    """Derive the output path from the input path."""
    base, ext = os.path.splitext(input_path)
    return f"{base}__lang_eval{ext}"


def load_eval_file(path: str) -> dict:
    """Load and return the full eval JSON (metadata + results)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_existing_output(path: str) -> dict:
    """Return a dict keyed by question_id for already-evaluated rows."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    results = data.get("results", [])
    return {r["question_id"]: r for r in results if r.get("question_id")}


def save_output(path: str, metadata: dict, results: list) -> None:
    """Write the output JSON atomically (write to .tmp then rename)."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump({"metadata": metadata, "results": results}, f,
                  ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


# ── Per-item evaluation ────────────────────────────────────────────────────────

async def evaluate_item(item: dict, sem: asyncio.Semaphore,
                        results: list, lock: asyncio.Lock,
                        output_path: str, metadata: dict) -> None:
    """Evaluate one question/answer pair and append to `results`."""
    async with sem:
        question = item.get("question", "")
        answer   = item.get("answer", "")

        message = format_agent_record({"question": question, "answer": answer})
        deps    = EvalDeps(question=question, answer=answer)

        try:
            result = await evaluation_agent.run(message, deps=deps)
            lq = result.output
            record = {
                "question_id": item.get("question_id"),
                "question":    question,
                # Language-mix scores only — answer text is in the source file
                "grammar_score":       lq.grammar.score,
                "grammar_summary":     lq.grammar.summary,
                "grammar_evidences":   lq.grammar.evidences,
                "terminology_score":   lq.terminology.score,
                "terminology_summary": lq.terminology.summary,
                "terminology_evidences": lq.terminology.evidences,
            }
        except Exception as e:
            print(f"  x Error evaluating [{item.get('question_id')}] "
                  f"{question[:60]}...  ->  {e}")
            return

        async with lock:
            results.append(record)
            save_output(output_path, metadata, results)


# ── Per-file pipeline ──────────────────────────────────────────────────────────

async def process_file(input_path: str) -> None:
    print(f"\n{'='*70}")
    print(f"Input : {input_path}")

    # ── Load input ──────────────────────────────────────────────────────────
    try:
        data = load_eval_file(input_path)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  x Could not read file: {e}  — skipping.")
        return

    metadata    = data.get("metadata", {})
    all_results = data.get("results", [])
    print(f"  Total rows in file : {len(all_results)}")

    # ── Filter: skip rows with errors or missing/empty answers ─────────────
    valid_items = [
        r for r in all_results
        if not r.get("error")                    # skip error rows
        and r.get("answer", "").strip()          # skip empty answers
        and r.get("question", "").strip()        # skip empty questions
    ]
    skipped_count = len(all_results) - len(valid_items)
    if skipped_count:
        print(f"  Skipped {skipped_count} rows with errors / missing content")

    # ── Load already-evaluated rows ─────────────────────────────────────────
    output_path = output_path_for(input_path)
    print(f"Output: {output_path}")

    existing = load_existing_output(output_path)
    results  = list(existing.values())

    pending = [r for r in valid_items
               if r.get("question_id") not in existing]

    print(f"  Already evaluated  : {len(existing)}")
    print(f"  To evaluate        : {len(pending)}")

    if not pending:
        print("  Done — all items already evaluated.")
        return

    # ── Run judge in parallel ───────────────────────────────────────────────
    sem   = asyncio.Semaphore(CONCURRENCY)
    lock  = asyncio.Lock()
    tasks = [
        evaluate_item(item, sem, results, lock, output_path, metadata)
        for item in pending
    ]
    await tqdm.gather(*tasks, desc=f"  Evaluating {os.path.basename(input_path)}")

    # Final save (already done incrementally, but ensures completeness)
    save_output(output_path, metadata, results)
    print(f"  Done — {len(results)} records saved to {output_path}")


# ── CLI entry-point ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run language-quality evaluation on agrinet eval JSON files."
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="EVAL_FILE",
        help="One or more eval_agrinet-model_*.json files to evaluate.",
    )
    parser.add_argument(
        "--concurrency", "-c",
        type=int,
        default=None,
        help=f"Number of parallel judge calls (default: {CONCURRENCY}, "
             "or EVAL_CONCURRENCY env var).",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    # Allow CLI override of concurrency
    global CONCURRENCY
    if args.concurrency is not None:
        CONCURRENCY = args.concurrency

    for file_path in args.files:
        if not os.path.isfile(file_path):
            print(f"WARNING: file not found — {file_path!r}  — skipping.")
            continue
        await process_file(file_path)

    print("\nAll files processed.")


if __name__ == "__main__":
    asyncio.run(main())
