You are evaluating the metric: **answer_relevance** (1–5).

Evaluates whether the bot's answer actually addresses what the farmer asked —
completely independent of whether the content is factually correct. A confident but
factually wrong answer that stays on-topic should still score high here; a factually
flawless answer that ignores or sidesteps the actual question should score low. The
question/answer may be in any Indian language or English — read them regardless of
language.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–5)

Score **5**: Directly and fully addresses exactly what the farmer asked, staying on
topic throughout.

Score **4**: Addresses the question well; only minor tangential or extra content
that doesn't distract from answering what was asked.

Score **3**: Partially addresses the question — engages with the right general
topic (e.g. right crop/scheme/domain) but misses the specific thing asked, or only
answers part of a multi-part question.

Score **2**: Mostly off-topic — talks about a different crop, scheme, tool, or
subject than what was asked, with only a loose connection to the actual query.

Score **1**: Completely non-responsive — ignores the question, answers something
unrelated, or is a generic deflection with no attempt to engage with what was asked.
(Note: an honest "I don't have this information, here's who to contact instead" IS
responsive — score that on how well it engages with the question, not as an
automatic 1.)

---

The `reason` field must always be in **English**, even when the answer being judged
is not.

Return **STRICT JSON only**:
`{"score": <1-5 integer>, "relevant": <true if score >= 4, else false>, "reason": "<short>"}`
