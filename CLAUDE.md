See `/mnt/raid/gautam/oan-brain/MAP.md` for the big picture across all OAN repos, and
`/mnt/raid/gautam/oan-brain/router.md` before starting any ambiguous task.

## This repo specifically

- Aggregate dev branch: `common_evals_dev` (a `bh-eval` remote branch also exists —
  relationship not yet confirmed).
- Python env: always use `/mnt/raid/gautam/python_envs/evals/bin/python3`.
- Run via `orchestrate_eval.py --config <path-to-a-pipeline_config>.py`; see
  `/mnt/raid/gautam/oan-brain/knowledge/bv-quality-eval.md` for a concrete example
  (factual accuracy / answer relevance metrics added here for BharatVistaar).
- Never push without asking first, every time.
