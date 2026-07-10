"""
promote.py — "File 2" for the holistic judge workflow: promote a fine-tuned
prompt (train.py's output) to be the new main judging prompt.

Fine-tuning (train.py) never touches prompts/evaluation_system_baseline.md —
it only writes to optimized_prompts/. This is the one command that copies a
fine-tuned prompt over the live baseline, so the NEXT thing that reads
config.EVAL_SYSTEM_PROMPT (a fresh train.py run, or any other consumer of
that file) picks up the improvement automatically — no human has to eyeball
scores and hand-edit a path.

The previous baseline is always backed up first (never silently discarded).

Usage
-----
  # Promote this run's best prompt (optimized_prompts/latest.md)
  python -m evaluator_alignment_prompts.promote.promote

  # Promote a specific historical version instead
  python -m evaluator_alignment_prompts.promote.promote --from optimized_prompts/stage2_bootstrap_20260710_045407.md
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

from evaluator_alignment_prompts.config import AlignmentConfig, EVAL_SYSTEM_PROMPT


def _parse_args():
    p = argparse.ArgumentParser(
        description="Promote a fine-tuned prompt to be the main judging prompt "
                    "(prompts/evaluation_system_baseline.md by default)."
    )
    p.add_argument(
        "--from", dest="source", type=Path, default=None,
        help="Prompt file to promote. Default: optimized_prompts/latest.md (this run's best).",
    )
    p.add_argument(
        "--to", dest="target", type=Path, default=None,
        help="File to overwrite. Default: config.EVAL_SYSTEM_PROMPT "
             "(prompts/evaluation_system_baseline.md).",
    )
    p.add_argument(
        "--no-backup", action="store_true",
        help="Skip backing up the current target file before overwriting (not recommended).",
    )
    return p.parse_args()


def promote(source: Path, target: Path, backup: bool = True) -> Path:
    if not source.exists():
        raise FileNotFoundError(
            f"Source prompt not found: {source}. Run train.py first, or pass --from explicitly."
        )

    new_content = source.read_text(encoding="utf-8")

    backup_path = None
    if backup and target.exists():
        archive_dir = target.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = archive_dir / f"{target.stem}_{timestamp}{target.suffix}"
        backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_content, encoding="utf-8")

    print("=" * 60)
    print("  PROMPT PROMOTED")
    print("=" * 60)
    print(f"  From: {source}")
    print(f"  To:   {target}")
    if backup_path:
        print(f"  Previous version backed up -> {backup_path}")
    else:
        print("  (no previous file to back up)")
    print("=" * 60)
    print(f"\n  The next train.py run will now start optimizing FROM this prompt.")
    return target


def main():
    args = _parse_args()
    cfg = AlignmentConfig()
    source = args.source or cfg.optimized_prompt_out
    target = args.target or EVAL_SYSTEM_PROMPT
    promote(source, target, backup=not args.no_backup)


if __name__ == "__main__":
    main()
