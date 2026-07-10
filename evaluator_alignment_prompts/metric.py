"""
metric.py — Human-agreement optimization metrics for DSPy.

All functions follow the DSPy metric contract:

    metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float

Return value is in [0, 1] where higher = better human agreement.

Metrics implemented
───────────────────
  exact_match_metric          — 1.0 iff score == human score (strict)
  adjacent_match_metric       — 1.0 if within ±1, else 0.0
  mae_metric                  — 1 - (|pred - human| / range)
  qwk_batch_metric             — Quadratic Weighted Kappa (batch, for reporting)
  composite_agreement_metric  — Weighted combination (the primary DSPy metric)
  multidim_agreement_metric   — For MultiDimEvaluatorModule optimization

Usage
─────
  Pass `composite_agreement_metric` (single-score module) or
  `multidim_agreement_metric` (multi-dim module) to COPRO / MIPROv2 as the
  `metric` arg.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Sequence

import dspy

from evaluator_alignment_prompts.config import (
    AGREEMENT_WEIGHTS,
    SCORE_MAX,
    SCORE_MIN,
)


# ─────────────────────────────────────────────────────────────────────
# Score extraction helpers
# ─────────────────────────────────────────────────────────────────────

def _extract_pred_score(pred: dspy.Prediction) -> Optional[float]:
    """Try multiple attributes to find the predicted numeric score."""
    # EvaluatorModule sets pred.score directly
    if hasattr(pred, "score") and pred.score is not None:
        try:
            return float(pred.score)
        except (ValueError, TypeError):
            pass

    # Fall back to parsing overall_score JSON string
    for attr in ("overall_score", "evaluation_json"):
        raw = getattr(pred, attr, None)
        if raw is None:
            continue
        try:
            data = json.loads(str(raw))
            val = data.get("score") or data.get("overall_score") or data.get("overall_average")
            if val is not None:
                return float(val)
        except Exception:
            pass
        nums = re.findall(r"\b([1-4])\b", str(raw))
        if nums:
            return float(nums[0])

    # MultiDimEvaluatorModule sets overall_average
    if hasattr(pred, "overall_average") and pred.overall_average is not None:
        try:
            return float(pred.overall_average)
        except (ValueError, TypeError):
            pass

    return None


def _clamp(v: float, lo: float = SCORE_MIN, hi: float = SCORE_MAX) -> float:
    return max(lo, min(hi, v))


# ─────────────────────────────────────────────────────────────────────
# Individual metric functions (DSPy-compatible)
# ─────────────────────────────────────────────────────────────────────

def exact_match_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """Score 1.0 iff predicted integer matches human integer exactly."""
    pred_score = _extract_pred_score(pred)
    if pred_score is None:
        return 0.0
    try:
        human = float(example.human_score)
    except (ValueError, TypeError, AttributeError):
        return 0.0
    return 1.0 if round(pred_score) == round(human) else 0.0


def adjacent_match_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Score 1.0 if within ±1 of human score, else 0.0.
    This is the standard 'lenient' inter-rater agreement criterion
    used in NLP evaluation benchmarks (e.g., STS, ROUGE variants).
    """
    pred_score = _extract_pred_score(pred)
    if pred_score is None:
        return 0.0
    try:
        human = float(example.human_score)
    except (ValueError, TypeError, AttributeError):
        return 0.0
    return 1.0 if abs(pred_score - human) <= 1.0 else 0.0


