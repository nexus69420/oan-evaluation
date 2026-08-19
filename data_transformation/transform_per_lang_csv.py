"""
Transformer for per-language scenario CSVs (e.g. english_gemma_scenario.csv).

Input columns: session_id, question_id, question, answer, tool_calls,
               tool_outputs, TTFT_answer, latency_answer

Output is one row PER SESSION (not per message). For single-turn sessions
the output is identical to the input row. For multi-turn sessions all turns
are collapsed into one row:

    {
      "question":            str,   # single-turn: the question
                                    # multi-turn:  full prior-context transcript
                                    #              (all turns except last answer)
      "answer":              str,   # always the LAST turn's answer
      "category":            str,   # "General" (no category in CSV)
      "agristack_required":  "Yes",
      "agent_turns":         [...], # combined from ALL turns in the session
      "retrieved_sources":   str,   # combined tool_outputs from ALL turns
      "session_id":          ...,
      "num_turns":           int,
      "TTFT_answer":         float | None,  # from first turn
      "latency_answer":      float | None,  # sum across all turns
    }

Each CSV tool-call entry is expanded into two agent-turn parts so that
ToolSequencingMetric (which looks for both "tool-call" and "tool-return"
in the serialised JSON) works correctly.

Usage (from the oan-evaluation directory):

    python -m data_transformation.transform_per_lang_csv
    python -m data_transformation.transform_per_lang_csv \\
        --csv /mnt/raid/gautam/inf_bh_dev/per_lang_csvs_gemma/english_gemma_scenario.csv \\
        --model-name english_gemma_scenario \\
        --limit 50
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from data_transformation.base import BaseDataTransform


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_ROOT = REPO_ROOT / "data" / "models"


def _safe_str(val: Any) -> str:
    """Convert val to str, returning '' for None/NaN/blank."""
    if val is None:
        return ""
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return ""
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _parse_raw_tool_calls(raw) -> List[Dict[str, Any]]:
    """Return chronologically ordered list of {name, input, output} dicts."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        calls = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []
    return [
        {"name": c.get("name"), "input": c.get("input"), "output": c.get("output")}
        for c in reversed(calls)
    ]


def _parse_tool_calls(raw) -> List[Dict[str, Any]]:
    """Convert a tool_calls JSON string into agent_turns list."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    try:
        calls = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return []

    # Source CSV stores calls newest-first; reverse to chronological order.
    turns: List[Dict[str, Any]] = []
    for call in reversed(calls):
        name = call.get("name", "unknown_tool")
        turns.append({
            "parts": [{
                "part_kind": "tool-call",
                "tool_name": name,
                "args": call.get("input", {}),
                "trace_id": call.get("trace_id"),
                "observation_id": call.get("observation_id"),
            }],
            "kind": "response",
        })
        turns.append({
            "parts": [{
                "part_kind": "tool-return",
                "tool_name": name,
                "content": call.get("output", ""),
                "latency_ms": call.get("latency_ms"),
            }],
            "kind": "response",
        })
    return turns


def _transform_row(rec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    question = str(rec.get("question") or "").strip()
    answer = str(rec.get("answer") or "").strip()
    if not question or not answer:
        return None

    return {
        "question": question,
        "answer": answer,
        "category": "General",
        "agristack_required": "Yes",
        "agent_turns": _parse_tool_calls(rec.get("tool_calls")),
        "tool_calls_raw": _parse_raw_tool_calls(rec.get("tool_calls")),
        "retrieved_sources": _safe_str(rec.get("tool_outputs")),
        "session_id": rec.get("session_id"),
        "question_id": rec.get("question_id"),
        "TTFT_answer": rec.get("TTFT_answer"),
        "latency_answer": rec.get("latency_answer"),
    }


def _collapse_session(turns: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Collapse a list of per-turn rows (same session_id) into one session row."""
    valid = [t for t in turns if t is not None]
    if not valid:
        return None

    if len(valid) == 1:
        row = dict(valid[0])
        row["num_turns"] = 1
        return row

    # Build a conversation transcript for the question field:
    # All turns shown as "User: ... / Bot: ..." except the final bot answer,
    # which becomes the top-level `answer` field.
    lines = []
    for i, turn in enumerate(valid):
        prefix = f"[Turn {i + 1}]"
        lines.append(f"{prefix}\nUser: {turn['question']}")
        if i < len(valid) - 1:
            lines.append(f"Bot: {turn['answer']}")
    conversation_question = "\n".join(lines)

    # Combine agent_turns, tool_calls_raw, and retrieved_sources across all turns
    all_agent_turns: List[Dict[str, Any]] = []
    all_tool_calls_raw: List[Dict[str, Any]] = []
    all_sources: List[str] = []
    for turn in valid:
        all_agent_turns.extend(turn.get("agent_turns") or [])
        all_tool_calls_raw.extend(turn.get("tool_calls_raw") or [])
        src = (turn.get("retrieved_sources") or "").strip()
        if src:
            all_sources.append(src)

    # Sum latency; take TTFT from first turn
    try:
        total_latency = sum(
            float(t["latency_answer"]) for t in valid if t.get("latency_answer") is not None
        )
    except (TypeError, ValueError):
        total_latency = None

    return {
        "question": conversation_question,
        "answer": valid[-1]["answer"],
        "category": valid[0].get("category", "General"),
        "agristack_required": valid[0].get("agristack_required", "Yes"),
        "agent_turns": all_agent_turns,
        "tool_calls_raw": all_tool_calls_raw,
        "retrieved_sources": "\n\n---\n\n".join(all_sources),
        "session_id": valid[0].get("session_id"),
        "num_turns": len(valid),
        "TTFT_answer": valid[0].get("TTFT_answer"),
        "latency_answer": total_latency,
    }


