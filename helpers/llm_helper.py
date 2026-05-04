from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic_ai import Agent


async def llm_call(
    *,
    prompt: str,
    llm: Dict[str, Any],
    system_prompt: Optional[str] = None,
) -> Dict[str, Any]:
    """Common LLM helper used by metric plugins.

    The `llm` dict is passed through as Agent kwargs (strict mode).
    """
    if not isinstance(llm, dict):
        raise ValueError("llm config must be a dict of Agent kwargs")

    agent_kwargs = dict(llm)
    agent_kwargs.setdefault("output_type", str)
    agent_kwargs.setdefault("instrument", False)

    if system_prompt is not None and "system_prompt" not in agent_kwargs:
        agent_kwargs["system_prompt"] = system_prompt

    agent = Agent(**agent_kwargs)
    result = await agent.run(prompt)
    usage = result.usage()
    return {
        "text": result.output,
        "usage": {
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
            "details": dict(usage.details),
        },
    }
