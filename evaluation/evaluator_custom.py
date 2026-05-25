from __future__ import annotations
import json
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from dotenv import load_dotenv
load_dotenv()
# import logfire
# logfire.configure(scrubbing=False)

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.append(current_dir)

from helpers.utils import get_prompt


@dataclass
class EvaluationDeps:
    category: str

def format_agent_record(record):
    """
    Formats a Type-2 'Agent Record' (with separated question/answer/turns)
    into the same clean transcript format.
    Includes 'thinking' traces.
    """
    lines = []
    
    # --- 1. Context Header ---
    cat = record.get('category', 'Unknown')
    
    # Map 'agristack_required' to Icon
    agristack_val = record.get('agristack_required', 'No')
    agristack_icon = "✅" if agristack_val == 'Yes' else "❌"
    
    lines.append(f"🏷️  Context: [{cat}] | Agristack: {agristack_icon}")
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


def build_evaluation_agent(llm: Dict[str, Any]) -> Agent:
    """
    Build an evaluation agent.

    `llm` is passed through directly as kwargs to `pydantic_ai.Agent`.
    No hidden defaults are applied; invalid/missing payload should fail fast.
    """
    if not isinstance(llm, dict):
        raise ValueError("Missing/invalid llm config: expected a dict of Agent kwargs.")

    merged = dict(llm)
    # Pricing fields are for reporting/cost estimation and are not valid
    # pydantic-ai Agent constructor kwargs.
    merged.pop("input_token_cost_per_1m", None)
    merged.pop("output_token_cost_per_1m", None)
    merged["name"] = "Evaluation Agent"
    merged["deps_type"] = EvaluationDeps
    merged["instrument"] = False
    merged["output_type"] = EvaluationResult
    agent = Agent(**merged)

    @agent.system_prompt(dynamic=True)
    def dynamic_system_prompt(ctx: RunContext) -> str:
        return _build_system_prompt(ctx.deps.category)

    return agent


def _usage_to_dict(usage_obj: Any) -> Dict[str, Any]:
    details = getattr(usage_obj, "details", None) or {}
    return {
        "input_tokens": int(getattr(usage_obj, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage_obj, "output_tokens", 0) or 0),
        "total_tokens": int(getattr(usage_obj, "total_tokens", 0) or 0),
        "details": dict(details),
    }


def _estimate_cost(usage: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
    input_rate = llm.get("input_token_cost_per_1m")
    output_rate = llm.get("output_token_cost_per_1m")

    if input_rate is None or output_rate is None:
        return {
            "cost_usd": None,
            "cost_formula": "Set llm.input_token_cost_per_1m and llm.output_token_cost_per_1m to enable cost estimation",
        }

    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    input_cost = (input_tokens / 1_000_000) * float(input_rate)
    output_cost = (output_tokens / 1_000_000) * float(output_rate)
    total_cost = input_cost + output_cost

    return {
        "cost_usd": round(total_cost, 8),
        "input_cost_usd": round(input_cost, 8),
        "output_cost_usd": round(output_cost, 8),
        "input_token_cost_per_1m": float(input_rate),
        "output_token_cost_per_1m": float(output_rate),
    }


async def evaluate_record_with_judge(
    record: Dict[str, Any],
    llm: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Thin reusable wrapper around the current judge flow.
    """
    category = record.get("category", "")
    message = format_agent_record(record)
    runtime_agent = build_evaluation_agent(llm)
    eval_result = await runtime_agent.run(
        message,
        deps=EvaluationDeps(category=category),
    )
    usage_dict = _usage_to_dict(eval_result.usage())
    eval_dict = eval_result.output.to_eval_dict()
    eval_dict["runtime"] = {
        "token_usage": usage_dict,
        "cost_estimate": _estimate_cost(usage_dict, llm),
    }
    return eval_dict



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
        description="Brief justification in English with reasoning; may quote Marathi snippets as supporting evidence"
    )

# =============================================================================
# DIMENSION 1: PROCESS FIDELITY
# =============================================================================

class ProcessFidelity(BaseModel):
    """Evaluates whether the agent followed prescribed workflows and maintained output hygiene."""
    
    agristack_workflow: SubDimensionScore = Field(
        ..., 
        description="Called fetch_agristack_data first when marked available"
    )
    term_identification: SubDimensionScore = Field(
        ..., 
        description="Used search_terms before search_documents for advisory queries"
    )
    tool_sequencing: SubDimensionScore = Field(
        ..., 
        description="Correct tool order (geocode→service, scheme_codes→scheme_info)"
    )
    search_quality: SubDimensionScore = Field(
        ..., 
        description="Effective 2-5 word English queries with relevant terms"
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

class MarathiQuality(BaseModel):
    """Evaluates Marathi language correctness, terminology, and naturalness."""
    
    grammar: SubDimensionScore = Field(
        ..., 
        description="Grammatically correct, complete sentences"
    )
    terminology: SubDimensionScore = Field(
        ..., 
        description="Uses proper Marathi agricultural terms from glossary"
    )
    language_purity: SubDimensionScore = Field(
        ..., 
        description="No inappropriate English-Marathi mixing within sentences"
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
    - Marathi Quality: Grammar, terminology, fluency
    
    Critical failures (score=UNACCEPTABLE) in safety_compliance, no_fabrication, or 
    source_alignment result in overall_pass=False regardless of other scores.
    """
    
    process_fidelity: ProcessFidelity
    factual_grounding: FactualGrounding
    response_usefulness: ResponseUsefulness
    marathi_quality: MarathiQuality
    
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
            "marathi_quality": {
                "scores": self._dimension_to_dict(self.marathi_quality),
                "average": self._calculate_dimension_average(self.marathi_quality)
            }
        }
        
        # Calculate overall average from all valid sub-dimension scores (equal weight per sub-dimension)
        all_scores = []
        for dimension in [self.process_fidelity, self.factual_grounding, 
                          self.response_usefulness, self.marathi_quality]:
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

def _build_system_prompt(category: str) -> str:
    category_normalized = category.lower().replace(' ', '_')    
    # For agri_services we can combine:
    if category_normalized in ['kvk','soil_lab','warehouse','chc']:
        category_prompt = get_prompt('category/agri_services')
    elif category_normalized in ['weather_historical','weather_forecast']:
        category_prompt = get_prompt('category/weather')        
    else:
        category_prompt = get_prompt('category/' + category_normalized)

    master_prompt = get_prompt('evaluation_system')
    return master_prompt + "\n\n" + category_prompt
