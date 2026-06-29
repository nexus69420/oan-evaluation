from __future__ import annotations
import os
import sys
from enum import IntEnum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
load_dotenv()
import logfire
logfire.configure(scrubbing=False)

current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.append(current_dir)

from helpers.utils import get_prompt


def format_agent_record(record):
    """Format a question/answer record into a clean transcript for the judge."""
    lines = []

    lines.append("👤 USER:")
    lines.append(f"{record.get('question', '').strip()}")
    lines.append("-" * 40)

    lines.append("🤖 ASSISTANT:")
    lines.append(f"{record.get('answer', '').strip()}")
    lines.append("=" * 60)

    return "\n".join(lines)


class Rating(IntEnum):
    UNACCEPTABLE = 1
    POOR = 2
    ACCEPTABLE = 3
    GOOD = 4
    EXCELLENT = 5


class SubDimensionScore(BaseModel):
    score: Optional[Rating] = Field(
        None,
        description="Rating 1-5, or null if not applicable"
    )
    evidence: str = Field(
        ...,
        description="Exact quoted phrase(s) from the response as evidence; commentary in English"
    )


# =============================================================================
# For now, not using these dimensions
# =============================================================================

# class ProcessFidelity(BaseModel):
#     """Evaluates whether the agent followed prescribed workflows."""
#     agristack_workflow: SubDimensionScore
#     term_identification: SubDimensionScore
#     tool_sequencing: SubDimensionScore
#     search_quality: SubDimensionScore
#     output_hygiene: SubDimensionScore

# class FactualGrounding(BaseModel):
#     """Evaluates whether claims are supported by tool outputs."""
#     source_alignment: SubDimensionScore
#     no_fabrication: SubDimensionScore
#     citation_accuracy: SubDimensionScore
#     safety_compliance: SubDimensionScore

# class ResponseUsefulness(BaseModel):
#     """Evaluates whether the response is helpful to the farmer."""
#     completeness: SubDimensionScore
#     actionability: SubDimensionScore
#     context_fit: SubDimensionScore
#     clarity: SubDimensionScore
#     conversation_closure: SubDimensionScore


# =============================================================================
# LANGUAGE MIX QUALITY — Active
# =============================================================================

class LanguageQuality(BaseModel):
    """Scores the four language sub-dimensions for Hindi/English mix in Marathi responses."""

    grammar: SubDimensionScore = Field(
        ...,
        description="Marathi sentence structure correctness; penalize Hindi verb forms and conjunctions"
    )
    marathi_terminology: SubDimensionScore = Field(
        ...,
        description="Standard Marathi agricultural terms used; penalize Hindi equivalents (फसल, मिट्टी, खाद, सिंचाई)"
    )
    language_purity: SubDimensionScore = Field(
        ...,
        description="Freedom from Hindi/English mixing: slash-pairs, parenthetical glosses, inline foreign words, Hindi closings"
    )
    fluency: SubDimensionScore = Field(
        ...,
        description="Natural conversational Marathi for a rural Maharashtra farmer; penalize code-switching that breaks flow"
    )


class EvaluationResult(BaseModel):
    """
    Language mix evaluation result for a Maha Vistaar response.
    Detects inappropriate Hindi and English in Marathi agricultural responses.
    """

    language_quality: LanguageQuality

    mix_detected: bool = Field(
        ...,
        description="True if ANY Hindi or English intrusion is found, even a single word"
    )
    mix_severity: Rating = Field(
        ...,
        description="1=none, 2=mild (1-2 words), 3=moderate (3-6), 4=heavy (7+ or full Hindi sentence), 5=dominant Hindi/English"
    )
    mixed_hindi_phrases: List[str] = Field(
        default_factory=list,
        description="Exhaustive list of every violation quoted exactly from the response, each labeled with its type"
    )
    summary: str = Field(
        ...,
        description="2-3 sentences in English: total violation count, dominant pattern type, single highest-impact fix"
    )

    def _sub_to_dict(self, sub: SubDimensionScore) -> Dict[str, Any]:
        return {
            "score": sub.score.value if sub.score else None,
            "evidence": sub.evidence,
        }

    def to_eval_dict(self) -> Dict[str, Any]:
        scores = {
            name: self._sub_to_dict(getattr(self.language_quality, name))
            for name in LanguageQuality.model_fields
        }

        valid_scores = [v["score"] for v in scores.values() if v["score"] is not None]
        language_avg = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else None

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


# =============================================================================
# JUDGE MODEL — JUDGE_BASE_URL and JUDGE_MODEL_NAME must be set in .env
# API key is not used by vLLM; timeout defaults to 120s if not set
# =============================================================================

_JUDGE_BASE_URL   = os.environ["JUDGE_BASE_URL"]
_JUDGE_MODEL_NAME = os.environ["JUDGE_MODEL_NAME"]
_JUDGE_TIMEOUT    = int(os.getenv("JUDGE_TIMEOUT", "120"))

_judge_model = OpenAIModel(
    model_name=_JUDGE_MODEL_NAME,
    provider=OpenAIProvider(
        base_url=_JUDGE_BASE_URL,
        api_key="none",
    ),
)

evaluation_agent = Agent(
    model=_judge_model,
    name="Language Mix Evaluation Agent",
    instrument=False,
    output_type=EvaluationResult,
    retries=3,
    model_settings=OpenAIModelSettings(
        timeout=_JUDGE_TIMEOUT,
    )
)


@evaluation_agent.system_prompt
def system_prompt() -> str:
    return get_prompt('language_mix_evaluation')
