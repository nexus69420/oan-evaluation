# DSPy Evaluator Alignment

**What this repo does, in one sentence:** you give it examples of an AI
response plus the score a human gave it, and it rewrites the prompt of an
LLM judge until the judge's scores agree with the human's — so next time,
you don't need a human to grade new responses.

## The idea, in plain terms

Say you have an AI assistant, and a human reviewer scores its responses
(1-4, good/bad, whatever scale). That's slow and doesn't scale. So you build
an LLM "judge" — another AI whose only job is to read a response and guess
the score a human would give it. The problem: the judge's first-draft
instructions (the "prompt") are rarely well calibrated. It might be too
strict, too lenient, or focused on the wrong things.

This repo automates fixing that. It:

1. Takes examples of `(question, context, response, human_score)`.
2. Runs the current judge prompt on those examples and checks how far the
   judge's guesses are from the real human scores.
3. Asks another LLM to rewrite the judge's instructions to close that gap.
4. Repeats, keeping whichever version agrees with humans best.
5. Tests the winner on examples it has never seen, so you know it actually
   generalizes.

The output is a plain text prompt file. Drop it into whatever system runs
your real judge, and it now scores like your human reviewer would — without
a human in the loop.

### The tools under the hood (DSPy / COPRO / Bootstrap), in plain terms

