from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModelSettings


async def llm_call(
    *,
    prompt: str,
    model_name: str = "gpt-5",
    system_prompt: Optional[str] = None,
    temperature: float = 0.0,
    timeout: int = 60,
    reasoning_effort: str = "low",
) -> str:
    """
    Generic async LLM helper for metric-level calls.
    """
    agent = Agent(
        model=model_name,
        output_type=str,
        system_prompt=system_prompt,
        model_settings=OpenAIResponsesModelSettings(
            temperature=temperature,
            timeout=timeout,
            openai_reasoning_effort=reasoning_effort,
        ),
        instrument=False,
    )
    result = await agent.run(prompt)
    return result.output
