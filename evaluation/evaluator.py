from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
from dotenv import load_dotenv
load_dotenv()
import logfire
logfire.configure(scrubbing=False)

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.append(current_dir)

from helpers.utils import get_prompt


@dataclass
class EvaluationDeps:
    category: str

def format_conversation_record(record):
    """
    Formats a Type-2 'Conversation Record' (with separated question/answer/turns)
    into the same clean transcript format.
    Includes 'thinking' traces.
    """
    lines = []
    
    # --- 1. Context Header ---
    cat = record.get('category', 'Unknown')
    
    lines.append(f"🏷️  Context: [{cat}]")
    lines.append("=" * 60)
    lines.append("")

    # --- 2. USER QUERY ---
    lines.append("👤 USER:")
    lines.append(f"{record.get('question', '').strip()}")
    lines.append("-" * 40)

    # --- 3. MIDDLE STEPS (Agent Turns) ---
    for turn in record.get('agent_turns', []):
        for part in turn.get('parts', []):
            part_kind = part.get('part_kind')
            
            # A. THINKING / REASONING
            if part_kind == 'thinking':
                content = part.get('content', '')
                lines.append("💭 THOUGHT:")
                lines.append(f"{str(content).strip()}")
                lines.append("-" * 40)

            # B. TOOL CALL
            elif part_kind == 'tool-call':
                name = part.get('tool_name')
                args = part.get('args', '{}')
                
                lines.append(f"⚙️  ACTION: {name}")
                lines.append(f"    Args: {args}")

            # C. TOOL RETURN
            elif part_kind == 'tool-return':
                content = part.get('content', '')
                
                # formatting check: is it json?
                if isinstance(content, (dict, list)):
                     content_str = json.dumps(content, ensure_ascii=False, indent=2)
                else:
                     content_str = str(content)

                lines.append(f"📥 RESULT: {content_str.strip()}")
                lines.append("-" * 40)

    # --- 4. FINAL ANSWER ---
    lines.append("🤖 ASSISTANT:")
    lines.append(f"{record.get('answer', '').strip()}")
    lines.append("=" * 60)

    return "\n".join(lines)


# =========================================================================
class Rating(IntEnum):
    """Likert-scale rating for evaluation sub-dimensions."""
    UNACCEPTABLE = 1  # Critical failure - harmful, fabricated, or complete breakdown
    POOR = 2          # Major issues significantly affecting usefulness or correctness
    ACCEPTABLE = 3    # Meets minimum requirements with noticeable gaps
    GOOD = 4          # Strong performance with only minor issues
    EXCELLENT = 5     # Exemplary, matches gold-standard behavior


class SubDimensionScore(BaseModel):
    """Score for a single evaluation sub-dimension."""
    score: Optional[Rating] = Field(
        None, 
        description="Rating 1-5, or null if not applicable to this query type"
    )
    evidence: str = Field(
        ..., 
        description="Brief justification in English with reasoning; may quote Hindi snippets as supporting evidence"
    )

# =============================================================================
# DIMENSION 1: PROCESS FIDELITY
# =============================================================================

class ProcessFidelity(BaseModel):
    """Evaluates whether the agent followed prescribed workflows and maintained output hygiene."""
    
    intent_accuracy: SubDimensionScore = Field(
        ..., 
        description="Correctly identifies the intent of the user's query"
    )
    moderation_compliance: SubDimensionScore = Field(
        ..., 
        description="Valid Agricultural confirmed; invalid queries declined correctly"
    )
    tool_sequencing: SubDimensionScore = Field(
        ..., 
        description="Correct tool order (geocode→service, scheme_codes→scheme_info)"
    )
    tool_usage: SubDimensionScore = Field(
        ..., 
        description="Correct tool (search_terms→search_pests_diseases, search_documents→search_documents)"
    )
    output_hygiene: SubDimensionScore = Field(
        ..., 
        description="No tool names leaked, no internal thinking exposed, no artifacts"
    )


# =============================================================================
# DIMENSION 2: FACTUAL GROUNDING
# =============================================================================

class FactualGrounding(BaseModel):
    """Evaluates whether claims are supported by tool outputs with no fabrication or harm."""
    
    source_alignment: SubDimensionScore = Field(
        ..., 
        description="All factual claims traceable to specific tool outputs"
    )
    no_fabrication: SubDimensionScore = Field(
        ..., 
        description="No invented data when tools return empty; gaps acknowledged"
    )
    citation_accuracy: SubDimensionScore = Field(
        ..., 
        description="Sources cited with farmer-friendly names, not internal tool names"
    )
    safety_compliance: SubDimensionScore = Field(
        ..., 
        description="Correct dosages, no banned chemicals, legal practices only"
    )


# =============================================================================
# DIMENSION 3: RESPONSE USEFULNESS
# =============================================================================

class ResponseUsefulness(BaseModel):
    """Evaluates whether the response is actually helpful to the farmer."""
    
    completeness: SubDimensionScore = Field(
        ..., 
        description="Addresses all parts of farmer's query"
    )
    actionability: SubDimensionScore = Field(
        ..., 
        description="Specific, timed, quantified advice (varieties, dosages, timing)"
    )
    context_fit: SubDimensionScore = Field(
        ..., 
        description="Uses farmer profile/location data appropriately when available"
    )
    clarity: SubDimensionScore = Field(
        ..., 
        description="Clear structure, readable formatting, appropriate length"
    )
    conversation_closure: SubDimensionScore = Field(
        ..., 
        description="Ends with relevant, specific follow-up question or next step"
    )


# =============================================================================
# DIMENSION 4: MARATHI LINGUISTIC QUALITY
# =============================================================================

