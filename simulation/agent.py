# simulation/agent.py

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIChatModelSettings
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv()

_PROMPT_PATH = Path(__file__).parent / "user.md"

_PROMPT_DEFAULTS: dict[str, Any] = {
    "name": "किसान",
    "village": "—",
    "district": "—",
    "state": "—",
    "crops": "—",
    "land_acres": "—",
    "phone": "—",
    "aadhaar": "—",
    "pm_kisan_reg_no": "—",
    "shc_cycle": "—",
    "grievance_reg_no": "—",
    "scenario_description": "",
    "language": "hi",
}


@dataclass
class UserSimDeps:
    """Inputs for the user sim agent: profile (for {{ placeholders }}), last assistant message, use_case/intent/language."""
    profile: dict[str, Any]
    assistant_message: str
    use_case: str = ""
    intent: str = ""
    language: str = "hi"


def _load_user_prompt(ctx: RunContext[UserSimDeps]) -> str:
    """Load user.md and fill {{ key }} from profile (with defaults)."""
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt not found: {_PROMPT_PATH}")

    text = _PROMPT_PATH.read_text(encoding="utf-8")
    profile = {**_PROMPT_DEFAULTS, **(ctx.deps.profile or {})}
    profile["language"] = ctx.deps.language or profile["language"]

    if not profile.get("scenario_description") and (ctx.deps.use_case or ctx.deps.intent):
        profile["scenario_description"] = f"{ctx.deps.use_case or ''}: {ctx.deps.intent or ''}".strip(": ")

    for key, value in profile.items():
        text = text.replace("{{ " + key + " }}", str(value or ""))
    return text


user_sim_agent = Agent(
    model=OpenAIChatModel(
        "gpt-4o-mini",
        provider=OpenAIProvider(api_key=os.getenv("OPENAI_API_KEY")),
    ),
    name="User Simulation Agent",
    deps_type=UserSimDeps,
    output_type=str,
    retries=3,
    model_settings=OpenAIChatModelSettings(
        temperature=0.4,
        max_tokens=256,
        timeout=60,
    ),
)


@user_sim_agent.system_prompt
def system_prompt(ctx: RunContext[UserSimDeps]) -> str:
    return _load_user_prompt(ctx)


async def get_next_user_message(
    use_case: str,
    intent: str,
    assistant_message: str,
    *,
    language: str = "hi",
    profile: dict[str, Any] | None = None,
    message_history: list[tuple[str, str]] | None = None,
) -> str:
    """Generate one next farmer message. message_history = list of (user, assistant) pairs for context."""
    deps = UserSimDeps(
        profile=profile or {},
        assistant_message=assistant_message or "",
        use_case=use_case,
        intent=intent,
        language=language,
    )

    # Normalize to string (callers may pass a list of alternatives)
    last_msg = assistant_message
    if isinstance(last_msg, list):
        last_msg = (last_msg[0] if last_msg else "") or ""
    last_msg = (last_msg or "").strip()
    if last_msg:
        user_prompt = f"The assistant just said:\n\n{last_msg}\n\nReply only to this message with one short, natural response (one sentence). Use the language specified in your instructions."
    else:
        user_prompt = "Begin the conversation based on your goal. Use the language specified in your instructions."

    kwargs: dict[str, Any] = {"deps": deps}
    if message_history:
        kwargs["message_history"] = message_history
    result = await user_sim_agent.run(user_prompt, **kwargs)
    return (result.output or "").strip()
