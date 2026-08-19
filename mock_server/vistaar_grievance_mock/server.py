#!/usr/bin/env python3
"""
PM-Kisan grievance mock server (port 5691 by default).

Handles the three encrypted REST endpoints that pmkisan_grievance.py calls:
  POST /GrievanceAadhaarToken  — Aadhaar → token lookup (always fails; use reg number)
  POST /LodgeGrievance         — submit a grievance
  POST /GrievanceStatusCheck   — check grievance status

All requests arrive as {"EncryptedRequest": "<b64>"} and are decrypted with AES-GCM.
All responses are returned as {"d": {"__type": "...", "output": "<b64>"}} where
output encrypts to the actual JSON payload.

Environment (set in mock_server/.env or shell):
  GRIEVANCE_KEY_1   — 64-hex-char (32-byte) AES key  [required]
  GRIEVANCE_KEY_2   — 24-hex-char (12-byte) IV        [required]
  GRIEVANCE_HOST    — bind host (default 127.0.0.1)
  GRIEVANCE_PORT    — bind port (default 5691)
  GRIEVANCE_REGISTRY — path to common_registry.json (default: ../common_registry.json)

Matching .env keys must also be set in bharat-oan-api:
  GRIEVANCE_KEY_1, GRIEVANCE_KEY_2, GRIEVANCE_BASE_URL=http://127.0.0.1:5691
"""
from __future__ import annotations

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent
_MOCK_SERVER_ROOT = _SERVER_DIR.parent

# Lazy import: load env from mock_server/.env if present
_env_loader = _MOCK_SERVER_ROOT / "beckn_search_proxy" / "env_loader.py"
if _env_loader.exists():
    if str(_MOCK_SERVER_ROOT / "beckn_search_proxy") not in sys.path:
        sys.path.insert(0, str(_MOCK_SERVER_ROOT / "beckn_search_proxy"))
    try:
        from env_loader import load_proxy_env  # type: ignore
        load_proxy_env(_MOCK_SERVER_ROOT / "beckn_search_proxy")
    except Exception:
        pass

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
except ImportError:
    print(
        "ERROR: 'cryptography' package not installed. "
        "Run: pip install cryptography",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# Crypto helpers
# ---------------------------------------------------------------------------

def _get_keys() -> tuple[bytes, bytes]:
    k1 = os.environ.get("GRIEVANCE_KEY_1", "")
    k2 = os.environ.get("GRIEVANCE_KEY_2", "")
    if not k1 or not k2:
        raise RuntimeError(
            "GRIEVANCE_KEY_1 and GRIEVANCE_KEY_2 must be set "
            "(64-hex and 24-hex strings respectively)."
        )
    return bytes.fromhex(k1), bytes.fromhex(k2)


def _decrypt(encrypted_b64: str, key: bytes, iv: bytes) -> dict:
    ciphertext = base64.b64decode(encrypted_b64)
    plaintext = AESGCM(key).decrypt(iv, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))


def _encrypt(payload: dict, key: bytes, iv: bytes) -> str:
    plaintext = json.dumps(payload, ensure_ascii=False)
    ciphertext = AESGCM(key).encrypt(iv, plaintext.encode("utf-8"), None)
    return base64.b64encode(ciphertext).decode("utf-8")


