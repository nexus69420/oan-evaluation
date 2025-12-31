from __future__ import annotations
import json
import os
import sys
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from dotenv import load_dotenv
load_dotenv()
import logfire
logfire.configure(scrubbing=False)

# Get the parent directory - oan-evaluation
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(current_dir)
os.chdir(current_dir)
sys.path.append(current_dir)

from helpers.utils import get_prompt

def _json_dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False)


def format_agent_turns_to_markdown(
    agent_turns: List[Dict[str, Any]],
    *,
    collapse_thinking: bool = True,
    collapse_tool_payloads: bool = False,
) -> str:
    """
    Convert agent_turns into readable Markdown.

    Assumes turn shape (flexible):
      turn: { "role": "...", "parts": [ ... ], ... }
      part: { "part_kind": "...", ... }

    Thinking is ALWAYS included.
    Tool call/return payloads are rendered as JSON fenced blocks.
    """

    out: List[str] = []
    out.append("# Agent Trace\n")

    for i, turn in enumerate(agent_turns, start=1):
        role = turn.get("role") or turn.get("speaker") or "unknown"
        turn_id = turn.get("id") or turn.get("turn_id")

        header = f"## Turn {i} ({role})"
        if turn_id is not None:
            header += f" `{turn_id}`"
        out.append(header)

        parts = turn.get("parts") or []
        if not parts:
            out.append("_No parts_")
            out.append("")
            continue

        for j, part in enumerate(parts, start=1):
            kind = part.get("part_kind") or part.get("kind") or "unknown"
            out.append(f"### Part {j}: `{kind}`")

            if kind in ("text", "message", "content"):
                text = part.get("content") or part.get("text") or ""
                out.append(text.rstrip() if text.strip() else "_Empty text_")

            elif kind in ("thinking", "reasoning"):
                thinking = part.get("content") or part.get("text") or ""
                if not thinking.strip():
                    out.append("_Empty thinking_")
                elif collapse_thinking:
                    out.append("<details>")
                    out.append("<summary>Thinking</summary>\n")
                    out.append("```text")
                    out.append(thinking.rstrip())
                    out.append("```")
                    out.append("</details>")
                else:
                    out.append("```text")
                    out.append(thinking.rstrip())
                    out.append("```")

            elif kind in ("tool-call", "tool_call"):
                tool_name = part.get("tool_name") or part.get("name") or part.get("tool") or "unknown_tool"
                args = part.get("args") or part.get("arguments") or {}
                call_id = part.get("call_id") or part.get("tool_call_id")

                meta = f"**Tool call:** `{tool_name}`"
                if call_id:
                    meta += f"  \n**Call id:** `{call_id}`"
                out.append(meta)

                payload = {"tool": tool_name, "arguments": args}
                if collapse_tool_payloads:
                    out.append("<details>")
                    out.append("<summary>Arguments (JSON)</summary>\n")
                    out.append("```json")
                    out.append(_json_dump(payload))
                    out.append("```")
                    out.append("</details>")
                else:
                    out.append("```json")
                    out.append(_json_dump(payload))
                    out.append("```")

            elif kind in ("tool-return", "tool_result", "tool-output", "tool_output"):
                tool_name = part.get("tool_name") or part.get("name") or part.get("tool") or "unknown_tool"
                call_id = part.get("call_id") or part.get("tool_call_id")
                result = part.get("result")
                error = part.get("error")

                meta = f"**Tool return:** `{tool_name}`"
                if call_id:
                    meta += f"  \n**Call id:** `{call_id}`"
                out.append(meta)

                payload: Dict[str, Any] = {"tool": tool_name}
                if error is not None:
                    payload["error"] = error
                if result is not None:
                    payload["result"] = result

                if collapse_tool_payloads:
                    out.append("<details>")
                    out.append("<summary>Result (JSON)</summary>\n")
                    out.append("```json")
                    out.append(_json_dump(payload))
                    out.append("```")
                    out.append("</details>")
                else:
                    out.append("```json")
                    out.append(_json_dump(payload))
                    out.append("```")

            elif kind in ("retry-prompt", "retry_prompt"):
                prompt = part.get("content") or part.get("text") or ""
                out.append("> **Retry prompt**")
                out.append("> " + "\n> ".join(prompt.rstrip().splitlines()) if prompt.strip() else "> _Empty retry prompt_")

            else:
                out.append("_Unrecognized part kind; dumping raw part_")
                out.append("```json")
                out.append(_json_dump(part))
                out.append("```")

            out.append("")  # blank line between parts

        out.append("")  # blank line between turns

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
    marathi: Optional[MarathiQuality] = None  # include only if selected_language == "mr"

    overall_score: int = Field(..., ge=0, le=100)
    summary: str = Field(..., description="1–3 lines: strongest points + top improvement")


evaluation_agent = Agent(
    model='gpt-5',
    name="Evaluation Agent",
    instrument=True,
    output_type=EvaluationResult,
    retries=2,
    system_prompt=get_prompt('evaluation_system'),
)
