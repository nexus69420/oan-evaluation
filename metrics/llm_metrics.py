from __future__ import annotations

import json
from typing import Any, Dict

from .base import BaseMetric, MetricResult
from .llm_metric_utils import run_llm_metric


class _LlmMetricBase(BaseMetric):
    prompt_file: str = ""

    async def evaluate(
        self,
        *,
        row_json: Dict[str, Any],
        transformed_json: Dict[str, Any],
        variables: Dict[str, Any],
        config: Dict[str, Any],
    ) -> MetricResult:
        return await run_llm_metric(
            metric_name=self.metric_name,
            prompt_file=self.prompt_file,
            row_json=row_json,
            transformed_json=transformed_json,
            variables=variables,
            config=config,
        )


# LLM metrics (one LLM call per metric)
class CitationComprehensivenessMetric(_LlmMetricBase):
    metric_name = "citation_comprehensiveness"
    prompt_file = "citation_comprehensiveness.md"


class NoFabricationMetric(_LlmMetricBase):
    metric_name = "no_fabrication"
    prompt_file = "no_fabrication.md"


class CitationAccuracyMetric(_LlmMetricBase):
    metric_name = "citation_accuracy"
    prompt_file = "citation_accuracy.md"


class CompletenessMetric(_LlmMetricBase):
    metric_name = "completeness"
    prompt_file = "completeness.md"


class ActionabilityMetric(_LlmMetricBase):
    metric_name = "actionability"
    prompt_file = "actionability.md"


class SafetyComplianceMetric(_LlmMetricBase):
    metric_name = "safety_compliance"
    prompt_file = "safety_compliance.md"


class ContextFitMetric(_LlmMetricBase):
    metric_name = "context_fit"
    prompt_file = "context_fit.md"


class ConversationClosureMetric(_LlmMetricBase):
    metric_name = "conversation_closure"
    prompt_file = "conversation_closure.md"


class GrammarMetric(_LlmMetricBase):
    metric_name = "grammar"
    prompt_file = "grammar.md"


class TerminologyMetric(_LlmMetricBase):
    metric_name = "terminology"
    prompt_file = "terminology.md"


class LanguagePurityMetric(_LlmMetricBase):
    metric_name = "language_purity"
    prompt_file = "language_purity.md"


class FluencyMetric(_LlmMetricBase):
    metric_name = "fluency"
    prompt_file = "fluency.md"


class TranslationMetric(_LlmMetricBase):
    metric_name = "translation"
    prompt_file = "translation.md"


class VoiceComprehensivenessMetric(_LlmMetricBase):
    metric_name = "comprehensiveness"
    prompt_file = "voice_comprehensiveness.md"


class ToneMetric(_LlmMetricBase):
    metric_name = "tone"
    prompt_file = "tone.md"


class TermIdentificationMetric(_LlmMetricBase):
    metric_name = "term_identification"
    prompt_file = "term_identification.md"


# Non-LLM metrics
class BrevityMetric(BaseMetric):
    metric_name = "brevity"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        answer = str(variables.get("answer") or transformed_json.get("answer") or row_json.get("answer") or "")
        wc = len(answer.split())
        limit = int(config.get("max_words", 120))
        score = 1.0 if wc <= limit else 0.0
        reason = f"word_count={wc}, max_words={limit}"
        return MetricResult(metric_name=self.metric_name, score=score, reason=reason, metadata={"word_count": wc, "max_words": limit})


class VoiceReadyMetric(BaseMetric):
    metric_name = "voice_ready"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        answer = str(variables.get("answer") or transformed_json.get("answer") or row_json.get("answer") or "")
        artifacts = ["#", "*", "```", "|", "[", "]"]
        has_artifact = any(a in answer for a in artifacts)
        return MetricResult(
            metric_name=self.metric_name,
            score=0.0 if has_artifact else 1.0,
            reason="Contains markdown/text artifacts" if has_artifact else "No obvious text artifacts",
            metadata={"artifacts_checked": artifacts},
        )


