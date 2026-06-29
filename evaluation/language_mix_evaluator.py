"""GPT-5 judge for Hindi–Marathi language mix evaluation only."""

from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv

load_dotenv()

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.append(current_dir)

from evaluator import Rating, SubDimensionScore
from helpers.utils import get_prompt


def format_qa_pair(question: str, answer: str) -> str:
    """Format question and answer for the language-only judge."""
    return (
        "Evaluate the ASSISTANT response for Hindi–Marathi language quality only.\n"
        "=" * 60 + "\n\n"
        f"USER QUESTION:\n{question.strip()}\n\n"
        "-" * 40 + "\n\n"
        f"ASSISTANT ANSWER:\n{answer.strip()}\n"
        "=" * 60
    )


class LanguageMixQuality(BaseModel):
    """Hindi–Marathi language quality sub-dimensions."""

    grammar: SubDimensionScore = Field(
        ...,
        description="Marathi grammar and sentence structure correctness",
    )
    marathi_terminology: SubDimensionScore = Field(
        ...,
        description="Standard Marathi agricultural terms; penalize Hindi equivalents",
    )
    language_purity: SubDimensionScore = Field(
        ...,
        description="No inappropriate Hindi–Marathi mixing within sentences",
    )
    fluency: SubDimensionScore = Field(
        ...,
        description="Natural conversational Marathi for rural farmers",
    )


class LanguageMixResult(BaseModel):
    """Language-only evaluation result for a question/answer pair."""

    language_quality: LanguageMixQuality
    mix_detected: bool = Field(
        ...,
        description="True if inappropriate Hindi appears in an otherwise Marathi response",
    )
    mix_severity: Rating = Field(
        ...,
        description="1=none, 2=mild, 3=moderate, 4=heavy, 5=dominant Hindi",
    )
    mixed_hindi_phrases: List[str] = Field(
        default_factory=list,
        description="Quoted Hindi words/phrases found in the Marathi response",
    )
    summary: str = Field(
        ...,
        description="2–3 sentences in English: mix assessment and top language issue",
    )

    def _avg_score(self, dimension: BaseModel) -> Optional[float]:
        scores = []
        for field_name in dimension.model_fields:
            sub: SubDimensionScore = getattr(dimension, field_name)
            if sub.score is not None:
                scores.append(sub.score.value)
        return round(sum(scores) / len(scores), 2) if scores else None

    def _sub_to_dict(self, sub: SubDimensionScore) -> Dict[str, Any]:
        return {
            "score": sub.score.value if sub.score else None,
            "evidence": sub.evidence,
        }

    def to_eval_dict(self) -> Dict[str, Any]:
        scores = {
            name: self._sub_to_dict(getattr(self.language_quality, name))
            for name in self.language_quality.model_fields
        }
        language_avg = self._avg_score(self.language_quality)
        return {
            "dimensions": {
                "language_quality": {
                    "scores": scores,
                    "average": language_avg,
                }
            },
            "mix_detected": self.mix_detected,
            "mix_severity": self.mix_severity.value,
            "mixed_hindi_phrases": self.mixed_hindi_phrases,
            "summary": self.summary,
            "metrics": {
                "language_quality_avg": language_avg,
                "mix_detected": self.mix_detected,
                "mix_severity": self.mix_severity.value,
            },
        }


_judge_model = OpenAIModel(
    model_name='google/gemma-4-31b-it',
    provider=OpenAIProvider(
        base_url='http://10.128.170.2:8080/v1',
        api_key='none',
    ),
)

language_mix_agent = Agent(
    model=_judge_model,
    name="Language Mix Evaluation Agent",
    instrument=False,
    output_type=LanguageMixResult,
    retries=3,
    model_settings=OpenAIModelSettings(
        timeout=60,
    ),
)


@language_mix_agent.system_prompt
def language_mix_system_prompt() -> str:
    return get_prompt("language_mix_evaluation")
