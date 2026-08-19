You are evaluating the metric: **actionability** (0/1) for two responses.

Measures how easily a user (a farmer) can implement the advice provided.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1, applied independently to each response)

Score **1**: The answer mentions clearly what the farmer can do — clear, concrete action points.
Score **0**: Theoretical or vague advice that provides no clear starting point for the farmer.

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
