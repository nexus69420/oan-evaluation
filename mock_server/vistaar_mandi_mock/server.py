#!/usr/bin/env python3
"""
Standalone mandi mock (Beckn POST /search). For routing + upstream proxy use
beckn_search_proxy/server.py instead.

Listen: http://127.0.0.1:5690/search

Set in bharat-oan-api:
  BAP_ENDPOINT=http://127.0.0.1:5690
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from mandi_response import (
    PROXY_FALLTHROUGH,
    build_empty_on_search,
    try_build_mandi_mock,
)

REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), fmt % args))

    def _send_json(self, status: int, obj: dict):
        b = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/health"):
            body = {
                "ok": True,
                "service": "vistaar_mandi_mock",
                "endpoints": {"POST /search": "Beckn mandi price-discovery (mock only)"},
                "registry": str(REGISTRY_PATH),
                "note": "Use beckn_search_proxy for upstream + conditional mocks.",
            }
            self._send_json(200, body)
            return
        self.send_error(404)

    def do_POST(self):
        if self.path.rstrip("/") != "/search":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        try:
            req_ctx = body["context"]
        except (KeyError, TypeError):
            self._send_json(400, {"error": "missing context"})
            return

        if req_ctx.get("action") != "search":
            self._send_json(400, {"error": "expected context.action search"})
            return

        bpp_fallback = os.environ.get("BPP_URI", "http://127.0.0.1:5690")
        out = try_build_mandi_mock(
            body,
            REGISTRY_PATH,
            allowed_city_keys=None,
            bpp_uri_fallback=bpp_fallback,
        )
        if out is PROXY_FALLTHROUGH:
            out = build_empty_on_search(req_ctx, bpp_uri_fallback=bpp_fallback)
        self._send_json(200, out)


def main():
    host = os.environ.get("MOCK_HOST", "127.0.0.1")
    port = int(os.environ.get("MOCK_PORT", "5690"))
    httpd = HTTPServer((host, port), Handler)
    print(f"vistaar_mandi_mock listening on http://{host}:{port}/search", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
