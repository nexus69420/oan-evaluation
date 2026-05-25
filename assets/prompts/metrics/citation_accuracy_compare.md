You are evaluating the metric: **citation_accuracy** (0/1) for two responses.

Evaluates whether the model correctly attributes information to the provided sources and ensures that every piece of information used is properly cited.

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

Score **1**: All information pulled from sources is correctly cited with the corresponding reference. Citations are present where expected (especially for advisory-style questions).
Score **0**: No citations are provided at all when it's an advisory-style question, **or** a citation points to the wrong source.

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
