"""
metrics_dataset.py — Loads per-metric labeled examples for per-metric prompt
fine-tuning (train_metrics.py).

Reuses the SAME train/val/test CSVs as dataset.py (question, context,
agent_response, ...) but targets one metric's own score/notes columns
instead of the holistic `human_score` column — e.g. `citation_accuracy_score`
/ `citation_accuracy_notes` rather than `human_score` / `human_notes`.

Which metric maps to which columns is defined in
prompts/metrics/metrics_config.json (see train_metrics.py / promote_metrics.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import dspy

from evaluator_alignment_prompts import config as _cfg
from evaluator_alignment_prompts.config import AlignmentConfig, TEST_CSV, TRAIN_CSV, VAL_CSV


@dataclass
class MetricDatasetStats:
    """Diagnostic stats printed after per-metric dataset construction."""
    total_examples: int = 0
    per_split:      Dict[str, int] = field(default_factory=dict)
    score_counts:   Dict[float, int] = field(default_factory=dict)
    skipped_rows:   int = 0

    def __str__(self) -> str:
        lines = [
            f"  Total examples  : {self.total_examples}",
            f"  Per split       : {self.per_split}",
            f"  Score dist      : {dict(sorted(self.score_counts.items()))}",
            f"  Skipped rows    : {self.skipped_rows} (missing question/response/score)",
        ]
        return "\n".join(lines)


def _clean(val) -> str:
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()


def _load_metric_split(
    csv_path: Path,
    score_col: str,
    notes_col: Optional[str],
    stats: MetricDatasetStats,
    split_name: str,
    include_notes_as_input: bool,
) -> List[dspy.Example]:
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f"{split_name} CSV not found: {csv_path}. "
            f"Pass --{split_name}-csv or set the {split_name.upper()}_CSV env var."
        )

    df = pd.read_csv(csv_path)
    required = {_cfg.COL_QUESTION, _cfg.COL_RESPONSE, score_col}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{csv_path} is missing required columns for this metric: {missing}. "
            f"Check prompts/metrics/metrics_config.json's score_col/notes_col entries."
        )

    examples: List[dspy.Example] = []
    for _, row in df.iterrows():
        question       = _clean(row.get(_cfg.COL_QUESTION))
        agent_response = _clean(row.get(_cfg.COL_RESPONSE))

        try:
            score = float(row[score_col])
        except (ValueError, TypeError):
            stats.skipped_rows += 1
            continue

        if not question or not agent_response:
            stats.skipped_rows += 1
            continue

        context = _clean(row.get(_cfg.COL_CONTEXT)) or "(no context provided)"
        note    = _clean(row.get(notes_col)) if notes_col else ""

        bucket = round(score, 2)
        stats.score_counts[bucket] = stats.score_counts.get(bucket, 0) + 1

        # Field name kept generic (`human_score` / `human_notes`) so the
        # existing agreement-metric functions in metric.py work unchanged
        # regardless of which metric's column actually supplied the value.
        ex_fields: Dict = {
            "question":       question,
            "context":        context,
            "agent_response": agent_response,
            "human_score":    score,
        }

        if include_notes_as_input:
            ex_fields["human_notes"] = note
            ex = dspy.Example(**ex_fields).with_inputs(
                "question", "context", "agent_response", "human_notes"
            )
        else:
            ex = dspy.Example(**ex_fields).with_inputs(
                "question", "context", "agent_response"
            )
        examples.append(ex)

    stats.per_split[split_name] = len(examples)
    return examples


def _strip_notes(examples: List[dspy.Example]) -> List[dspy.Example]:
    """Return copies with human_notes blanked — val/test must stay blind."""
    blinded = []
    for ex in examples:
        data = dict(ex.toDict())
        data["human_notes"] = ""
        new_ex = dspy.Example(**data).with_inputs("question", "context", "agent_response")
        blinded.append(new_ex)
    return blinded


def load_metric_dataset(
    metric_name: str,
    score_col: str,
    cfg: AlignmentConfig,
    notes_col: Optional[str] = None,
    train_csv: Optional[Path] = None,
    val_csv: Optional[Path] = None,
    test_csv: Optional[Path] = None,
    include_notes_as_input: bool = True,
    verbose: bool = True,
) -> Tuple[List[dspy.Example], List[dspy.Example], List[dspy.Example], MetricDatasetStats]:
    """
    Load pre-split train/val/test CSVs into DSPy Examples for ONE metric.

    Returns (trainset, valset, testset, stats).
    """
    train_csv = Path(train_csv or TRAIN_CSV)
    val_csv   = Path(val_csv or VAL_CSV)
    test_csv  = Path(test_csv or TEST_CSV)

    stats = MetricDatasetStats()
    trainset = _load_metric_split(train_csv, score_col, notes_col, stats, "train", include_notes_as_input)
    valset   = _load_metric_split(val_csv,   score_col, notes_col, stats, "val",   include_notes_as_input)
    testset  = _load_metric_split(test_csv,  score_col, notes_col, stats, "test",  include_notes_as_input)
    stats.total_examples = len(trainset) + len(valset) + len(testset)

    if cfg.max_train:
        trainset = trainset[: cfg.max_train]
    if cfg.max_val:
        valset = valset[: cfg.max_val]
    if cfg.max_test:
        testset = testset[: cfg.max_test]

    if include_notes_as_input:
        valset = _strip_notes(valset)
        testset = _strip_notes(testset)

    if verbose:
        print(
            f"[metrics_dataset:{metric_name}] Loaded {stats.total_examples} examples "
            f"(train={len(trainset)}, val={len(valset)}, test={len(testset)})"
        )
        print(stats)

    if len(trainset) < 5:
        raise RuntimeError(
            f"[{metric_name}] Training set too small ({len(trainset)} usable rows) after filtering. "
            f"Check that '{score_col}' has numeric values in {train_csv}."
        )

    return trainset, valset, testset, stats
