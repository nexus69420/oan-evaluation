"""
Build Beckn on_search JSON for mandi mocks (used by vistaar_mandi_mock server and beckn_search_proxy).
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROXY_FALLTHROUGH = "__proxy_upstream__"


def load_registry(registry_path: Path) -> dict[str, Any]:
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def city_tables(reg: dict[str, Any]) -> tuple[dict[str, tuple[float, float, str]], float]:
    cities = {c["key"]: (c["latitude"], c["longitude"], c["query"].split(",")[0]) for c in reg["cities"]}
    tol = float(reg.get("match_tolerance_deg_per_axis", 1.0))
    return cities, tol


def nearest_city(
    lat: float,
    lon: float,
    cities: dict[str, tuple[float, float, str]],
    max_axis_offset_deg: float,
) -> tuple[str, float, str] | None:
    best: tuple[str, float, str] | None = None
    for key, (clat, clon, label) in cities.items():
        d = max(abs(lat - clat), abs(lon - clon))
        if best is None or d < best[1]:
            best = (key, d, label)
    if best is None or best[1] > max_axis_offset_deg:
        return None
    return best


def parse_mandi_stop(body: dict) -> tuple[float, float, int]:
    stop = body["message"]["intent"]["fulfillment"]["stops"][0]
    lat = float(stop["location"]["lat"])
    lon = float(stop["location"]["lon"])
    code = int(stop["commoditycode"])
    return lat, lon, code


def prices_for(city_key: str, code: int) -> tuple[int, int, int]:
    digest = hashlib.sha256(f"{city_key}:{code}".encode()).hexdigest()
    h = int(digest[:12], 16) % (10**9)
    base = 3500 + (h % 4500)
    spread = 120 + (h % 400)
    return base, max(500, base - spread), base + spread


def arrival_dd_mm_yyyy() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%d/%m/%Y")


def tag_list(
    commodity: str,
    market: str,
    district: str,
    state: str,
    modal: int,
    min_p: int,
    max_p: int,
) -> list[dict]:
    return [
        {"descriptor": {"code": "Commodity"}, "value": commodity},
        {"descriptor": {"code": "Market"}, "value": market},
        {"descriptor": {"code": "District"}, "value": district},
        {"descriptor": {"code": "State"}, "value": state},
        {"descriptor": {"code": "Modal Price"}, "value": str(modal)},
        {"descriptor": {"code": "Min Price"}, "value": str(min_p)},
        {"descriptor": {"code": "Max Price"}, "value": str(max_p)},
        {"descriptor": {"code": "Price Unit"}, "value": "Rs./Quintal"},
        {"descriptor": {"code": "Arrival Date"}, "value": arrival_dd_mm_yyyy()},
    ]


STATE_BY_CITY = {
    "kozhikode": ("Kozhikode", "Kerala"),
    "kochi": ("Ernakulam", "Kerala"),
    "bangalore": ("Bengaluru Urban", "Karnataka"),
    "mumbai": ("Mumbai", "Maharashtra"),
    "chandigarh": ("Chandigarh", "Chandigarh"),
}


def mock_catalog(
    city_key: str,
    code: int,
    commodity_name: str,
    cities: dict[str, tuple[float, float, str]],
) -> dict:
    district, state = STATE_BY_CITY[city_key]
    modal, min_p, max_p = prices_for(city_key, code)
    _, _, city_label = cities[city_key]
    market_a = f"{city_label} APMC — Yard 1 (mock)"
    market_b = f"{city_label} wholesale hub (mock)"
    items = [
        {
            "id": f"mock-{city_key}-{code}-1",
            "descriptor": {"name": commodity_name},
            "tags": [
                {
                    "descriptor": {"code": "mandi_item"},
                    "list": tag_list(commodity_name, market_a, district, state, modal, min_p, max_p),
                }
            ],
        },
        {
            "id": f"mock-{city_key}-{code}-2",
            "descriptor": {"name": commodity_name},
            "tags": [
                {
                    "descriptor": {"code": "mandi_item"},
                    "list": tag_list(
                        commodity_name,
                        market_b,
                        district,
                        state,
                        int(modal * 0.97),
                        int(min_p * 0.95),
                        int(max_p * 0.99),
                    ),
                }
            ],
        },
    ]
    return {
        "descriptor": {"name": "Mandi catalog (mock)"},
        "providers": [
            {
                "id": "mock-bpp-mandi",
                "descriptor": {"name": "Mock BPP — mandi prices"},
                "items": items,
            }
        ],
    }


def search_response(req_ctx: dict, catalog: dict | None, bpp_uri_default: str | None = None) -> dict:
    now_ts = str(int(datetime.now(timezone.utc).timestamp()))
    out_ctx = {
        "domain": req_ctx.get("domain", "schemes:vistaar"),
        "action": "on_search",
        "version": req_ctx.get("version", "1.1.0"),
        "bap_id": req_ctx.get("bap_id"),
        "bap_uri": req_ctx.get("bap_uri"),
        "bpp_id": req_ctx.get("bpp_id"),
        "bpp_uri": req_ctx.get("bpp_uri") or bpp_uri_default,
        "transaction_id": req_ctx.get("transaction_id", str(uuid.uuid4())),
        "message_id": str(uuid.uuid4()),
        "timestamp": now_ts,
        "ttl": req_ctx.get("ttl", "PT10M"),
    }
    out_ctx = {k: v for k, v in out_ctx.items() if v is not None}

    if catalog is None:
        return {"context": out_ctx, "responses": []}

    inner_ctx = {**out_ctx, "message_id": str(uuid.uuid4())}
    return {
        "context": out_ctx,
        "responses": [
            {
                "context": inner_ctx,
                "message": {"catalog": catalog},
            }
        ],
    }


def commodity_map(reg: dict[str, Any]) -> dict[int, str]:
    return {c["agmkt_code"]: c["canonical_name"] for c in reg["commodities"]}


def build_empty_on_search(req_ctx: dict, bpp_uri_fallback: str | None = None) -> dict:
    """Beckn on_search with no catalog rows (same shape as real empty discovery)."""
    return search_response(req_ctx, None, bpp_uri_fallback)


def try_build_mandi_mock(
    body: dict,
    registry_path: Path,
    *,
    allowed_city_keys: frozenset[str] | None = None,
    bpp_uri_fallback: str | None = None,
) -> dict | str:
    """
    If body is mandi price-discovery and nearest city is allowed and commodity is known,
    return on_search JSON dict.

    If mandi + allowed city but unknown commodity → PROXY_FALLTHROUGH (caller should hit upstream).

    If not mandi or parse error → PROXY_FALLTHROUGH.

    For standalone mandi-only server (no proxy): caller may interpret parse errors differently.
    """
    try:
        req_ctx = body["context"]
        cat_code = body["message"]["intent"]["category"]["descriptor"]["code"]
        item_code = body["message"]["intent"]["item"]["descriptor"]["code"]
    except (KeyError, TypeError):
        return PROXY_FALLTHROUGH

    if req_ctx.get("action") != "search":
        return PROXY_FALLTHROUGH
    if cat_code != "price-discovery" or item_code != "mandi":
        return PROXY_FALLTHROUGH

    try:
        lat, lon, commodity_code = parse_mandi_stop(body)
    except (KeyError, TypeError, ValueError):
        return PROXY_FALLTHROUGH

    reg = load_registry(registry_path)
    cities, tol = city_tables(reg)
    commodities = commodity_map(reg)

    hit = nearest_city(lat, lon, cities, tol)
    if not hit:
        return PROXY_FALLTHROUGH
    city_key = hit[0]
    if allowed_city_keys is not None and city_key not in allowed_city_keys:
        return PROXY_FALLTHROUGH

    name = commodities.get(commodity_code)
    if not name:
        return PROXY_FALLTHROUGH

    catalog = mock_catalog(city_key, commodity_code, name, cities)
    return search_response(req_ctx, catalog, bpp_uri_fallback)
