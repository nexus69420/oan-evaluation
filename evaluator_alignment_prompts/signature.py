"""
signature.py — DSPy Signatures for evaluator alignment.

Architecture
────────────
Two complementary signature families:

1. EvaluationSignature  — Predicts a single scalar (overall_score) + rubric.
   Used by COPRO / MIPROv2 to optimize the primary prompt instruction.

2. MultiDimEvaluationSignature — Predicts multiple sub-dimension scores as
   a structured JSON string. Used for multi-dimensional optimization.

3. AgreementSignature  — The meta-evaluator: judges whether the LLM score
   matches the human score. Used as the optimization metric delegate.

4. BlindEvaluationSignature — Production inference signature (no human_notes).

Design rationale
────────────────
* DSPy optimizers mutate `__doc__` (the signature instruction) while keeping
  field definitions stable. Separating the "what to score" (field descs)
  from "how to score" (instruction / rubric) allows targeted mutation.
* Confidence output is included so uncertainty can be calibrated.
* human_notes is an *optional* input — present during training/optimization
  (so the optimizer learns error patterns) and absent during inference.

Customizing for your domain
────────────────────────────
The rubric text below is a generic starting point. To calibrate to your
own domain (e.g. a specific product, language, or safety policy), either:
  a) Edit the docstrings below directly, or
  b) Point config.BASELINE_PROMPT_PATH at your own rubric file — module.py's
     `load_from_prompt_file()` will use it as the starting instruction
     instead of the docstring here.
"""
from __future__ import annotations

import dspy


# ─────────────────────────────────────────────────────────────────────
# 1. Primary evaluation signature (single scalar)
# ─────────────────────────────────────────────────────────────────────

class EvaluationSignature(dspy.Signature):
    """
    You are a calibrated evaluator for an AI assistant. Your task is to
    assign a quality score (1-4) that EXACTLY matches how a trained human
    expert would score the same response.

    Scoring rubric:
      4 = Fully answers ALL aspects of the query; correct terminology;
          grounded in retrieved context; no fabrication.
      3 = Answers the main question but has a MINOR gap: one wrong term,
          one missing detail, slight over-generalisation.
      2 = Partial answer OR answers a related-but-different topic; missing
          critical information; noticeable errors.
      1 = Wrong answer, off-topic, harmful advice, or unidentifiable query.

    Key signals that lower scores:
      - Incorrect domain terminology.
      - Grammar or language errors.
      - Fabricated data (facts, numbers, contacts, timelines) not in the context.
      - Excessive formatting/markdown that obscures meaning.
      - Requests answered in the wrong language or register.

    Output ONLY a JSON object:
      {"score": <1-4 integer>, "reason": "<one sentence>",
       "confidence": "<High|Medium|Low>"}
    """

    # ── Inputs ──────────────────────────────────────────────────────
    question: str = dspy.InputField(
        desc="The user's query."
    )
    context: str = dspy.InputField(
        desc=(
            "Tool outputs and search results that the agent had access to. "
            "Used to verify factual grounding — if the context is empty "
            "and the agent fabricated data, that is a critical failure."
        )
    )
    agent_response: str = dspy.InputField(
        desc="The agent's response to evaluate."
    )
    human_notes: str = dspy.InputField(
        desc=(
            "OPTIONAL reviewer hint. May name a specific error. "
            "Use this as a rubric calibration signal, not as the sole basis for scoring."
        ),
        default="",
    )

    # ── Outputs ─────────────────────────────────────────────────────
    overall_score: str = dspy.OutputField(
        desc=(
            "Integer 1-4 matching the human rubric. "
            "Return as a JSON string: "
            '{"score": <int>, "reason": "<str>", "confidence": "<High|Medium|Low>"}'
        )
    )


# ─────────────────────────────────────────────────────────────────────
# 2. Multi-dimensional evaluation signature
# ─────────────────────────────────────────────────────────────────────

