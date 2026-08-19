from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from config.llm_profiles import normalize_llm_profiles

DEFAULT_MODEL_NAME = "gemma4_voice20_eval"

_DEFAULT_LLM: Dict[str, Any] = {
    "model": "gpt-5.4-mini",
    "retries": 3,
    "model_settings": {
        "temperature": 0.0,
        "timeout": 60,
    },
    "input_token_cost_per_1m": 0.75,
    "output_token_cost_per_1m": 4.5,
}


class DataTransformConfig:
    def __init__(
        self,
        transformer_class: str = "data_transformation.default_transform.DefaultDataTransform",
        selected_output_keys: Optional[List[str]] = None,
        transformer_kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.transformer_class = transformer_class
        self.selected_output_keys = selected_output_keys or [
            "question",
            "answer",
            "category",
            "agent_turns",
            "agristack_required",
        ]
        self.transformer_kwargs = transformer_kwargs or {}


class ModelEvaluationConfig:
    """
    Judge LLM configuration.

    ``llm`` may be either:

    - **Single judge** (unchanged): one dict with a string top-level ``"model"``.
    - **Named profiles**: a dict mapping profile names to full judge configs
      (each value is a dict with its own string ``"model"``). Use
      ``default_llm_profile`` to pick which profile applies to metrics that do
      not specify one.

    ``metric_classes`` entries are normally class path strings. You may instead
    use ``("metrics.llm_metrics.FooMetric", "profile_name")`` so that metric uses
    the named profile. Equivalent dict form:
    ``{"class": "...", "llm_profile": "profile_name"}``.

    Per-metric overrides in ``metric_configs`` may set ``"llm_profile"`` or a
    full ``"llm"`` dict (the latter bypasses profiles entirely).
    """

    def __init__(
        self,
        metric_classes: Optional[List[Any]] = None,
        metric_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        llm: Optional[Dict[str, Any]] = None,
        default_llm_profile: Optional[str] = None,
        prompt_dir: Optional[str] = None,
    ) -> None:
        self.prompt_dir = prompt_dir or "assets/prompts/metrics"
        self.metric_classes = metric_classes or [
            "metrics.llm_metrics.CitationComprehensivenessMetric",
            "metrics.llm_metrics.NoFabricationMetric",
            "metrics.llm_metrics.CitationAccuracyMetric",
            "metrics.llm_metrics.AccuracyCompletenessMetric",
            "metrics.llm_metrics.ActionabilityMetric",
            "metrics.llm_metrics.SafetyComplianceMetric",
            "metrics.llm_metrics.ContextFitMetric",
            "metrics.llm_metrics.ConversationClosureMetric",
            "metrics.llm_metrics.SourceDataComprehensivenessMetric",
            "metrics.llm_metrics.GrammarFluencyMetric",
            "metrics.llm_metrics.TerminologyMetric",
            "metrics.llm_metrics.LanguagePurityMetric",
            "metrics.llm_metrics.TranslationAccuracyMetric",
            "metrics.llm_metrics.VoiceComprehensivenessMetric",
            "metrics.llm_metrics.ToneMetric",
            "metrics.llm_metrics.TermIdentificationMetric",
            "metrics.llm_metrics.BrevityMetric",
            "metrics.llm_metrics.VoiceReadyTextMetric",
            "metrics.llm_metrics.ElapsedSecondsMetric",
            "metrics.llm_metrics.TTFBMetric",
            "metrics.llm_metrics.WordCountMetric",
            "metrics.llm_metrics.TokenUsageInputMetric",
            "metrics.llm_metrics.TokenUsageOutputMetric",
            "metrics.llm_metrics.ErrorMetric",
            "metrics.llm_metrics.AgristackWorkflowMetric",
            "metrics.llm_metrics.ToolSequencingMetric",
            "metrics.llm_metrics.SearchQualityMetric",
            "metrics.llm_metrics.OutputHygieneMetric",
            "metrics.llm_metrics.LanguageMixingMetric",
        ]
        self.metric_configs = metric_configs or {}
        self.llm_profiles, self.default_llm_profile, self.llm = normalize_llm_profiles(
            llm,
            default_llm_profile=default_llm_profile,
            single_llm_fallback=_DEFAULT_LLM,
        )


class PipelineConfig:
    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        num_samples: Optional[int] = 10,
        max_concurrent: int = 20,
        checkpoint_interval_minutes: float = 2.0,
        fail_open: bool = True,
        data_transform: Optional[DataTransformConfig] = None,
        model_evaluation: Optional[ModelEvaluationConfig] = None,
    ) -> None:
        self.model_name = model_name
        self.input_path = input_path
        self.output_path = output_path
        self.num_samples = num_samples
        self.max_concurrent = max_concurrent
        self.checkpoint_interval_minutes = checkpoint_interval_minutes
        self.fail_open = fail_open
        self.data_transform = data_transform or DataTransformConfig()
        self.model_evaluation = model_evaluation or ModelEvaluationConfig()

    def resolve_paths(self, repo_root: Path) -> None:
        model_dir = repo_root / "data" / "models" / self.model_name
        if not self.input_path:
            self.input_path = str(model_dir / "data.json")
        if not self.output_path:
            self.output_path = str(model_dir / "evaluation.json")


CONFIG = PipelineConfig()
