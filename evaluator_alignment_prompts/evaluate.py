"""
evaluate.py — Evaluation and error analysis for the alignment pipeline.

Functions
---------
  evaluate_on_split()         Run the evaluator on a set and collect predictions.
  compute_full_report()       Full agreement report (all metrics).
  generate_confusion_matrix() Confusion matrix as a formatted table.
  find_worst_disagreements()  Top-k examples with largest human-LLM gap.
  score_distribution()        Score histograms for human and LLM.
  generate_error_report()     Auto-generated markdown error analysis artifact.
  compare_prompt_versions()   Side-by-side comparison of two prompt versions.

All analysis functions return plain dicts/lists for easy serialization.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import dspy
from dspy.evaluate import Evaluate

from evaluator_alignment_prompts.config import (
    ARTIFACTS_DIR,
    SCORE_MAX,
    SCORE_MIN,
    AlignmentConfig,
)
from evaluator_alignment_prompts.metric import (
    composite_agreement_metric,
    evaluate_agreement,
)
from evaluator_alignment_prompts.module import EvaluatorModule


# ---------------------------------------------------------------------
# Prediction collection
# ---------------------------------------------------------------------

def evaluate_on_split(
    module: EvaluatorModule,
    dataset: List[dspy.Example],
    cfg: AlignmentConfig,
    metric=None,
    verbose: bool = True,
) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Run the module on every example in `dataset`.

    Returns:
      (aggregate_metric_score, list_of_per_example_dicts)
    """
    if metric is None:
        metric = composite_agreement_metric

    evaluator = Evaluate(
        devset=dataset,
        metric=metric,
        num_threads=cfg.num_threads,
        display_progress=verbose,
        display_table=0,
        return_all_scores=True,
    )

    result = evaluator(module)
    if isinstance(result, tuple):
        agg_score, per_scores = result
    else:
        agg_score, per_scores = float(result), []

    # Collect predictions manually for detailed analysis
    records: List[Dict[str, Any]] = []
    n_failed = 0
    for i, ex in enumerate(dataset):
        try:
            pred = module(
                question=ex.question,
                context=ex.context,
                agent_response=ex.agent_response,
                human_notes=getattr(ex, "human_notes", ""),
            )
            if pred.score is None:
                raise ValueError("module returned score=None (parse/schema failure)")
            pred_score = float(pred.score)
        except Exception as e:
            n_failed += 1
            pred_score = float(SCORE_MIN)
            pred = dspy.Prediction(score=pred_score, reason=f"ERROR: {e}")

        records.append(
            {
                "idx":         i,
                "question":    ex.question[:120],
                "human_score": float(ex.human_score),
                "pred_score":  pred_score,
                "pred_reason": getattr(pred, "reason", ""),
                "confidence":  getattr(pred, "confidence", ""),
                "verdict":     getattr(ex, "verdict", ""),
                "human_notes": getattr(ex, "human_notes", ""),
                "abs_error":   abs(pred_score - float(ex.human_score)),
            }
        )

    if n_failed:
        print(f"[evaluate] WARNING: {n_failed}/{len(dataset)} predictions failed to parse "
              f"and were defaulted to SCORE_MIN={SCORE_MIN} — check module output format.")

    if verbose:
        print(f"[evaluate] Aggregate metric: {agg_score:.4f} over {len(dataset)} examples")

    return float(agg_score), records


# ---------------------------------------------------------------------
# Agreement report
# ---------------------------------------------------------------------

def compute_full_report(records: List[Dict]) -> Dict[str, Any]:
    """
    Compute all agreement metrics from a list of prediction records.
    Compatible with metric.evaluate_agreement().
    """
    human = [r["human_score"] for r in records]
    pred  = [r["pred_score"]  for r in records]
    return evaluate_agreement(human, pred, SCORE_MIN, SCORE_MAX)


# ---------------------------------------------------------------------
# Confusion matrix
# ---------------------------------------------------------------------

def generate_confusion_matrix(records: List[Dict]) -> Dict[str, Any]:
    """
    Build a confusion matrix (human rows × predicted columns).
    Both axes cover the configured score range.
    """
    labels = list(range(SCORE_MIN, SCORE_MAX + 1))
    matrix: Dict[int, Dict[int, int]] = {h: {p: 0 for p in labels} for h in labels}

    for r in records:
        h = int(round(r["human_score"]))
        p = int(round(r["pred_score"]))
        h = max(SCORE_MIN, min(SCORE_MAX, h))
        p = max(SCORE_MIN, min(SCORE_MAX, p))
        matrix[h][p] += 1

    header = "Human \\ Pred | " + " | ".join(str(l) for l in labels)
    separator = "--- | " + " | ".join(["---"] * len(labels))
    rows = []
    for h in labels:
        row = f"**{h}** | " + " | ".join(str(matrix[h][p]) for p in labels)
        rows.append(row)

    table_md = "\n".join([header, separator] + rows)
    return {"matrix": matrix, "table_md": table_md, "labels": labels}


