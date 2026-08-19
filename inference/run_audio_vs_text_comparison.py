#!/usr/bin/env python3
"""
Compare text-input vs audio-input inference over the 50 TTS'd benchmark questions
(sarvam_tts/, driven by sarvam_tts/manifest.csv — 50 questions x 10 languages).

For each (question_id, lang_code) row in manifest.csv, runs two pipelines:
  text  : GET  {BASE_URL}/api/chat/       with query = manifest text
  audio : POST {BASE_URL}/api/transcribe/ (service_type=gemma4) on the wav file,
          then GET {BASE_URL}/api/chat/   with query = the resulting transcript

Writes one output row per (question_id, lang_code) with both pipelines' answers,
transcript, and latencies side by side for direct comparison.

Env / .env (inf_bh_dev/.env): TOKEN, BASE_URL (optional; CLI wins).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any, NamedTuple

import httpx
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

ROOT = Path(__file__).resolve().parent
DEFAULT_ENV = ROOT / ".env"
MANIFEST_CSV = ROOT / "sarvam_tts" / "manifest.csv"
OUTPUT_CSV_NAME = "audio_vs_text_benchmark_results.csv"
SAVE_INTERVAL_SEC = 30.0

OUTPUT_FIELDNAMES = [
    "session_id", "question_id", "category", "lang_code", "question_text",
    "text_answer", "text_ttft_ms", "text_latency_ms",
    "audio_transcript", "audio_asr_latency_ms",
    "audio_answer", "audio_ttft_ms", "audio_latency_ms", "audio_total_latency_ms",
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


class StreamResult(NamedTuple):
    text: str
    ttft_ms: float
    total_ms: float


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError)),
)
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
            raise RuntimeError(f"HTTP {e.response.status_code}: {body[:2000]}") from e
    t_end = time.perf_counter()
    total_ms = (t_end - t_start) * 1000.0
    ttft_ms = (t_first - t_start) * 1000.0 if t_first is not None else total_ms
    return StreamResult(body.strip(), ttft_ms, total_ms)


class TranscribeResult(NamedTuple):
    text: str
    latency_ms: float


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError)),
)
async def transcribe_gemma4(
    client: httpx.AsyncClient,
    *,
    url: str,
    token: str,
    audio_path: Path,
    session_id: str,
) -> TranscribeResult:
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"audio_content": audio_b64, "service_type": "gemma4", "session_id": session_id}
    t_start = time.perf_counter()
    resp = await client.post(url, headers=headers, json=payload, timeout=120.0)
    resp.raise_for_status()
    data = resp.json()
    total_ms = (time.perf_counter() - t_start) * 1000.0
    return TranscribeResult((data.get("text") or "").strip(), total_ms)


def read_manifest(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def count_filled(rows: list[dict[str, Any]]) -> int:
    return sum(1 for r in rows if (r.get("text_answer") or "").strip() and (r.get("audio_answer") or "").strip())


async def run_one(
    manifest_row: dict[str, Any],
    *,
    out_row: dict[str, Any],
    chat_client: httpx.AsyncClient,
    asr_client: httpx.AsyncClient,
    chat_url: str,
    transcribe_url: str,
    token: str,
    user_id: str,
    run_uuid: str,
    sem: asyncio.Semaphore,
) -> None:
    qid = manifest_row["question_id"]
    lang = manifest_row["lang_code"]
    question_text = manifest_row["text"]
    audio_path = Path(manifest_row["file"])
    label = f"{qid}/{lang}"

    async with sem:
        # --- text pipeline ---
        try:
            text_session = f"{run_uuid}_{lang}_{qid}_text"
            res = await stream_chat_answer(
                chat_client, url=chat_url, token=token, query=question_text,
                source_lang=lang, target_lang=lang, user_id=user_id, session_id=text_session,
            )
            out_row["text_answer"] = res.text
            out_row["text_ttft_ms"] = f"{res.ttft_ms:.2f}"
            out_row["text_latency_ms"] = f"{res.total_ms:.2f}"
            print(f"  [{label}] text: ok ({len(res.text)} chars, {res.total_ms:.0f}ms)")
        except Exception as e:
            out_row["text_answer"] = f"ERROR: {e}"
            print(f"  [{label}] text: FAIL {e!r}")

        # --- audio pipeline: ASR then chat ---
        try:
            asr_session = f"{run_uuid}_{lang}_{qid}_asr"
            asr_res = await transcribe_gemma4(
                asr_client, url=transcribe_url, token=token, audio_path=audio_path, session_id=asr_session,
            )
            out_row["audio_transcript"] = asr_res.text
            out_row["audio_asr_latency_ms"] = f"{asr_res.latency_ms:.2f}"
            print(f"  [{label}] asr: ok ({asr_res.latency_ms:.0f}ms) :: {asr_res.text[:80]!r}")

            audio_session = f"{run_uuid}_{lang}_{qid}_audio"
            chat_res = await stream_chat_answer(
                chat_client, url=chat_url, token=token, query=asr_res.text,
                source_lang=lang, target_lang=lang, user_id=user_id, session_id=audio_session,
            )
            out_row["audio_answer"] = chat_res.text
            out_row["audio_ttft_ms"] = f"{chat_res.ttft_ms:.2f}"
            out_row["audio_latency_ms"] = f"{chat_res.total_ms:.2f}"
            out_row["audio_total_latency_ms"] = f"{asr_res.latency_ms + chat_res.total_ms:.2f}"
            print(f"  [{label}] audio: ok ({len(chat_res.text)} chars, {chat_res.total_ms:.0f}ms)")
        except Exception as e:
            out_row["audio_answer"] = f"ERROR: {e}"
            print(f"  [{label}] audio: FAIL {e!r}")


async def async_main(args: argparse.Namespace) -> None:
    load_dotenv(DEFAULT_ENV)
    apply_env(DEFAULT_ENV)

    token = (args.token or os.environ.get("TOKEN", "")).strip()
    if not token:
        print("Set TOKEN in env or inf_bh_dev/.env, or pass --token", file=sys.stderr)
        raise SystemExit(1)

    base = (args.base_url or os.environ.get("BASE_URL", "http://127.0.0.1:8000")).rstrip("/")
    chat_url = f"{base}/api/chat/"
    transcribe_url = f"{base}/api/transcribe/"

    manifest_rows = read_manifest(Path(args.manifest_csv))
    if args.languages:
        wanted = {l.strip().lower() for l in args.languages.split(",")}
        manifest_rows = [r for r in manifest_rows if r["lang_code"] in wanted]
    if args.max_rows is not None:
        manifest_rows = manifest_rows[: max(0, args.max_rows)]

    out_rows: list[dict[str, Any]] = []
    for r in manifest_rows:
        out_rows.append({
            "session_id": r["session_id"], "question_id": r["question_id"],
            "category": r["category"], "lang_code": r["lang_code"], "question_text": r["text"],
            "text_answer": "", "text_ttft_ms": "", "text_latency_ms": "",
            "audio_transcript": "", "audio_asr_latency_ms": "",
            "audio_answer": "", "audio_ttft_ms": "", "audio_latency_ms": "", "audio_total_latency_ms": "",
        })

    output_path = Path(args.output_csv).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_uuid = uuid.uuid4().hex[:8]

    print(f"chat_url={chat_url} transcribe_url={transcribe_url}")
    print(f"run_uuid={run_uuid} rows={len(out_rows)} concurrency={args.concurrency}")
    print(f"output -> {output_path}")

    rows_lock = asyncio.Lock()

    async def periodic_saver() -> None:
        try:
            while True:
                await asyncio.sleep(args.save_interval_sec)
                async with rows_lock:
                    write_csv(output_path, OUTPUT_FIELDNAMES, out_rows)
                    filled = count_filled(out_rows)
                print(f"[checkpoint {time.strftime('%H:%M:%S')}] wrote {output_path} — {filled}/{len(out_rows)} rows complete")
        except asyncio.CancelledError:
            async with rows_lock:
                write_csv(output_path, OUTPUT_FIELDNAMES, out_rows)
            raise

    save_task: asyncio.Task[None] | None = None
    if args.save_interval_sec > 0:
        save_task = asyncio.create_task(periodic_saver())

    write_csv(output_path, OUTPUT_FIELDNAMES, out_rows)

    sem = asyncio.Semaphore(args.concurrency)
    limits = httpx.Limits(max_keepalive_connections=args.concurrency + 4, max_connections=args.concurrency + 4)
    # Separate clients for streaming chat (GET) vs one-shot transcribe (POST) —
    # interleaving both request types on one httpx connection pool causes the
    # server to close a reused keep-alive connection mid-stream on a later
    # chat call (reproduced: chat -> transcribe -> chat fails; either pair alone is fine).
    try:
        async with httpx.AsyncClient(limits=limits) as chat_client, httpx.AsyncClient(limits=limits) as asr_client:
            await asyncio.gather(*(
                run_one(
                    r, out_row=out_rows[i], chat_client=chat_client, asr_client=asr_client, chat_url=chat_url,
                    transcribe_url=transcribe_url, token=token, user_id=args.user_id,
                    run_uuid=run_uuid, sem=sem,
                )
                for i, r in enumerate(manifest_rows)
            ))
    finally:
        if save_task is not None:
            save_task.cancel()
            try:
                await save_task
            except asyncio.CancelledError:
                pass

    write_csv(output_path, OUTPUT_FIELDNAMES, out_rows)
    filled = count_filled(out_rows)
    print(f"\nWrote final {output_path} ({filled}/{len(out_rows)} rows complete)")


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Compare text vs audio-input inference over sarvam_tts benchmark questions.")
    ap.add_argument("--manifest-csv", default=str(MANIFEST_CSV))
    ap.add_argument("--output-csv", default=str(ROOT / "output" / "audio_vs_text" / OUTPUT_CSV_NAME))
    ap.add_argument("--save-interval-sec", type=float, default=SAVE_INTERVAL_SEC)
    ap.add_argument("--base-url", default=os.environ.get("BASE_URL", ""))
    ap.add_argument("--token", default=os.environ.get("TOKEN", ""))
    ap.add_argument("--user-id", default="benchmark-user")
    ap.add_argument("--concurrency", type=int, default=5)
    ap.add_argument("--languages", default="", help="comma-separated lang codes to include (default: all in manifest)")
    ap.add_argument("--max-rows", type=int, default=None, help="only first N manifest rows (debug)")
    return ap


def main() -> None:
    args = build_argparser().parse_args()
    asyncio.run(async_main(args))


if __name__ == "__main__":
    main()
