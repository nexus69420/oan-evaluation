"""Formatter utilities for converting between Logfire and Pydantic AI message formats."""
from __future__ import annotations
from typing import Any, Dict, Iterable, List, Optional, Sequence
import json
from pydantic_ai.messages import (
    ModelMessage, ModelRequest, ModelResponse,
    SystemPromptPart, UserPromptPart, ToolReturnPart, RetryPromptPart,
    TextPart, ToolCallPart, 
    ModelRequestPart, ModelResponsePart,
    ModelMessagesTypeAdapter
)


def _as_dict(maybe_json: Any) -> Dict[str, Any]:
    """Convert a JSON-like object to a dictionary."""
    if maybe_json is None:
        return {}
    if isinstance(maybe_json, dict):
        return maybe_json
    if isinstance(maybe_json, str):
        try:
            return json.loads(maybe_json)
        except Exception:
            return {"__raw__": maybe_json}
    return {"__raw__": maybe_json}

def _extract_role(d: Dict[str, Any]) -> str:
    """Extract the role from the dictionary."""
    role = d.get("role") or d.get("event") or d.get("name") or ""
    if isinstance(role, str) and role.startswith("gen_ai."):
        parts = role.split(".")
        if len(parts) >= 2:
            role = parts[1]
    return role

def _extract_content(d: Dict[str, Any]) -> Optional[str]:
    """Extract the content from the dictionary."""
    for key in ("content", "text", "message", "body"):
        v = d.get(key)
        if v is not None:
            return v
    return None

