# Inference

Generates model answers by calling a live bot (bharat-oan-api / mh-oan-api-family
`/api/chat/`), so `evaluation/` has something to score. 

Copy `.env.example` to `.env` in this folder and fill in `TOKEN`/`BASE_URL` before
running anything. 

## Scripts

- **`run_text_inference.py`** — single-turn, independent-row inference. Reads a
  benchmark CSV, calls `/api/chat/` per row (per configured language "pass"), writes
  the answer + TTFB/latency back to the output CSV. The general-purpose default.
- **`run_sequential_scenario.py`** — real multi-turn conversations: groups CSV rows by
  `session_id` and sends them in order, so each question is answered in the context of
  the previous ones in that session (server-side history, no simulator). Despite the
  name, not English-specific — point `SCENARIO_INPUT_CSV` at any per-language CSV.
- **`run_simulated_scenario.py`** — same multi-turn idea, but for CSVs with only one
  seed question per session: Gemma plays the farmer and generates realistic follow-ups
  based on the bot's own last answer, for N turns. Gemma never answers the actual
  question, only simulates the next thing a farmer would ask.
- **`run_audio_vs_text_comparison.py`** — for a fixed set of TTS'd questions, runs both
  the text pipeline and the transcribe-then-chat audio pipeline per question, side by
  side, for direct comparison. Needs its `sarvam_tts/` manifest + audio fixture, not
  yet migrated (see below).

All four are async, bounded-concurrency, and take `--base-url`/`--token` (or the `TOKEN`/
`BASE_URL` env vars) the same way. Outputs default into `output/<script>/` —
`output/text_inference/`, `output/sequential_scenario/`, `output/simulated_scenario/`,
`output/audio_vs_text/` — created automatically if missing. **`output/` is always
gitignored**, regardless of which script wrote into it — regenerate by rerunning, don't
commit. Inputs (fixture CSVs like `benchmark_questions.csv`, or a `per_lang_csvs/`
folder you populate yourself) are separate and stay tracked.