class MultiDimEvaluationSignature(dspy.Signature):
    """
    You are a calibrated multi-dimensional evaluator for an AI assistant.
    Score EACH sub-dimension independently on a 1-5 integer scale (or null
    if N/A). Your per-dimension scores must be consistent with how a
    trained human expert panel would rate the same response.

    Dimensions:
      PROCESS FIDELITY (1-5)
        workflow_adherence    — Correct use of any structured input/profile data
        term_identification   — Correct identification of domain-specific terms
        tool_sequencing        — Tools called in the right order
        search_quality         — Effective search queries
        output_hygiene         — No internal artifacts leaked to the response

      FACTUAL GROUNDING (1-5)
        source_alignment      — All claims traceable to context
        no_fabrication         — No invented data (facts, contacts, timelines)
        citation_accuracy      — Correct source attribution format
        safety_compliance      — Correct, safe, legally-compliant guidance only

      RESPONSE USEFULNESS (1-5)
        completeness           — All parts of the query addressed
        actionability           — Specific, concrete, actionable advice
        context_fit             — Appropriate for the user's stated situation
        clarity                  — Clear structure, readable length
        conversation_closure    — Ends with a helpful next step

      LANGUAGE QUALITY (1-5)
        grammar                  — Correct grammar
        terminology               — Domain-correct vocabulary
        language_purity           — Minimal inappropriate language mixing
        fluency                    — Natural, conversational tone

    Return STRICT JSON matching the schema shown in the instructions.
    Null scores are allowed for sub-dimensions that are genuinely N/A.
    """

    question: str = dspy.InputField(
        desc="The user's query."
    )
    context: str = dspy.InputField(
        desc="Tool outputs and retrieved search results available to the agent."
    )
    agent_response: str = dspy.InputField(
        desc="The agent's response to evaluate."
    )
    human_notes: str = dspy.InputField(
        desc="Optional human reviewer notes identifying specific errors.",
        default="",
    )

    evaluation_json: str = dspy.OutputField(
        desc=(
            "Complete evaluation JSON with all 4 dimension groups, "
            "each sub-dimension having {score: int|null, evidence: str}, "
            "plus summary, overall_average, and critical_failures list."
        )
    )


# ─────────────────────────────────────────────────────────────────────
# 3. Agreement meta-signature (used inside the optimization metric)
# ─────────────────────────────────────────────────────────────────────

class AgreementSignature(dspy.Signature):
    """
    Determine whether the predicted evaluation score is aligned with the
    human expert score. Consider partial agreement (within 1 point) as
    'close'. Your output feeds directly into the optimization loop.
    """

    human_score: str = dspy.InputField(
        desc="The gold-standard score assigned by a trained human evaluator (1-4)."
    )
    predicted_score: str = dspy.InputField(
        desc="The score predicted by the LLM evaluator (1-4)."
    )
    human_notes: str = dspy.InputField(
        desc="Human reviewer's notes explaining what was wrong.",
        default="",
    )

    agreement_level: str = dspy.OutputField(
        desc=(
            "One of: 'exact' (scores match), 'close' (within 1), "
            "'partial' (within 2), 'far' (differ by >2). "
            "Return as JSON: "
            '{"agreement": "<exact|close|partial|far>", '
            '"reason": "<one sentence>"}'
        )
    )


# ─────────────────────────────────────────────────────────────────────
# 4. Blind inference signature (no human_notes — for production use)
# ─────────────────────────────────────────────────────────────────────

class BlindEvaluationSignature(dspy.Signature):
    """
    Production evaluator: no reviewer hints are available.
    Apply the learned rubric to produce a calibrated score (1-4).
    Output JSON: {"score": <int>, "reason": "<str>", "confidence": "<High|Medium|Low>"}
    """

    question: str = dspy.InputField(
        desc="The user's query."
    )
    context: str = dspy.InputField(
        desc="Tool outputs / retrieved content available to the agent."
    )
    agent_response: str = dspy.InputField(
        desc="The agent's response to evaluate."
    )

    overall_score: str = dspy.OutputField(
        desc='JSON: {"score": <1-4 int>, "reason": "<str>", "confidence": "<str>"}'
    )
