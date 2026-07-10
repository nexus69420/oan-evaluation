"""
evaluator_alignment_prompts/__init__.py

Public API for the evaluator alignment package.
"""
from evaluator_alignment_prompts.config   import AlignmentConfig
from evaluator_alignment_prompts.dataset  import load_dataset
from evaluator_alignment_prompts.module   import EvaluatorModule, MultiDimEvaluatorModule, BlindEvaluatorModule
from evaluator_alignment_prompts.metric   import composite_agreement_metric, evaluate_agreement
from evaluator_alignment_prompts.evaluate import (
    evaluate_on_split,
    compute_full_report,
    generate_error_report,
)

__all__ = [
    "AlignmentConfig",
    "load_dataset",
    "EvaluatorModule",
    "MultiDimEvaluatorModule",
    "BlindEvaluatorModule",
    "composite_agreement_metric",
    "evaluate_agreement",
    "evaluate_on_split",
    "compute_full_report",
    "generate_error_report",
]