def mae_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Normalized inverse MAE: 1 - (|pred - human| / scale_range).
    Range = SCORE_MAX - SCORE_MIN (e.g. 3 for a 1-4 scale).
    Returns 1.0 for perfect match, 0.0 for maximum error.
    """
    pred_score = _extract_pred_score(pred)
    if pred_score is None:
        return 0.0
    try:
        human = float(example.human_score)
    except (ValueError, TypeError, AttributeError):
        return 0.0
    scale_range = SCORE_MAX - SCORE_MIN
    mae = abs(_clamp(pred_score) - human)
    return max(0.0, 1.0 - mae / scale_range)


def json_validity_metric(
    example: dspy.Example, pred: dspy.Prediction, trace=None
) -> float:
    """
    Bonus metric: returns 1.0 if the evaluator output is parseable JSON.
    Penalizes prompt mutations that cause formatting breakdown.
    """
    for attr in ("overall_score", "evaluation_json"):
        raw = getattr(pred, attr, None)
        if raw is None:
            continue
        try:
            json.loads(str(raw))
            return 1.0
        except Exception:
            match = re.search(r"\{[^}]+\}", str(raw))
            if match:
                try:
                    json.loads(match.group(0))
                    return 0.8  # Partial credit for recoverable JSON
                except Exception:
                    pass
    return 0.0


# ─────────────────────────────────────────────────────────────────────
# Composite metric (PRIMARY — use this with COPRO / MIPROv2)
# ─────────────────────────────────────────────────────────────────────

def composite_agreement_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace=None,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Weighted composite of human-agreement sub-metrics.

    Default weights come from config.AGREEMENT_WEIGHTS:
      exact_match              : 0.20
      mae_normalized            : 0.30   (highest weight — penalizes large errors)
      adjacent_match             : 0.20
      quadratic_weighted_kappa   : 0.30  (approximated per-example for optimization)

    Why this combination?
    - Exact match catches perfect calibration.
    - MAE penalizes large errors proportionally.
    - Adjacent match tolerates human annotator noise (inter-rater ±1 is normal).
    - QWK proxy punishes large disagreements more heavily than small ones.

    Heavy penalty (×0.5) is applied when JSON output is invalid — this
    prevents the optimizer from finding degenerate prompts that skip scoring.
    """
    w = weights or AGREEMENT_WEIGHTS

    em  = exact_match_metric(example, pred, trace)
    adj = adjacent_match_metric(example, pred, trace)
    mae = mae_metric(example, pred, trace)
    jv  = json_validity_metric(example, pred, trace)

    # Per-example QWK proxy: map distance to weight.
    # Real QWK needs a corpus; here we use (1 - (dist/range)^2) as a
    # per-example approximation of the quadratic penalty.
    pred_score = _extract_pred_score(pred)
    qwk_proxy = 0.0
    if pred_score is not None:
        try:
            human = float(example.human_score)
            dist = abs(_clamp(pred_score) - human)
            scale_range = SCORE_MAX - SCORE_MIN
            qwk_proxy = 1.0 - (dist / scale_range) ** 2
        except Exception:
            qwk_proxy = 0.0

    score = (
        w.get("exact_match",                0.20) * em
        + w.get("mae_normalized",           0.30) * mae
        + w.get("adjacent_match",           0.20) * adj
        + w.get("quadratic_weighted_kappa", 0.30) * qwk_proxy
    )

    # Formatting penalty: if output is not valid JSON at all, cut score in half
    if jv < 0.5:
        score *= 0.5

    return float(score)


# ─────────────────────────────────────────────────────────────────────
# Scale-aware metric factory (for SingleMetricEvaluatorModule / train_metrics.py)
# ─────────────────────────────────────────────────────────────────────

def make_agreement_metric(
    score_min: float,
    score_max: float,
    weights: Optional[Dict[str, float]] = None,
):
    """
    Build a composite agreement metric bound to a SPECIFIC score range.

    composite_agreement_metric (above) hardcodes the global SCORE_MIN/SCORE_MAX
    from config.py — fine for the single holistic judge, but per-metric
    optimization (train_metrics.py) needs each metric scored against its OWN
    scale (e.g. 0/1 for citation_accuracy vs 1-4 for accuracy_completeness).
    This returns a closure with the same weighted formula, evaluated against
    the given range instead.
    """
    w = weights or AGREEMENT_WEIGHTS
    scale_range = (score_max - score_min) or 1.0

    def _metric(example: dspy.Example, pred: dspy.Prediction, trace=None) -> float:
        pred_score = _extract_pred_score(pred)

        jv = json_validity_metric(example, pred, trace)

        if pred_score is None:
            return 0.0
        try:
            human = float(example.human_score)
        except (ValueError, TypeError, AttributeError):
            return 0.0

        pred_clamped = max(score_min, min(score_max, pred_score))
        dist = abs(pred_clamped - human)

        em       = 1.0 if round(pred_clamped) == round(human) else 0.0
        adjacent = 1.0 if dist <= 1.0 else 0.0
        mae_norm = max(0.0, 1.0 - dist / scale_range)
        qwk_proxy = 1.0 - (dist / scale_range) ** 2

        score = (
            w.get("exact_match",                0.20) * em
            + w.get("mae_normalized",           0.30) * mae_norm
            + w.get("adjacent_match",           0.20) * adjacent
            + w.get("quadratic_weighted_kappa", 0.30) * qwk_proxy
        )

        if jv < 0.5:
            score *= 0.5

        return float(score)

    return _metric


# ─────────────────────────────────────────────────────────────────────
# Multi-dimensional metric (for MultiDimEvaluatorModule)
# ─────────────────────────────────────────────────────────────────────