# ---------------------------------------------------------------------
# Worst disagreements
# ---------------------------------------------------------------------

def find_worst_disagreements(
    records: List[Dict], top_k: int = 20
) -> List[Dict]:
    """
    Return the top-k examples with the largest absolute error.
    Useful for identifying systematic prompt failures.
    """
    sorted_recs = sorted(records, key=lambda r: r["abs_error"], reverse=True)
    return sorted_recs[:top_k]


# ---------------------------------------------------------------------
# Score distributions
# ---------------------------------------------------------------------

def score_distribution(records: List[Dict]) -> Dict[str, Dict[int, int]]:
    """
    Return score histograms for both human and predicted scores.
    """
    human_dist: Dict[int, int] = Counter(int(round(r["human_score"])) for r in records)
    pred_dist:  Dict[int, int] = Counter(int(round(r["pred_score"]))  for r in records)
    return {"human": dict(human_dist), "predicted": dict(pred_dist)}


# ---------------------------------------------------------------------
# Common error pattern detection
# ---------------------------------------------------------------------

def analyze_error_patterns(records: List[Dict]) -> Dict[str, Any]:
    """
    Automatically detect common evaluator error patterns.

    Patterns detected:
    1. Score inflation  — LLM consistently scores higher than humans.
    2. Score deflation  — LLM consistently scores lower.
    3. Verdict bias     — Errors cluster on specific human verdicts.
    4. Note-correlated  — Errors higher when human_notes are present.
    5. Confidence mismatch — High-confidence but wrong predictions.
    """
    if not records:
        return {}

    errors   = [r["pred_score"] - r["human_score"] for r in records]
    mean_err = sum(errors) / len(errors)

    verdict_errors: Dict[str, List[float]] = defaultdict(list)
    for r in records:
        verdict_errors[r["verdict"]].append(r["abs_error"])
    verdict_mae = {
        v: round(sum(errs) / len(errs), 3)
        for v, errs in verdict_errors.items()
        if errs
    }

    with_notes    = [r for r in records if r.get("human_notes")]
    without_notes = [r for r in records if not r.get("human_notes")]
    mae_with    = (sum(r["abs_error"] for r in with_notes)    / len(with_notes))    if with_notes else 0
    mae_without = (sum(r["abs_error"] for r in without_notes) / len(without_notes)) if without_notes else 0

    high_conf_wrong = [
        r for r in records
        if r.get("confidence") == "High" and r["abs_error"] >= 2
    ]

    return {
        "mean_signed_error":     round(mean_err, 3),
        "bias":                  "inflation" if mean_err > 0.3 else
                                 "deflation" if mean_err < -0.3 else "neutral",
        "verdict_mae":           verdict_mae,
        "mae_with_notes":        round(mae_with, 3),
        "mae_without_notes":     round(mae_without, 3),
        "notes_help":            mae_with < mae_without,
        "high_conf_wrong_count": len(high_conf_wrong),
        "suggestions": _generate_suggestions(mean_err, verdict_mae, mae_with, mae_without),
    }


def _generate_suggestions(
    mean_err: float,
    verdict_mae: Dict[str, float],
    mae_with: float,
    mae_without: float,
) -> List[str]:
    """Auto-generate prompt improvement suggestions from error analysis."""
    suggestions = []

    if mean_err > 0.3:
        suggestions.append(
            "Score inflation detected: tighten the rubric for the top score — "
            "add examples of responses that LOOK good but have minor issues."
        )
    elif mean_err < -0.3:
        suggestions.append(
            "Score deflation detected: the evaluator is too harsh. "
            "Add positive examples showing what earns a top score despite minor notes."
        )

    worst_verdict = max(verdict_mae, key=verdict_mae.get) if verdict_mae else None
    if worst_verdict and verdict_mae[worst_verdict] > 1.0:
        suggestions.append(
            f"Highest MAE on '{worst_verdict}' verdicts "
            f"(MAE={verdict_mae[worst_verdict]:.2f}). "
            "Add few-shot examples specifically for this verdict category."
        )

    if mae_with > mae_without + 0.3:
        suggestions.append(
            "Errors are HIGHER when human notes are present — the model may "
            "be over-relying on note presence as a quality signal. "
            "Consider removing human_notes from the input during blind evaluation."
        )
    elif mae_without > mae_with + 0.3:
        suggestions.append(
            "Notes significantly help alignment (MAE drops from "
            f"{mae_without:.2f} to {mae_with:.2f}). "
            "Consider incorporating rubric examples from human notes into the prompt."
        )

    return suggestions


