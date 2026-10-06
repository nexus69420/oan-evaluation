"""Gemma LLM-as-judge for Amul turns. Prompts live in assets/prompts/metrics/amul/."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen

PROMPT_DIR = Path(__file__).resolve().parents[2] / "assets" / "prompts" / "metrics" / "amul"

JUDGES: dict[str, list[str]] = {
    "grounding": ["source_alignment", "no_fabrication", "citation_accuracy"],
    "gujarati_language": ["grammar", "terminology", "language_purity", "fluency", "gujarati_language"],
    "prod_reference": ["reference_agreement"],
    "task_success": ["task_success"],
    "translation_meaning": ["translation_meaning"],
    "safety": ["safety_compliance"],
    "search_quality": ["search_quality"],
    "recovery": ["recovery_clarification"],
    "context_retention": ["context_retention"],
    "agristack": ["agristack_workflow"],
    "term_identification": ["term_identification"],
    "tool_sequencing": ["tool_sequencing"],
    "completeness": ["completeness"],
    "actionability": ["actionability"],
    "context_fit": ["context_fit"],
    "clarity": ["clarity"],
    "conversation_closure": ["conversation_closure"],
    "persona": ["persona_adherence"],
    "brevity": ["brevity"],
    "content_gap": ["content_gap"],
}

# Judges that only apply when the turn carries this field.
JUDGE_REQUIRES = {"prod_reference": "prod_reference"}

# Knowledge results run to ~90k chars (47 union schemes); truncating them makes supported facts look invented.
MAX_TOOL_OUTPUT_CHARS = 120_000
MAX_HISTORY_TOOL_CHARS = 30_000


def eval_farmer_context() -> str:
    """Farmer profile and technicians the eval stub serves; production runs should pass the real profile."""
    from mock_server.amul_pashu_mock.server import FARMER, TECHNICIANS

    return json.dumps({"farmer": FARMER, "ai_technicians": TECHNICIANS}, ensure_ascii=False, indent=1)


def _fmt_tool_calls(turn: dict) -> str:
    if not turn["tool_calls"]:
        return "(no tools called in this turn)"
    lines = []
    for i, call in enumerate(turn["tool_calls"], 1):
        output = call.get("output")
        output = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
        if len(output) > MAX_TOOL_OUTPUT_CHARS:
            output = output[:MAX_TOOL_OUTPUT_CHARS] + " ...[truncated]"
        lines.append(f"{i}. {call['name']}({json.dumps(call.get('input'), ensure_ascii=False)})\n   result: {output}")
    return "\n".join(lines)


def _fmt_history(turn: dict, session: list[dict]) -> str:
    earlier = [t for t in session if t["turn_index"] < turn["turn_index"]]
    if not earlier:
        return "(this is the first turn)"
    blocks = []
    for t in earlier:
        lines = [f"Turn {t['turn_index']} farmer: {t.get('question_en') or t.get('question_gu')}"]
        for call in t["tool_calls"]:
            output = call.get("output")
            output = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
            if len(output) > MAX_HISTORY_TOOL_CHARS:
                output = output[:MAX_HISTORY_TOOL_CHARS] + " ...[truncated]"
            lines.append(f"Turn {t['turn_index']} tool {call['name']}({json.dumps(call.get('input'), ensure_ascii=False)}) result: {output}")
        lines.append(f"Turn {t['turn_index']} agent: {t.get('answer_en') or t.get('answer_gu')}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _fmt_prod_reference(turn: dict) -> str:
    refs = turn.get("prod_reference") or []
    return "\n\n".join(
        f"Reference {i} — {r['tool']}({json.dumps(r['input'], ensure_ascii=False)}), match {r['similarity']}%:\n{r['output']}"
        for i, r in enumerate(refs, 1)
    )


class Judge:
    def __init__(self, farmer_context: str) -> None:
        base = os.environ.get("SCENARIO_GEMMA_BASE_URL")
        key = os.environ.get("LITELLM_API_KEY")
        if not (base and key):
            raise SystemExit("SCENARIO_GEMMA_BASE_URL and LITELLM_API_KEY are required for judge metrics")
        self.url = base.rstrip("/") + "/chat/completions"
        self.key = key
        self.model = (os.environ.get("SCENARIO_GEMMA_MODEL") or "gemma-4-31b-it").removeprefix("openai/")
        self.farmer_context = farmer_context

    def prompt_version(self, judge: str) -> str:
        text = (PROMPT_DIR / f"{judge}.md").read_text(encoding="utf-8")
        return f"{judge}@{hashlib.sha1(text.encode()).hexdigest()[:8]}"

    def _render(self, judge: str, turn: dict, session: list[dict]) -> str:
        values = {
            "farmer_context": self.farmer_context,
            "history": _fmt_history(turn, session),
            "tool_calls": _fmt_tool_calls(turn),
            "question": turn.get("question_en") or turn.get("question_gu") or "",
            "answer": turn.get("answer_en") or turn.get("answer_gu") or "",
            "question_gu": turn.get("question_gu") or "",
            "answer_gu": turn.get("answer_gu") or "",
            "prod_reference": _fmt_prod_reference(turn),
            "glossary": "\n".join(f"- {en} -> {gu}" for en, gu in turn.get("glossary") or []) or "(no glossary terms in this answer)",
        }
        text = (PROMPT_DIR / f"{judge}.md").read_text(encoding="utf-8")
        return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values.get(m.group(1), m.group(0)), text)

    def _complete(self, prompt: str) -> str:
        from urllib.error import HTTPError

        last_error: Exception | None = None
        for use_json in (True, False):
            body = {"model": self.model, "temperature": 0, "messages": [{"role": "user", "content": prompt}]}
            if use_json:
                body["response_format"] = {"type": "json_object"}
            req = Request(
                self.url,
                data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                    "User-Agent": "amul-eval/1.0",
                },
            )
            try:
                with urlopen(req, timeout=300) as resp:
                    return json.load(resp)["choices"][0]["message"]["content"]
            except HTTPError as exc:
                last_error = exc
                if use_json:
                    continue
                raise
        raise RuntimeError(f"judge request failed: {last_error}")

    @staticmethod
    def _parse(text: str, metrics: list[str]) -> dict[str, tuple[float | None, str]]:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            raise ValueError("no JSON in judge reply")
        blob = match.group()
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            try:
                data = json.loads(blob.replace('\\"', '"'))
            except json.JSONDecodeError:
                return _scores_from_broken(text, metrics)
        parsed = {}
        for metric in metrics:
            entry = data.get(metric)
            if not isinstance(entry, dict) or "score" not in entry:
                raise ValueError(f"missing {metric}")
            score = entry["score"]
            if isinstance(score, str) and score.strip().lower() in ("null", "none", "n/a"):
                score = None
            if score is not None and (isinstance(score, bool) or score not in (1, 2, 3, 4, 5)):
                raise ValueError(f"{metric} score out of range: {score!r}")
            parsed[metric] = (None if score is None else float(score), str(entry.get("evidence") or "").strip())
        return parsed

    def run(self, judge: str, turn: dict, session: list[dict]) -> dict[str, tuple[float | None, str]]:
        prompt = self._render(judge, turn, session)
        error: Exception | None = None
        for _ in range(2):
            try:
                return self._parse(self._complete(prompt), JUDGES[judge])
            except (ValueError, json.JSONDecodeError) as exc:
                error = exc
        raise RuntimeError(f"{judge} judge failed twice: {error}")


def _scores_from_broken(text: str, metrics: list[str]) -> dict[str, tuple[float | None, str]]:
    """Gemma sometimes mixes escaped and raw quotes in one object. Pull the scores out anyway."""
    parsed = {}
    for metric in metrics:
        found = re.search(
            rf"{re.escape(metric)}(?:\\?\"|\s|:|\{{)*score(?:\\?\"|\s|:)*\s*(null|[1-5])",
            text,
            re.I,
        )
        if not found:
            raise ValueError(f"missing {metric}")
        raw = found.group(1)
        score = None if raw.lower() == "null" else float(raw)
        if score is not None and score not in (1, 2, 3, 4, 5):
            raise ValueError(f"{metric} score out of range: {score!r}")
        parsed[metric] = (score, "Score recovered from a malformed judge reply.")
    return parsed
