"""
optimizer.py — DSPy optimizer selection, configuration, and execution.

Optimizer Comparison & Recommendation
═══════════════════════════════════════

+-------------------------------┬----------------------------------------------┬------------------┬-----------------------------------------------------┐
| Optimizer                     | How it works                                 | Cost             | Suitability for evaluator alignment                 |
+-------------------------------┼----------------------------------------------┼------------------┼-----------------------------------------------------┤
| BootstrapFewShot              | Auto-generates few-shot demos from trainset. | Low              | Good start; adds calibration examples to prompt.    |
|                               | No instruction mutation.                     |                  | Does NOT refine rubric wording.                      |
+-------------------------------┼----------------------------------------------┼------------------┼-----------------------------------------------------┤
| BootstrapFewShotWithRandom-   | BFS + random search over subsets of demos.  | Medium           | Better than BFS alone; still no instruction edit.   |
| Search                        |                                              |                  |                                                     |
+-------------------------------┼----------------------------------------------┼------------------┼-----------------------------------------------------┤
| COPRO                         | LLM proposes new instruction candidates;     | Medium-High      | * Strong for evaluator prompts: directly mutates    |
|                               | hill-climbs on validation metric.            | (breadth×depth   |   the rubric wording. Fast convergence on ~30-80    |
|                               | Keeps best-scoring instruction at each depth.| LLM calls)       |   examples. Primary choice.                          |
+-------------------------------┼----------------------------------------------┼------------------┼-----------------------------------------------------┤
| MIPROv2                       | Generates instructions AND few-shot demos    | High             | ** Best quality ceiling: optimizes both rubric AND  |
|                               | jointly via Bayesian search (optuna).        | (num_trials ×    |   exemplars. Use when COPRO plateaus. Requires 50+  |
|                               | Multi-stage: propose -> select -> compile.    |  inference calls) |   examples.                                         |
+-------------------------------┴----------------------------------------------┴------------------┴-----------------------------------------------------┘

RECOMMENDATION: Two-stage strategy
----------------------------------
  Stage 1 — COPRO (fast, cheap, targets rubric wording)
    -> Starts from the baseline prompt (config.EVAL_SYSTEM_PROMPT)
    -> Optimizes instruction to reduce human-LLM score gap
    -> Output: stage1_copro.json + improved instruction string

  Stage 2 — BootstrapFewShot on top of Stage 1 output
    -> Takes the COPRO-refined instruction
    -> Selects best training examples as few-shot demos
    -> Adds concrete examples with human notes as calibration anchors
    -> Output: stage2_bootstrap.json (instruction + demos)
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import dspy
from dotenv import load_dotenv

from evaluator_alignment_prompts.config import (
    BFS_MAX_BOOTSTRAPPED,
    BFS_MAX_LABELED,
    MIPRO_NUM_CANDIDATES,
    MIPRO_INIT_TEMP,
    MIPRO_NUM_TRIALS,
    PROMPT_REGISTRY_FILE,
    AlignmentConfig,
)
from evaluator_alignment_prompts.metric import composite_agreement_metric
from evaluator_alignment_prompts.module import EvaluatorModule

load_dotenv()


# ---------------------------------------------------------------------
# LM setup
# ---------------------------------------------------------------------

def configure_lm(cfg: AlignmentConfig) -> dspy.LM:
    """Configure and return the judge LM, registering it with DSPy."""
    lm_kwargs: Dict[str, Any] = dict(
        api_key=os.environ.get(cfg.judge_api_key_env) or "dummy",
        max_tokens=cfg.judge_max_tokens,
        temperature=0.0,
    )
    if cfg.judge_api_base:
        lm_kwargs["api_base"] = cfg.judge_api_base
    lm = dspy.LM(cfg.judge_model, **lm_kwargs)
    dspy.configure(lm=lm)
    return lm


def configure_optimizer_lm(cfg: AlignmentConfig) -> Optional[dspy.LM]:
    """
    Configure the model that PROPOSES candidate instruction rewrites
    (COPRO's prompt_model) — deliberately separate from the judge model
    so the model being calibrated never grades its own rewrite.
    Returns None (self-optimization fallback) if no model/key is set.
    """
    if not cfg.optimizer_model:
        return None
    api_key = os.environ.get(cfg.optimizer_api_key_env)
    if not api_key:
        print(f"[optimizer] optimizer_model set but {cfg.optimizer_api_key_env} missing — "
              "falling back to the judge model proposing its own rewrites.")
        return None
    lm = dspy.LM(cfg.optimizer_model, api_key=api_key, max_tokens=cfg.judge_max_tokens, temperature=1.0)
    print(f"[optimizer] Prompt optimizer (candidate proposer): {cfg.optimizer_model}")
    return lm


# ---------------------------------------------------------------------
# Stage 1: COPRO
# ---------------------------------------------------------------------

def run_copro(
    module: EvaluatorModule,
    trainset: List[dspy.Example],
    cfg: AlignmentConfig,
    metric=None,
    prompt_model: Optional[dspy.LM] = None,
) -> EvaluatorModule:
    """
    Run COPRO to optimize the evaluator instruction.

    COPRO mutates `module.predict.signature.instructions` (the __doc__)
    across `depth` iterations, generating `breadth` candidate instructions
    per iteration and selecting the one with the highest metric score.
    """
    from dspy.teleprompt import COPRO

    if metric is None:
        metric = composite_agreement_metric

    print(
        f"[optimizer] Starting COPRO  "
        f"breadth={cfg.copro_breadth}  depth={cfg.copro_depth}"
    )

    optimizer = COPRO(
        metric=metric,
        breadth=cfg.copro_breadth,
        depth=cfg.copro_depth,
        init_temperature=cfg.copro_init_temp,
        prompt_model=prompt_model,
    )

    optimized = optimizer.compile(
        module,
        trainset=trainset,
        eval_kwargs={
            "num_threads": cfg.num_threads,
            "display_progress": True,
        },
    )

    out_path = cfg.artifacts_dir / "stage1_copro.json"
    optimized.save(str(out_path))
    print(f"[optimizer] COPRO saved -> {out_path}")

    return optimized


# ---------------------------------------------------------------------
# Stage 2: BootstrapFewShot
# ---------------------------------------------------------------------

def run_bootstrap(
    module: EvaluatorModule,
    trainset: List[dspy.Example],
    cfg: AlignmentConfig,
    metric=None,
) -> EvaluatorModule:
    """
    Bootstrap few-shot demonstrations onto an already-optimized module.

    BFS selects training examples where the module already succeeds
    (metric > threshold) and stores them as demos in the prompt.
    Human notes in the training examples act as the rationale that BFS
    propagates into the few-shot prompt.
    """
    from dspy.teleprompt import BootstrapFewShot

    if metric is None:
        metric = composite_agreement_metric

    print(
        f"[optimizer] Starting BootstrapFewShot  "
        f"max_bootstrapped={BFS_MAX_BOOTSTRAPPED}  "
        f"max_labeled={BFS_MAX_LABELED}"
    )

    optimizer = BootstrapFewShot(
        metric=metric,
        max_bootstrapped_demos=BFS_MAX_BOOTSTRAPPED,
        max_labeled_demos=BFS_MAX_LABELED,
    )

    optimized = optimizer.compile(module, trainset=trainset)

    out_path = cfg.artifacts_dir / "stage2_bootstrap.json"
    optimized.save(str(out_path))
    print(f"[optimizer] Bootstrap saved -> {out_path}")

    return optimized


# ---------------------------------------------------------------------
# Stage 3: MIPROv2 (premium — run after COPRO plateau)
# ---------------------------------------------------------------------

def run_mipro(
    module: EvaluatorModule,
    trainset: List[dspy.Example],
    valset: List[dspy.Example],
    cfg: AlignmentConfig,
    metric=None,
) -> EvaluatorModule:
    """
    Run MIPROv2 for joint instruction + demo optimization.

    Use this when COPRO has plateaued and you have budget for ~200 LLM calls.
    """
    from dspy.teleprompt import MIPROv2

    if metric is None:
        metric = composite_agreement_metric

    print(
        f"[optimizer] Starting MIPROv2  "
        f"num_candidates={MIPRO_NUM_CANDIDATES}  "
        f"num_trials={MIPRO_NUM_TRIALS}"
    )

    optimizer = MIPROv2(
        metric=metric,
        num_candidates=MIPRO_NUM_CANDIDATES,
        init_temperature=MIPRO_INIT_TEMP,
        verbose=True,
    )

    optimized = optimizer.compile(
        module,
        trainset=trainset,
        num_trials=MIPRO_NUM_TRIALS,
        minibatch=True,
        minibatch_size=min(25, len(trainset)),
        minibatch_full_eval_steps=5,
        requires_permission_to_run=False,
    )

    out_path = cfg.artifacts_dir / "stage3_mipro.json"
    optimized.save(str(out_path))
    print(f"[optimizer] MIPROv2 saved -> {out_path}")

    return optimized


# ---------------------------------------------------------------------
# Prompt versioning — tracks all optimized instructions
# ---------------------------------------------------------------------

def _build_full_prompt(optimized_instruction: str, original_prompt_path: Path) -> str:
    """
    Merge the COPRO-optimized instruction back into the full original prompt.

    DSPy's COPRO only rewrites the signature 'instruction' field — a short
    header paragraph. The rest of the prompt (rubric tables, dimension
    definitions, scoring criteria, JSON schema) must be preserved.

    Strategy:
      - The original prompt header ends at the first '---' separator line.
      - We replace everything BEFORE the first '---' with the new instruction.
      - Everything from '---' onward is kept exactly as-is.
    """
    if not original_prompt_path.exists():
        return optimized_instruction

    original = original_prompt_path.read_text(encoding="utf-8")
    lines    = original.splitlines(keepends=True)

    sep_idx = next(
        (i for i, line in enumerate(lines) if line.strip() == "---"),
        None,
    )

    if sep_idx is None:
        sep_idx = next(
            (i for i, line in enumerate(lines) if line.strip().startswith("```json")),
            None,
        )

    if sep_idx is None:
        return optimized_instruction + "\n\n" + original

    body = "".join(lines[sep_idx:])
    full_prompt = optimized_instruction.rstrip() + "\n\n" + body
    return full_prompt


def save_optimized_prompt(
    module: EvaluatorModule,
    version_tag: str,
    val_score: float,
    cfg: AlignmentConfig,
    update_latest: bool = True,
) -> None:
    """
    Save the optimized prompt to TWO places:

    1. <optimized_prompts_dir>/<version_tag>.md   -- timestamped, permanent history.
       Every run creates a new file; nothing is ever overwritten.

    2. <optimized_prompt_out>  -- latest copy, always the run's best module.
       Drop-in replacement for whatever pipeline consumes the rubric.

    Pass update_latest=False for intermediate per-stage saves (history only) —
    only the run's overall best_module should ever overwrite the latest copy,
    otherwise whichever stage happens to run last silently wins even if an
    earlier stage scored higher.
    """
    from evaluator_alignment_prompts.config import EVAL_SYSTEM_PROMPT

    optimized_instruction = module.get_instruction()
    full_prompt = _build_full_prompt(optimized_instruction, EVAL_SYSTEM_PROMPT)

    line_count = full_prompt.count("\n") + 1
    print(f"[optimizer] Building full prompt: {line_count} lines "
          f"(instruction merged into baseline {EVAL_SYSTEM_PROMPT.name})")

    # -- 1. Timestamped file in dedicated folder --------------------
    cfg.optimized_prompts_dir.mkdir(parents=True, exist_ok=True)
    timestamped_path = cfg.optimized_prompts_dir / f"{version_tag}.md"
    timestamped_path.write_text(full_prompt, encoding="utf-8")
    print(f"[optimizer] Prompt saved (history) -> {timestamped_path}")

    # -- 2. Latest copy -----------------------------------------------
    if update_latest:
        cfg.optimized_prompt_out.parent.mkdir(parents=True, exist_ok=True)
        cfg.optimized_prompt_out.write_text(full_prompt, encoding="utf-8")
        print(f"[optimizer] Prompt saved (latest)  -> {cfg.optimized_prompt_out}")
    else:
        print("[optimizer] Skipped latest-copy update (not this run's best so far)")

    # -- 3. Version registry ----------------------------------------
    registry: Dict[str, Any] = {}
    if PROMPT_REGISTRY_FILE.exists():
        try:
            registry = json.loads(PROMPT_REGISTRY_FILE.read_text())
        except Exception:
            registry = {}

    registry[version_tag] = {
        "val_score":        round(val_score, 4),
        "line_count":       line_count,
        "optimized_intro":  optimized_instruction[:300] + "..." if len(optimized_instruction) > 300 else optimized_instruction,
        "timestamped_file": str(timestamped_path),
        "latest_copy":      str(cfg.optimized_prompt_out) if update_latest else None,
        "is_run_best":      update_latest,
    }

    PROMPT_REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROMPT_REGISTRY_FILE.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[optimizer] Version '{version_tag}' logged -> {PROMPT_REGISTRY_FILE}")


# ---------------------------------------------------------------------
# Token usage report — rich terminal output with per-model pricing
# ---------------------------------------------------------------------

def print_token_report(lm: dspy.LM, cfg: Optional[AlignmentConfig] = None) -> None:
    """
    Print a detailed token usage and cost report to the terminal.

    Uses pricing from AlignmentConfig so switching models automatically
    updates the cost calculation.
    """
    model_name  = cfg.judge_model              if cfg else "unknown"
    input_rate  = cfg.judge_input_cost_per_1m  if cfg else 0.0
    output_rate = cfg.judge_output_cost_per_1m if cfg else 0.0

    total_prompt     = 0
    total_completion = 0

    def _extract_tokens(usage_obj) -> tuple:
        """Return (prompt_tokens, completion_tokens) from any usage shape."""
        if usage_obj is None:
            return 0, 0
        if hasattr(usage_obj, "prompt_tokens"):
            return (
                int(usage_obj.prompt_tokens      or 0),
                int(getattr(usage_obj, "completion_tokens", 0) or 0),
            )
        if hasattr(usage_obj, "input_tokens"):
            return (
                int(usage_obj.input_tokens  or 0),
                int(getattr(usage_obj, "output_tokens", 0) or 0),
            )
        if isinstance(usage_obj, dict):
            pt = int(usage_obj.get("prompt_tokens",  0) or
                     usage_obj.get("input_tokens",   0) or 0)
            ct = int(usage_obj.get("completion_tokens", 0) or
                     usage_obj.get("output_tokens",     0) or 0)
            return pt, ct
        return 0, 0

    for call in lm.history:
        if not isinstance(call, dict):
            continue

        usage = call.get("usage")
        if usage:
            pt, ct = _extract_tokens(usage)
            total_prompt     += pt
            total_completion += ct
            continue

        resp = call.get("response")
        if resp is None:
            continue
        usage = getattr(resp, "usage", None)
        if usage is None and isinstance(resp, dict):
            usage = resp.get("usage")
        pt, ct = _extract_tokens(usage)
        total_prompt     += pt
        total_completion += ct

    total_tokens = total_prompt + total_completion
    input_cost   = (total_prompt     / 1_000_000) * input_rate
    output_cost  = (total_completion / 1_000_000) * output_rate
    total_cost   = input_cost + output_cost

    W = 56
    BORDER = "=" * W

    print("\n" + BORDER)
    print(f"{'  TOKEN USAGE & API COST REPORT':^{W}}")
    print(BORDER)
    print(f"  Model          : {model_name}")
    print(f"  Pricing        : ${input_rate:.3f} / 1M input  |  ${output_rate:.3f} / 1M output")
    print("-" * W)
    print(f"  API Calls      : {len(lm.history):>10,}")
    print(f"  Prompt Tokens  : {total_prompt:>10,}   (cost: ${input_cost:.5f})")
    print(f"  Output Tokens  : {total_completion:>10,}   (cost: ${output_cost:.5f})")
    print(f"  TOTAL Tokens   : {total_tokens:>10,}")
    print("-" * W)
    print(f"  TOTAL COST     : ${total_cost:.5f}  USD")
    if total_cost < 0.01:
        print(f"                   (< $0.01 — very cheap run)")
    elif total_cost < 0.10:
        print(f"                   (< $0.10 — cheap run)")
    elif total_cost < 1.00:
        print(f"                   (< $1.00 — moderate cost)")
    else:
        print(f"                   (> $1.00 — consider reducing breadth/depth)")
    print(BORDER + "\n")