# ---------------------------------------------------------------------
# Full error report artifact
# ---------------------------------------------------------------------

def generate_error_report(
    records: List[Dict],
    report: Dict,
    patterns: Dict,
    confusion: Dict,
    version_tag: str = "latest",
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate a markdown error analysis artifact.
    """
    if output_path is None:
        output_path = ARTIFACTS_DIR / f"error_report_{version_tag}.md"

    worst = find_worst_disagreements(records, top_k=10)
    dist  = score_distribution(records)

    lines = [
        f"# Evaluator Alignment Error Report — {version_tag}",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Agreement Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Exact Match | {report.get('exact_match', 'n/a')} |",
        f"| Adjacent Match (±1) | {report.get('adjacent_match', 'n/a')} |",
        f"| MAE | {report.get('mae', 'n/a')} |",
        f"| MAE Normalized | {report.get('mae_normalized', 'n/a')} |",
        f"| QWK | {report.get('qwk', 'n/a')} |",
        f"| Pearson r | {report.get('pearson_r', 'n/a')} |",
        f"| Spearman ρ | {report.get('spearman_rho', 'n/a')} |",
        f"| N examples | {report.get('n', len(records))} |",
        "",
        "## Score Distributions",
        "",
        "| Score | Human Count | LLM Count |",
        "|-------|-------------|-----------|",
    ]
    for s in range(SCORE_MIN, SCORE_MAX + 1):
        h_cnt = dist["human"].get(s, 0)
        p_cnt = dist["predicted"].get(s, 0)
        lines.append(f"| {s} | {h_cnt} | {p_cnt} |")

    lines += [
        "",
        "## Confusion Matrix",
        "",
        "_Rows = Human score, Columns = LLM predicted score_",
        "",
        confusion.get("table_md", ""),
        "",
        "## Bias & Pattern Analysis",
        "",
        f"- **Mean signed error**: {patterns.get('mean_signed_error', 'n/a')} "
        f"({patterns.get('bias', 'unknown')})",
        f"- **MAE with human notes**: {patterns.get('mae_with_notes', 'n/a')}",
        f"- **MAE without human notes**: {patterns.get('mae_without_notes', 'n/a')}",
        f"- **Notes help alignment**: {patterns.get('notes_help', 'n/a')}",
        f"- **High-confidence wrong predictions**: {patterns.get('high_conf_wrong_count', 'n/a')}",
        "",
        "### Per-Verdict MAE",
        "",
        "| Verdict | MAE |",
        "|---------|-----|",
    ]
    for v, mae_val in (patterns.get("verdict_mae") or {}).items():
        lines.append(f"| {v} | {mae_val} |")

    lines += [
        "",
        "## Prompt Improvement Suggestions",
        "",
    ]
    for i, suggestion in enumerate(patterns.get("suggestions", []), 1):
        lines.append(f"{i}. {suggestion}")

    lines += [
        "",
        "## Top-10 Worst Disagreements",
        "",
        "| # | Human | LLM | Error | Verdict | Notes |",
        "|---|-------|-----|-------|---------|-------|",
    ]
    for i, r in enumerate(worst, 1):
        notes_short = (r.get("human_notes") or "")[:60].replace("|", "/")
        lines.append(
            f"| {i} | {int(r['human_score'])} | {r['pred_score']:.1f} | "
            f"{r['abs_error']:.1f} | {r['verdict']} | {notes_short} |"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[evaluate] Error report -> {output_path}")
    return output_path


# ---------------------------------------------------------------------
# Prompt version comparison
# ---------------------------------------------------------------------

def compare_prompt_versions(
    report_a: Dict,
    report_b: Dict,
    label_a: str = "Baseline",
    label_b: str = "Optimized",
) -> str:
    """
    Return a markdown comparison table between two agreement reports.
    """
    metrics = ["exact_match", "adjacent_match", "mae", "qwk", "pearson_r"]
    lines = [
        f"| Metric | {label_a} | {label_b} | Delta |",
        "|--------|-----------|-----------|-------|",
    ]
    for m in metrics:
        a = report_a.get(m, float("nan"))
        b = report_b.get(m, float("nan"))
        delta = b - a if isinstance(a, float) and isinstance(b, float) else "n/a"
        sign = "+" if isinstance(delta, float) and delta > 0 else ""
        lines.append(f"| {m} | {a} | {b} | {sign}{delta} |")
    return "\n".join(lines)
