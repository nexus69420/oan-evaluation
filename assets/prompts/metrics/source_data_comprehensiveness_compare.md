You are evaluating the metric: **source_data_comprehensiveness** (0/1) for two responses.

Checks whether the bot gives a relevant answer versus saying that it does not have the data to respond.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1, applied independently to each response)

Score **1**: The bot gives a **relevant answer** to the question.
Score **0**: The bot says that it **does not have the data** to respond, or explicitly declines to answer due to lack of information.

---

Score each response independently, then pick the better one. The `reason` fields must always be in **English**.

Return **STRICT JSON only**:
```json
{
  "score_a": <0_or_1>,
  "reason_a": "<short>",
  "score_b": <0_or_1>,
  "reason_b": "<short>",
  "better_response": "<response_a | response_b | both>",
  "better_response_reason": "<why one is better or why there is no difference>"
}
```
