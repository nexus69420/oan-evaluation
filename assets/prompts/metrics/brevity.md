You are evaluating the metric: **brevity** (1–4).

The answer should be short and spoken in under 30 seconds. If a comprehensive answer would be long, the bot should say the crux/first part and ask a follow-up for the rest.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

**Word count:** {{ word_count }}

---

## Rubric (integer score 1–4)

As a rough guide: ~30 seconds of speech ≈ 70–80 words; ~60 seconds ≈ 140–160 words. Use these as reference but judge holistically — a tightly worded 90-word answer may still feel "under 30 seconds" while a padded 60-word answer may not.

Score **4**: The response is compact, can be spoken in **under 30 seconds**, and includes a **follow-up question** offering to continue with the rest of the answer.

Score **3**: The response is short (speakable in under 30 seconds) but there is **no proper follow-up** question for the remaining detail.

Score **2**: The response is **around 30–60 seconds** of speech — too long for a single voice turn but not excessively so.

Score **1**: The response is **more than 60 seconds** of speech — far too long for a voice interaction.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"estimated_seconds": <number>, "has_followup": <true_or_false>, "notes": ""}}`
