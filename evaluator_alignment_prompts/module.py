"""
module.py — DSPy Modules for the evaluator alignment pipeline.

Two modules are provided:

  EvaluatorModule  — Single-score evaluator (integrates with COPRO/MIPROv2).
                     Loads config.EVAL_SYSTEM_PROMPT as its baseline.

  MultiDimEvaluatorModule — Full multi-dimension evaluator that mirrors a
                     structured, nested evaluation schema. Uses
                     ChainOfThought for better step-by-step reasoning.

  BlindEvaluatorModule — Production inference module (no human_notes).

All modules can be saved/loaded via dspy.Module.save() / .load().
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

import dspy

from evaluator_alignment_prompts.config import EVAL_SYSTEM_PROMPT, SCORE_MAX, SCORE_MIN
from evaluator_alignment_prompts.signature import (
    BlindEvaluationSignature,
    EvaluationSignature,
    MultiDimEvaluationSignature,
)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _parse_score_from_json(text: str) -> Optional[float]:
    """
    Extract a numeric score from a JSON string or raw text.
    Returns None if parsing fails.
    """
    try:
        data = json.loads(text)
        val = data.get("score") or data.get("overall_score")
        return float(val) if val is not None else None
    except Exception:
        pass

    match = re.search(r"\{[^}]+\}", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            val = data.get("score") or data.get("overall_score")
            return float(val) if val is not None else None
        except Exception:
            pass

    nums = re.findall(r"\b([1-4])\b", text)
    if nums:
        return float(nums[0])

    return None


def _parse_confidence(text: str) -> str:
    """Extract confidence level from JSON output."""
    try:
        data = json.loads(text)
        return str(data.get("confidence", "Medium"))
    except Exception:
        for level in ("High", "Medium", "Low"):
            if level.lower() in text.lower():
                return level
        return "Medium"


def _parse_reason(text: str) -> str:
    """Extract reason string from JSON output."""
    try:
        data = json.loads(text)
        return str(data.get("reason", ""))
    except Exception:
        return text[:200]


def _clamp(value: float, lo: float = SCORE_MIN, hi: float = SCORE_MAX) -> float:
    return max(lo, min(hi, value))


# ─────────────────────────────────────────────────────────────────────
# 1. Single-score Evaluator Module
# ─────────────────────────────────────────────────────────────────────

class EvaluatorModule(dspy.Module):
    """
    Single-score evaluator aligned to human judgements.

    Forward signature:
      (question, context, agent_response[, human_notes])
      → EvalPrediction(score, confidence, reason, raw)

    After optimization, save it with:

        module.save("artifacts/optimized_evaluator.json")
    """

    def __init__(self, baseline_instruction: Optional[str] = None):
        super().__init__()

        if baseline_instruction:
            sig = EvaluationSignature.with_instructions(baseline_instruction)
            self.predict = dspy.Predict(sig)
        else:
            self.predict = dspy.Predict(EvaluationSignature)

    @classmethod
    def load_from_prompt_file(
        cls, prompt_path: Path = EVAL_SYSTEM_PROMPT
    ) -> "EvaluatorModule":
        """
        Initialise with config.EVAL_SYSTEM_PROMPT as the baseline instruction.
        """
        text = prompt_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        # Heuristic: the JSON schema starts with ```json
        cutoff = next(
            (i for i, l in enumerate(lines) if l.strip().startswith("```json")),
            len(lines),
        )
        instruction = "".join(lines[:cutoff]).strip()
        return cls(baseline_instruction=instruction)

    def forward(
        self,
        question: str,
        context: str,
        agent_response: str,
        human_notes: str = "",
    ) -> dspy.Prediction:
        pred = self.predict(
            question=question,
            context=context,
            agent_response=agent_response,
            human_notes=human_notes,
        )
        raw = str(pred.overall_score)
        score = _parse_score_from_json(raw)
        score = _clamp(score or SCORE_MIN)
        return dspy.Prediction(
            overall_score=raw,
            score=score,
            confidence=_parse_confidence(raw),
            reason=_parse_reason(raw),
        )

    def get_instruction(self) -> str:
        """Return the current (possibly optimized) instruction string."""
        return self.predict.signature.instructions


# ─────────────────────────────────────────────────────────────────────
# 2. Multi-dimensional Evaluator Module
# ─────────────────────────────────────────────────────────────────────

class MultiDimEvaluatorModule(dspy.Module):
    """
    Full multi-dimension evaluator matching a structured, nested evaluation
    schema (see signature.MultiDimEvaluationSignature).

    Uses ChainOfThought so the LLM reasons step-by-step before producing
    the structured JSON — this consistently improves structured output
    accuracy on complex multi-field tasks.

    Output: dspy.Prediction with:
      - evaluation_json  : raw JSON string
      - parsed           : Dict with all dimension scores
      - overall_average  : float
      - critical_failures: list[str]
    """

    def __init__(self, baseline_instruction: Optional[str] = None):
        super().__init__()

        if baseline_instruction:
            sig = MultiDimEvaluationSignature.with_instructions(baseline_instruction)
            self.cot = dspy.ChainOfThought(sig)
        else:
            self.cot = dspy.ChainOfThought(MultiDimEvaluationSignature)

    @classmethod
    def load_from_prompt_file(
        cls, prompt_path: Path = EVAL_SYSTEM_PROMPT
    ) -> "MultiDimEvaluatorModule":
        text = prompt_path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        cutoff = next(
            (i for i, l in enumerate(lines) if l.strip().startswith("```json")),
            len(lines),
        )
        instruction = "".join(lines[:cutoff]).strip()
        return cls(baseline_instruction=instruction)

    def _parse_multidim(self, text: str) -> Dict[str, Any]:
        """Parse full evaluation JSON; return empty dict on failure."""
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", text)
            if match:
                try:
                    return json.loads(match.group(0))
                except Exception:
                    pass
        return {}

    # Non-dimension keys the model puts at the top level alongside the
    # actual dimension groups (self-reported summary/aggregate — NOT used
    # for scoring; we independently recompute instead of trusting these).
    _META_KEYS = {"summary", "overall_average", "critical_failures"}

    def _walk_scores(self, node: Any) -> list:
        """Recursively collect every 'score' value found at any depth.

        The model is NOT consistent about nesting depth: some responses
        give one score per top-level dimension directly, others nest
        further into named sub-dimensions. A fixed-depth traversal misses
        whichever shape it wasn't written for; walking recursively handles
        both (and any other depth) uniformly.
        """
        scores = []
        if not isinstance(node, dict):
            return scores
        val = node.get("score")
        if val is not None and not isinstance(val, dict):
            try:
                scores.append(float(val))
            except (ValueError, TypeError):
                pass
        for key, child in node.items():
            if key == "score":
                continue
            if isinstance(child, dict):
                scores.extend(self._walk_scores(child))
        return scores

    def _compute_overall(self, parsed: Dict) -> Optional[float]:
        """
        Independently recompute the mean of all sub-dimension scores rather
        than trusting the model's self-reported "overall_average" (guards
        against arithmetic mistakes in the model's own summary).
        """
        all_scores = []
        for key, dim_data in parsed.items():
            if key in self._META_KEYS or not isinstance(dim_data, dict):
                continue
            all_scores.extend(self._walk_scores(dim_data))
        return round(sum(all_scores) / len(all_scores), 3) if all_scores else None

    def _get_critical_failures(self, parsed: Dict) -> list:
        critical_sub_dims = {
            "tool_sequencing", "no_fabrication",
            "source_alignment", "completeness", "citation_accuracy",
            "safety_compliance",
        }
        failures = []
        for dim_name, dim_data in parsed.items():
            if dim_name in self._META_KEYS or not isinstance(dim_data, dict):
                continue
            for sub_name, sub_data in dim_data.items():
                if not isinstance(sub_data, dict):
                    continue
                if sub_name in critical_sub_dims and sub_data.get("score") == 1:
                    failures.append(f"{dim_name}.{sub_name}")
        return failures

    def forward(
        self,
        question: str,
        context: str,
        agent_response: str,
        human_notes: str = "",
    ) -> dspy.Prediction:
        pred = self.cot(
            question=question,
            context=context,
            agent_response=agent_response,
            human_notes=human_notes,
        )
        raw = str(pred.evaluation_json)
        parsed = self._parse_multidim(raw)
        overall = self._compute_overall(parsed)
        failures = self._get_critical_failures(parsed)

        # overall_average is on the model's native 1-5 scale. `.score` is a
        # clamped 1-4 alias so this module is a drop-in replacement for
        # EvaluatorModule wherever code expects `.score` against human_score.
        score = _clamp(overall) if overall is not None else None

        return dspy.Prediction(
            evaluation_json=raw,
            parsed=parsed,
            overall_average=overall,
            score=score,
            reason=parsed.get("summary", "") if isinstance(parsed, dict) else "",
            confidence="Medium",
            critical_failures=failures,
        )

    def get_instruction(self) -> str:
        """Return the current (possibly optimized) instruction string."""
        return self.cot.predict.signature.instructions


# ─────────────────────────────────────────────────────────────────────
# 3. Blind Inference Module (production, no human_notes)
# ─────────────────────────────────────────────────────────────────────

class BlindEvaluatorModule(dspy.Module):
    """
    Production evaluator: no reviewer hints.
    Loads a previously optimized program file if available.
    """

    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict(BlindEvaluationSignature)

    @classmethod
    def from_optimized(cls, path: Path) -> "BlindEvaluatorModule":
        """Load a previously optimized DSPy program."""
        instance = cls()
        instance.load(str(path))
        return instance

    def forward(
        self,
        question: str,
        context: str,
        agent_response: str,
    ) -> dspy.Prediction:
        pred = self.predict(
            question=question,
            context=context,
            agent_response=agent_response,
        )
        raw = str(pred.overall_score)
        score = _parse_score_from_json(raw)
        score = _clamp(score or SCORE_MIN)
        return dspy.Prediction(
            overall_score=raw,
            score=score,
            confidence=_parse_confidence(raw),
            reason=_parse_reason(raw),
        )
