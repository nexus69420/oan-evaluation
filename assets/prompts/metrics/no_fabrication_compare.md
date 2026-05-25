You are evaluating the metric: **no_fabrication** (0/1) for two responses.

The model must not provide advice, dosages, or "common knowledge" facts that are not in the retrieved sources. If the sources do not contain relevant information, the model must state that it does not have the answer. It is a failure (Score 0) if the model uses external facts to "fill the gaps."

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

**Retrieved sources (raw):**
```
{{ retrieved_sources }}
```

---

## Rubric (integer score 0 or 1, applied independently to each response)

Score **1** (No Fabrication): Every fact, number, and instruction in the answer is found in the retrieved sources. If sources are irrelevant, the model correctly states it cannot answer.
Score **0** (Fabricated): The response includes some fact, number, or instruction **not found** in the sources, or it provides a "correct" answer using external knowledge because the sources were insufficient.

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
