#!/usr/bin/env python3
"""Rule engine checks without starting HTTP (no upstream calls)."""
import json
import os
from pathlib import Path

from engine import apply_rules, substitute_env
from env_loader import load_proxy_env

HERE = Path(__file__).resolve().parent


def main() -> int:
    load_proxy_env(HERE)
    cfg = substitute_env(json.loads((HERE / "config.json").read_text(encoding="utf-8")))
    rules = cfg["rules"]
    os.environ["BPP_URI"] = "https://bpp-network-playground-sandbox-vistaar.da.gov.in"

    kochi = {
        "context": {
            "action": "search",
            "domain": "schemes:vistaar",
            "version": "1.1.0",
            "bap_id": "bap-network-playground-sandbox-vistaar.da.gov.in",
            "bap_uri": "https://bap-network-playground-sandbox-vistaar.da.gov.in",
            "bpp_id": "bpp-network-playground-sandbox-vistaar.da.gov.in",
            "bpp_uri": "https://bpp-network-playground-sandbox-vistaar.da.gov.in",
            "transaction_id": "t",
            "message_id": "m",
            "timestamp": "1",
        },
        "message": {
            "intent": {
                "category": {"descriptor": {"code": "price-discovery"}},
                "item": {"descriptor": {"code": "mandi"}},
                "fulfillment": {
                    "stops": [
                        {
                            "location": {"lat": "9.9679032", "lon": "76.2444378"},
                            "time": {
                                "range": {
                                    "start": "2025-01-01T00:00:00Z",
                                    "end": "2025-01-02T00:00:00Z",
                                }
                            },
                            "commoditycode": 15,
                        }
                    ]
                },
            }
        },
    }
    r = apply_rules(kochi, rules, HERE)
    assert r is not None and r.get("responses"), "expected mock for Kochi mandi cotton"
    kochi["message"]["intent"]["fulfillment"]["stops"][0]["location"] = {"lat": "22.3", "lon": "71.3"}
    r2 = apply_rules(kochi, rules, HERE)
    assert r2 is None, "expected proxy fallthrough for coords not near listed cities"
    print("smoke_local: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
