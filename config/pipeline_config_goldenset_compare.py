from __future__ import annotations

from config.pipeline_config import DataTransformConfig, ModelEvaluationConfig, PipelineConfig

CONFIG = PipelineConfig(
    model_name="goldenset_compare",
    num_samples=400,
    batch_size=50,
    model_evaluation=ModelEvaluationConfig(
        metric_classes=[
            # Response Usefulness
            "metrics.llm_metrics.AccuracyCompletenessCompareMetric",
            "metrics.llm_metrics.ActionabilityCompareMetric",
            "metrics.llm_metrics.ConversationClosureCompareMetric",
            "metrics.llm_metrics.SourceDataComprehensivenessCompareMetric",
            # Linguistic Quality
            "metrics.llm_metrics.TranslationAccuracyCompareMetric",
            "metrics.llm_metrics.GrammarFluencyCompareMetric",
            "metrics.llm_metrics.LanguagePurityCompareMetric",
            # Factual Grounding
            "metrics.llm_metrics.NoFabricationCompareMetric",
            "metrics.llm_metrics.CitationAccuracyCompareMetric",
            # Source Retrieval Quality
            "metrics.llm_metrics.CitationComprehensivenessCompareMetric",
        ],
    ),
    data_transform=DataTransformConfig(
        selected_output_keys=[
            "question",
            "response_a",
            "response_b",
            "category",
            "agent_turns",
            "agristack_required",
            "retrieved_sources_a",
            "retrieved_sources_b",
        ],
    ),
)
