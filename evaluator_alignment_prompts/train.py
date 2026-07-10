"""
train.py — Main training loop for evaluator alignment optimization.

Runs the complete pipeline:

  1. Load train/val/test CSVs
  2. Baseline evaluation (before optimization)
  3. Stage 1: COPRO prompt optimization
  4. Stage 2: BootstrapFewShot demo selection
  5. Final evaluation on held-out test set
  6. Error analysis & report generation
  7. Save the optimized prompt (timestamped + "latest" copy)

Usage
-----
  # Minimal — 3 CSVs, everything else from config.py / .env defaults
  python -m evaluator_alignment_prompts.train \\
      --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv

  # COPRO only
  python -m evaluator_alignment_prompts.train --optimizer copro ...

  # MIPROv2 (expensive — use after COPRO plateau)
  python -m evaluator_alignment_prompts.train --optimizer mipro ...

  # Load an existing optimized module and only run evaluation
  python -m evaluator_alignment_prompts.train --eval-only artifacts/stage2_bootstrap.json ...

  # Override hyperparameters
  python -m evaluator_alignment_prompts.train --breadth 6 --depth 4 --max-train 100 ...

Stopping criteria
-----------------
  The loop terminates when:
    a) All stages complete, or
    b) Composite agreement metric reaches `--target-score` (default 80, 0-100 scale), or
    c) Validation improvement < `--min-improvement` for 2 stages
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# -- Make sure the project root is importable -------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from dotenv import load_dotenv
load_dotenv()

import dspy

from evaluator_alignment_prompts.config import (
    ARTIFACTS_DIR,
    EVAL_SYSTEM_PROMPT,
    TEST_CSV,
    TRAIN_CSV,
    VAL_CSV,
    AlignmentConfig,
)
from evaluator_alignment_prompts.dataset import load_dataset
from evaluator_alignment_prompts.evaluate import (
    analyze_error_patterns,
    compare_prompt_versions,
    compute_full_report,
    evaluate_on_split,
    generate_confusion_matrix,
    generate_error_report,
)
from evaluator_alignment_prompts.metric import multidim_agreement_metric
from evaluator_alignment_prompts.module import MultiDimEvaluatorModule
from evaluator_alignment_prompts.optimizer import (
    configure_lm,
    configure_optimizer_lm,
    print_token_report,
    run_bootstrap,
    run_copro,
    run_mipro,
    save_optimized_prompt,
)


# ---------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(
        description="Optimize a DSPy evaluator prompt to align with human judgements, "
                     "given a train/val/test CSV split."
    )
    p.add_argument("--train-csv", type=Path, default=TRAIN_CSV, help="Path to the training CSV.")
    p.add_argument("--val-csv",   type=Path, default=VAL_CSV,   help="Path to the validation CSV.")
    p.add_argument("--test-csv",  type=Path, default=TEST_CSV,  help="Path to the held-out test CSV.")
    p.add_argument(
        "--optimizer",
        choices=["copro", "bootstrap", "mipro", "two-stage"],
        default="two-stage",
        help="Optimizer to use. 'two-stage' = COPRO -> Bootstrap (recommended).",
    )
    p.add_argument(
        "--eval-only",
        metavar="PATH",
        default=None,
        help="Skip optimization; load an existing .json module and evaluate only.",
    )
    p.add_argument("--breadth",   type=int, default=None, help="COPRO breadth override.")
    p.add_argument("--depth",     type=int, default=None, help="COPRO depth override.")
    p.add_argument("--max-train", type=int, default=None, help="Cap on training examples used.")
    p.add_argument("--max-val",   type=int, default=None, help="Cap on validation examples used.")
    p.add_argument("--max-test",  type=int, default=None, help="Cap on test examples used.")
    p.add_argument(
        "--target-score", type=float, default=80.0,
        # DSPy Evaluate returns metrics on a 0-100 scale.
        help="Stop early if val metric reaches this value (0-100 scale, default 80.0).",
    )
    p.add_argument(
        "--min-improvement", type=float, default=0.5,
        help="Min improvement per stage to keep optimizing (0-100 scale, default 0.5).",
    )
    p.add_argument(
        "--no-notes", action="store_true",
        help="Exclude human notes from input features (blind mode).",
    )
    return p.parse_args()


# ---------------------------------------------------------------------
# Main training loop
# ---------------------------------------------------------------------

def main():
    args = _parse_args()
    cfg  = AlignmentConfig()

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
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # -- 1. Configure LM ---------------------------------------------
    lm = configure_lm(cfg)
    print(f"[train] Judge LM: {cfg.judge_model}")
    optimizer_lm = configure_optimizer_lm(cfg)

    # -- 2. Load dataset ---------------------------------------------
    include_notes = not args.no_notes
    trainset, valset, testset, stats = load_dataset(
        cfg,
        train_csv=args.train_csv,
        val_csv=args.val_csv,
        test_csv=args.test_csv,
        include_notes_as_input=include_notes,
        verbose=True,
    )

    # -- 3. Load / construct baseline module -------------------------
    if args.eval_only:
        print(f"[train] Loading existing module: {args.eval_only}")
        module = MultiDimEvaluatorModule()
        module.load(args.eval_only)
    else:
        module = MultiDimEvaluatorModule.load_from_prompt_file(EVAL_SYSTEM_PROMPT)
        print(f"[train] Loaded baseline from {EVAL_SYSTEM_PROMPT}")

    # -- 4. Baseline evaluation --------------------------------------
    print("\n[train] --- BASELINE EVALUATION ---")
    baseline_val_score, baseline_val_records = evaluate_on_split(
        module, valset, cfg, metric=multidim_agreement_metric, verbose=True
    )
    baseline_report = compute_full_report(baseline_val_records)
    print(f"[train] Baseline val composite: {baseline_val_score:.4f}")
    print(f"[train] Baseline QWK: {baseline_report.get('qwk', 'n/a')}")
    print(f"[train] Baseline exact match: {baseline_report.get('exact_match', 'n/a')}")

    generate_error_report(
        records=baseline_val_records,
        report=baseline_report,
        patterns=analyze_error_patterns(baseline_val_records),
        confusion=generate_confusion_matrix(baseline_val_records),
        version_tag=f"baseline_{run_tag}",
    )

    if args.eval_only:
        _run_final_test(module, testset, cfg, run_tag, baseline_report)
        print_token_report(lm, cfg)
        _print_save_summary(cfg, run_tag)
        return

    if baseline_val_score >= args.target_score:
        print(
            f"[train] Baseline already meets target score "
            f"({baseline_val_score:.4f} >= {args.target_score}). Skipping optimization."
        )
        save_optimized_prompt(module, f"baseline_{run_tag}", baseline_val_score, cfg)
        _run_final_test(module, testset, cfg, run_tag, baseline_report)
        print_token_report(lm, cfg)
        _print_save_summary(cfg, run_tag)
        return

    # -- 5. Optimization stages --------------------------------------
    best_module    = module
    best_val_score = baseline_val_score
    best_report    = baseline_report
    stagnation     = 0

    optimizer = args.optimizer

    if optimizer in ("copro", "two-stage"):
        print("\n[train] --- STAGE 1: COPRO ---")
        try:
            stage1 = run_copro(module, trainset, cfg, multidim_agreement_metric, prompt_model=optimizer_lm)
        except Exception as e:
            print(f"[train] COPRO failed: {e}. Skipping to bootstrap.")
            stage1 = module

        s1_score, s1_records = evaluate_on_split(stage1, valset, cfg, metric=multidim_agreement_metric, verbose=True)
        s1_report = compute_full_report(s1_records)
        print(f"[train] Stage-1 val composite: {s1_score:.4f}")

        generate_error_report(
            records=s1_records,
            report=s1_report,
            patterns=analyze_error_patterns(s1_records),
            confusion=generate_confusion_matrix(s1_records),
            version_tag=f"stage1_copro_{run_tag}",
        )

        improvement = s1_score - best_val_score
        if improvement >= args.min_improvement:
            best_module    = stage1
            best_val_score = s1_score
            best_report    = s1_report
            stagnation     = 0
            print(f"[train] Stage 1 improved by {improvement:.4f}")
        else:
            stagnation += 1
            print(f"[train] Stage 1 did not improve (Δ={improvement:.4f}). Stagnation={stagnation}")

        save_optimized_prompt(stage1, f"stage1_copro_{run_tag}", s1_score, cfg, update_latest=False)

    if optimizer in ("bootstrap", "two-stage") and stagnation < 2:
        print("\n[train] --- STAGE 2: BootstrapFewShot ---")
        try:
            stage2 = run_bootstrap(best_module, trainset, cfg, multidim_agreement_metric)
        except Exception as e:
            print(f"[train] Bootstrap failed: {e}. Keeping Stage 1 output.")
            stage2 = best_module

        s2_score, s2_records = evaluate_on_split(stage2, valset, cfg, metric=multidim_agreement_metric, verbose=True)
        s2_report = compute_full_report(s2_records)
        print(f"[train] Stage-2 val composite: {s2_score:.4f}")

        generate_error_report(
            records=s2_records,
            report=s2_report,
            patterns=analyze_error_patterns(s2_records),
            confusion=generate_confusion_matrix(s2_records),
            version_tag=f"stage2_bootstrap_{run_tag}",
        )

        improvement = s2_score - best_val_score
        if improvement >= args.min_improvement:
            best_module    = stage2
            best_val_score = s2_score
            best_report    = s2_report
            print(f"[train] Stage 2 improved by {improvement:.4f}")
        else:
            print(f"[train] Stage 2 did not improve (Δ={improvement:.4f}). Keeping Stage 1.")

        save_optimized_prompt(stage2, f"stage2_bootstrap_{run_tag}", s2_score, cfg, update_latest=False)

    if optimizer == "mipro":
        print("\n[train] --- MIPRO v2 ---")
        try:
            mipro_module = run_mipro(module, trainset, valset, cfg, multidim_agreement_metric)
        except Exception as e:
            print(f"[train] MIPROv2 failed: {e}")
            mipro_module = module

        mp_score, mp_records = evaluate_on_split(mipro_module, valset, cfg, metric=multidim_agreement_metric, verbose=True)
        mp_report = compute_full_report(mp_records)
        print(f"[train] MIPROv2 val composite: {mp_score:.4f}")
        if mp_score > best_val_score:
            best_module    = mipro_module
            best_val_score = mp_score
            best_report    = mp_report

        save_optimized_prompt(mipro_module, f"mipro_{run_tag}", mp_score, cfg, update_latest=False)

    # -- 6. Deploy the run's actual best module (not just whichever ---
    #      stage happened to run last) as the "latest" copy.
    save_optimized_prompt(best_module, f"best_{run_tag}", best_val_score, cfg, update_latest=True)

    print("\n[train] --- PROMPT VERSION COMPARISON ---")
    comparison_md = compare_prompt_versions(
        baseline_report, best_report, "Baseline", "Optimized"
    )
    print(comparison_md)

    # -- 7. Final test evaluation -------------------------------------
    _run_final_test(best_module, testset, cfg, run_tag, best_report)

    # -- 8. Token usage & cost -----------------------------------------
    print_token_report(lm, cfg)

    # -- 9. Save-path summary -------------------------------------------
    _print_save_summary(cfg, run_tag)


def _run_final_test(
    module: MultiDimEvaluatorModule,
    testset,
    cfg: AlignmentConfig,
    run_tag: str,
    val_report: dict,
) -> None:
    """Evaluate on the held-out test set and write the final report."""
    print("\n[train] --- FINAL TEST EVALUATION ---")
    test_score, test_records = evaluate_on_split(module, testset, cfg, metric=multidim_agreement_metric, verbose=True)
    test_report    = compute_full_report(test_records)
    test_patterns  = analyze_error_patterns(test_records)
    test_confusion = generate_confusion_matrix(test_records)

    print(f"[train] Test composite:   {test_score:.4f}")
    print(f"[train] Test QWK:         {test_report.get('qwk', 'n/a')}")
    print(f"[train] Test exact match: {test_report.get('exact_match', 'n/a')}")

    report_path = generate_error_report(
        records=test_records,
        report=test_report,
        patterns=test_patterns,
        confusion=test_confusion,
        version_tag=f"final_test_{run_tag}",
        output_path=ARTIFACTS_DIR / f"final_test_report_{run_tag}.md",
    )
    print(f"[train] Final report -> {report_path}")

    summary = {
        "run_tag":        run_tag,
        "test_composite": round(test_score, 4),
        "test_report":    test_report,
        "val_report":     val_report,
        "error_patterns": test_patterns,
    }
    summary_path = ARTIFACTS_DIR / f"summary_{run_tag}.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[train] Summary -> {summary_path}")


def _print_save_summary(cfg: AlignmentConfig, run_tag: str) -> None:
    """Print a clear summary of every file saved during this run."""
    W = 64
    BORDER = "=" * W

    artifacts  = cfg.artifacts_dir
    opt_dir    = cfg.optimized_prompts_dir
    ref_prompt = cfg.optimized_prompt_out

    print("\n" + BORDER)
    print(f"{'  FILES SAVED THIS RUN':^{W}}")
    print(BORDER)

    print(f"  OPTIMIZED PROMPTS  ->  {opt_dir}")
    print(f"  (one file per run, never overwritten)")
    saved_prompts = sorted(opt_dir.glob(f"*{run_tag}*.md"))
    if saved_prompts:
        for p in saved_prompts:
            print(f"    [OK]  {p.name}")
    else:
        for p in sorted(opt_dir.glob("*.md"))[-3:]:
            print(f"    [OK]  {p.name}")
    print()

    print(f"  LATEST COPY (best prompt from this run):")
    print(f"    [OK]  {ref_prompt}")
    print()

    print(f"  DSPy PROGRAMS (instruction + demos):")
    for fname in ["stage1_copro.json", "stage2_bootstrap.json", "stage3_mipro.json"]:
        p = artifacts / fname
        if p.exists():
            print(f"    [OK]  {fname}")
            print(f"       {p}")
    print()

    print(f"  ANALYSIS REPORTS:")
    for p in sorted(artifacts.glob(f"*{run_tag}*")):
        print(f"    [OK]  {p.name}")
    print()

    print(BORDER)
    print(f"{'  TO CHANGE YOUR BASELINE PROMPT':^{W}}")
    print(BORDER)
    print(f"  The optimizer always starts from config.EVAL_SYSTEM_PROMPT, currently:")
    print(f"    {cfg.optimized_prompt_out.parent.parent / 'prompts' / 'evaluation_system_baseline.md'}")
    print()
    print(f"  To use a previous optimized prompt as the new baseline:")
    print(f"    1. Pick a file from:  {opt_dir}")
    print(f"    2. Set BASELINE_PROMPT_PATH (env var / .env) to that file's path.")
    print(f"    3. Re-run: python -m evaluator_alignment_prompts.train --train-csv ... --val-csv ... --test-csv ...")
    print(BORDER + "\n")


if __name__ == "__main__":
    main()
