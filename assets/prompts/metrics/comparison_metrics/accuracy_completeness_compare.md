You are evaluating the metric: **accuracy_completeness** (1–4) for two responses.

Evaluates whether each response accurately and fully answers the user's query. The model is allowed to say that it doesn't have the data to respond if that's the case.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4, applied independently to each response)

Score **4**: Fully answers **all** aspects of the query with necessary detail.
Score **3**: Answers the **main** question but leaves out a **minor** detail.
Score **2**: Provides a **partial** answer or answers something related but **not** the actual question.
Score **1**: The response is **incorrect** or talks about a **different** scheme/crop/topic.

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
