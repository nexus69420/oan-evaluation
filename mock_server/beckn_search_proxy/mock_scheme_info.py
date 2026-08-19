"""
Handler for Scheme Info mock — POST /search with category.code == "schemes-agri".

Reads scheme content from common_registry.json and returns a Beckn on_search response
shaped to match the SchemeResponse Pydantic model in bharat-oan-api/agents/tools/scheme_info.py.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_REGISTRY_CACHE: dict[str, dict] = {}


def _load_registry(path: Path) -> dict:
    key = str(path)
    if key not in _REGISTRY_CACHE:
        with open(path, "r", encoding="utf-8") as f:
            _REGISTRY_CACHE[key] = json.load(f)
    return _REGISTRY_CACHE[key]


def _build_context(incoming: dict, action: str, now: str) -> dict:
    ctx = incoming.get("context", {})
    return {
        "domain": ctx.get("domain", "schemes:vistaar"),
        "action": action,
        "version": ctx.get("version", "1.1.0"),
        "bap_id": ctx.get("bap_id", os.getenv("BAP_ID", "")),
        "bap_uri": ctx.get("bap_uri", os.getenv("BAP_URI", "")),
        "bpp_id": ctx.get("bpp_id", os.getenv("BPP_ID", "")),
        "bpp_uri": ctx.get("bpp_uri", os.getenv("BPP_URI", "")),
        "message_id": ctx.get("message_id", str(uuid.uuid4())),
        "transaction_id": ctx.get("transaction_id", str(uuid.uuid4())),
        "timestamp": now,
        "ttl": ctx.get("ttl", "PT10M"),
        "location": ctx.get("location", {"country": {"code": "IND"}, "city": {"code": "*"}}),
    }


def _build_response_context(incoming: dict, action: str, now: str) -> dict:
    ctx = incoming.get("context", {})
    return {
        "domain": ctx.get("domain", "schemes:vistaar"),
        "action": action,
        "version": ctx.get("version", "1.1.0"),
        "bpp_id": ctx.get("bpp_id", os.getenv("BPP_ID", "")),
        "bpp_uri": ctx.get("bpp_uri", os.getenv("BPP_URI", "")),
        "message_id": ctx.get("message_id", str(uuid.uuid4())),
        "transaction_id": ctx.get("transaction_id", str(uuid.uuid4())),
        "timestamp": now,
    }


def build_scheme_info_response(body: dict, registry_path: Path) -> dict:
    """
    Build a Beckn on_search response for scheme info.

    Reads scheme_name from message.intent.item.descriptor.name (or .code).
    Returns a valid SchemeResponse-shaped dict, or an empty catalog if unknown.
    """
    registry = _load_registry(registry_path)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    intent = body.get("message", {}).get("intent", {})
    descriptor = intent.get("item", {}).get("descriptor", {})
    scheme_name = (descriptor.get("name") or descriptor.get("code") or "").lower().strip()

    out_ctx = _build_context(body, "on_search", now)
    resp_ctx = _build_response_context(body, "on_search", now)

    scheme = registry.get("schemes", {}).get(scheme_name)

    if scheme is None:
        # Unknown scheme — return empty catalog so bharat-oan-api shows "No scheme data found."
        return {
            "context": out_ctx,
            "responses": [
                {
                    "context": resp_ctx,
                    "message": {
                        "catalog": {
                            "descriptor": {"name": "Agricultural Schemes", "code": "schemes-agri"},
                            "providers": [],
                        }
                    },
                }
            ],
        }

    tags_list = [
        {
            "descriptor": {
                "name": tag_item["name"],
                "code": tag_item["name"].lower().replace(" ", "-"),
            },
            "value": tag_item["value"],
            "display": True,
        }
        for tag_item in scheme.get("tags", [])
    ]

    return {
        "context": out_ctx,
        "responses": [
            {
                "context": resp_ctx,
                "message": {
                    "catalog": {
                        "descriptor": {
                            "name": "Agricultural Schemes",
                            "code": "schemes-agri",
                        },
                        "providers": [
                            {
                                "id": scheme.get("provider_id", "gov-india"),
                                "descriptor": {
                                    "name": scheme.get("provider_name", "Government of India"),
                                },
                                "items": [
                                    {
                                        "id": scheme_name,
                                        "descriptor": {
                                            "name": scheme.get("display_name", scheme_name.upper()),
                                            "code": scheme_name,
                                            "short_desc": scheme.get("short_desc", ""),
                                        },
                                        "tags": [
                                            {
                                                "display": True,
                                                "descriptor": {
                                                    "name": "Scheme Details",
                                                    "code": "scheme-details",
                                                },
                                                "list": tags_list,
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                },
            }
        ],
    }
