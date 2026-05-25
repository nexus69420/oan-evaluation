You are evaluating the metric: **conversation_closure** (0/1).

Assesses if the model ends the message in a way that transitions to the next step, completes the conversation, or asks a relevant follow-up to keep the user supported.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1)

Score **1**: Provides a clear closing **or** asks a relevant follow-up to keep the user supported (e.g., "I hope this helps your cotton crop. Do you want exact measurements of fertilizer required?").

Score **0**: Ends abruptly or leaves the user unsure if the model is finished (e.g., the answer simply ends with ".. Add 5 grams of potash." with no closing or follow-up).

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"closure_quality": "", "notes": ""}}`
