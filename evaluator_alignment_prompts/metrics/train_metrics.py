"""
train_metrics.py — Per-metric prompt fine-tuning ("File 1" for the
per-metric workflow).

Companion to train.py, which tunes ONE holistic prompt covering every
dimension at once. This tunes each metric's prompt INDEPENDENTLY — e.g.
accuracy_completeness, citation_accuracy, no_fabrication, actionability —
against its own labeled score column in the same train/val/test CSVs,
using COPRO.

Why COPRO-only by default (unlike train.py's two-stage default): narrow,
single-metric rubrics are exactly where COPRO's instruction-rewriting reliably
helps, but adding BootstrapFewShot demos on top of an already-narrow prompt
has been observed to *hurt* — a few concrete demos can overfit and pull the
judge away from a rule that generalizes better in prose. Pass --optimizer
two-stage to try Bootstrap on top anyway.

Usage
-----
  # All metrics defined in prompts/metrics/metrics_config.json
  python -m evaluator_alignment_prompts.metrics.train_metrics

  # Just specific metrics
  python -m evaluator_alignment_prompts.metrics.train_metrics --metrics citation_accuracy,no_fabrication

  # Override CSVs / hyperparameters
  python -m evaluator_alignment_prompts.metrics.train_metrics \\
      --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv \\
      --breadth 4 --depth 3 --target-score 85

Output (per metric)
--------------------
  optimized_prompts/metrics/<metric>_<timestamp>.md   -- history, never overwritten
  optimized_prompts/metrics/<metric>_latest.md        -- this run's best for that metric
  artifacts/metrics/metric_prompt_registry.json       -- every version's val score, per metric

Use promote_metrics.py to copy a metric's best optimized prompt over its
live baseline in prompts/metrics/<metric>.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

import dspy

from evaluator_alignment_prompts.config import AlignmentConfig
from evaluator_alignment_prompts.metric import evaluate_agreement, make_agreement_metric
from evaluator_alignment_prompts.metrics.metric_module import SingleMetricEvaluatorModule
from evaluator_alignment_prompts.metrics.metrics_dataset import load_metric_dataset
from evaluator_alignment_prompts.optimizer import (
    configure_lm,
    configure_optimizer_lm,
    print_token_report,
)


# ---------------------------------------------------------------------
# metrics_config.json
# ---------------------------------------------------------------------

def _load_metrics_config(path: Path) -> Dict[str, dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Metrics config not found: {path}. Define your metrics there as "
            f'{{"metric_name": {{"prompt_file": ..., "score_min": ..., "score_max": ..., '
            f'"score_col": ..., "notes_col": ...}}}}.'
        )
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Fine-tune each per-metric judge prompt independently against its own labeled score column."
    )
    p.add_argument("--train-csv", type=Path, default=None)
    p.add_argument("--val-csv",   type=Path, default=None)
    p.add_argument("--test-csv",  type=Path, default=None)
    p.add_argument(
        "--metrics", type=str, default=None,
        help="Comma-separated metric names to run (default: all in metrics_config.json).",
    )
    p.add_argument(
        "--optimizer", choices=["copro", "bootstrap", "two-stage"], default="copro",
        help="Per-metric optimizer. Default 'copro' (see module docstring for why).",
    )
    p.add_argument("--breadth", type=int, default=None)
    p.add_argument("--depth",   type=int, default=None)
    p.add_argument("--max-train", type=int, default=None)
    p.add_argument("--max-val",   type=int, default=None)
    p.add_argument("--max-test",  type=int, default=None)
    p.add_argument(
        "--target-score", type=float, default=80.0,
        help="Stop early (per metric) if val score reaches this (0-100 scale, default 80.0).",
    )
    p.add_argument("--no-notes", action="store_true", help="Exclude human notes from input features.")
    return p.parse_args()


# ---------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------

def _run_eval(module, examples, metric_fn, cfg) -> float:
    evaluator = dspy.Evaluate(
        devset=examples, metric=metric_fn,
        num_threads=cfg.num_threads, display_progress=True,
    )
    result = evaluator(module)
    return float(getattr(result, "score", result))


def _agreement_report(module, examples, score_min: float, score_max: float) -> dict:
    if not examples:
        return {}
    human, preds = [], []
    for ex in examples:
        pred = module(**ex.inputs())
        human.append(ex.human_score)
        preds.append(pred.score)
    return evaluate_agreement(human, preds, min_rating=int(score_min), max_rating=int(score_max))


# ---------------------------------------------------------------------
# Saving optimized per-metric prompts
# ---------------------------------------------------------------------

def _save_metric_prompt(
    module: SingleMetricEvaluatorModule,
    metric_name: str,
    prompt_path: Path,
    version_tag: str,
    val_score: float,
    cfg: AlignmentConfig,
    update_latest: bool,
) -> None:
    """
    Save the optimized per-metric instruction as: a provenance header
    (matching the convention already used in real per-metric prompt files —
    "<!-- OPTIMIZED (tag) | Score: NN.NN% -->"), the new instruction, then
    the original raw prompt file appended below a "<!-- JINJA TEMPLATE -->"
    marker so any category-conditional branches are preserved for reference.
    """
    instruction = module.get_instruction()
    original_raw = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""

    # If this baseline was already promoted once, it already carries its own
    # "<!-- OPTIMIZED ... -->" header + "<!-- JINJA TEMPLATE -->" marker.
    # Keep only the TRUE template tail (after the last marker) so repeated
    # optimize -> promote -> optimize cycles stay a single level deep instead
    # of nesting a new header inside the previous run's header forever.
    marker = "<!-- JINJA TEMPLATE -->"
    marker_idx = original_raw.rfind(marker)
    template_body = original_raw[marker_idx + len(marker):].strip() if marker_idx != -1 else original_raw.strip()

    header = f"<!-- OPTIMIZED ({version_tag}) | Score: {val_score:.2f}% -->\n\n"
    full_prompt = header + instruction.strip() + "\n"
    if template_body:
        full_prompt += "\n" + marker + "\n" + template_body + "\n"

    cfg.metrics_optimized_dir.mkdir(parents=True, exist_ok=True)
    ts_path = cfg.metrics_optimized_dir / f"{metric_name}_{version_tag}.md"
    ts_path.write_text(full_prompt, encoding="utf-8")
    print(f"[train_metrics:{metric_name}] Saved (history) -> {ts_path}")

    latest_path = cfg.metrics_optimized_dir / f"{metric_name}_latest.md"
    if update_latest:
        latest_path.write_text(full_prompt, encoding="utf-8")
        print(f"[train_metrics:{metric_name}] Saved (latest)  -> {latest_path}")

    registry: Dict[str, dict] = {}
    if cfg.metrics_registry_file.exists():
        try:
            registry = json.loads(cfg.metrics_registry_file.read_text())
        except Exception:
            registry = {}
    registry.setdefault(metric_name, {})
    registry[metric_name][version_tag] = {
        "val_score": round(val_score, 4),
        "timestamped_file": str(ts_path),
        "latest_copy": str(latest_path) if update_latest else None,
        "is_metric_best": update_latest,
    }
    cfg.metrics_registry_file.parent.mkdir(parents=True, exist_ok=True)
    cfg.metrics_registry_file.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[train_metrics:{metric_name}] Version '{version_tag}' logged -> {cfg.metrics_registry_file}")


# ---------------------------------------------------------------------
# Per-metric training loop
# ---------------------------------------------------------------------

def _train_one_metric(
    metric_name: str,
    metric_cfg: dict,
    args,
    cfg: AlignmentConfig,
    optimizer_lm: Optional[dspy.LM],
    run_tag: str,
) -> None:
    print(f"\n{'=' * 60}\n  METRIC: {metric_name}\n{'=' * 60}")

    score_min = float(metric_cfg["score_min"])
    score_max = float(metric_cfg["score_max"])
    prompt_path = cfg.metrics_dir / metric_cfg["prompt_file"]
    metric_fn = make_agreement_metric(score_min, score_max)

    include_notes = not args.no_notes
    trainset, valset, testset, stats = load_metric_dataset(
        metric_name=metric_name,
        score_col=metric_cfg["score_col"],
        notes_col=metric_cfg.get("notes_col"),
        cfg=cfg,
        train_csv=args.train_csv,
        val_csv=args.val_csv,
        test_csv=args.test_csv,
        include_notes_as_input=include_notes,
        verbose=True,
    )

    module = SingleMetricEvaluatorModule.load_from_prompt_file(
        metric_name, prompt_path, score_min, score_max
    )
    print(f"[train_metrics:{metric_name}] Loaded baseline from {prompt_path}  (scale {score_min}-{score_max})")

    baseline_score = _run_eval(module, valset, metric_fn, cfg)
    baseline_report = _agreement_report(module, valset, score_min, score_max)
    print(f"[train_metrics:{metric_name}] Baseline val composite: {baseline_score:.4f}  "
          f"exact_match={baseline_report.get('exact_match', 'n/a')}")

    if baseline_score >= args.target_score:
        print(f"[train_metrics:{metric_name}] Baseline already meets target "
              f"({baseline_score:.4f} >= {args.target_score}). Skipping optimization.")
        _save_metric_prompt(module, metric_name, prompt_path, f"baseline_{run_tag}", baseline_score, cfg, update_latest=True)
        return

    best_module, best_score = module, baseline_score

    if args.optimizer in ("copro", "two-stage"):
        from dspy.teleprompt import COPRO

        print(f"[train_metrics:{metric_name}] Starting COPRO  breadth={cfg.copro_breadth}  depth={cfg.copro_depth}")
        copro = COPRO(
            metric=metric_fn,
            breadth=cfg.copro_breadth,
            depth=cfg.copro_depth,
            init_temperature=cfg.copro_init_temp,
            prompt_model=optimizer_lm,
        )
        try:
            stage1 = copro.compile(
                module, trainset=trainset,
                eval_kwargs={"num_threads": cfg.num_threads, "display_progress": True},
            )
        except Exception as e:
            print(f"[train_metrics:{metric_name}] COPRO failed: {e}. Keeping baseline.")
            stage1 = module

        s1_score = _run_eval(stage1, valset, metric_fn, cfg)
        print(f"[train_metrics:{metric_name}] COPRO val composite: {s1_score:.4f}")
        _save_metric_prompt(stage1, metric_name, prompt_path, f"copro_{run_tag}", s1_score, cfg,
                             update_latest=(s1_score >= best_score))
        if s1_score >= best_score:
            best_module, best_score = stage1, s1_score

    if args.optimizer in ("bootstrap", "two-stage"):
        from dspy.teleprompt import BootstrapFewShot
        from evaluator_alignment_prompts.config import BFS_MAX_BOOTSTRAPPED, BFS_MAX_LABELED

        print(f"[train_metrics:{metric_name}] Starting BootstrapFewShot")
        bfs = BootstrapFewShot(
            metric=metric_fn,
            max_bootstrapped_demos=BFS_MAX_BOOTSTRAPPED,
            max_labeled_demos=BFS_MAX_LABELED,
        )
        try:
            stage2 = bfs.compile(best_module, trainset=trainset)
        except Exception as e:
            print(f"[train_metrics:{metric_name}] Bootstrap failed: {e}. Keeping previous best.")
            stage2 = best_module

        s2_score = _run_eval(stage2, valset, metric_fn, cfg)
        print(f"[train_metrics:{metric_name}] Bootstrap val composite: {s2_score:.4f}")
        _save_metric_prompt(stage2, metric_name, prompt_path, f"bootstrap_{run_tag}", s2_score, cfg,
                             update_latest=(s2_score >= best_score))
        if s2_score >= best_score:
            best_module, best_score = stage2, s2_score

    test_score = _run_eval(best_module, testset, metric_fn, cfg)
    test_report = _agreement_report(best_module, testset, score_min, score_max)
    print(f"[train_metrics:{metric_name}] Best val composite:  {best_score:.4f}")
    print(f"[train_metrics:{metric_name}] Test composite:      {test_score:.4f}  "
          f"exact_match={test_report.get('exact_match', 'n/a')}  qwk={test_report.get('qwk', 'n/a')}")


def main():
    args = _parse_args()
    cfg = AlignmentConfig()

    if args.breadth:
        cfg.copro_breadth = args.breadth
    if args.depth:
        cfg.copro_depth = args.depth
    if args.max_train:
        cfg.max_train = args.max_train
    if args.max_val:
        cfg.max_val = args.max_val
    if args.max_test:
        cfg.max_test = args.max_test

    run_tag = datetime.now().strftime("%Y%m%d_%H%M%S")

    lm = configure_lm(cfg)
    print(f"[train_metrics] Judge LM: {cfg.judge_model}")
    optimizer_lm = configure_optimizer_lm(cfg)

    metrics_config = _load_metrics_config(cfg.metrics_config_file)
    requested = (
        [m.strip() for m in args.metrics.split(",")] if args.metrics else list(metrics_config.keys())
    )
    unknown = [m for m in requested if m not in metrics_config]
    if unknown:
        raise ValueError(f"Unknown metric(s) {unknown}. Known metrics: {list(metrics_config.keys())}")

    for metric_name in requested:
        _train_one_metric(metric_name, metrics_config[metric_name], args, cfg, optimizer_lm, run_tag)

    print_token_report(lm, cfg)


if __name__ == "__main__":
    main()
