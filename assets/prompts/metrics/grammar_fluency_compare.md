You are evaluating the metric: **grammar_fluency** (1–4) for two responses.

Evaluates grammatical correctness in the target language. The tone should be friendly while speaking in perfect language and style that the farmer can understand easily.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4, applied independently to each response)

Score **4**: Sounds like a native speaker wrote it — perfect structure, grammar, and a friendly tone.
Score **3**: Grammar and structure are overall correct but the language is too cold/technical, or some parts don't read very naturally.
Score **2**: Feels word-by-word translated; grammar doesn't make sense in multiple places.
Score **1**: The answer is grammatically completely incorrect.

---

Score each response independently, then pick the better one. The `reason` fields must always be in **English**.

Return **STRICT JSON only**:
```json
{
  "score_a": <1-4>,
  "reason_a": "<short>",
  "score_b": <1-4>,
  "reason_b": "<short>",
  "better_response": "<response_a | response_b | both>",
  "better_response_reason": "<why one is better or why there is no difference>"
}
```
