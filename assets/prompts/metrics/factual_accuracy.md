You are evaluating the metric: **factual_accuracy** (1–5).

Evaluates whether the factual claims in the bot's answer are correct — independent of
whether the answer is complete or on-topic. Ground your judgment in the tool
outputs below when tools were used (prices, scheme details, weather data, search
results, milk/document records, etc.). If no tools were used, judge correctness
against your own knowledge of Indian agriculture/government schemes. The answer
may be in any Indian language or English — read it regardless of language.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

**Tool calls made and their outputs (ground truth for grounding, if any):**
{{ agent_turns }}

---

## Rubric (integer score 1–5)

Score **5**: Every factual claim (numbers, dates, prices, eligibility, names, practices)
is correct and, where tools were used, matches the tool output exactly. Also score 5
if the bot has no factual claims to get wrong — e.g. it honestly says it lacks the
data or hit a technical error, without inventing anything.

Score **4**: Factually correct overall; at most a negligible imprecision (e.g. rounding)
that would not mislead the farmer or change what they'd do.

Score **3**: Mostly correct but contains one minor factual error or an imprecise
number/fact not supported by the tool output — could mildly mislead but isn't
dangerous or central to the answer.

Score **2**: Contains a significant factual error — a wrong price, date, dosage,
eligibility rule, or scheme detail — that is not supported by the tool output or by
correct agricultural/policy knowledge.

Score **1**: The answer is fabricated (invents data the tools didn't return),
directly contradicts the tool output, or states something factually false in a way
that could cause real harm (e.g. wrong pesticide dosage, wrong subsidy amount,
wrong contact/timeline promised as certain).

---

The `reason` field must always be in **English**, even when the answer being judged
is not.

Return **STRICT JSON only**:
`{"score": <1-5 integer>, "factually_correct": <true if score >= 4, else false>, "reason": "<short>", "evidence": "<what in the answer or tool output drove this score>"}`
