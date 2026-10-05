# Amul metrics status (issue #1)

Tracks the 26 metrics listed in [issue #1](https://github.com/OpenAgriNet/oan-evaluation/issues/1), section 3,
against what is live on Langfuse (dataset `amul-seed-questions`).
Update this file whenever a metric is added, changed, or found to be wrong.

Last updated: 2026-10-03

Runs on Langfuse:
- `seed-gu-capture-3` (current): content tools working through the dev Beckn seeker, 60-day milk stub,
  milk-today question reworded, realistic technician names.
- `seed-gu-capture-2` (old): every content tool failed (X1). Kept for comparison; scored with the same judges, using
  the farmer context it was captured with (`--farmer-context`, old technician names).

Run everything on the H100 (dry run without `--post`):

    python -m evaluation.amul.run_amul_eval --run seed-gu-capture-3 --env-file inference/.env \
        --prod-reference --glossary-container amul_app_eval \
        --judges grounding,gujarati_language,prod_reference,task_success,translation_meaning,safety,search_quality,recovery,context_retention,agristack,term_identification,tool_sequencing --post

`--glossary-container` needs Docker access to the agent container; it builds each answer's glossary with the agent's
own code. Langfuse can take a minute to list freshly linked run items; score after that.

`milk_total`, `expected_tools`, `task_success`, and `translation_meaning` were posted to `seed-gu-capture-3` on 2026-10-03 (checks v5).

## Eval run checklist

Use this for the next capture. Golden answers (X3) are out of scope until Amul writes them.

Before capture:

- [ ] Dev Langfuse `https://langfuse.dev.amulai.in` answers `/api/public/health`. The host is the dev jump `4.187.152.138`; if that VM is stopped, stop.
- [ ] `amul_app_eval` is up on `127.0.0.1:8095`. Do not touch `amul_app` on port 8000 or `/home/aicloud/docs-pipeline`.
- [ ] `run.env` guards hold: `BASE_URL` is `:8095`, phone `9000000001`, eval chat key set.
- [ ] Booking stays on the stub. `check_loan_eligibility` stays blocked.

Capture, link, score:

- [ ] On the H100, load `run.env` and run `inference/run_sequential_scenario.py`. Record `run_uuid`. Session ids are `{run_uuid}_gu_{session_id}`.
- [ ] Link each seed row the same day with `POST /api/public/dataset-run-items`. Wait a minute, then confirm 75 run items.
- [ ] Score with the command above, and include judges `task_success,translation_meaning`. Dry-run first. `--post` only after the user says so.
- [ ] Re-read the run from Langfuse. A new blank that is not in the blank-cell list is a failure.
- [ ] Update this file. Do not commit or push unless the user asks.

Closed for the metrics that are already live or in code:

- [x] `milk_total` posted. `milk-week-2` is 0 (72.7 L vs 68.4 L). `milk-week-3` is 1.
- [x] `expected_tools` posted, 53 turns, mean 0.94. Clarification turns stay blank. Fails: `health-heat` turns 2 and 5 (no document search), `scheme-gov-1` (union lookup instead of Vistaar).
- [x] `task_success` posted, 74/75, mean 4.96. The thank-you turn is null. Low: `scheme-all-3` described a loan the tools did not return.
- [x] `translation_meaning` posted, 75/75, mean 4.79. Lows: transliterated ticket `EVAL-NET-0007`, Soil Health Card rendered as a generic health card, union assistance called a central-government scheme.
- [x] `search_quality` posted, 17 searches, mean 4.06. Five are 2 because the reply used the pregnant-animal passage for an animal that is not pregnant (`health-anoestrus-2`, `health-conceive` 1–3, `health-heat-4`). `scheme-heifer-2` is 4: the query names Vasudhara and the reply says that dairy is not in the results. A missed search stays on `expected_tools`.
- [x] `recovery_clarification` posted, 29/75, mean 4.66. Two 2s: `scheme-all-1` and `scheme-apply-1` described PM-KISAN, KCC, and PMFBY after Vistaar returned temporarily unavailable. Two 3s: `ai-home-1` and `ai-seed-en-1` asked for species and technician in the same reply.
- [x] `context_retention` posted, 47/75, mean 4.91. First turn of each session is null. Lows: `milk-week-4` asks which union after that farmer's milk records were already shown; `health-visit-2` asks again whether to book a doctor after the farmer already asked for one.
- [x] `agristack_workflow` posted, 66/75, mean 4.92. This agent has a farmer profile, not an Agristack tool. Lows: `milk-week-4` asks which union though the profile says Banas; `scheme-all-3` offers a Kheda bank loan to a Banaskantha farmer.
- [x] `term_identification` posted, 22/75, mean 5.00. This agent has no `search_terms` tool. The score is the lookup argument. Every search or scheme argument named the farmer's term. A wrong passage stays on `search_quality`. A missed search stays on `expected_tools`.
- [x] `tool_sequencing` posted, 44/75, mean 4.91. Order and whether a booking waited. Four 4s repeat the same scheme request in `get_union_scheme_data` and `search_documents` (`scheme-all-2`, `scheme-calf-1`, `scheme-gap-1`, `scheme-loan-1`). A missed or wrong single tool stays on `expected_tools`. A bad argument stays on `tool_arguments`.

Still manual, or not part of this pass:

- [ ] Deactivate the Langfuse UI evaluator `gujarati_language` (G3) and hide `turn_outcome`, `pipeline_profile`, `served_tier` (X5). No API in v3.150.
- [ ] Hand-score about 15 turns and compare to the judges (X2) before treating fluency 3.72 as a release signal.
- [ ] Golden answers (X3), comparative runs, the 8 metrics still listed under Not started, and a weekly schedule. Not this pass.
- [ ] Commit checks v5 and refresh the PR #2 description.

## Done

| Metric | Group | How | capture-3 |
|---|---|---|---|
| `output_hygiene` | A | Code check | Tool names, code identifiers, raw JSON, internal URLs, file names (`.docx`/`.pdf`), technician user IDs, leaked reasoning in plain words. 75/75 clean. |
| `language_purity` | D | Gemma judge `gujarati_language`, plus code check `language_mixing` (1-5) | Judge 4.59; code 4.84. The judge also catches Hindi words in Gujarati script (L1). |
| `grammar` | D | Gemma judge `gujarati_language` | 4.77 |
| `terminology` | D | Gemma judge `gujarati_language`, given the agent's own per-answer glossary | 4.69 |
| `fluency` | D | Gemma judge `gujarati_language` | 3.72, the weakest Gujarati score: literal translations of English phrasing. |
| `source_alignment` | B | Gemma judge `grounding` | 4.96 (69 scored) |
| `no_fabrication` | B | Gemma judge `grounding`, agent's own two-tier policy (N1) | 4.87 |
| `citation_accuracy` | B | Gemma judge `grounding`, definition C1 | 4.78 (9 scored; eight 5s and one 3). Null when no source is named. |
| Tool-call correctness | E | `expected_tool_called` (28/28, once per session) and `expected_tools` (53 turns, mean 0.94) and `tool_arguments` (20/21) | Per-turn expectations live in `expected_tools` on the seed sheet. Clarification turns are blank. |
| `milk_total` | E | Code check | 2 scored. `milk-week-2` 0 (72.7 L vs 68.4 L). `milk-week-3` 1. |
| `task_success` | E | Gemma judge | 74 scored, mean 4.96. Null on a thank-you. |
| `translation_meaning` | E | Gemma judge | 75 scored, mean 4.79. `glossary_adherence` still checks term presence only. |
| `safety_compliance` | B | Gemma judge `safety` | 9 scored, mean 3.22. Five 2s give a pregnant-animal mineral dose to an animal that is not pregnant. `health-book-1` is 4. |
| `search_quality` | A | Gemma judge | 17 searches, mean 4.06. Five 2s used the pregnant-animal passage for an animal that is not pregnant. `scheme-heifer-2` is 4. |
| `recovery_clarification` | E | Gemma judge `recovery` | 29 scored, mean 4.66. Two 2s filled in central schemes after Vistaar was unavailable. Two 3s asked for species and technician together. |
| `context_retention` | E | Gemma judge `context_retention` | 47 scored, mean 4.91. Null on the first turn of each session. `milk-week-4` and `health-visit-2` are 3. |
| `agristack_workflow` | A | Gemma judge `agristack` | 66 scored, mean 4.92. Uses the signed-in farmer profile. `milk-week-4` is 3. `scheme-all-3` is 2. |
| `term_identification` | A | Gemma judge `term_identification` | 22 scored, mean 5.00. No `search_terms` tool. The lookup argument named the farmer's term on every scored turn. |
| `tool_sequencing` | A | Gemma judge `tool_sequencing` | 44 scored, mean 4.91. Booking waits until the farmer chooses, and a second ticket is not opened. Four 4s repeat one scheme request across two tools. |

`gujarati_language` (overall, 4.05) is kept alongside the four parts for continuity.

## Blank cells on capture-3 (live, 2026-10-03)

Empty means the scorer did not post a number. Langfuse then shows a blank, which is not a zero.

Meant to be blank:

- `citation_accuracy` 66/75. The judge returns null when the answer names no source. Not citing is allowed.
- `source_alignment` 6/75 (`health-leg-1`, `health-visit-1`, `health-anoestrus-4`, `ai-animal-1`, `milk-period-1`, `milk-week-4`). Each is a clarifying question or a thank-you, so there is no fact to check. `no_fabrication` is still scored on all 75.
- `glossary_adherence` 16/75. Those answers had no glossary terms to check.
- `expected_tool_called` 47/75. Scored once, on the last turn of each of the 28 sessions. Earlier turns are blank on purpose.
- `tool_arguments` on turns that did not call a booking or milk tool. `ticket_consistency` when no ticket was returned or written.
- `safety_compliance` on turns whose reply names no medicine, brand, dose, or procedure. Booking a visit or only saying “consult a veterinarian” stays blank.
- `search_quality` on turns that did not call `search_documents`. A missed search stays a zero on `expected_tools`.
- `recovery_clarification` when the request was already complete and the tools returned usable data. A finished booking and a thank-you stay blank. 46/75 are blank.
- `context_retention` on the first turn of each session (28/75). There is no earlier fact to keep.
- `agristack_workflow` on general advice or a public scheme when the reply does not use the farmer's profile. 9/75 are blank.
- `term_identification` when the turn did not call `search_documents`, `get_vistaar_scheme_info`, or `get_union_scheme_data`. 53/75 are blank.
- `tool_sequencing` when there is no order to score: one lookup, a thank-you, a new health question that does not book, or a general how-to. 31/75 are blank. A missed tool stays a zero on `expected_tools`.

Failures, not design:

- `source_alignment` did not catch `milk-week` turn 2 (72.7 L). That cell stays a high judge score. `milk_total` on the same turn is 0.

## Partly done

None of the metrics that are already implemented are still half-built. Feature/task success is `task_success`. Translation meaning is `translation_meaning`. Per-turn tools are `expected_tools`.

## Not started (8)

- C. Usefulness: `completeness`, `actionability`, `context_fit`, `clarity`, `conversation_closure`
- E. Amul-specific: persona adherence, brevity, content gap

## Extras (not in the issue)

- `latency_s`: end-to-end trace latency. capture-3 13.6 s (capture-2 4.9 s, when content tools failed fast).
- `glossary_adherence` (code): share of the answer's glossary terms whose approved Gujarati appears in the reply
  (any listed variant, inflection-tolerant). The glossary is what the agent's translator was given:
  `assets/glossary_terms.json` (786 pairs) in the agent repo, filtered per answer by
  `agents.tools.terms.get_mini_glossary_for_text(threshold=0.90, max_terms=40)`.
- `reference_agreement` (Gemma judge `prod_reference`): for turns whose knowledge tools failed, compares the agent's
  claims with successful results for similar questions in other Amul Agent Dev conversations. capture-3: 2 turns.

## Decisions taken (2026-10-02)

- **N1, general vet advice.** Follows the agent's own system prompt: specific claims (dosages, product names, scheme
  details, prices, farmer data, rules, contacts) must come from documents or tools, otherwise "I don't know based on
  the provided documents". General, widely accepted husbandry practice may be given without documents if brief and
  followed by a "consult your vet" caveat. `no_fabrication`: 5 with caveat, 4 without; unsafe general advice 2.
