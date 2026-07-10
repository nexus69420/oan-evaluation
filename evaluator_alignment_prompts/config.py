"""
config.py — Central, environment-driven configuration for the DSPy
evaluator-alignment tuning pipeline.

Every path, model, and CSV column name can be overridden via an
environment variable (or a .env file — copy .env.example to .env and
edit it). Nothing here is hardcoded to a specific project; the defaults
are safe, generic starting points.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────────────────────────────
# Env-var helpers
# ─────────────────────────────────────────────────────────────────────
def _env_str(name: str, default: str) -> str:
    val = os.environ.get(name)
    return val if val not in (None, "") else default


def _env_opt_str(name: str, default: Optional[str]) -> Optional[str]:
    val = os.environ.get(name)
    if val is None:
        return default
    return val or None


def _env_int(name: str, default: int) -> int:
    val = os.environ.get(name)
    return int(val) if val else default


def _env_float(name: str, default: float) -> float:
    val = os.environ.get(name)
    return float(val) if val else default


def _env_path(name: str, default: Path) -> Path:
    val = os.environ.get(name)
    return Path(val) if val else default


# ─────────────────────────────────────────────────────────────────────
# Input data — 3 pre-split CSVs (train / val / test)
# ─────────────────────────────────────────────────────────────────────
TRAIN_CSV = _env_path("TRAIN_CSV", REPO_ROOT / "data" / "train.csv")
VAL_CSV   = _env_path("VAL_CSV",   REPO_ROOT / "data" / "val.csv")
TEST_CSV  = _env_path("TEST_CSV",  REPO_ROOT / "data" / "test.csv")

# CSV column names — override these if your CSV uses different headers.
# Only COL_QUESTION, COL_RESPONSE, and COL_SCORE are required; the rest
# are optional and degrade gracefully if the column is absent.
COL_QUESTION   = _env_str("COL_QUESTION",   "question")
COL_CONTEXT    = _env_str("COL_CONTEXT",    "context")
COL_RESPONSE   = _env_str("COL_RESPONSE",   "agent_response")
COL_SCORE      = _env_str("COL_SCORE",      "human_score")
COL_NOTES      = _env_str("COL_NOTES",      "human_notes")
COL_VERDICT    = _env_str("COL_VERDICT",    "verdict")
COL_CONFIDENCE = _env_str("COL_CONFIDENCE", "confidence")

# Score range used in your CSVs (e.g. 1-4, 1-5, 0-10). Must match your data.
SCORE_MIN = _env_int("SCORE_MIN", 1)
SCORE_MAX = _env_int("SCORE_MAX", 4)

# ─────────────────────────────────────────────────────────────────────
# Output folders / files
# ─────────────────────────────────────────────────────────────────────
ARTIFACTS_DIR         = _env_path("ARTIFACTS_DIR", REPO_ROOT / "artifacts")
OPTIMIZED_PROMPTS_DIR = _env_path("OPTIMIZED_PROMPTS_DIR", REPO_ROOT / "optimized_prompts")
OPTIMIZED_PROMPT_OUT  = _env_path("LATEST_PROMPT_PATH", OPTIMIZED_PROMPTS_DIR / "latest.md")
PROMPT_REGISTRY_FILE  = _env_path("PROMPT_REGISTRY_FILE", ARTIFACTS_DIR / "prompt_registry.json")

# ─────────────────────────────────────────────────────────────────────
# ★ Baseline judge prompt — the starting point the optimizer improves.
#   Point this at your own rubric file to start from something other
#   than the bundled generic default.
# ─────────────────────────────────────────────────────────────────────
EVAL_SYSTEM_PROMPT = _env_path(
    "BASELINE_PROMPT_PATH", REPO_ROOT / "prompts" / "evaluation_system_baseline.md"
)

# ─────────────────────────────────────────────────────────────────────
# Per-metric fine-tuning (train_metrics.py / promote_metrics.py).
# Each metric (accuracy_completeness, citation_accuracy, ...) gets its own
# narrow prompt file under METRICS_DIR, registered in metrics_config.json
# with its own CSV score/notes columns and score range.
# ─────────────────────────────────────────────────────────────────────
METRICS_DIR           = _env_path("METRICS_DIR", REPO_ROOT / "prompts" / "metrics")
METRICS_CONFIG_FILE   = _env_path("METRICS_CONFIG_FILE", METRICS_DIR / "metrics_config.json")
METRICS_ARCHIVE_DIR   = _env_path("METRICS_ARCHIVE_DIR", METRICS_DIR / "archive")
METRICS_OPTIMIZED_DIR = _env_path("METRICS_OPTIMIZED_DIR", OPTIMIZED_PROMPTS_DIR / "metrics")
METRICS_ARTIFACTS_DIR = _env_path("METRICS_ARTIFACTS_DIR", ARTIFACTS_DIR / "metrics")
METRICS_REGISTRY_FILE = _env_path("METRICS_REGISTRY_FILE", METRICS_ARTIFACTS_DIR / "metric_prompt_registry.json")

# ─────────────────────────────────────────────────────────────────────
# Judge LLM — the model being calibrated (scores agent_response).
# For a self-hosted / vLLM endpoint, set JUDGE_API_BASE and point
# JUDGE_MODEL at the OpenAI-compatible model id (e.g. "openai/<model>").
# ─────────────────────────────────────────────────────────────────────
JUDGE_MODEL              = _env_str("JUDGE_MODEL", "openai/gpt-4o-mini")
JUDGE_API_BASE           = _env_opt_str("JUDGE_API_BASE", None)
JUDGE_MAX_TOKENS         = _env_int("JUDGE_MAX_TOKENS", 4_000)
JUDGE_API_KEY_ENV        = _env_str("JUDGE_API_KEY_ENV", "OPENAI_API_KEY")  # name of the env var holding the key
JUDGE_INPUT_COST_PER_1M  = _env_float("JUDGE_INPUT_COST_PER_1M", 0.15)
JUDGE_OUTPUT_COST_PER_1M = _env_float("JUDGE_OUTPUT_COST_PER_1M", 0.60)

# ─────────────────────────────────────────────────────────────────────
# Prompt optimizer model — proposes candidate instruction rewrites
# (COPRO's prompt_model). Deliberately a DIFFERENT model than JUDGE_MODEL:
# the model being calibrated shouldn't also grade its own rewrite.
# Set OPTIMIZER_MODEL="" to disable and fall back to self-optimization.
# ─────────────────────────────────────────────────────────────────────
OPTIMIZER_MODEL       = _env_opt_str("OPTIMIZER_MODEL", "openai/gpt-4o-mini")
OPTIMIZER_API_KEY_ENV = _env_str("OPTIMIZER_API_KEY_ENV", "OPENAI_API_KEY")

# ─────────────────────────────────────────────────────────────────────
# Dataset size caps — keep optimization cost predictable.
# Set to 0 to disable a cap (use the full CSV).
# ─────────────────────────────────────────────────────────────────────
MAX_TRAIN = _env_int("MAX_TRAIN", 80)
MAX_VAL   = _env_int("MAX_VAL", 30)
MAX_TEST  = _env_int("MAX_TEST", 30)

# ─────────────────────────────────────────────────────────────────────
# Agreement metric weights — how the composite score is built from
# component metrics (see metric.py). Should sum to ~1.0.
# ─────────────────────────────────────────────────────────────────────
AGREEMENT_WEIGHTS: Dict[str, float] = {
    "exact_match":              _env_float("WEIGHT_EXACT_MATCH", 0.20),
    "mae_normalized":           _env_float("WEIGHT_MAE", 0.30),
    "adjacent_match":           _env_float("WEIGHT_ADJACENT_MATCH", 0.20),
    "quadratic_weighted_kappa": _env_float("WEIGHT_QWK", 0.30),
}

# ─────────────────────────────────────────────────────────────────────
# COPRO optimizer settings (Stage 1 — instruction rewriting)
# ─────────────────────────────────────────────────────────────────────
COPRO_BREADTH   = _env_int("COPRO_BREADTH", 4)
COPRO_DEPTH     = _env_int("COPRO_DEPTH", 3)
COPRO_INIT_TEMP = _env_float("COPRO_INIT_TEMP", 0.7)

# MIPROv2 (optional Stage 3 — joint instruction + demo search)
MIPRO_NUM_CANDIDATES = _env_int("MIPRO_NUM_CANDIDATES", 10)
MIPRO_NUM_TRIALS     = _env_int("MIPRO_NUM_TRIALS", 20)
MIPRO_INIT_TEMP      = _env_float("MIPRO_INIT_TEMP", 1.0)

# BootstrapFewShot (Stage 2 — few-shot demo selection)
BFS_MAX_BOOTSTRAPPED = _env_int("BFS_MAX_BOOTSTRAPPED", 8)
BFS_MAX_LABELED       = _env_int("BFS_MAX_LABELED", 4)

# Parallel threads for DSPy evaluation calls
NUM_THREADS = _env_int("NUM_THREADS", 4)


@dataclass
class AlignmentConfig:
    """Runtime configuration snapshot — override any field from the CLI or code."""

    judge_model: str                    = JUDGE_MODEL
    judge_api_base: Optional[str]       = JUDGE_API_BASE
    judge_max_tokens: int               = JUDGE_MAX_TOKENS
    judge_api_key_env: str              = JUDGE_API_KEY_ENV
    optimizer_model: Optional[str]      = OPTIMIZER_MODEL
    optimizer_api_key_env: str          = OPTIMIZER_API_KEY_ENV
    judge_input_cost_per_1m: float      = JUDGE_INPUT_COST_PER_1M
    judge_output_cost_per_1m: float     = JUDGE_OUTPUT_COST_PER_1M
    max_train: int                      = MAX_TRAIN
    max_val: int                        = MAX_VAL
    max_test: int                       = MAX_TEST
    agreement_weights: Dict[str, float] = field(default_factory=lambda: dict(AGREEMENT_WEIGHTS))
    score_min: int                      = SCORE_MIN
    score_max: int                      = SCORE_MAX
    copro_breadth: int                  = COPRO_BREADTH
    copro_depth: int                    = COPRO_DEPTH
    copro_init_temp: float              = COPRO_INIT_TEMP
    num_threads: int                    = NUM_THREADS
    artifacts_dir: Path                 = ARTIFACTS_DIR
    optimized_prompts_dir: Path         = OPTIMIZED_PROMPTS_DIR
    optimized_prompt_out: Path          = OPTIMIZED_PROMPT_OUT
    metrics_dir: Path                   = METRICS_DIR
    metrics_config_file: Path           = METRICS_CONFIG_FILE
    metrics_archive_dir: Path           = METRICS_ARCHIVE_DIR
    metrics_optimized_dir: Path         = METRICS_OPTIMIZED_DIR
    metrics_artifacts_dir: Path         = METRICS_ARTIFACTS_DIR
    metrics_registry_file: Path         = METRICS_REGISTRY_FILE

    def __post_init__(self):
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.optimized_prompts_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_optimized_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_archive_dir.mkdir(parents=True, exist_ok=True)
