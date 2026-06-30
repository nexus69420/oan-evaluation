from __future__ import annotations
import os
import sys
from enum import IntEnum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel, OpenAIChatModelSettings
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
    evidences: List[str] = Field(
        default_factory=list,
        description=(
            "Exact verbatim phrases from the response that triggered violations on this dimension. "
            "Each entry must appear character-for-character in the original response "
            "(Marathi/Hindi/English script preserved, no paraphrasing or translation). "
            "Empty list if there are no violations."
        )
    )
    summary: str = Field(
        ...,
        description=(
            "1-2 sentence summary in English: violation count and dominant pattern for this dimension, "
            "plus the single highest-impact fix. State that the dimension is clean if evidences is empty."
        )
    )
    score: Optional[Rating] = Field(
        None,
        description=(
            "Rating on a 1-5 scale where higher = better Marathi "
            "(1=unacceptable, 2=poor, 3=acceptable, 4=good, 5=excellent). "
            "Use null only if the dimension cannot be assessed (e.g., empty response or no language content)."
        )
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
    """Language-purity evaluation of a Marathi agent response on two sub-dimensions.

    Each sub-dimension carries verbatim evidence, a short English summary, and a 1-5 score
    where higher = better Marathi. Structural (grammar) and lexical (terminology) violations
    are reported separately so the same phrase is never double-counted.
    """

    grammar: SubDimensionScore = Field(
        ...,
        description=(
            "Structural Marathi correctness: sentence construction, verb conjugation, "
            "postpositions, conjunctions, copulas, pronouns, question formation. "
            "Violations here are Hindi grammatical/structural words or constructions breaking "
            "Marathi syntax (e.g., है, हैं, के लिए, और, यह, क्या). "
            "Score 1-5, higher = better Marathi grammar."
        )
    )
    terminology: SubDimensionScore = Field(
        ...,
        description=(
            "Lexical Marathi correctness: nouns, adjectives, adverbs, agricultural vocabulary, "
            "and freedom from Devanagari-transliterated or Roman-script English. "
            "Violations here are Hindi or English words substituting for a standard Marathi term "
            "(e.g., फसल for पीक, मैनेजमेंट for व्यवस्थापन, बेहतर for उत्तम), including parenthetical "
            "Hindi glosses and slash-paired bilingual forms. "
            "Score 1-5, higher = better Marathi terminology."
        )
    )
    
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
    output_type=LanguageQuality,
    retries=3,
    model_settings=OpenAIChatModelSettings(
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": True
            }
        }
    )
)


@evaluation_agent.system_prompt
def system_prompt() -> str:
    return get_prompt('language_mix_evaluation')
