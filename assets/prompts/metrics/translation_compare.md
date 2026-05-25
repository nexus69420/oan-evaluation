You are evaluating the metric: **translation_accuracy** (1–4) for two responses.

Evaluates the accuracy of translations, especially for agriculture-specific terminology.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4, applied independently to each response)

Score **4**: Everything is translated correctly and uses correct agricultural terms in the target language.
Score **3**: General translation is correct but there are some mistakes for agriculture-specific terms or technical vocabulary.
Score **2**: There are multiple mistakes that change the meaning of the translation in some parts.
Score **1**: There are major errors that change the overall meaning of the answer.

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