def _extract_tool_calls(d: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract the tool calls from the dictionary."""
    calls = d.get("tool_calls") or d.get("toolCalls") or []
    out = []
    for c in calls or []:
        if isinstance(c, dict) and "function" in c:
            fid = c.get("id") or c.get("tool_call_id") or c.get("call_id")
            fname = c["function"].get("name")
            fargs = c["function"].get("arguments")
            args = _as_dict(fargs)
            out.append({"tool_call_id": fid, "tool_name": fname, "args": args})
        elif isinstance(c, dict):
            out.append({
                "tool_call_id": c.get("id") or c.get("tool_call_id") or c.get("call_id"),
                "tool_name": c.get("tool_name") or c.get("name"),
                "args": _as_dict(c.get("args") or c.get("arguments")),
            })
    return [x for x in out if x.get("tool_call_id") and x.get("tool_name")]

def _extract_tool_return(d: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract the tool return from the dictionary."""
    tid = d.get("tool_call_id") or d.get("call_id") or d.get("id")
    tname = d.get("tool_name") or d.get("name") or (d.get("function") or {}).get("name")
    if "return_value" in d:
        payload = d["return_value"]
    elif "output" in d:
        payload = d["output"]
    else:
        payload = d.get("content")
    if tid and tname is not None:
        return {"tool_call_id": tid, "tool_name": tname, "content": payload}
    return None

def _is_retry_prompt(d: Dict[str, Any]) -> bool:
    """Check if the dictionary is a retry prompt."""
    role = _extract_role(d)
    return "retry" in role or d.get("retry_prompt") is True or d.get("type") == "retry-prompt"
    
def convert_logfire_to_pydantic_ai_messages(entries: Iterable[Any]) -> List[ModelMessage]:
    """
    Convert a list of Logfire/OpenAI-shaped message dicts into canonical Pydantic-AI ModelMessage objects.
    
    Idempotent: if entries already contain ModelRequest/ModelResponse instances, they are returned unchanged.
    """
    out: List[ModelMessage] = []

    for raw in entries:
        # --- Already normalized (idempotent case) ---
        if isinstance(raw, (ModelRequest, ModelResponse)):
            out.append(raw)
            continue

        # --- Must be dict-like for normalization ---
        if not isinstance(raw, dict):
            continue

        # --- Canonical dict with kind+parts ---
        if "kind" in raw and "parts" in raw:
            msg = ModelMessagesTypeAdapter.validate_python([raw])[0]
            out.append(msg)
            continue

        role = _extract_role(raw)

        # --- USER ---
        if role == "user":
            content = _extract_content(raw)
            if content:
                out.append(ModelRequest(parts=[UserPromptPart(content=content)]))
            continue

        # --- SYSTEM ---
        if role == "system":
            out.append(ModelRequest(parts=[SystemPromptPart(content=_extract_content(raw) or "")]))
            continue

        # --- ASSISTANT ---
        if role == "assistant":
            parts = []
            for call in _extract_tool_calls(raw):
                parts.append(ToolCallPart(
                    tool_name=call["tool_name"],
                    args=call.get("args") or {},
                    tool_call_id=call["tool_call_id"],
                ))
            content = _extract_content(raw)
            if content:
                parts.append(TextPart(content=content))
            if parts:
                out.append(ModelResponse(parts=parts))
            continue

        # --- TOOL RETURN ---
        if role in ("tool", "function", "tools", "tool-return") or raw.get("part_kind") == "tool-return":
            tr = _extract_tool_return(raw)
            if tr:
                out.append(ModelRequest(parts=[ToolReturnPart(
                    tool_name=tr["tool_name"],
                    tool_call_id=tr["tool_call_id"],
                    content=tr["content"],
                )]))
            continue

        # --- RETRY PROMPT ---
        if _is_retry_prompt(raw):
            out.append(ModelRequest(parts=[RetryPromptPart(
                content=_extract_content(raw) or "",
                tool_name=raw.get("tool_name"),
                tool_call_id=raw.get("tool_call_id"),
            )]))
            continue

        # --- Fallback: treat as assistant text ---
        content = _extract_content(raw)
        if content:
            out.append(ModelResponse(parts=[TextPart(content=content)]))

    return out


def pydantic_to_openai_chat_messages(messages: Sequence[ModelMessage]) -> List[Dict[str, Any]]:
    """
    Convert to Chat Completions messages array: [{role, content, tool_calls?}, ...]
    ToolReturnPart maps to role='tool' with tool_call_id.
    """
    chat_messages: List[Dict[str, Any]] = []

    for m in messages:
        if isinstance(m, ModelRequest):
            for p in m.parts:
                if isinstance(p, SystemPromptPart):
                    chat_messages.append({"role": "system", "content": p.content})
                elif isinstance(p, UserPromptPart):
                    chat_messages.append({"role": "user", "content": getattr(p, "content", "")})
                elif isinstance(p, ToolReturnPart):
                    # tool result back to assistant: role=tool
                    content = p.content if p.content is not None else p.model_response_object()
                    chat_messages.append({
                        "role": "tool",
                        "tool_call_id": p.tool_call_id,
                        "content": content if isinstance(content, str) else (json.dumps(content, ensure_ascii=False, indent=None, separators=(",", ":"))),
                    })
                elif isinstance(p, RetryPromptPart):
                    chat_messages.append({"role": "system", "content": f"Retry: {p.content}"})
        elif isinstance(m, ModelResponse):
            # combine text parts into one assistant content; include tool_calls if any
            assistant_texts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []
            for p in m.parts:
                if isinstance(p, TextPart) and p.content:
                    assistant_texts.append(p.content)
                elif isinstance(p, (ToolCallPart)):
                    args = p.args if isinstance(p.args, dict) else p.args or {}
                    tool_calls.append({
                        "id": p.tool_call_id,
                        "type": "function",
                        "function": {
                            "name": p.tool_name,
                            "arguments": json.dumps(args, ensure_ascii=False, indent=None, separators=(",", ":")),
                        }
                    })
            # Emit assistant message if there is text or tool_calls
            if assistant_texts or tool_calls:
                msg: Dict[str, Any] = {
                    "role": "assistant",
                    "content": "\n".join(assistant_texts) if assistant_texts else "",
                }
                if tool_calls:
                    msg["tool_calls"] = tool_calls
                chat_messages.append(msg)
    return chat_messages