def multidim_agreement_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace=None,
) -> float:
    """
    Agreement metric for multi-dimensional predictions.

    Your CSVs provide only an overall human_score, so this compares
    pred.overall_average against example.human_score. JSON validity is
    also enforced.

    For experiments where per-dimension human labels exist, replace this
    with dimension-specific MAE aggregation.
    """
    jv = json_validity_metric(example, pred, trace)

    pred_overall = None
    if hasattr(pred, "overall_average"):
        pred_overall = pred.overall_average
    if pred_overall is None:
        pred_overall = _extract_pred_score(pred)

    if pred_overall is None:
        return 0.0

    # Re-scale: the multi-dim signature scores 1-5 sub-dimensions while
    # human_score may be on a different scale (e.g. 1-4) — clamp to the
    # configured human score range so the two are comparable.
    pred_overall_clamped = _clamp(float(pred_overall), SCORE_MIN, SCORE_MAX)

    try:
        human = float(example.human_score)
    except (ValueError, TypeError, AttributeError):
        return 0.0

    scale_range = SCORE_MAX - SCORE_MIN or 1
    mae = abs(pred_overall_clamped - human)
    mae_score = max(0.0, 1.0 - mae / scale_range)

    # Weight: 70% score agreement, 30% JSON validity
    return 0.70 * mae_score + 0.30 * jv


# ─────────────────────────────────────────────────────────────────────
# Batch analytics (for reporting, not DSPy optimization)
# ─────────────────────────────────────────────────────────────────────

def compute_batch_qwk(
    human_scores: Sequence[int],
    pred_scores: Sequence[int],
    min_rating: int = SCORE_MIN,
    max_rating: int = SCORE_MAX,
) -> float:
    """
    Quadratic Weighted Kappa over a list of (human, predicted) score pairs.

    QWK is the standard metric for inter-rater agreement on ordinal scales
    (used in Kaggle competitions, educational assessment, NLP eval papers).

    Returns float in [-1, 1] where:
      1.0  = perfect agreement
      0.0  = chance agreement
      <0   = worse than chance
    """
    import numpy as np  # local import — only needed for batch reporting

    human_arr = np.array(human_scores, dtype=int)
    pred_arr  = np.array(pred_scores,  dtype=int)
    n_classes = max_rating - min_rating + 1

    conf = np.zeros((n_classes, n_classes), dtype=int)
    for h, p in zip(human_arr, pred_arr):
        i = int(h) - min_rating
        j = int(p) - min_rating
        if 0 <= i < n_classes and 0 <= j < n_classes:
            conf[i, j] += 1

    weight = np.zeros((n_classes, n_classes), dtype=float)
    for i in range(n_classes):
        for j in range(n_classes):
            weight[i, j] = (i - j) ** 2 / (n_classes - 1) ** 2

    act_hist = conf.sum(axis=1)
    pred_hist = conf.sum(axis=0)
    n = len(human_scores)
    expected = np.outer(act_hist, pred_hist).astype(float) / (n or 1)

    observed_penalty = (weight * conf).sum()
    expected_penalty = (weight * expected).sum()

    if expected_penalty == 0:
        return 1.0

    return float(1.0 - observed_penalty / expected_penalty)


def compute_pearson(
    human_scores: Sequence[float],
    pred_scores: Sequence[float],
) -> float:
    """Pearson correlation between human and predicted scores."""
    import numpy as np
    h = np.array(human_scores, dtype=float)
    p = np.array(pred_scores,  dtype=float)
    if h.std() == 0 or p.std() == 0:
        return 0.0
    return float(np.corrcoef(h, p)[0, 1])


def compute_spearman(
    human_scores: Sequence[float],
    pred_scores: Sequence[float],
) -> float:
    """Spearman rank correlation between human and predicted scores."""
    from scipy.stats import spearmanr
    corr, _ = spearmanr(human_scores, pred_scores)
    return float(corr)


def evaluate_agreement(
    human_scores: List[float],
    pred_scores:  List[float],
    min_rating: int = SCORE_MIN,
    max_rating: int = SCORE_MAX,
) -> Dict[str, float]:
    """
    Compute a full agreement report for a batch of predictions.
    Used by evaluate.py for test-set reporting.
    """
    n = len(human_scores)
    if n == 0:
        return {}

    h_int = [round(s) for s in human_scores]
    p_int = [round(s) for s in pred_scores]

    exact    = sum(1 for h, p in zip(h_int, p_int) if h == p) / n
    adjacent = sum(1 for h, p in zip(h_int, p_int) if abs(h - p) <= 1) / n
    mae      = sum(abs(h - p) for h, p in zip(human_scores, pred_scores)) / n
    mae_norm = 1.0 - mae / (max_rating - min_rating)

    try:
        qwk = compute_batch_qwk(h_int, p_int, min_rating, max_rating)
    except Exception:
        qwk = float("nan")

    try:
        pearson = compute_pearson(human_scores, pred_scores)
    except Exception:
        pearson = float("nan")

    try:
        spearman = compute_spearman(human_scores, pred_scores)
    except Exception:
        spearman = float("nan")

    return {
        "exact_match":    round(exact, 4),
        "adjacent_match": round(adjacent, 4),
        "mae":            round(mae, 4),
        "mae_normalized": round(mae_norm, 4),
        "qwk":            round(qwk, 4),
        "pearson_r":      round(pearson, 4),
        "spearman_rho":   round(spearman, 4),
        "n":              n,
    }