- **[DSPy](https://github.com/stanfordnlp/dspy)** is a library for treating
  prompts as *things a program can automatically improve*, instead of text
  you hand-edit forever. You describe what goes in and out of a prompt, give
  it a scoring function, and DSPy searches for better instruction wording.
- **COPRO** is the specific search DSPy uses here: it asks an LLM to propose
  a few rewritten versions of the instructions, tries each one on your
  examples, keeps the best-scoring version, and repeats a few rounds
  (`--breadth` = how many rewrites to try per round, `--depth` = how many
  rounds). This is what actually changes the *wording* of the rubric.
- **BootstrapFewShot** doesn't touch the wording — instead it picks a
  handful of your training examples where the judge already does well and
  attaches them to the prompt as worked examples ("here's a response scored
  3, and why"). Concrete examples often calibrate a judge faster than more
  prose.

## Two ways to fine-tune

This repo supports two related workflows. Use whichever matches how your
judge is structured:

| | **Holistic** (`train.py`) | **Per-metric** (`metrics/train_metrics.py`) |
|---|---|---|
| Tunes | ONE prompt that scores everything at once | Several small prompts, each scoring ONE narrow thing |
| Example | "Score this response 1-4 overall" | "Does this response cite its source correctly? (0/1)", "Is it factually grounded? (0/1)", separately |
| Best for | A single simple judge | A judge broken into named metrics (accuracy, citations, no-fabrication, actionability, ...) |
| Optimizer default | COPRO then BootstrapFewShot | COPRO only (see below for why) |

**Why per-metric optimization defaults to COPRO only, with Bootstrap
skipped:** narrow, single-purpose rubrics are exactly where rewording the
instructions (COPRO) helps most. Bolting a few worked examples onto an
already-narrow prompt (BootstrapFewShot) has been observed, in practice, to
make things *worse* — a handful of concrete demos can overfit to their
specifics and pull the judge away from a rule that actually generalizes
better as plain prose. Pass `--optimizer two-stage` to `train_metrics.py` if
you want to try Bootstrap on top anyway.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # or use an existing venv
pip install -r requirements.txt

cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# Holistic: tune one overall judge prompt
python -m evaluator_alignment_prompts.train \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv

# Per-metric: tune several narrow judge prompts independently
python -m evaluator_alignment_prompts.metrics.train_metrics \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv
```

The repo ships with a small sample `data/train.csv` / `val.csv` / `test.csv`
(agriculture Q&A, generic — replace with your own) so both commands above
run immediately and produce a real result. Each costs a few cents with the
default `gpt-4o-mini` judge.

## New to this repo? Step by step

### 1. Set up the environment
```bash
cd dspy-evaluator-alignment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Add your API key
```bash
cp .env.example .env
```
Then edit `.env` and set:
```
OPENAI_API_KEY=sk-...
```
That's the only required setting — everything else (model, score range,
file paths) has a working default.

### 3. Get your data into the right shape
Put 3 CSVs — `train.csv`, `val.csv`, `test.csv` — in `data/`, each with at
minimum: `question`, `agent_response`, `human_score`. The repo already
ships small sample CSVs in exactly this shape, so **you can skip this step
entirely for your first run** and just try it on the bundled sample data.

### 4. Run a first fine-tuning pass (pick one)

**Holistic** — one prompt scores everything at once:
```bash
python -m evaluator_alignment_prompts.train \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv
```

**Per-metric** — several narrow prompts, each scoring one thing (accuracy,
citations, no-fabrication, actionability):
```bash
python -m evaluator_alignment_prompts.metrics.train_metrics \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv
```

You can run both if you're not sure which fits — they don't conflict. Watch
the terminal for `Baseline val composite` vs the final `Test composite`
score — that tells you whether it actually improved.

### 5. Look at what it produced
```bash
cat optimized_prompts/latest.md              # holistic: best rewritten prompt
cat optimized_prompts/metrics/*_latest.md     # per-metric: best rewritten prompt, per metric
```
Also worth a look: `artifacts/error_report_*.md` (holistic) — shows exactly
which examples the judge got wrong and why.

### 6. If you like the result, promote it
This is the one manual step that makes a fine-tuned prompt "live":
```bash
# Holistic
python -m evaluator_alignment_prompts.promote.promote

# Per-metric (all metrics, or just one)
python -m evaluator_alignment_prompts.promote.promote_metrics --all
python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy
```
This overwrites `prompts/evaluation_system_baseline.md` (or
`prompts/metrics/<metric>.md`) with the new version, backing up whatever
was there first.

### 7. Iterate
Re-run step 4 — it now starts from the prompt you just promoted, so each
round builds on the last. Repeat 4→6 until scores plateau.

**Once you have your own data:** swap in your real CSVs at step 3, and if
your CSV uses different column names or a different score scale (e.g. 1–5
instead of 1–4), set `COL_QUESTION` / `COL_SCORE` / `SCORE_MIN` / `SCORE_MAX`
etc. in `.env` instead of renaming your data — see `.env.example` for the
full list.

## What you need to provide

Three CSVs — already split into train/validation/test — each with these
columns:

| Column | Required | Meaning |
|---|---|---|
| `question` | yes | The query the response is answering. |
| `agent_response` | yes | The response being judged. |
| `human_score` | yes, for the **holistic** workflow | The ground-truth overall score a human gave that response (e.g. 1–4). |
| `context` | no | Retrieved context / tool output the responder had access to. Used to catch fabrication. |
| `human_notes` | no | A reviewer's note on what was wrong. Kept as an input on **train only** — validation/test are always blind, since production inference never has this available. |
| `verdict` | no | A free-text label (e.g. `good`/`bad`) — used only to break down error analysis by category, never fed to the model. |
| `confidence` | no | A reviewer confidence label — used only in error analysis. |
| `<metric>_score` | yes, for the **per-metric** workflow, one per metric | e.g. `citation_accuracy_score`, `no_fabrication_score` — the human score for that ONE narrow metric. See `prompts/metrics/metrics_config.json`. |
| `<metric>_notes` | no | Same idea as `human_notes`, but per metric. |

If your CSV uses different column names, set `COL_QUESTION`, `COL_RESPONSE`,
`COL_SCORE`, etc. in `.env` instead of renaming your data (see
`.env.example`). The bundled sample CSVs already carry both `human_score`
(for `train.py`) and four `<metric>_score` columns (for `train_metrics.py`)
on the same rows — you don't need separate files for the two workflows.

**Why 3 CSVs and not 1?** Held-out validation/test sets are what make the
optimization trustworthy — the optimizer never sees val/test data during
training, so their scores tell you whether the tuned prompt actually
generalizes rather than having memorized your training examples. If you
only have one CSV, split it yourself (e.g. 60/20/20) before running this.

## Example: running on a real dataset with different column names

`data/pivot_real/` is a worked example of pointing this repo at a CSV that
wasn't built for it — a real production evaluation export (`pivot_source.csv`,
185 rows, split 70/15/15 into `train.csv`/`val.csv`/`test.csv`). Its columns
don't match our bundled toy data at all:

