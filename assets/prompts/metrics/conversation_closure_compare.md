You are evaluating the metric: **conversation_closure** (0/1) for two responses.

Assesses if the model ends the message in a way that transitions to the next step, completes the conversation, or asks a relevant follow-up.

**Question:** {{ question }}

**Response A:** {{ response_a }}

**Response B:** {{ response_b }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1, applied independently to each response)

Score **1**: Provides a clear closing **or** asks a relevant follow-up to keep the user supported.
Score **0**: Ends abruptly or leaves the user unsure if the model is finished.

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
