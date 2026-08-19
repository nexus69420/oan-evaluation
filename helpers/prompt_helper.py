from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from jinja2 import Environment, FileSystemLoader, TemplateNotFound


PromptSpec = Union[str, Dict[str, Any]]


def _resolve_template(prompt_file: str, prompt_dir: str) -> tuple[str, str]:
    candidate = Path(prompt_file)
    if candidate.exists():
        return str(candidate.parent), candidate.name

    name = prompt_file
    if "." not in Path(prompt_file).name:
        name = f"{prompt_file}.md"
    return prompt_dir, name


def render_prompt(
    prompt_file: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    prompt_dir: str = "assets/prompts",
) -> str:
    """
    Render one prompt file with Jinja context.
    """
    resolved_dir, resolved_name = _resolve_template(prompt_file, prompt_dir)
    env = Environment(
        loader=FileSystemLoader(resolved_dir),
        autoescape=False,
    )
    template = env.get_template(resolved_name)
    return template.render(**(context or {}))


def try_render_prompt(
    prompt_file: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    prompt_dir: str = "assets/prompts",
) -> Optional[str]:
    """Like render_prompt but returns None if the template file does not exist."""
    try:
        return render_prompt(prompt_file, context=context, prompt_dir=prompt_dir)
    except TemplateNotFound:
        return None


def combine_prompts(
    prompt_specs: Iterable[PromptSpec],
    *,
    global_context: Optional[Dict[str, Any]] = None,
    default_prompt_dir: str = "assets/prompts",
    separator: str = "\n\n",
) -> str:
    """
    Combine multiple rendered prompts.

    Each prompt spec can be:
    - str: treated as prompt file path/name
    - dict with keys:
      - prompt_file (required)
      - context (optional)
      - prompt_dir (optional)
    """
    rendered_chunks: List[str] = []
    base_context = global_context or {}

    for spec in prompt_specs:
        if isinstance(spec, str):
            rendered_chunks.append(
                render_prompt(spec, context=base_context, prompt_dir=default_prompt_dir)
            )
            continue

        prompt_file = spec["prompt_file"]
        context = dict(base_context)
        context.update(spec.get("context", {}))
        prompt_dir = spec.get("prompt_dir", default_prompt_dir)
        rendered_chunks.append(
            render_prompt(prompt_file, context=context, prompt_dir=prompt_dir)
        )

    return separator.join(rendered_chunks)
