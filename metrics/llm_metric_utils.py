from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

from helpers.llm_helper import llm_call
from helpers.prompt_helper import render_prompt, try_render_prompt

from .base import MetricResult


def build_context(
    row_json: Dict[str, Any],
    transformed_json: Dict[str, Any],
    variables: Dict[str, Any],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Build template context from row, transformed row, and passed variables."""
    context: Dict[str, Any] = {}
    context.update(row_json)
    context.update(transformed_json)
    context.update(variables)
    context.update(config.get("variables", {}))

    answer = str(context.get("answer") or "")
    context.setdefault("word_count", len(answer.split()))
    context.setdefault(
        "agent_turns",
        json.dumps(
            transformed_json.get("agent_turns", row_json.get("agent_turns", [])),
            ensure_ascii=False,
        ),
    )
    return context


def parse_json_result(text: str) -> Dict[str, Any]:
    """Parse a JSON object from model output."""
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("Metric LLM response did not contain JSON object")
    return json.loads(match.group(0))


def estimate_cost(usage: Dict[str, Any], llm: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate request cost from token usage and provided pricing.

    Supported llm config keys:
    - input_token_cost_per_1m
    - output_token_cost_per_1m
    """
    input_rate = llm.get("input_token_cost_per_1m")
    output_rate = llm.get("output_token_cost_per_1m")

    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)

    if input_rate is None or output_rate is None:
        return {
            "cost_usd": None,
            "cost_formula": "Set llm.input_token_cost_per_1m and llm.output_token_cost_per_1m to enable cost estimation",
        }

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


async def run_llm_metric(
    *,
    metric_name: str,
    prompt_file: str,
    row_json: Dict[str, Any],
    transformed_json: Dict[str, Any],
    variables: Dict[str, Any],
    config: Dict[str, Any],
) -> MetricResult:
    """Shared execution path for all LLM-backed metrics."""
    llm = config["llm"]
    prompt_dir = config.get("prompt_dir", "assets/prompts/metrics")
    context = build_context(row_json, transformed_json, variables, config)

    specific_dir = str(Path(prompt_dir) / "bv_specific")
    specific_context = {**context, **config.get("specific_kwargs", {})}
    specific = try_render_prompt(prompt_file, context=specific_context, prompt_dir=specific_dir)

    main_prompt = render_prompt(prompt_file, context=context, prompt_dir=prompt_dir)
    prompt = f"{specific}\n\n{main_prompt}" if specific else main_prompt

    started_at = time.perf_counter()
    llm_response = await llm_call(prompt=prompt, llm=llm)
    elapsed = time.perf_counter() - started_at

    raw_text = str(llm_response.get("text", ""))
    usage = llm_response.get("usage", {})
    cost = estimate_cost(usage, llm)

    parsed = parse_json_result(raw_text)
    return MetricResult(
        metric_name=metric_name,
        score=parsed.get("score"),
        reason=parsed.get("reason", ""),
        metadata={
            "rubric": parsed.get("rubric", ""),
            "details": parsed.get("details", {}),
            "elapsed_seconds": round(elapsed, 4),
            "token_usage": usage,
            "cost_estimate": cost,
        },
    )


async def run_llm_compare_metric(
    *,
    metric_name: str,
    prompt_file: str,
    row_json: Dict[str, Any],
    transformed_json: Dict[str, Any],
    variables: Dict[str, Any],
    config: Dict[str, Any],
) -> MetricResult:
    """Execution path for comparative (A vs B) LLM metrics."""
    llm = config["llm"]
    prompt_dir = config.get("prompt_dir", "assets/prompts/metrics")
    context = build_context(row_json, transformed_json, variables, config)
    prompt = render_prompt(prompt_file, context=context, prompt_dir=prompt_dir)

    started_at = time.perf_counter()
    llm_response = await llm_call(prompt=prompt, llm=llm)
    elapsed = time.perf_counter() - started_at

    raw_text = str(llm_response.get("text", ""))
    usage = llm_response.get("usage", {})
    cost = estimate_cost(usage, llm)

    parsed = parse_json_result(raw_text)

    better = parsed.get("better_response", "")
    return MetricResult(
        metric_name=metric_name,
        score=None,
        reason=parsed.get("better_response_reason", ""),
        metadata={
            "score_a": parsed.get("score_a"),
            "reason_a": parsed.get("reason_a", ""),
            "score_b": parsed.get("score_b"),
            "reason_b": parsed.get("reason_b", ""),
            "better_response": better,
            "better_response_reason": parsed.get("better_response_reason", ""),
            "elapsed_seconds": round(elapsed, 4),
            "token_usage": usage,
            "cost_estimate": cost,
        },
    )
