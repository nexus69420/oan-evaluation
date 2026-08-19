from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def _now_ts() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _echo_context(body: dict, action: str) -> dict:
    ctx = body.get("context", {})
    return {
        "domain": ctx.get("domain", "schemes:vistaar"),
        "action": action,
        "version": ctx.get("version", "1.1.0"),
        "bap_id": ctx.get("bap_id"),
        "bap_uri": ctx.get("bap_uri"),
        "bpp_id": ctx.get("bpp_id"),
        "bpp_uri": ctx.get("bpp_uri"),
        "transaction_id": ctx.get("transaction_id", str(uuid.uuid4())),
        "message_id": str(uuid.uuid4()),
        "timestamp": _now_ts(),
    }


def _get_tag_value(tags: list, code: str) -> str | None:
    """Extract a tag value by descriptor code from a list of tag dicts."""
    for t in tags or []:
        if isinstance(t, dict) and t.get("descriptor", {}).get("code") == code:
            return t.get("value")
    return None


def build_pmfby_init_response(body: dict, registry_path: Path) -> dict:
    """OTP init — return an OTP Sent response matching real sandbox format."""
    ctx = _echo_context(body, "on_init")
    response_item = {
        "context": ctx,
        "message": {
            "order": {
                "provider": {"id": "pmfby-agri"},
                "items": [
                    {
                        "id": "pmfby",
                        "descriptor": {
                            "name": "OTP Sent",
                            "short_desc": "OTP sent successfully to your registered mobile number.",
                        },
                        "tags": [],
                    }
                ],
                "type": "DEFAULT",
            }
        },
    }
    return {"context": ctx, "responses": [response_item]}


def build_pmfby_status_response(body: dict, registry_path: Path) -> dict | None:
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)

    farmers = reg.get("farmers", {})
    farmer = next(iter(farmers.values()), {}) if farmers else {}
    pmfby = farmer.get("pmfby", {})
    policies = pmfby.get("policies", {})
    if not policies:
        return None

    # Extract inquiry params from fulfillment tags
    try:
        tags = (
            body["message"]["order"]["fulfillments"][0]
            ["customer"]["person"]["tags"]
        )
    except (KeyError, IndexError, TypeError):
        tags = []

    inquiry_type = _get_tag_value(tags, "inquiry_type") or "policy_status"
    year = _get_tag_value(tags, "year") or ""
    season = _get_tag_value(tags, "season") or ""

    # Find the matching policy (season-year key e.g. "Kharif-2024")
    policy_key = f"{season}-{year}" if season and year else None
    policy = policies.get(policy_key) if policy_key else None
    if policy is None:
        # Fall back to the first available policy
        policy = next(iter(policies.values()))
        policy_key = next(iter(policies.keys()))

    farmer_name = farmer.get("name", "Farmer")
    farmer_phone = next(iter(farmers.keys()), "")

    if inquiry_type == "claim_status":
        item_name = "Claim Status"
        detail_list = [
            {"descriptor": {"name": "Farmer Name"}, "value": farmer_name, "display": True},
            {"descriptor": {"name": "Application No"}, "value": policy["application_no"], "display": True},
            {"descriptor": {"name": "Policy Number"}, "value": policy["policy_number"], "display": True},
            {"descriptor": {"name": "Crop"}, "value": policy["crop"], "display": True},
            {"descriptor": {"name": "Season"}, "value": policy_key.replace("-", " "), "display": True},
            {"descriptor": {"name": "Sum Insured"}, "value": f"₹{policy['sum_insured']:,}", "display": True},
            {"descriptor": {"name": "Claim Status"}, "value": policy["claim_status"], "display": True},
            {"descriptor": {"name": "Claim Amount"}, "value": f"₹{policy['claim_amount']:,}", "display": True},
        ]
    else:
        item_name = "Policy Status"
        detail_list = [
            {"descriptor": {"name": "Farmer Name"}, "value": farmer_name, "display": True},
            {"descriptor": {"name": "Application No"}, "value": policy["application_no"], "display": True},
            {"descriptor": {"name": "Policy Number"}, "value": policy["policy_number"], "display": True},
            {"descriptor": {"name": "Crop"}, "value": policy["crop"], "display": True},
            {"descriptor": {"name": "Season"}, "value": policy_key.replace("-", " "), "display": True},
            {"descriptor": {"name": "Area (ha)"}, "value": str(policy["area_ha"]), "display": True},
            {"descriptor": {"name": "Sum Insured"}, "value": f"₹{policy['sum_insured']:,}", "display": True},
            {"descriptor": {"name": "Premium Paid"}, "value": f"₹{policy['premium_paid']:,}", "display": True},
            {"descriptor": {"name": "Policy Status"}, "value": policy["policy_status"], "display": True},
            {"descriptor": {"name": "Enrolment Date"}, "value": policy["enrolment_date"], "display": True},
        ]

    ctx = _echo_context(body, "on_status")
    response_item = {
        "context": ctx,
        "message": {
            "order": {
                "providers": [
                    {
                        "descriptor": {
                            "name": "PMFBY",
                            "short_desc": "Pradhan Mantri Fasal Bima Yojana",
                        },
                        "items": [
                            {
                                "id": "pmfby-status",
                                "descriptor": {"name": item_name},
                                "tags": [{"list": detail_list}],
                            }
                        ],
                    }
                ]
            }
        },
    }
    return {"context": ctx, "responses": [response_item]}


def build_pmfby_grievance_response(body: dict, registry_path: Path) -> dict:
    """Grievance submit — return a ticket number in the grievance-response tag format."""
    ticket_no = f"PMFBY{datetime.now(timezone.utc).strftime('%Y%m%d')}KL{uuid.uuid4().hex[:6].upper()}"
    ctx = _echo_context(body, "on_init")
    return {
        "context": ctx,
        "responses": [
            {
                "context": ctx,
                "message": {
                    "order": {
                        "tags": [
                            {
                                "display": True,
                                "descriptor": {"code": "grievance-response"},
                                "list": [
                                    {"descriptor": {"code": "status"}, "value": "Success", "display": True},
                                    {"descriptor": {"code": "ticket-no"}, "value": ticket_no, "display": True},
                                    {"descriptor": {"code": "message"}, "value": "Grievance registered successfully. You will be notified once it is reviewed.", "display": True},
                                ],
                            }
                        ]
                    }
                },
            }
        ],
    }
