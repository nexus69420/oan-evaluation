"""
dataset.py — Loads three pre-split CSVs (train / val / test) into DSPy
Examples for the evaluator-alignment optimizer.

Expected CSV columns (names configurable via config.py / env vars):
  question         — the input query being answered
  agent_response   — the response being judged
  human_score      — the ground-truth quality score a human gave that response
  context          — (optional) retrieved context / tool output the agent had
  human_notes      — (optional) reviewer note on what was wrong (kept as an
                      input on the TRAIN set only — val/test are always blind)
  verdict          — (optional) free-text label, used only for error-analysis
                      stratification, never fed into the model as a signal
  confidence       — (optional) reviewer confidence label

Only question, agent_response, and human_score are required. Everything
else degrades gracefully (missing column -> empty string) if absent.
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
class DatasetStats:
    """Diagnostic stats printed after dataset construction."""
    total_examples: int = 0
    per_split:      Dict[str, int] = field(default_factory=dict)
    score_counts:   Dict[int, int] = field(default_factory=dict)
    verdict_counts: Dict[str, int] = field(default_factory=dict)
    skipped_rows:   int = 0

    def __str__(self) -> str:
        lines = [
            f"  Total examples  : {self.total_examples}",
            f"  Per split       : {self.per_split}",
            f"  Score dist      : {dict(sorted(self.score_counts.items()))}",
            f"  Verdict dist    : {dict(sorted(self.verdict_counts.items()))}",
            f"  Skipped rows    : {self.skipped_rows} (missing question/response/score)",
        ]
        return "\n".join(lines)


def _normalize_score(score: float, lo: float, hi: float) -> float:
    """Map [lo, hi] -> [0.0, 1.0]."""
    return (score - lo) / (hi - lo) if hi != lo else 0.0


def _clean(val) -> str:
    if val is None or pd.isna(val):
        return ""
    return str(val).strip()


def _load_split(
    csv_path: Path,
    cfg: AlignmentConfig,
    stats: DatasetStats,
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
    required = {_cfg.COL_QUESTION, _cfg.COL_RESPONSE, _cfg.COL_SCORE}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"{csv_path} is missing required columns: {missing}. "
            f"If your CSV uses different headers, set COL_QUESTION / COL_RESPONSE / "
            f"COL_SCORE (env vars) to match."
        )

    examples: List[dspy.Example] = []
    for _, row in df.iterrows():
        question       = _clean(row.get(_cfg.COL_QUESTION))
        agent_response = _clean(row.get(_cfg.COL_RESPONSE))

        try:
            human_score = float(row[_cfg.COL_SCORE])
        except (ValueError, TypeError):
            stats.skipped_rows += 1
            continue

        if not question or not agent_response:
            stats.skipped_rows += 1
            continue

        context    = _clean(row.get(_cfg.COL_CONTEXT)) or "(no context provided)"
        note       = _clean(row.get(_cfg.COL_NOTES))
        verdict    = _clean(row.get(_cfg.COL_VERDICT)).lower() or "unknown"
        confidence = _clean(row.get(_cfg.COL_CONFIDENCE))

        score_bucket = int(round(human_score))
        stats.score_counts[score_bucket] = stats.score_counts.get(score_bucket, 0) + 1
        stats.verdict_counts[verdict] = stats.verdict_counts.get(verdict, 0) + 1

        ex_fields: Dict = {
            "question":         question,
            "context":          context,
            "agent_response":   agent_response,
            "human_score":      human_score,
            "verdict":          verdict,
            "confidence":       confidence,
            "normalized_score": _normalize_score(human_score, cfg.score_min, cfg.score_max),
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


def load_dataset(
    cfg: AlignmentConfig,
    train_csv: Optional[Path] = None,
    val_csv: Optional[Path] = None,
    test_csv: Optional[Path] = None,
    include_notes_as_input: bool = True,
    verbose: bool = True,
) -> Tuple[List[dspy.Example], List[dspy.Example], List[dspy.Example], DatasetStats]:
    """
    Load pre-split train/val/test CSVs into DSPy Examples.

    Returns (trainset, valset, testset, stats).
    """
    train_csv = Path(train_csv or TRAIN_CSV)
    val_csv   = Path(val_csv or VAL_CSV)
    test_csv  = Path(test_csv or TEST_CSV)

    stats = DatasetStats()
    trainset = _load_split(train_csv, cfg, stats, "train", include_notes_as_input)
    valset   = _load_split(val_csv,   cfg, stats, "val",   include_notes_as_input)
    testset  = _load_split(test_csv,  cfg, stats, "test",  include_notes_as_input)
    stats.total_examples = len(trainset) + len(valset) + len(testset)

    if cfg.max_train:
        trainset = trainset[: cfg.max_train]
    if cfg.max_val:
        valset = valset[: cfg.max_val]
    if cfg.max_test:
        testset = testset[: cfg.max_test]

    # Val/test must always be blind to human_notes, regardless of
    # include_notes_as_input. Production inference NEVER has a human note
    # available — the note column can spell out the error directly (e.g.
    # "wrong word X correct Y"), so leaving it on the held-out sets doesn't
    # measure real judging ability. Only the trainset may keep notes
    # (Bootstrap uses them as calibration rationale for few-shot demos).
    if include_notes_as_input:
        valset = _strip_notes(valset)
        testset = _strip_notes(testset)

    if verbose:
        print(
            f"[dataset] Loaded {stats.total_examples} examples "
            f"(train={len(trainset)}, val={len(valset)}, test={len(testset)})"
        )
        print(stats)
        if include_notes_as_input:
            print("[dataset] human_notes kept for train only — val/test are blind (production-realistic).")

    if len(trainset) < 5:
        raise RuntimeError(
            f"Training set too small ({len(trainset)} usable rows) after filtering. "
            f"Check that '{_cfg.COL_SCORE}' has numeric values and "
            f"'{_cfg.COL_QUESTION}' / '{_cfg.COL_RESPONSE}' are populated in {train_csv}."
        )

    return trainset, valset, testset, stats


# ---------------------------------------------------------------------
# Standalone inspection
# ---------------------------------------------------------------------
if __name__ == "__main__":
    cfg = AlignmentConfig()
    train, val, test, stats = load_dataset(cfg, verbose=True)
    if train:
        print("\nFirst training example:")
        ex = train[0]
        for k in ex.inputs():
            print(f"  {k}: {str(ex[k])[:120]}")
        print(f"  human_score: {ex.human_score}")
        print(f"  verdict    : {ex.verdict}")