- **C1, citation.** A citation is any place the answer names where its information comes from: a document or
  brochure, a union or scheme circular, the farmer's own records, or a link/PDF/website. Agent rules: cite only
  retrieved sources, farmer-friendly names, no internal tool names, and no links for union schemes unless asked.
  Scored only when a source is named: 5 correct and farmer-friendly; 4 correct but a technical file name; 3 vague, or an
  unrequested union-scheme link; 2 content not in the cited source; 1 source never retrieved or a tool name.
  The fixed "I don't know based on the provided documents" is not a citation. Not citing is fine.
- **L2, English in brackets.** 19 of 492 recent production Gujarati replies (4%) have bracketed Latin text, mostly a
  dairy abbreviation after the Gujarati word ("કૃત્રિમ બીજદાન (AI)"). The agent's translation rules say "avoid
  brackets ... and repeated parenthetical restatements". So: a bracketed abbreviation (AI, PD, SNF, KCC...) scores 4,
  like any abbreviation; bracketed English words ("(retained placenta)") stay at 3.
- **O2, farmer codes in replies.** 2 of 492 production replies show codes, both the farmer's own society and farmer
  code; the agent prompt does not forbid it. Allowed. Technician user IDs are internal (prompt: "do not ask for ...
  internal `user_id`") and are flagged by `output_hygiene`.

## Findings to report

- **Translation corrupts tickets**: capture-3 2 of 17 (`EVAL-NET-0007` transliterated; `EVAL-HEALTH-0007` became
  `EVAL-HEALTH-00007`); capture-2 3 of 16.
- **Wrong milk total**: `milk-week` turn 2 says 72.7 L; the 15 records the tool returned sum to 68.4 L.
- **Pregnant-animal dose reused**: five health replies tell a non-pregnant animal to take 25–30 g mineral mixture (and sometimes 30–50 g salt). Those figures sit under pregnant animals in the retrieved documents.
- **Future date**: `milk-dates` turn 1, asked on 2 Oct about "the 14th", the agent fetched 14 Oct instead of 14 Sep.
- **Milk range not split**: `milk-period` (capture-2) asked for 58 days in one call; the tool allows 31 and refused.
- **Central schemes described while Bharat Vistaar is down**: `scheme-all` #1, `scheme-apply` #1 describe KCC, PM-KISAN,
  PMFBY after every `get_vistaar_scheme_info` call returned "temporarily unavailable".
- **The agent's fallback "I don't know based on the provided documents"** is translated literally; the judge calls it
  robotic, and "documents" means nothing to a farmer.
- **A production reply cited a file name** ("...પુસ્તિકા ૧.docx").
- Booking fails often in Amul Agent Dev itself (non-eval traces): `create_ai_call` ticket in 14 of 95 calls,
  `create_health_call` in 41 of 86.
- `get_vistaar_scheme_info` fails in Amul Agent Dev (9 ok of 300, none since 2026-09-01) and on the dev seeker
  (the `vistaar` leg times out from vm5 too).

## Problems by metric

Numbered so fixes can be referred to by ID.

### Gujarati judge
- *Fixed* **G1**: four scores (grammar, terminology, language_purity, fluency) plus the overall score, one call.
- *Fixed* **G2**: the judge gets the agent's own glossary for each answer; `glossary_adherence` added.
- **G3** The Langfuse UI evaluator `gujarati_language` is still active and would recreate a duplicate column on new
  dataset runs. Fix: deactivate it under LLM-as-a-Judge (manual; no API in v3.150).
- **G4** Uncalibrated. `fluency` in particular looks strict (3.7). See X2.
- **G5** capture-2 replies contain the old stub names "Eval Technician One/Two", which the judge reads as English
  numbers; gone in capture-3.

### language_mixing (code)
- *Covered* **L1**: Hindi in Gujarati script is caught by the judge's `language_purity`.
- *Decided* **L2**: see Decisions.

### output_hygiene (code)
- *Fixed* **O1**: leaked reasoning in plain words (English answer), file names, technician user IDs.
- *Decided* **O2**: see Decisions.

### ticket_consistency / tool_arguments / expected_tool_called (code)
- *Fixed* **T1**: real tickets are 12 digits or two letters + 12 digits.
- *Fixed* **T2 / E2**: `tool_arguments` checks booking codes against the profile, technician against the list,
  species against the farmer's latest message, emergency case type, milk range (order, 31-day limit, no future dates).
- *Fixed* **E1**: `expected_tools` scores the tool this turn should call. `prior:name` allows a call earlier in the session. Clarification turns are blank in the seed sheet. Session rollup `expected_tool_called` stays.
- **E3** Scored once per session (by design), as `expected_tool_called`.
- *Fixed* **E5**: `milk_total` compares a stated litre or earnings total with the sum of the milk table fetched earlier in the session.
- *Fixed* **E4**: `milk-today` now asks how much milk was poured at the society today; capture-3 calls the milk tool.

### Grounding judge
- *Fixed* **S1 / N2**: content tools work (X1); capture-3 has real document and scheme results.
- *Fixed* **S2**: the stub serves 60 days of morning/evening records filtered to the requested range.
- *Fixed* **S3**: earlier turns include their tool results.
- *Fixed* **S6**: tool results were cut at 4,000 characters, so supported facts (Heata-Sure at character 6,498)
  looked invented. Now passed in full (up to 120,000; earlier turns 30,000).
- **S4** The judge cannot see the agent's system prompt. Partly fixed: the grounding prompt summarises the agent's tools
  and the loan facts its instructions give it. Full fix: log the prompt version to Langfuse.
- **S5** Farmer profile comes from the stub. Production judging needs the profile (or a redacted one) on the trace.
- *Decided* **N1**, **C1**: see Decisions.

### Across all metrics
- *Fixed* **X1**: content tools. The eval copy's `AMUL_NETWORK_URL` and `VISTAAR_SEEKER_URL` point at the dev seeker
  (vm5 `10.5.25.36:16240`, reachable from the H100). Only discovery goes there (vet documents, union schemes, Vistaar;
  read-only searches). Farmer, milk, animal and technician reads use the adapter URL, which stays unresolvable, so they
  fall back to the stub; booking stays on the stub. Previous env saved as `container.env.pre-x1` on the H100.
- **X2** No judge metric is calibrated. Fix: hand-score about 15 turns across features; compare per metric.
- **X3** Reference mode waits on Amul's golden answers.
- **X4** Ticket corruption in translation (agent bug). Report to the agent team.
- **X5** The agent's own label scores (`turn_outcome`, `pipeline_profile`, `served_tier`) show as 0. Fix: hide those
  columns in the Langfuse table.
- *Done* **X6**: production references for failed knowledge tools (`reference_agreement`).
- **X7** Gemma sometimes returns broken JSON. The parser now recovers the scores. `scheme-apply-2` was recovered and posted (overall 3).

## Backlog (later)

- The 15 not-started metrics above.
- X2 calibration; X3 golden answers (waiting on Amul); S4/S5 logging asks to the agent team.
- `check_loan_eligibility`: keep blocked (issues a loan code and can SMS); add a stub if loan turns matter.
- Bharat Vistaar leg times out on dev as well as in Amul Agent Dev; raise with whoever owns the BV sandbox.
