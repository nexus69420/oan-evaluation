"""Utility functions for data processing and HuggingFace dataset creation."""
import json
from typing import Dict, List, Any, Set


def list_tool_calls(messages: List[Dict[str, Any]]) -> List[str]:
    """Extract unique tool names from a conversation."""
    tools = set()
    for msg in messages:
        if msg.get("role") == "assistant" and "tool_calls" in msg:
            for tc in msg["tool_calls"]:
                if "function" in tc and "name" in tc["function"]:
                    tools.add(tc["function"]["name"])
    return sorted(list(tools))


def normalize_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a message to include all fields expected by HuggingFace Features.
    
    Ensures every message has role, content, tool_calls, tool_call_id, and name fields,
    even if some are None or empty.
    """
    normalized = {
        "role": msg.get("role", ""),
        "content": msg.get("content") or "",  # Ensure it's a string, not None
        "tool_calls": [],  # Default to empty list, not None
        "tool_call_id": "",  # Default to empty string, not None
        "name": "",  # Default to empty string for tool messages
    }
    
    # Handle tool_calls (only for assistant messages with tool calls)
    if msg.get("tool_calls"):
        normalized["tool_calls"] = [
            {
                "id": tc.get("id", ""),
                "type": tc.get("type", "function"),
                "function": {
                    "name": tc.get("function", {}).get("name", ""),
                    "arguments": tc.get("function", {}).get("arguments", "{}"),
                }
            }
            for tc in msg["tool_calls"]
        ]
    
    # Handle tool_call_id (for tool messages)
    if msg.get("tool_call_id"):
        normalized["tool_call_id"] = msg["tool_call_id"]
    elif msg.get("id"):  # Fallback to 'id' field if tool_call_id not present
        normalized["tool_call_id"] = msg["id"]
    
    # Handle name field (for tool messages)
    if msg.get("name"):
        normalized["name"] = msg["name"]
    
    return normalized

def remove_system_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove system messages from a list of messages."""
    if not isinstance(messages, list):
        return []
    return [msg for msg in messages if msg.get("role") != "system"]

def create_record(span: Dict, normalize: bool = False) -> Dict:
    """
    Create a record from a span item.
    
    Args:
        span: Raw span data from LogFire with 'span_id', 'created_at', and 'attributes'
    
    Returns:
        Formatted record
    """
    convo = span['attributes']['all_messages_events']
    convo = remove_system_messages(convo)
    if normalize:
        convo = [normalize_message(msg) for msg in convo]
    
    record = {
        "id": span['span_id'],
        "timestamp": span['created_at'], 
        "messages_json": json.dumps(convo, ensure_ascii=False, indent=None, separators=(",", ":")),
        "tools": list_tool_calls(convo),
    }    
    return record