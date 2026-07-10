"""
promote_metrics.py — "File 2" for the per-metric workflow: promote each
metric's fine-tuned prompt (train_metrics.py's output) to be its new main
judging prompt in prompts/metrics/<metric>.md.

Mirrors promote.py, but per metric: train_metrics.py never touches
prompts/metrics/*.md directly — it only writes to optimized_prompts/metrics/.
This copies each metric's best fine-tuned prompt over its live baseline, so
the next train_metrics.py run (or any other consumer of prompts/metrics/)
picks up the improvement. The previous version of each promoted file is
always backed up first.

Usage
-----
  # Promote every metric's latest fine-tuned prompt
  python -m evaluator_alignment_prompts.promote.promote_metrics --all

  # Promote just one metric
  python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy

  # Promote a specific historical version for one metric
  python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy \\
      --from optimized_prompts/metrics/citation_accuracy_copro_20260710_050000.md
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

from evaluator_alignment_prompts.config import AlignmentConfig
from evaluator_alignment_prompts.metrics.train_metrics import _load_metrics_config


def _parse_args():
    p = argparse.ArgumentParser(
        description="Promote fine-tuned per-metric prompts to be the main judging prompts "
                    "in prompts/metrics/<metric>.md."
    )
    p.add_argument("--metric", type=str, default=None, help="A single metric name to promote.")
    p.add_argument("--all", action="store_true", help="Promote every metric in metrics_config.json.")
    p.add_argument(
        "--from", dest="source", type=Path, default=None,
        help="Explicit prompt file to promote (only valid with --metric). "
             "Default: optimized_prompts/metrics/<metric>_latest.md.",
    )
    p.add_argument("--no-backup", action="store_true", help="Skip backing up the current file.")
    return p.parse_args()


def promote_one(metric_name: str, prompt_file: str, cfg: AlignmentConfig, source: Path = None, backup: bool = True) -> Path:
    target = cfg.metrics_dir / prompt_file
    src = source or (cfg.metrics_optimized_dir / f"{metric_name}_latest.md")

    if not src.exists():
        raise FileNotFoundError(
            f"[{metric_name}] Source prompt not found: {src}. "
            f"Run train_metrics.py --metrics {metric_name} first, or pass --from explicitly."
        )

    new_content = src.read_text(encoding="utf-8")

    backup_path = None
    if backup and target.exists():
        cfg.metrics_archive_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = cfg.metrics_archive_dir / f"{metric_name}_{timestamp}.md"
        backup_path.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(new_content, encoding="utf-8")

    print(f"[promote_metrics:{metric_name}] {src} -> {target}"
          + (f"  (backup -> {backup_path})" if backup_path else "  (no previous file to back up)"))
    return target


def main():
    args = _parse_args()
    cfg = AlignmentConfig()
    metrics_config = _load_metrics_config(cfg.metrics_config_file)

    if args.metric:
        if args.metric not in metrics_config:
            raise ValueError(f"Unknown metric '{args.metric}'. Known: {list(metrics_config.keys())}")
        targets = [args.metric]
    elif args.all:
        targets = list(metrics_config.keys())
    else:
        raise SystemExit("Pass --metric <name> or --all.")

    if args.source and len(targets) > 1:
        raise SystemExit("--from can only be used together with a single --metric.")

    print("=" * 60)
    print("  PER-METRIC PROMPTS PROMOTED")
    print("=" * 60)
    for metric_name in targets:
        promote_one(
            metric_name,
            metrics_config[metric_name]["prompt_file"],
            cfg,
            source=args.source,
            backup=not args.no_backup,
        )
    print("=" * 60)
    print("\n  The next train_metrics.py run will now start optimizing FROM these prompts.")


if __name__ == "__main__":
    main()