def _envelope(type_str: str, payload: dict, key: bytes, iv: bytes) -> dict:
    return {"d": {"__type": type_str, "output": _encrypt(payload, key, iv)}}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def _load_registry() -> dict:
    reg_path_env = os.environ.get("GRIEVANCE_REGISTRY", "")
    if reg_path_env:
        reg_path = Path(reg_path_env).expanduser().resolve()
    else:
        reg_path = _MOCK_SERVER_ROOT / "common_registry.json"
    with open(reg_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Endpoint handlers (operate on decrypted dicts)
# ---------------------------------------------------------------------------

def _handle_aadhaar_token(payload: dict) -> dict:
    # We don't support Aadhaar lookup in the test environment.
    # The tool falls back gracefully when this returns False.
    return {"Responce": "False", "message": "Aadhaar lookup not available in mock environment."}


def _handle_lodge_grievance(payload: dict) -> dict:
    identity_no = payload.get("IdentityNo", "")
    description = payload.get("GrievanceDescription", "")

    reg = _load_registry()
    farmers = reg.get("farmers", {})
    farmer_data = next(iter(farmers.values()), {}) if farmers else {}
    pmkisan = farmer_data.get("pmkisan", {})
    known_reg_no = pmkisan.get("registration_number", "")

    if identity_no == known_reg_no:
        existing = farmer_data.get("grievances", [])
        if existing:
            return {
                "Responce": "False",
                "message": (
                    "Grievance already registered. "
                    "Use the status check to see your existing grievance."
                ),
            }

    return {"Responce": "True", "message": "Grievance registered successfully."}


def _handle_grievance_status(payload: dict) -> dict:
    identity_no = payload.get("IdentityNo", "")

    reg = _load_registry()
    farmers = reg.get("farmers", {})
    farmer_data = next(iter(farmers.values()), {}) if farmers else {}
    pmkisan = farmer_data.get("pmkisan", {})
    known_reg_no = pmkisan.get("registration_number", "")

    if identity_no != known_reg_no:
        return {"Responce": "False", "message": "No grievances found for this registration number."}

    grievances = farmer_data.get("grievances", [])
    if not grievances:
        return {"Responce": "False", "message": "No grievances found for this registration number."}

    g = grievances[0]
    detail = {
        "Reg_No": g.get("registration_number", known_reg_no),
        "GrievanceDate": g.get("grievance_date"),
        "GrievanceDescription": g.get("description"),
        "OfficerReply": g.get("officer_reply"),
        "OfficeReplyDate": g.get("office_reply_date"),
    }
    return {"Responce": "True", "details": [detail]}


_PATH_HANDLERS = {
    "/GrievanceAadhaarToken": ("GrievanceAadhaarToken_result", _handle_aadhaar_token),
    "/LodgeGrievance": ("LodgeGrievance_result", _handle_lodge_grievance),
    "/GrievanceStatusCheck": ("GrievanceStatusCheck_result", _handle_grievance_status),
}


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class GrievanceHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(
            "%s - - [%s] %s\n"
            % (self.address_string(), self.log_date_time_string(), fmt % args)
        )

    def _send_json(self, status: int, obj: dict) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/health"):
            self._send_json(200, {"ok": True, "service": "vistaar_grievance_mock"})
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.rstrip("/") or "/"
        if path not in _PATH_HANDLERS:
            self.send_error(404)
            return

        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"

        try:
            outer = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return

        encrypted_request = outer.get("EncryptedRequest", "")
        if not encrypted_request:
            self._send_json(400, {"error": "missing EncryptedRequest"})
            return

        try:
            key, iv = _get_keys()
        except RuntimeError as e:
            self._send_json(500, {"error": str(e)})
            return

        try:
            payload = _decrypt(encrypted_request, key, iv)
        except Exception as e:
            self._send_json(400, {"error": f"decryption failed: {e}"})
            return

        type_str, handler_fn = _PATH_HANDLERS[path]
        try:
            result = handler_fn(payload)
        except Exception as e:
            self._send_json(500, {"error": f"handler error: {e}"})
            return

        try:
            envelope = _envelope(type_str, result, key, iv)
        except Exception as e:
            self._send_json(500, {"error": f"encryption failed: {e}"})
            return

        self._send_json(200, envelope)


def main():
    host = os.environ.get("GRIEVANCE_HOST", "127.0.0.1")
    port = int(os.environ.get("GRIEVANCE_PORT", "5691"))
    httpd = HTTPServer((host, port), GrievanceHandler)
    print(f"vistaar_grievance_mock http://{host}:{port}", flush=True)
    print(
        "  endpoints: /GrievanceAadhaarToken  /LodgeGrievance  /GrievanceStatusCheck",
        flush=True,
    )
    httpd.serve_forever()


if __name__ == "__main__":
    main()
