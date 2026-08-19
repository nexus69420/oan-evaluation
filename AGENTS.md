Read `/mnt/raid/gautam/oan-brain/router.md` and `/mnt/raid/gautam/oan-brain/MAP.md` before
starting any ambiguous task — they're the shared source of truth across every tool
pointed at this codebase (same content Claude Code gets from `CLAUDE.md` here).

## Hard rules — restated explicitly here because this tool has no built-in equivalent

- **Never `git push` or commit anything remotely without asking the user first, every
  single time, no exceptions.**
- Never write repo secrets (`.git/config`, `.env*` contents, tokens) into
  `/mnt/raid/gautam/oan-brain/` or anywhere outside this repo.

## This repo specifically

- Aggregate dev branch: `common_evals_dev` (a `bh-eval` remote branch also exists —
  relationship not yet confirmed).
- Python env: always use `/mnt/raid/gautam/python_envs/evals/bin/python3`.
- Run via `orchestrate_eval.py --config <path-to-a-pipeline_config>.py`; see
  `/mnt/raid/gautam/oan-brain/knowledge/bv-quality-eval.md` for a concrete example.
