from __future__ import annotations

from typing import Any, Dict

from evaluation.evaluator_custom import evaluate_record_with_judge

from .base import BaseMetric, MetricResult


class AgriEvalMetrics(BaseMetric):
    """
    Adapter metric that preserves the existing evaluator behavior.

    It runs the current pydantic-ai judge and maps output into the plugin contract.
    """

    metric_name = "agri_eval_metrics"

    async def evaluate(
        self,
        *,
        row_json: Dict[str, Any],
        transformed_json: Dict[str, Any],
        variables: Dict[str, Any],
        config: Dict[str, Any],
    ) -> MetricResult:
        llm = config["llm"]
        eval_dict = await evaluate_record_with_judge(transformed_json, llm=llm)
        score = eval_dict.get("metrics", {}).get("overall_average")
        reason = eval_dict.get("summary", "Evaluation completed via agri eval metrics.")
        runtime = eval_dict.get("runtime", {}) if isinstance(eval_dict, dict) else {}
        token_usage = runtime.get("token_usage", {}) if isinstance(runtime, dict) else {}
        cost_estimate = runtime.get("cost_estimate", {}) if isinstance(runtime, dict) else {}

        return MetricResult(
            metric_name=self.metric_name,
            score=score,
            reason=reason,
            metadata={
                "category": transformed_json.get("category", row_json.get("category", "")),
                "evaluation": eval_dict,
                "token_usage": token_usage,
                "cost_estimate": cost_estimate,
            },
        )