| | Toy sample data | `data/pivot_real/` |
|---|---|---|
| Response column | `agent_response` | `answer` |
| Score column naming | `citation_accuracy_score` (single underscore) | `citation_accuracy__score` (double underscore) |
| Score column per metric | 4 metrics (incl. `actionability`) | 3 overlapping metrics + 2 others we don't have prompts for (`source_data_comprehensiveness`, `tool_call_quality`) + one excluded on purpose (`translation_accuracy` — real scores cluster at 9–10, too narrow a range to optimize against) |

Rather than renaming the CSV or editing any Python, this is handled with
config alone:

- **`prompts/metrics/metrics_config_pivot.json`** — a second copy of
  `metrics_config.json`, with `score_col`/`notes_col` corrected to this
  CSV's real double-underscore column names (only for the 3 metrics that
  exist in both datasets: `accuracy_completeness`, `citation_accuracy`,
  `no_fabrication`). It doesn't contain any of the CSV's actual data — just
  the column-name lookup, same idea as the default config.
- **`METRICS_CONFIG_FILE`** and **`COL_RESPONSE`** environment variables —
  both already existed for exactly this purpose — point them at the new
  config and the `answer` column for this run only:

```bash
METRICS_CONFIG_FILE=prompts/metrics/metrics_config_pivot.json \
COL_RESPONSE=answer \
python -m evaluator_alignment_prompts.metrics.train_metrics \
  --train-csv data/pivot_real/train.csv --val-csv data/pivot_real/val.csv --test-csv data/pivot_real/test.csv \
  --metrics accuracy_completeness,citation_accuracy,no_fabrication \
  --breadth 2 --depth 1
```

The default `prompts/metrics/metrics_config.json` (used by the plain
`python -m evaluator_alignment_prompts.metrics.train_metrics` command earlier
in this README) is untouched and still targets the toy sample CSVs — this is
purely an additional, opt-in example, not a replacement.

## Promoting a fine-tuned prompt (going from "tuned" to "the judge you actually use")

**`train.py` / `train_metrics.py` experiment. `promote.py` / `promote_metrics.py` ship it.**

- **Training** tries to improve the judge's prompt: it rewrites the wording,
  tests each attempt against your labeled examples, and saves every attempt
  as a new timestamped file under `optimized_prompts/`. Nothing your judge
  actually uses day-to-day changes — it's all drafts sitting in a folder for
  you to review scores on.
- **Promoting** takes one of those drafts (by default, the best one from
  your last training run) and copies it over the real, live prompt file
  your judge reads. That's the moment a fine-tuned prompt stops being an
  experiment and becomes what's actually used.

Analogy: training is writing and testing several drafts of an essay and
saving each one. Promoting is hitting "publish" on the draft you liked best
— and it keeps a backup of whatever was published before, in case you want
to roll back. You always train first, look at the scores, then promote if
you're happy — it's a deliberate second step, never automatic.

Fine-tuning (`train.py` / `train_metrics.py`) never touches your live prompt
files — it only writes new, timestamped versions under `optimized_prompts/`,
so you can review scores before committing to anything. **Promoting** is the
one extra step that copies a fine-tuned version over the prompt your judge
actually reads day to day — no more hand-picking a file and editing a path.

```bash
# Holistic: promote optimized_prompts/latest.md -> prompts/evaluation_system_baseline.md
python -m evaluator_alignment_prompts.promote.promote

# Per-metric: promote every metric's latest fine-tuned prompt
python -m evaluator_alignment_prompts.promote.promote_metrics --all

# ...or just one metric
python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy
```