# ---------------------------------------------------------------------------
# BaseDataTransform integration (for use in pipeline configs)
# ---------------------------------------------------------------------------

class PerLangCsvTransform(BaseDataTransform):
    """Row-level transformer; wraps _transform_row for pipeline use."""

    def transform(self, row_json: Dict[str, Any]) -> Dict[str, Any]:
        result = _transform_row(row_json)
        return result if result is not None else row_json


# ---------------------------------------------------------------------------
# Standalone script
# ---------------------------------------------------------------------------

def transform_csv(
    csv_path: Path,
    out_root: Path,
    model_name: str,
    *,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError("pandas is required: pip install pandas") from e

    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Group by session_id preserving original order, then optionally limit sessions
    session_groups: Dict[Any, List[Dict[str, Any]]] = {}
    for rec in df.to_dict(orient="records"):
        sid = rec.get("session_id")
        session_groups.setdefault(sid, []).append(rec)

    if limit is not None:
        session_ids = list(session_groups.keys())[:limit]
        session_groups = {k: session_groups[k] for k in session_ids}

    # e.g. "gujarati_gemma_scenario" → "Gujarati"
    output_language = model_name.split("_")[0].capitalize()

    rows: List[Dict[str, Any]] = []
    skipped = 0
    for sid, turn_recs in session_groups.items():
        turn_rows = [_transform_row(r) for r in turn_recs]
        session_row = _collapse_session([t for t in turn_rows if t is not None])
        if session_row is None:
            skipped += 1
            continue
        session_row["output_language"] = output_language
        rows.append(session_row)

    out_dir = out_root / model_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    multi_turn = sum(1 for r in rows if r.get("num_turns", 1) > 1)
    with_tools = sum(1 for r in rows if r["agent_turns"])
    return {
        "output_path": str(out_path),
        "sessions_written": len(rows),
        "sessions_skipped_empty": skipped,
        "sessions_multi_turn": multi_turn,
        "sessions_with_tool_calls": with_tools,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transform a per-language scenario CSV into evaluator JSON."
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(
            Path("/mnt/raid/gautam/inf_bh_dev/per_lang_csvs_gemma/english_gemma_scenario.csv")
        ),
        help="Path to input CSV",
    )
    parser.add_argument(
        "--model-name",
        type=str,
        default="english_gemma_scenario",
        help="Output model directory name under data/models/",
    )
    parser.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_ROOT))
    parser.add_argument("--limit", type=int, default=None, metavar="N")
    args = parser.parse_args()

    csv_path = Path(args.csv).expanduser().resolve()
    out_root = Path(args.out_dir).expanduser().resolve()

    info = transform_csv(csv_path, out_root, args.model_name, limit=args.limit)

    print(f"CSV:        {csv_path}")
    print(f"Output:     {info['output_path']}")
    print(f"Sessions:   {info['sessions_written']} written, {info['sessions_skipped_empty']} skipped")
    print(f"Multi-turn: {info['sessions_multi_turn']} sessions have >1 turn")
    print(f"Tool calls: {info['sessions_with_tool_calls']} sessions have tool calls")


if __name__ == "__main__":
    main()
