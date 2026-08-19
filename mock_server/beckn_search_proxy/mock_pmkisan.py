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


def build_pmkisan_init_response(body: dict, registry_path: Path) -> dict:
    ctx = _echo_context(body, "on_init")
    response_item = {
        "context": ctx,
        "message": {
            "order": {
                "provider": {"id": "pmkisan-bpp"},
                "items": [
                    {
                        "id": "pmkisan-status",
                        "tags": [
                            {
                                "display": True,
                                "descriptor": {
                                    "short_desc": "OTP sent to registered mobile number."
                                },
                            }
                        ],
                    }
                ],
            }
        },
    }
    return {"context": ctx, "responses": [response_item]}


def build_pmkisan_status_response(body: dict, registry_path: Path) -> dict | None:
    with open(registry_path, "r", encoding="utf-8") as f:
        reg = json.load(f)

    otp = str(body.get("message", {}).get("order_id", ""))
    if otp != "1111":
        return None

    farmers = reg.get("farmers", {})
    if not farmers:
        return None

    # Use the first farmer in the registry (Ravi Kumar / 9876543210)
    farmer_phone, farmer = next(iter(farmers.items()))
    pmkisan = farmer.get("pmkisan", {})

    reg_no = pmkisan.get("registration_number", "UNKNOWN")
    reg_date = pmkisan.get("registration_date", "")
    last_inst = pmkisan.get("last_installment_number", 0)
    ekyc = pmkisan.get("ekyc_status", "")
    location = pmkisan.get("location", "")

    long_desc = (
        "=== PM KISAN BENEFICIARY STATUS ===\n"
        f"Registration Number : {reg_no}\n"
        f"Registration Date   : {reg_date}\n"
        f"Last Installment No.: {last_inst}\n"
        f"eKYC Status         : {ekyc}\n"
        f"Location            : {location}"
    )

    ctx = _echo_context(body, "on_status")
    ts = _now_ts()
    response_item = {
        "context": ctx,
        "message": {
            "order": {
                "id": otp,
                "state": "COMPLETED",
                "provider": {
                    "id": "pmkisan-bpp",
                    "descriptor": {"name": "PM-KISAN"},
                },
                "items": [
                    {
                        "id": "pmkisan-status",
                        "descriptor": {"name": "PM Kisan Beneficiary Status"},
                    }
                ],
                "fulfillments": [
                    {
                        "customer": {
                            "person": {"name": farmer.get("name", "Farmer")},
                            "contact": {"phone": farmer_phone},
                        },
                        "state": {
                            "descriptor": {
                                "name": "Beneficiary Status Retrieved",
                                "long_desc": long_desc,
                            },
                            "updated_at": ts,
                        },
                    }
                ],
            }
        },
    }
    return {"context": ctx, "responses": [response_item]}
