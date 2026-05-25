from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from config.llm_profiles import normalize_llm_profiles

DEFAULT_MODEL_NAME = "goldenset_full_review_v3_legacy"

_DEFAULT_LLM: Dict[str, Any] = {
    "model": "gpt-4.1",
    "retries": 3,
    "model_settings": {
        "temperature": 0.0,
        "timeout": 60,
    },
    "input_token_cost_per_1m": 2.0,
    "output_token_cost_per_1m": 8.0,
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
    def __init__(
        self,
        metric_classes: Optional[List[Any]] = None,
        metric_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        llm: Optional[Dict[str, Any]] = None,
        default_llm_profile: Optional[str] = None,
    ) -> None:
        # Legacy path: only the old evaluator flow.
        self.metric_classes = metric_classes or [
            "metrics.agri_eval_metrics.AgriEvalMetrics",
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
        num_samples: Optional[int] = 20,
        max_concurrent: int = 30,
        batch_size: int = 20,
        fail_open: bool = True,
        data_transform: Optional[DataTransformConfig] = None,
        model_evaluation: Optional[ModelEvaluationConfig] = None,
    ) -> None:
        self.model_name = model_name
        self.input_path = input_path
        self.output_path = output_path
        self.num_samples = num_samples
        self.max_concurrent = max_concurrent
        self.batch_size = batch_size
        self.fail_open = fail_open
        self.data_transform = data_transform or DataTransformConfig()
        self.model_evaluation = model_evaluation or ModelEvaluationConfig()

    def resolve_paths(self, repo_root: Path) -> None:
        model_dir = repo_root / "data" / "models" / self.model_name.replace("/", "_")
        if not self.input_path:
            self.input_path = str(model_dir / "data.json")
        if not self.output_path:
            self.output_path = str(model_dir / "evaluation_legacy.json")


CONFIG = PipelineConfig()
