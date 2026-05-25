You are evaluating the metric: **source_data_comprehensiveness** (0/1).

Checks whether the bot gives a relevant answer versus saying that it does not have the data to respond to the question.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1)

Score **1**: The bot gives a **relevant answer** to the question.

Score **0**: The bot says that it **does not have the data** to respond to the question, or explicitly declines to answer due to lack of information.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"notes": ""}}`
