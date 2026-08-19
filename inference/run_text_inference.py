#!/usr/bin/env python3
"""
Stream chat inference over benchmark CSV rows (async, bounded concurrency).

For each configured pass (in order): read input_column as query, call
GET {BASE_URL}/api/chat/ with source_lang / target_lang, write to output_column.

Default order: all English (question_english -> answers_en), then all Hindi
(question_hindi -> answers_hi). Override with --passes-json or --passes-file.

Per pass, also writes TTFT_{output_column} and latency_{output_column} (milliseconds,
e.g. TTFT_answers_en, latency_answers_en).

While running, the output CSV is rewritten every SAVE_INTERVAL_SEC (see top of file).

Env / .env (inf_bh_dev/.env): TOKEN, BASE_URL (optional; CLI wins).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any, NamedTuple

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = ROOT / ".env"

# ---------------------------------------------------------------------------
# Defaults — edit these to set input/output filenames (relative to this folder
# unless you use an absolute path). CLI --input-csv / --output-csv override.
# ---------------------------------------------------------------------------
INPUT_CSV_NAME = "benchmark_questions.csv"
OUTPUT_CSV_NAME = "benchmark_questions_with_answers_gemma_all_langs.csv"
SAVE_INTERVAL_SEC = 30.0
LANGFUSE_WAIT_SEC = 5.0  # seconds to wait after chat response before querying Langfuse

DEFAULT_PASSES: list[dict[str, str]] = [
    {"input_column": "question_english",  "output_column": "answers_en", "source_lang": "en", "target_lang": "en"},
    {"input_column": "question_hindi",    "output_column": "answers_hi", "source_lang": "hi", "target_lang": "hi"},
    {"input_column": "question_marathi",  "output_column": "answers_mr", "source_lang": "mr", "target_lang": "mr"},
    {"input_column": "question_gujarati", "output_column": "answers_gu", "source_lang": "gu", "target_lang": "gu"},
    {"input_column": "question_malayalam","output_column": "answers_ml", "source_lang": "ml", "target_lang": "ml"},
    {"input_column": "question_kannada",  "output_column": "answers_kn", "source_lang": "kn", "target_lang": "kn"},
    {"input_column": "question_tamil",    "output_column": "answers_ta", "source_lang": "ta", "target_lang": "ta"},
    {"input_column": "question_telugu",   "output_column": "answers_te", "source_lang": "te", "target_lang": "te"},
    {"input_column": "question_bengali",  "output_column": "answers_bn", "source_lang": "bn", "target_lang": "bn"},
    {"input_column": "question_odia",     "output_column": "answers_or", "source_lang": "or", "target_lang": "or"},
]


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        out[k] = v
    return out


def apply_env(path: Path) -> None:
    for k, v in parse_env_file(path).items():
        if k not in os.environ:
            os.environ[k] = v


def load_passes(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.passes_file:
        p = Path(args.passes_file).expanduser().resolve()
        data = json.loads(p.read_text(encoding="utf-8"))
    elif args.passes_json:
        data = json.loads(args.passes_json)
    else:
        return list(DEFAULT_PASSES)
    if not isinstance(data, list) or not data:
        raise SystemExit("passes must be a non-empty JSON array")
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            raise SystemExit(f"passes[{i}] must be an object")
        for key in ("input_column", "output_column", "source_lang", "target_lang"):
            if key not in item or not str(item[key]).strip():
                raise SystemExit(f"passes[{i}] missing or empty {key!r}")
    return [dict(x) for x in data]


def assign_question_ids(rows: list[dict[str, Any]]) -> None:
    """Add question_id = '{session_id}-{n}' (1-indexed within each session group)."""
    counters: dict[str, int] = defaultdict(int)
    for row in rows:
        sid = str(row.get("session_id") or "unknown")
        counters[sid] += 1
        row["question_id"] = f"{sid}-{counters[sid]}"


def ttft_column_name(output_column: str) -> str:
    return f"TTFT_{output_column}"


def latency_column_name(output_column: str) -> str:
    return f"latency_{output_column}"


def tool_calls_column_name(output_column: str) -> str:
    return f"tool_calls_{output_column}"


class StreamResult(NamedTuple):
    text: str
    ttft_ms: float
    total_ms: float


async def stream_chat_answer(
    client: httpx.AsyncClient,
    *,
    url: str,
    token: str,
    query: str,
    source_lang: str,
    target_lang: str,
    user_id: str,
    session_id: str,
) -> StreamResult:
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "query": query,
        "source_lang": source_lang,
        "target_lang": target_lang,
        "user_id": user_id,
        "session_id": session_id,
    }
    chunks: list[str] = []
    t_start = time.perf_counter()
    t_first: float | None = None
    async with client.stream("GET", url, headers=headers, params=params, timeout=600.0) as resp:
        async for text in resp.aiter_text():
            if t_first is None:
                t_first = time.perf_counter()
            chunks.append(text)
        body = "".join(chunks)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(
                f"HTTP {e.response.status_code}: {body[:2000]}"
            ) from e
    t_end = time.perf_counter()
    total_ms = (t_end - t_start) * 1000.0
    ttft_ms = (t_first - t_start) * 1000.0 if t_first is not None else total_ms
    return StreamResult(body.strip(), ttft_ms, total_ms)


async def fetch_langfuse_tool_calls(
    client: httpx.AsyncClient,
    *,
    langfuse_base_url: str,
    langfuse_public_key: str,
    langfuse_secret_key: str,
    session_id: str,
    wait_sec: float = LANGFUSE_WAIT_SEC,
) -> list[dict[str, Any]]:
    """Wait for Langfuse flush, get latest trace for session_id, return its tool calls."""
    await asyncio.sleep(wait_sec)
    auth = (langfuse_public_key, langfuse_secret_key)
    try:
        resp = await client.get(
            f"{langfuse_base_url}/api/public/traces",
            params={"sessionId": session_id, "limit": 1},
            auth=auth,
            timeout=30.0,
        )
        resp.raise_for_status()
        traces = resp.json().get("data", [])
        if not traces:
            return []
        trace_id = traces[0]["id"]

        resp2 = await client.get(
            f"{langfuse_base_url}/api/public/observations",
            params={"traceId": trace_id, "type": "TOOL"},
            auth=auth,
            timeout=30.0,
        )
        resp2.raise_for_status()
        observations = resp2.json().get("data", [])

        # Fetch full detail for each tool observation to get input/output
        async def fetch_one(obs: dict[str, Any]) -> dict[str, Any]:
            obs_id = obs.get("id", "")
            try:
                r = await client.get(
                    f"{langfuse_base_url}/api/public/observations/{obs_id}",
                    auth=auth,
                    timeout=30.0,
                )
                r.raise_for_status()
                full = r.json()
                return {
                    "name": full.get("name", ""),
                    "latency_ms": round((full.get("latency") or 0) * 1000, 1),
                    "input": full.get("input"),
                    "output": full.get("output"),
                    "trace_id": trace_id,
                    "observation_id": obs_id,
                }
            except Exception as e:
                return {
                    "name": obs.get("name", ""),
                    "latency_ms": round((obs.get("latency") or 0) * 1000, 1),
                    "error": str(e),
                    "trace_id": trace_id,
                    "observation_id": obs_id,
                }

        return list(await asyncio.gather(*(fetch_one(obs) for obs in observations)))
    except Exception as e:
        return [{"error": str(e)}]


async def run_pass(
    *,
    rows: list[dict[str, Any]],
    pass_cfg: dict[str, str],
    client: httpx.AsyncClient,
    url: str,
    token: str,
    user_id: str,
    run_uuid: str,
    pass_slug: str,
    concurrency: int,
    rows_lock: asyncio.Lock,
    langfuse_base_url: str = "",
    langfuse_public_key: str = "",
    langfuse_secret_key: str = "",
    langfuse_wait_sec: float = LANGFUSE_WAIT_SEC,
) -> None:
    in_col = pass_cfg["input_column"]
    out_col = pass_cfg["output_column"]
    ttft_col = ttft_column_name(out_col)
    lat_col = latency_column_name(out_col)
    tool_col = tool_calls_column_name(out_col)
    src = pass_cfg["source_lang"]
    tgt = pass_cfg["target_lang"]
    lf_enabled = bool(langfuse_base_url and langfuse_public_key and langfuse_secret_key)

    sem = asyncio.Semaphore(concurrency)

    async def one(row_index: int, row: dict[str, Any]) -> None:
        q = (row.get(in_col) or "").strip()
        base_sid = str(row.get("session_id") or f"unknown-{row_index}")
        # uuid isolates this run from prior runs; lang isolates EN from HI
        question_id = f"{run_uuid}_{tgt}_{base_sid}"
        if not q:
            async with rows_lock:
                row[out_col] = ""
                row[ttft_col] = ""
                row[lat_col] = ""
                row[tool_col] = ""
            print(f"  row {row_index} [{question_id}]: skip empty {in_col!r}")
            return
        try:
            async with sem:
                res = await stream_chat_answer(
                    client,
                    url=url,
                    token=token,
                    query=q,
                    source_lang=src,
                    target_lang=tgt,
                    user_id=user_id,
                    session_id=question_id,
                )
            async with rows_lock:
                row[out_col] = res.text
                row[ttft_col] = f"{res.ttft_ms:.2f}"
                row[lat_col] = f"{res.total_ms:.2f}"
            preview = res.text.replace("\n", " ")[:120]
            print(
                f"  row {row_index} [{question_id}]: ok ({len(res.text)} chars, "
                f"TTFT={res.ttft_ms:.0f}ms total={res.total_ms:.0f}ms) :: {preview!r}"
            )
            if lf_enabled:
                # Langfuse fetch runs after releasing the semaphore — doesn't block other requests
                tool_calls = await fetch_langfuse_tool_calls(
                    client,
                    langfuse_base_url=langfuse_base_url,
                    langfuse_public_key=langfuse_public_key,
                    langfuse_secret_key=langfuse_secret_key,
                    session_id=question_id,
                    wait_sec=langfuse_wait_sec,
                )
                async with rows_lock:
                    row[tool_col] = json.dumps(tool_calls, ensure_ascii=False)
                tool_names = [t.get("name", "") for t in tool_calls if "name" in t]
                print(f"  row {row_index} [{question_id}]: tools={tool_names}")
        except Exception as e:
            async with rows_lock:
                row[out_col] = f"ERROR: {e}"
                row[ttft_col] = ""
                row[lat_col] = ""
                row[tool_col] = ""
            print(f"  row {row_index} [{question_id}]: FAIL {e!r}")

    await asyncio.gather(*(one(i, row) for i, row in enumerate(rows)))


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fieldnames = list(r.fieldnames or [])
        rows = [dict(x) for x in r]
    return fieldnames, rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def count_filled_answer_cells(rows: list[dict[str, Any]], passes: list[dict[str, str]]) -> int:
    cols = [p["output_column"] for p in passes]
    n = 0
    for row in rows:
        for c in cols:
            v = (row.get(c) or "").strip()
            if v:
                n += 1
    return n


async def async_main(args: argparse.Namespace) -> None:
    load_dotenv(DEFAULT_ENV)
    apply_env(DEFAULT_ENV)

    token = (args.token or os.environ.get("TOKEN", "")).strip()
    if not token:
        print("Set TOKEN in env or inf_bh_dev/.env, or pass --token", file=sys.stderr)
        raise SystemExit(1)

    base = (args.base_url or os.environ.get("BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    url = f"{base}/api/chat/"
    passes = load_passes(args)

    langfuse_base_url = (
        args.langfuse_base_url
        or os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or ""
    ).rstrip("/")
    langfuse_public_key = args.langfuse_public_key or os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key = args.langfuse_secret_key or os.environ.get("LANGFUSE_SECRET_KEY", "")
    langfuse_enabled = bool(langfuse_base_url and langfuse_public_key and langfuse_secret_key)

    input_path = Path(args.input_csv).expanduser().resolve()
    output_path = Path(args.output_csv).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames, rows = read_csv_rows(input_path)

    if args.max_rows is not None:
        rows = rows[: max(0, args.max_rows)]

    # question_id is pre-assigned in the CSV; fill any missing ones defensively
    if "question_id" not in fieldnames:
        insert_at = fieldnames.index("session_id") + 1 if "session_id" in fieldnames else 0
        fieldnames.insert(insert_at, "question_id")
        assign_question_ids(rows)

    for p in passes:
        oc = p["output_column"]
        for col in (oc, ttft_column_name(oc), latency_column_name(oc), tool_calls_column_name(oc)):
            if col not in fieldnames:
                fieldnames.append(col)

    run_uuid = uuid.uuid4().hex[:8]  # short 8-char hex, unique per run

    print(f"GET {url}")
    print(f"run_uuid={run_uuid} rows={len(rows)} concurrency={args.concurrency} passes={len(passes)}")
    print(f"Langfuse: {'enabled (' + langfuse_base_url + ')' if langfuse_enabled else 'disabled (set LANGFUSE_* env vars to enable)'}")
    if args.save_interval_sec > 0:
        print(f"periodic save every {args.save_interval_sec}s -> {output_path}")
    else:
        print("periodic save disabled (--save-interval-sec 0); only final write at end")
    for i, p in enumerate(passes):
        print(
            f"  pass {i}: {p['input_column']} -> {p['output_column']} "
            f"({p['source_lang']}/{p['target_lang']})"
        )

    rows_lock = asyncio.Lock()
    total_cells = len(rows) * len(passes)

    async def periodic_saver() -> None:
        try:
            while True:
                await asyncio.sleep(args.save_interval_sec)
                async with rows_lock:
                    write_csv(output_path, fieldnames, rows)
                    filled = count_filled_answer_cells(rows, passes)
                print(
                    f"[checkpoint {time.strftime('%H:%M:%S')}] "
                    f"wrote {output_path} — answer cells filled {filled}/{total_cells}"
                )
        except asyncio.CancelledError:
            async with rows_lock:
                write_csv(output_path, fieldnames, rows)
                filled = count_filled_answer_cells(rows, passes)
            print(
                f"[checkpoint {time.strftime('%H:%M:%S')}] "
                f"final periodic write {output_path} — answer cells filled {filled}/{total_cells}"
            )
            raise

    save_task: asyncio.Task[None] | None = None
    if args.save_interval_sec > 0:
        save_task = asyncio.create_task(periodic_saver())

    async with rows_lock:
        write_csv(output_path, fieldnames, rows)
    print(f"Initial template -> {output_path}")

    limits = httpx.Limits(max_keepalive_connections=args.concurrency + 4, max_connections=args.concurrency + 4)
    try:
        async with httpx.AsyncClient(limits=limits) as client:
            for i, p in enumerate(passes):
                slug = f"p{i}-{p['source_lang']}{p['target_lang']}"
                print(f"\n=== pass {i}/{len(passes)} {slug} ===")
                await run_pass(
                    rows=rows,
                    pass_cfg=p,
                    client=client,
                    url=url,
                    token=token,
                    user_id=args.user_id,
                    run_uuid=run_uuid,
                    pass_slug=slug,
                    concurrency=args.concurrency,
                    rows_lock=rows_lock,
                    langfuse_base_url=langfuse_base_url,
                    langfuse_public_key=langfuse_public_key,
                    langfuse_secret_key=langfuse_secret_key,
                    langfuse_wait_sec=args.langfuse_wait_sec,
                )
    finally:
        if save_task is not None:
            save_task.cancel()
            try:
                await save_task
            except asyncio.CancelledError:
                pass

    async with rows_lock:
        write_csv(output_path, fieldnames, rows)
    filled = count_filled_answer_cells(rows, passes)
    print(f"\nWrote final {output_path} (answer cells {filled}/{total_cells})")


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run streaming /api/chat/ over CSV benchmark rows.")
    ap.add_argument("--input-csv", default=str(ROOT / INPUT_CSV_NAME))
    ap.add_argument("--output-csv", default=str(ROOT / "output" / "text_inference" / OUTPUT_CSV_NAME))
    ap.add_argument(
        "--save-interval-sec",
        type=float,
        default=SAVE_INTERVAL_SEC,
        help="rewrite output CSV on this interval while running (0 disables periodic save)",
    )
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", ""), help="API base, e.g. http://localhost:8000")
    ap.add_argument("--token", default=os.environ.get("TOKEN", ""), help="JWT (default: env TOKEN)")
    ap.add_argument("--user-id", default="benchmark-user")
    ap.add_argument("--concurrency", type=int, default=5, help="parallel in-flight requests per pass")
    ap.add_argument("--langfuse-base-url", default="", help="Langfuse base URL (default: env LANGFUSE_BASE_URL)")
    ap.add_argument("--langfuse-public-key", default="", help="Langfuse public key (default: env LANGFUSE_PUBLIC_KEY)")
    ap.add_argument("--langfuse-secret-key", default="", help="Langfuse secret key (default: env LANGFUSE_SECRET_KEY)")
    ap.add_argument(
        "--langfuse-wait-sec",
        type=float,
        default=LANGFUSE_WAIT_SEC,
        help="seconds to wait after chat response before querying Langfuse (default: 5)",
    )
    ap.add_argument(
        "--passes-json",
        default="",
        help='JSON array of passes, e.g. \'[{"input_column":"q_en","output_column":"a_en","source_lang":"en","target_lang":"en"}]\'',
    )
    ap.add_argument("--passes-file", default="", help="Path to JSON file (same schema as --passes-json)")
    ap.add_argument("--max-rows", type=int, default=None, help="only first N rows (smoke / debug)")
    ap.add_argument(
        "--smoke-test",
        action="store_true",
        help="single GET with a fixed Hindi query; does not read CSV",
    )
    return ap


async def smoke_test(args: argparse.Namespace) -> None:
    load_dotenv(DEFAULT_ENV)
    apply_env(DEFAULT_ENV)
    token = (args.token or os.environ.get("TOKEN", "")).strip()
    if not token:
        raise SystemExit("TOKEN required")
    base = (args.base_url or os.environ.get("BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    url = f"{base}/api/chat/"
    q = "गेहूं में पीला रतुआ का इलाज क्या है?"
    limits = httpx.Limits(max_keepalive_connections=2, max_connections=2)
    async with httpx.AsyncClient(limits=limits) as client:
        res = await stream_chat_answer(
            client,
            url=url,
            token=token,
            query=q,
            source_lang="hi",
            target_lang="hi",
            user_id=args.user_id,
            session_id="smoke-session-1",
        )
    print(f"TTFT={res.ttft_ms:.2f} ms  total_latency={res.total_ms:.2f} ms")
    print("--- smoke response (first 2000 chars) ---")
    print(res.text[:2000])
    if len(res.text) > 2000:
        print(f"\n... ({len(res.text)} total chars)")


def main() -> None:
    ap = build_argparser()
    args = ap.parse_args()
    if args.smoke_test:
        asyncio.run(smoke_test(args))
    else:
        asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
