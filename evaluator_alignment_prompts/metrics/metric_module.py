"""
metric_module.py — Single-metric DSPy module for per-metric prompt fine-tuning.

Companion to module.py's holistic EvaluatorModule / MultiDimEvaluatorModule,
which score every dimension in one call. This module scores exactly ONE
narrow metric per call (e.g. accuracy_completeness, citation_accuracy,
no_fabrication, actionability) — matching the per-metric optimization loop
in train_metrics.py, where each metric's prompt is tuned independently
against its own labeled score column.

Real-world per-metric prompts are frequently authored as Jinja templates
with category-conditional branches (see prompts/metrics/*.md). Since the
bundled sample CSVs don't carry a `category` column, _render_metric_prompt
renders each template once at load time with no category set, so every
file's generic/else branch is used as the static instruction.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Optional

import dspy
from jinja2 import Template


def _render_metric_prompt(raw_text: str, category: Optional[str] = None) -> str:
    """Render a (possibly Jinja-templated) metric prompt file into static instruction text."""
    return Template(raw_text).render(category=category).strip()


class SingleMetricSignature(dspy.Signature):
    """
    You are evaluating one narrow quality metric for an AI assistant's
    response. Follow the specific rubric given in your instructions and
    output ONLY a JSON object.
    """

    question: str = dspy.InputField(desc="The user's query.")
    context: str = dspy.InputField(
        desc="Retrieved context / tool output the agent had access to."
    )
    agent_response: str = dspy.InputField(desc="The agent's response to evaluate.")
    human_notes: str = dspy.InputField(
        desc=(
            "OPTIONAL reviewer hint. May name a specific error. "
            "Use this as a rubric calibration signal, not as the sole basis for scoring."
        ),
        default="",
    )

    score_json: str = dspy.OutputField(
        desc='Return STRICT JSON only: {"score": <number>, "reason": "<short>"}'
    )


class SingleMetricEvaluatorModule(dspy.Module):
    """
    A narrow, single-metric judge.

    Forward signature:
      (question, context, agent_response[, human_notes])
      -> Prediction(score, reason, score_json)

    score is clamped to [score_min, score_max] — the scale for THIS metric,
    which may differ from other metrics (e.g. 0/1 for citation_accuracy vs
    1-4 for accuracy_completeness).
    """

    def __init__(
        self,
        metric_name: str,
        score_min: float,
        score_max: float,
        baseline_instruction: Optional[str] = None,
    ):
        super().__init__()
        self.metric_name = metric_name
        self.score_min = score_min
        self.score_max = score_max

        if baseline_instruction:
            sig = SingleMetricSignature.with_instructions(baseline_instruction)
            self.predict = dspy.Predict(sig)
        else:
            self.predict = dspy.Predict(SingleMetricSignature)

    @classmethod
    def load_from_prompt_file(
        cls,
        metric_name: str,
        prompt_path: Path,
        score_min: float,
        score_max: float,
        category: Optional[str] = None,
    ) -> "SingleMetricEvaluatorModule":
        """Load a metric's baseline instruction from its prompt file (rendering Jinja if present)."""
        raw = Path(prompt_path).read_text(encoding="utf-8")
        instruction = _render_metric_prompt(raw, category=category)
        return cls(metric_name, score_min, score_max, baseline_instruction=instruction)

    def _parse_score(self, text: str) -> Optional[float]:
        try:
            data = json.loads(text)
            val = data.get("score")
            if val is not None:
                return float(val)
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                data = json.loads(match.group(0))
                val = data.get("score")
                if val is not None:
                    return float(val)
            except Exception:
                pass
        nums = re.findall(r"-?\d+(?:\.\d+)?", text)
        return float(nums[0]) if nums else None

    def _parse_reason(self, text: str) -> str:
        try:
            data = json.loads(text)
            return str(data.get("reason", ""))
        except Exception:
            return text[:200]

    def _clamp(self, value: float) -> float:
        return max(self.score_min, min(self.score_max, value))

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
        raw = str(pred.score_json)
        parsed = self._parse_score(raw)
        score = self._clamp(parsed if parsed is not None else self.score_min)
        return dspy.Prediction(
            score_json=raw,
            score=score,
            reason=self._parse_reason(raw),
        )

    def get_instruction(self) -> str:
        """Return the current (possibly optimized) instruction string."""
        return self.predict.signature.instructions