class LanguageQuality(BaseModel):
    """Evaluates Hindi language correctness, terminology, and naturalness."""
    
    grammar: SubDimensionScore = Field(
        ..., 
        description="Grammatically correct, complete sentences"
    )
    terminology: SubDimensionScore = Field(
        ..., 
        description="Uses proper Hindi agricultural terms from glossary"
    )
    language_purity: SubDimensionScore = Field(
        ..., 
        description="No inappropriate English-Hindi mixing within sentences"
    )
    fluency: SubDimensionScore = Field(
        ..., 
        description="Reads naturally, conversational tone for rural context"
    )


# =============================================================================
# MAIN EVALUATION RESULT
# =============================================================================

class EvaluationResult(BaseModel):
    """
    Complete evaluation result for a MahaVistaar agricultural assistant response.
    
    Evaluates across 4 dimensions (16 sub-dimensions total):
    - Process Fidelity: Workflow compliance and output hygiene
    - Factual Grounding: Source alignment, no fabrication, safety
    - Response Usefulness: Completeness, actionability, clarity
    - Language Quality: Grammar, terminology, fluency
    
    Critical failures (score=UNACCEPTABLE) in safety_compliance, no_fabrication, or 
    source_alignment result in overall_pass=False regardless of other scores.
    """
    
    process_fidelity: ProcessFidelity
    factual_grounding: FactualGrounding
    response_usefulness: ResponseUsefulness
    language_quality: LanguageQuality
    
    summary: str = Field(
        ..., 
        description="2-3 sentences in English: key strength + top improvement area"
    )

    def _calculate_dimension_average(self, dimension: BaseModel) -> Optional[float]:
        """Calculate average score for a dimension, excluding N/A (None) scores."""
        scores = []
        for field_name in dimension.model_fields:
            sub_dim: SubDimensionScore = getattr(dimension, field_name)
            if sub_dim.score is not None:
                scores.append(sub_dim.score.value)
        return round(sum(scores) / len(scores), 2) if scores else None

    def _get_critical_failures(self) -> List[str]:
        """Identify critical failures (score=UNACCEPTABLE) in safety-critical sub-dimensions."""
        critical_fields = [
            ("factual_grounding", "safety_compliance"),
            ("factual_grounding", "no_fabrication"),
            ("factual_grounding", "source_alignment"),
        ]
        failures = []
        for dim_name, field_name in critical_fields:
            dimension = getattr(self, dim_name)
            sub_dim: SubDimensionScore = getattr(dimension, field_name)
            if sub_dim.score == Rating.UNACCEPTABLE:
                failures.append(f"{dim_name}.{field_name}")
        return failures

    def _sub_dim_to_dict(self, sub_dim: SubDimensionScore) -> Dict[str, Any]:
        """Convert sub-dimension to dict with numeric score."""
        return {
            "score": sub_dim.score.value if sub_dim.score else None,
            "evidence": sub_dim.evidence
        }

    def _dimension_to_dict(self, dimension: BaseModel) -> Dict[str, Any]:
        """Convert dimension to dict with numeric scores."""
        result = {}
        for field_name in dimension.model_fields:
            sub_dim: SubDimensionScore = getattr(dimension, field_name)
            result[field_name] = self._sub_dim_to_dict(sub_dim)
        return result

    def to_eval_dict(self) -> Dict[str, Any]:
        """
        Export evaluation as JSON-serializable dict with computed metrics.
        """
        dimensions = {
            "process_fidelity": {
                "scores": self._dimension_to_dict(self.process_fidelity),
                "average": self._calculate_dimension_average(self.process_fidelity)
            },
            "factual_grounding": {
                "scores": self._dimension_to_dict(self.factual_grounding),
                "average": self._calculate_dimension_average(self.factual_grounding)
            },
            "response_usefulness": {
                "scores": self._dimension_to_dict(self.response_usefulness),
                "average": self._calculate_dimension_average(self.response_usefulness)
            },
            "language_quality": {
                "scores": self._dimension_to_dict(self.language_quality),
                "average": self._calculate_dimension_average(self.language_quality)
            }
        }
        
        # Calculate overall average from all valid sub-dimension scores (equal weight per sub-dimension)
        all_scores = []
        for dimension in [self.process_fidelity, self.factual_grounding, 
                          self.response_usefulness, self.language_quality]:
            for field_name in dimension.model_fields:
                sub_dim: SubDimensionScore = getattr(dimension, field_name)
                if sub_dim.score is not None:
                    all_scores.append(sub_dim.score.value)
        overall_average = round(sum(all_scores) / len(all_scores), 2) if all_scores else None
        
        critical_failures = self._get_critical_failures()
        
        return {
            "dimensions": dimensions,
            "summary": self.summary,
            "metrics": {
                "overall_average": overall_average,
                "critical_failures": critical_failures,
                "critical_failure_count": len(critical_failures),
                "overall_pass": len(critical_failures) == 0
            }
        }

evaluation_agent = Agent(
    model='gpt-5',
    name="Evaluation Agent",
    deps_type=EvaluationDeps,
    instrument=False,
    output_type=EvaluationResult,
    retries=3,
    model_settings=OpenAIResponsesModelSettings(
        temperature=0.0,
        timeout=120,
        openai_reasoning_effort='low',
    )
)


@evaluation_agent.system_prompt(dynamic=True)
def system_prompt(ctx: RunContext) -> str:
    """Generate a dynamic system prompt based on the category."""
    category = ctx.deps.category
    master_prompt = get_prompt('evaluation_system')
    return master_prompt + "\n\n" + category