class ElapsedSecondsMetric(BaseMetric):
    metric_name = "elapsed_seconds"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        value = row_json.get("elapsed_seconds")
        return MetricResult(metric_name=self.metric_name, score=float(value) if value is not None else None, reason="Pulled from row field if present", metadata={})


class TTFBMetric(BaseMetric):
    metric_name = "ttfb"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        value = row_json.get("ttfb")
        return MetricResult(metric_name=self.metric_name, score=float(value) if value is not None else None, reason="Pulled from row field if present", metadata={})


class WordCountMetric(BaseMetric):
    metric_name = "word_count"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        answer = str(variables.get("answer") or transformed_json.get("answer") or row_json.get("answer") or "")
        wc = len(answer.split())
        return MetricResult(metric_name=self.metric_name, score=float(wc), reason="Computed from output text", metadata={"word_count": wc})


class TokenUsageInputMetric(BaseMetric):
    metric_name = "token_usage.input"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        usage = row_json.get("token_usage", {})
        value = usage.get("input")
        return MetricResult(metric_name=self.metric_name, score=float(value) if value is not None else None, reason="Pulled from row token_usage.input", metadata={})


class TokenUsageOutputMetric(BaseMetric):
    metric_name = "token_usage.output"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        usage = row_json.get("token_usage", {})
        value = usage.get("output")
        return MetricResult(metric_name=self.metric_name, score=float(value) if value is not None else None, reason="Pulled from row token_usage.output", metadata={})


class ErrorMetric(BaseMetric):
    metric_name = "error"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        err = row_json.get("error")
        return MetricResult(metric_name=self.metric_name, score=1.0 if err else 0.0, reason="Error present" if err else "No error present", metadata={"error": err})


class AgristackWorkflowMetric(BaseMetric):
    metric_name = "agristack_workflow"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        turns = transformed_json.get("agent_turns", row_json.get("agent_turns", []))
        text = json.dumps(turns, ensure_ascii=False).lower()
        expected = transformed_json.get("agristack_required", row_json.get("agristack_required", "No")) == "Yes"
        used = "agristack" in text
        score = 1.0 if (not expected or used) else 0.0
        reason = "Workflow requirement satisfied" if score == 1.0 else "Expected agristack flow missing"
        return MetricResult(metric_name=self.metric_name, score=score, reason=reason, metadata={"required": expected, "used": used})


class ToolSequencingMetric(BaseMetric):
    metric_name = "tool_sequencing"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        turns = transformed_json.get("agent_turns", row_json.get("agent_turns", []))
        text = json.dumps(turns, ensure_ascii=False).lower()
        score = 1.0 if "tool-call" in text and "tool-return" in text else 0.0
        return MetricResult(metric_name=self.metric_name, score=score, reason="Basic tool-call/tool-return sequence check", metadata={})


class SearchQualityMetric(BaseMetric):
    metric_name = "search_quality"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        turns = transformed_json.get("agent_turns", row_json.get("agent_turns", []))
        text = json.dumps(turns, ensure_ascii=False).lower()
        score = 1.0 if ("search" in text or "query" in text) else 0.0
        return MetricResult(metric_name=self.metric_name, score=score, reason="Heuristic search activity check", metadata={})


class OutputHygieneMetric(BaseMetric):
    metric_name = "output_hygiene"

    async def evaluate(self, *, row_json: Dict[str, Any], transformed_json: Dict[str, Any], variables: Dict[str, Any], config: Dict[str, Any]) -> MetricResult:
        answer = str(variables.get("answer") or transformed_json.get("answer") or row_json.get("answer") or "")
        bad_markers = ["tool-call", "tool-return", "internal", "debug"]
        clean = not any(marker in answer.lower() for marker in bad_markers)
        return MetricResult(metric_name=self.metric_name, score=1.0 if clean else 0.0, reason="No internal artifacts" if clean else "Potential internal artifacts in output", metadata={"markers": bad_markers})