Both commands **back up the file they're about to overwrite first**
(into `prompts/archive/` or `prompts/metrics/archive/`), so promoting is
always reversible. After promoting, the *next* fine-tuning run starts from
the newly promoted prompt — each round can build on the last.

Promoting only replaces the *prompt text*. It doesn't run the judge on new,
unlabeled data by itself — for that, use `BlindEvaluatorModule` (holistic) or
`SingleMetricEvaluatorModule` (per-metric) directly in your own inference
code, pointed at the promoted prompt file.

## What it produces

Every `train.py` run writes to (paths configurable, see `.env.example`):

```
optimized_prompts/
  stage1_copro_<timestamp>.md     # after rubric-rewriting stage
  stage2_bootstrap_<timestamp>.md # after adding few-shot demos
  best_<timestamp>.md             # this run's best-scoring prompt
  latest.md                       # always the best prompt across all runs

artifacts/
  stage1_copro.json               # DSPy program (instruction + demos)
  stage2_bootstrap.json
  error_report_*.md               # confusion matrix, worst disagreements, bias analysis
  final_test_report_<timestamp>.md
  summary_<timestamp>.json
  prompt_registry.json            # every version's validation score, in one place
```

Every `train_metrics.py` run writes the per-metric equivalent:

```
optimized_prompts/metrics/
  <metric>_<optimizer>_<timestamp>.md   # history, one file per metric per run
  <metric>_latest.md                    # this run's best for that metric

artifacts/metrics/
  metric_prompt_registry.json           # every metric's version history + scores
```

## How it works

1. **`dataset.py`** loads your three CSVs into DSPy `Example` objects.
   `human_notes` stays on the training set (it's a rationale signal for
   the Bootstrap stage) but is stripped from val/test so evaluation is
   always blind. `metrics/metrics_dataset.py` does the same thing, but reads
   one metric's own score/notes columns instead of `human_score`.
2. **`signature.py` / `module.py`** define the holistic judge: it reads
   `(question, context, agent_response)` and outputs a structured score
   across several sub-dimensions (grouped as process fidelity, factual
   grounding, response usefulness, language quality — edit these in
   `signature.py` or override the whole rubric via `prompts/evaluation_system_baseline.md`).
   `metrics/metric_module.py` defines the per-metric equivalent: one narrow
   judge per metric, each loaded from its own file in `prompts/metrics/`.
3. **`metric.py`** scores agreement between the judge's prediction and the
   human score (exact match, adjacent match, MAE, a QWK proxy) — this is
   what the optimizer maximizes. `make_agreement_metric(score_min, score_max)`
   builds the same formula for a metric with its own scale (e.g. 0/1 instead
   of 1-4), since different metrics can use different scales.
