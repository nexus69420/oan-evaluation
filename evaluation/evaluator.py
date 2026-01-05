from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModelSettings
from dotenv import load_dotenv
load_dotenv()
import logfire
logfire.configure(scrubbing=False)

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(current_dir)
sys.path.append(current_dir)

from helpers.utils import get_prompt


def format_agent_turns_to_markdown(
    agent_turns: List[Dict[str, Any]]) -> str:
    """
    Convert agent_turns into readable format by dumping parts as JSON.
    """
    out = []
    for t, turn in enumerate(agent_turns):
        out.append(f"## Turn {t+1}")
        out.append(json.dumps(turn['parts'], ensure_ascii=False, indent=2))
        out.append("\n\n")  # blank line between turns
    
    return "\n".join(out)

class Metric(BaseModel):
    score: int = Field(..., ge=0, le=5, description="Higher is better")
    explanation: str
    evidence: Optional[List[str]] = Field(None, description="Optional short snippets/pointers showing why this score was given")

class ProtocolCompliance(BaseModel):
    scope_discipline: Metric
    mandatory_tool_compliance: Metric
    agristack_workflow_compliance: Metric
    term_identification_compliance: Metric
    query_construction_discipline: Metric
    tool_selection_and_sequencing_quality: Metric

class GroundingAndTruthfulness(BaseModel):
    groundedness: Metric
    citation_claim_alignment: Metric
    factual_correctness_given_sources: Metric
    non_fabrication_discipline: Metric  # high = no invention / good uncertainty handling

class SafetyPolicy(BaseModel):
    safety_and_regulatory_compliance: Metric

class ResponseQuality(BaseModel):
    actionability: Metric
    completeness: Metric
    context_fit: Metric
    clarity_and_readability: Metric
    conversation_closure_quality: Metric  # high = ends with relevant follow-up

class MarathiQuality(BaseModel):
    marathi_linguistic_quality: Metric
    marathi_terminology_fidelity: Metric

class IntegrityHygiene(BaseModel):
    tool_name_confidentiality: Metric  # high = no leakage

class EvaluationResult(BaseModel):
    protocol: ProtocolCompliance
    grounding: GroundingAndTruthfulness
    safety: SafetyPolicy
    response: ResponseQuality
    integrity: IntegrityHygiene
    marathi: MarathiQuality  # Only evaluating Marathi for now

    overall_score: int = Field(..., ge=0, le=10)
    summary: str = Field(..., description="1–3 lines: strongest points + top improvement")


evaluation_agent = Agent(
    model='gpt-5',
    name="Evaluation Agent",
    instrument=True,
    output_type=EvaluationResult,
    retries=3,
    system_prompt=get_prompt('evaluation_system'),
    model_settings=OpenAIChatModelSettings(
        openai_reasoning_effort='medium',
    )
)
