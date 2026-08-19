#!/usr/bin/env python3
"""POST /search for every city × commodity in registry.json (expects server on 127.0.0.1:5690)."""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "http://127.0.0.1:5690/search"
REG = json.loads((Path(__file__).parent / "registry.json").read_text(encoding="utf-8"))


def _payload(lat: float, lon: float, commodity_code: int) -> dict:
    return {
        "context": {
            "domain": "schemes:vistaar",
            "action": "search",
            "version": "1.1.0",
            "bap_id": "bap-network-playground-sandbox-vistaar.da.gov.in",
            "bap_uri": "https://bap-network-playground-sandbox-vistaar.da.gov.in",
            "bpp_id": "bpp-network-playground-sandbox-vistaar.da.gov.in",
            "bpp_uri": "https://bpp-network-playground-sandbox-vistaar.da.gov.in",
            "transaction_id": "435c456f-86f2-4d5c-9587-3a99fc2eb823",
            "message_id": "a8255045-c002-4071-872e-348121dd21af",
            "timestamp": "1778529671",
            "ttl": "PT10M",
            "location": {"country": {"code": "IND"}, "city": {"code": "*"}},
        },
        "message": {
            "intent": {
                "category": {"descriptor": {"code": "price-discovery"}},
                "item": {"descriptor": {"code": "mandi"}},
                "fulfillment": {
                    "stops": [
                        {
                            "location": {"lat": str(lat), "lon": str(lon)},
                            "time": {
                                "range": {
                                    "start": "2025-08-01T08:00:00.108Z",
                                    "end": "2025-08-01T08:00:00.108Z",
                                }
                            },
                            "commoditycode": commodity_code,
                        }
                    ]
                },
            }
        },
    }


def main() -> int:
    ok = 0
    fail = 0
    for city in REG["cities"]:
        for crop in REG["commodities"]:
            lat, lon = city["latitude"], city["longitude"]
            code = crop["agmkt_code"]
            label = f"{city['key']} + {crop['crop']} ({code})"
            body = json.dumps(_payload(lat, lon, code)).encode()
            req = urllib.request.Request(
                BASE,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.load(resp)
            except urllib.error.HTTPError as e:
                print("FAIL", label, e.code, e.read().decode()[:200])
                fail += 1
                continue
            except ConnectionRefusedError:
                print(
                    "Connection refused. Start the mock first:\n"
                    "  cd mock_server/vistaar_mandi_mock && python3 server.py",
                    file=sys.stderr,
                )
                return 2
            except OSError as e:
                print("FAIL", label, e)
                fail += 1
                continue
            n = len(data.get("responses", []))
            if n != 1:
                print("FAIL", label, "expected 1 response block, got", n)
                fail += 1
                continue
            items = data["responses"][0]["message"]["catalog"]["providers"][0].get("items") or []
            if len(items) < 1:
                print("FAIL", label, "no items")
                fail += 1
                continue
            print("ok ", label)
            ok += 1
    print(f"\n{ok} passed, {fail} failed")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
