from __future__ import annotations

from config.pipeline_config import DataTransformConfig, ModelEvaluationConfig, PipelineConfig

# ── Judge LLM profiles ──────────────────────────────────────────────
# Add/remove/rename profiles here. Each metric below picks one by name.
LLM_PROFILES = {
    "gpt-5.4-mini": {
        "model": "gpt-5.1",
        "retries": 3,
        "model_settings": {"temperature": 0.0, "timeout": 60},
        "input_token_cost_per_1m": 1.25,
        "output_token_cost_per_1m": 10,
    },
    "gpt-4.1-mini": {
        "model": "gpt-5-mini",
        "retries": 3,
        "model_settings": {"temperature": 0.0, "timeout": 120},
        "input_token_cost_per_1m": 0.25,
        "output_token_cost_per_1m": 2.5,
    },
}

# ── Metric → profile assignment ─────────────────────────────────────
# Plain string  → uses default_llm_profile
# Tuple (class, profile) → uses that named profile
CONFIG = PipelineConfig(
    model_name="goldenset_gu_dev",
    num_samples=20,
    model_evaluation=ModelEvaluationConfig(
        llm=LLM_PROFILES,
        default_llm_profile="gpt-5.4-mini",
        metric_classes=[
            # Response Usefulness
            ("metrics.llm_metrics.AccuracyCompletenessMetric", "gpt-5.4-mini"),
            ("metrics.llm_metrics.ActionabilityMetric",        "gpt-5.4-mini"),
            ("metrics.llm_metrics.ConversationClosureMetric",  "gpt-5.4-mini"),
            ("metrics.llm_metrics.SourceDataComprehensivenessMetric", "gpt-5.4-mini"),
            # Linguistic Quality
            ("metrics.llm_metrics.TranslationAccuracyMetric",  "gpt-5.4-mini"),
            ("metrics.llm_metrics.GrammarFluencyMetric",       "gpt-5.4-mini"),
            ("metrics.llm_metrics.LanguagePurityMetric",       "gpt-5.4-mini"),
            # Factual Grounding
            ("metrics.llm_metrics.NoFabricationMetric",        "gpt-5.4-mini"),
            ("metrics.llm_metrics.CitationAccuracyMetric",     "gpt-5.4-mini"),
            # Source Retrieval Quality
            ("metrics.llm_metrics.CitationComprehensivenessSourcesMetric", "gpt-5.4-mini"),
            # Voice Quality
            ("metrics.llm_metrics.BrevityMetric",          "gpt-5.4-mini"),
            ("metrics.llm_metrics.VoiceReadyTextMetric",   "gpt-5.4-mini"),
        ],
    ),
    data_transform=DataTransformConfig(
        selected_output_keys=[
            "question",
            "answer",
            "category",
            "agent_turns",
            "agristack_required",
            "retrieved_sources",
        ],
    ),
)
