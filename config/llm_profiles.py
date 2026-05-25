from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional, Tuple


def normalize_llm_profiles(
    llm: Optional[Dict[str, Any]],
    *,
    default_llm_profile: Optional[str] = None,
    single_llm_fallback: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Dict[str, Any]], str, Dict[str, Any]]:
    """
    Build a name -> config map for judge LLMs.

    Two shapes for ``llm``:

    1) **Legacy single judge** (current behaviour): a dict with a string
       ``"model"`` at the top level. It becomes one profile named ``"default"``.

    2) **Named profiles**: a dict whose keys are profile names and whose values
       are full per-model configs (each value is a dict with string ``"model"``).

    ``default_llm_profile`` chooses which named profile applies to metric entries
    that do not specify a profile. If omitted, the first key in insertion order
    is used.

    Returns ``(llm_profiles, default_profile_key, default_llm_dict)`` where
    ``default_llm_dict`` is a copy of the resolved default profile for backward
    compatibility with code that expects a single ``.llm`` dict.
    """
    base = dict(single_llm_fallback or {})
    if llm is None:
        llm = base
    if not llm:
        raise ValueError("llm configuration is empty")

    # Legacy: one flat OpenAI-style block
    if isinstance(llm.get("model"), str):
        profiles = {"default": deepcopy(llm)}
        key = "default"
        return profiles, key, deepcopy(profiles[key])

    profiles: Dict[str, Dict[str, Any]] = {}
    for name, block in llm.items():
        if not isinstance(block, dict):
            raise ValueError(
                f"LLM profile {name!r} must be a dict; use legacy single-llm shape "
                "or a dict of profile_name -> llm_config."
            )
        if not isinstance(block.get("model"), str):
            raise ValueError(
                f"LLM profile {name!r} must include a string 'model' key, got {block!r}"
            )
        profiles[name] = deepcopy(block)

    if not profiles:
        raise ValueError("No LLM profiles could be parsed from llm=...")

    if default_llm_profile is None:
        chosen = next(iter(profiles))
    elif default_llm_profile not in profiles:
        raise ValueError(
            f"default_llm_profile {default_llm_profile!r} is not one of: {sorted(profiles)}"
        )
    else:
        chosen = default_llm_profile

    return profiles, chosen, deepcopy(profiles[chosen])