4. **`optimizer.py` / `train.py`** run a two-stage DSPy optimization for the
   holistic judge:
   - **Stage 1 (COPRO)** rewrites the judge's instruction text to close
     the gap with human scores.
   - **Stage 2 (BootstrapFewShot)** adds concrete calibration examples
     (using `human_notes` as rationale) on top of the Stage 1 rubric.
   - An optional **Stage 3 (MIPROv2)** jointly searches instructions +
     demos — more expensive, use if COPRO plateaus (`--optimizer mipro`).
   **`metrics/train_metrics.py`** runs the same idea per metric, COPRO-only
   by default (see [Two ways to fine-tune](#two-ways-to-fine-tune)).
5. **`evaluate.py`** produces the confusion matrix, worst-disagreement
   list, and bias diagnosis (is the judge systematically too lenient or
   too harsh?) used in every holistic report.
6. **`promote/promote.py` / `promote/promote_metrics.py`** copy a fine-tuned
   prompt over its live baseline file, backing up whatever was there first.

Some of the bundled per-metric prompts (`prompts/metrics/*.md`) are real
production rubrics written as [Jinja](https://jinja.palletsprojects.com/)
templates with category-specific branches (e.g. a different rubric for
"weather" vs "mandi price" queries). Since the bundled sample data has no
`category` column, they're rendered once at load time with no category set,
which resolves to each file's generic/fallback branch — genuinely usable out
of the box, but pointing this at your own categorized data will get you the
more specific branches.

## Configuration

Everything tunable lives in `evaluator_alignment_prompts/config.py`, and
every value there can be overridden by an environment variable (or `.env`
— see `.env.example` for the full list). Notably:

- `JUDGE_MODEL` / `JUDGE_API_BASE` — the model being calibrated. Works with
  any OpenAI-compatible endpoint, including self-hosted vLLM: set
  `JUDGE_API_BASE=http://localhost:8010/v1` and `JUDGE_MODEL=openai/<your-model>`.
- `OPTIMIZER_MODEL` — the model that *proposes* rewrites (COPRO's
  `prompt_model`). Deliberately kept separate from `JUDGE_MODEL` — the
  model being calibrated shouldn't grade its own rewrite.
- `SCORE_MIN` / `SCORE_MAX` — match this to your CSV's overall score scale
  (used by the holistic workflow; per-metric scales come from
  `prompts/metrics/metrics_config.json` instead).
- `BASELINE_PROMPT_PATH` — the starting holistic rubric. Point this at your
  own file to start from something other than the generic bundled default.
- `MAX_TRAIN` / `MAX_VAL` / `MAX_TEST` — caps to keep cost predictable
  while iterating; raise them once you're happy with the setup.

## CLI reference

### Holistic

```bash
python -m evaluator_alignment_prompts.train \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv \
  --optimizer two-stage \        # copro | bootstrap | mipro | two-stage (default)
  --breadth 4 --depth 3 \        # COPRO search width/iterations
  --max-train 80 --max-val 30 --max-test 30 \
  --target-score 80 \            # stop early if val score (0-100) hits this
  --min-improvement 0.5 \        # min per-stage gain (0-100) to keep going
  --no-notes                     # exclude human_notes even from training input
```

To evaluate an already-optimized program without re-running optimization:

```bash
python -m evaluator_alignment_prompts.train \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv \
  --eval-only artifacts/stage2_bootstrap.json
```

Promote the result:

```bash
python -m evaluator_alignment_prompts.promote.promote            # optimized_prompts/latest.md -> live baseline
python -m evaluator_alignment_prompts.promote.promote --from optimized_prompts/stage2_bootstrap_<timestamp>.md
```

### Per-metric

```bash
python -m evaluator_alignment_prompts.metrics.train_metrics \
  --train-csv data/train.csv --val-csv data/val.csv --test-csv data/test.csv \
  --metrics citation_accuracy,no_fabrication \  # default: every metric in metrics_config.json
  --optimizer copro \             # copro (default) | bootstrap | two-stage
  --breadth 4 --depth 3 \
  --max-train 80 --max-val 30 --max-test 30 \
  --target-score 80 \
  --no-notes
```

Promote the result:

```bash
python -m evaluator_alignment_prompts.promote.promote_metrics --all
python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy
python -m evaluator_alignment_prompts.promote.promote_metrics --metric citation_accuracy \
  --from optimized_prompts/metrics/citation_accuracy_copro_<timestamp>.md
```

## Repo layout

Every folder, explained:

```
evaluator_alignment_prompts/    # all the Python code lives here
  config.py                       # central settings: models, paths, score ranges, CSV
                                   #   column names — everything overridable via .env
  dataset.py                      # loads the 3 CSVs into DSPy Examples (holistic workflow)
  signature.py                    # the holistic judge's rubric / output schema (DSPy Signatures)
  module.py                       # the holistic judge itself (DSPy Modules)
  metric.py                       # human-agreement scoring functions — shared by BOTH workflows
  optimizer.py                    # runs COPRO / BootstrapFewShot / MIPROv2 (holistic workflow)
  evaluate.py                     # error analysis: confusion matrix, bias detection, reports
  train.py                        # CLI — fine-tune the ONE holistic judge prompt ("File 1")

  metrics/                        # everything needed to fine-tune per-metric prompts
    metric_module.py                 # the per-metric judge (DSPy Module) — one narrow judge
    metrics_dataset.py                # loads the 3 CSVs into DSPy Examples, per metric
    train_metrics.py                   # CLI — fine-tune each metric's prompt independently ("File 1")

  promote/                        # everything needed to "publish" a fine-tuned prompt
    promote.py                       # CLI — promote a fine-tuned HOLISTIC prompt ("File 2")
    promote_metrics.py                # CLI — promote fine-tuned PER-METRIC prompts ("File 2")

prompts/                        # the actual prompt TEXT your judge(s) use — not code
  evaluation_system_baseline.md   # the live holistic rubric. train.py starts here;
                                  #   promote.py overwrites this file when you publish
  archive/                        # auto-created backups of evaluation_system_baseline.md,
                                  #   one per promote.py run, so nothing is ever lost
  metrics/                        # the live per-metric rubrics
    metrics_config.json              # registry: metric name -> its prompt file, score
                                      #   range (e.g. 0-1 or 1-4), and CSV column names
    accuracy_completeness.md, citation_accuracy.md,
    no_fabrication.md, actionability.md   # one prompt file per metric. train_metrics.py
                                          #   starts here; promote_metrics.py overwrites
                                          #   these when you publish
    metrics_config_pivot.json        # alternate config for data/pivot_real/ (see
                                      #   "Example: running on a real dataset" above) —
                                      #   same 3 prompt files, different CSV column names
    archive/                        # auto-created backups, one per promote_metrics.py run

data/                            # your labeled examples
  train.csv, val.csv, test.csv    # sample data — replace with your own. Same 3 files
                                   #   serve BOTH workflows (holistic uses `human_score`,
                                   #   per-metric uses `<metric>_score` columns)
  pivot_real/                     # worked example: a real dataset with different column
                                   #   names, run via metrics_config_pivot.json above
    pivot_source.csv, train.csv, val.csv, test.csv

optimized_prompts/              # every fine-tuning ATTEMPT (drafts, never auto-published)
  latest.md, best_<ts>.md, stage1_copro_<ts>.md, ...   # holistic drafts (train.py output)
  metrics/                         # per-metric drafts (train_metrics.py output)
    <metric>_latest.md, <metric>_<optimizer>_<ts>.md, ...

artifacts/                      # reports and machine-readable run history (not prompts)
  prompt_registry.json             # every holistic version + its validation score
  error_report_*.md, final_test_report_*.md, summary_*.json   # holistic error analysis
  metrics/
    metric_prompt_registry.json      # every per-metric version + its validation score
```

**The pattern to remember:** `prompts/` is what your judge reads *right
now* (the only files `train.py`/`train_metrics.py` start from, and the only
files `promote.py`/`promote_metrics.py` write to). `optimized_prompts/` and
`artifacts/` are scratch space — every experiment's output, kept for
history, never used directly by anything until you explicitly promote one.

## Caveats

- This calibrates a **judge**, not an answer generator. If you want DSPy to
  tune a prompt that *produces* better answers (given question → reference
  answer pairs), that's a different module/metric than what's here.
- The multi-dimension rubric in `signature.py` is a generic starting
  taxonomy (process fidelity / factual grounding / usefulness / language
  quality). Edit the dimension names and descriptions in `signature.py`,
  or swap the whole thing out via `BASELINE_PROMPT_PATH`, to match your
  domain.
- `human_notes` (and per-metric `<metric>_notes`) on the training set can
  leak the answer if too literal (e.g. "wrong word X, should be Y") —
  that's intentional; it's a calibration signal for `BootstrapFewShot`, and
  it's always stripped from val/test so held-out scores stay honest.
- Promoting only swaps prompt *text*. It doesn't wire up an inference
  pipeline for scoring brand-new, unlabeled responses — that's on you (or a
  separate system) using `BlindEvaluatorModule` / `SingleMetricEvaluatorModule`
  with the promoted prompt file.
# promot-tuning
# promot-tuning
