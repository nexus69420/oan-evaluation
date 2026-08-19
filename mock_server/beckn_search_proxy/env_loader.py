"""Load key=value lines from .env files into os.environ (stdlib only).

Load order when BECKN_PROXY_ENV_FILE is unset:
  1. mock_server/.env
  2. mock_server/beckn_search_proxy/.env (optional overrides)

Shell-exported variables are never overwritten. Between files, later file wins in the
merged map, but any key already in os.environ before loading stays as-is.

Does not read bharat-oan-api/.env.
"""
from __future__ import annotations

import os
from pathlib import Path


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines into a dict. Missing file → empty dict."""
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out[key] = val
    return out


def _apply_env_dict(values: dict[str, str]) -> None:
    for key, val in values.items():
        if key not in os.environ:
            os.environ[key] = val


def load_proxy_env(proxy_package_dir: Path) -> list[Path]:
    """
    Populate os.environ from env files.

    If BECKN_PROXY_ENV_FILE is set, only that file is read (must exist to load anything).

    Otherwise reads ``mock_server/.env`` then ``beckn_search_proxy/.env``; keys from
    the second file override the first in the merged map (shell still wins).

    Returns list of paths that existed and were merged (may be empty).
    """
    single = os.environ.get("BECKN_PROXY_ENV_FILE", "").strip()
    if single:
        path = Path(single).expanduser().resolve()
        data = parse_env_file(path)
        if not data:
            return []
        _apply_env_dict(data)
        return [path]

    mock_root = proxy_package_dir.parent
    merged: dict[str, str] = {}
    loaded_paths: list[Path] = []
    for p in (mock_root / ".env", proxy_package_dir / ".env"):
        if p.is_file():
            merged.update(parse_env_file(p))
            loaded_paths.append(p.resolve())
    if merged:
        _apply_env_dict(merged)
    return loaded_paths
