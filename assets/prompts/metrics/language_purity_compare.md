You are evaluating the metric: **language_purity** (1–4) for two responses.

Evaluates whether each response stays in the target language without mixing scripts or words from another language.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4, applied independently to each response)

Score **4**: No language code-switching at all — stays fully in the target language.
Score **3**: Only English full forms or English numerals are used.
Score **2**: Randomly switches to English/Marathi/other-language words in some places.
Score **1**: Entire sections or a large chunk of the answer are in a different language.

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
