You are evaluating the metric: **citation_comprehensiveness** (1–4, retrieved sources only) for two responses.

You must score **only** whether the **retrieved sources** for each response are comprehensive enough to answer the **question**. Do **not** judge the response text itself.

**Question:** {{ question }}

**Category:** {{ category }}

**Retrieved sources for Response A (raw):**
```
{{ retrieved_sources_a }}
```

**Retrieved sources for Response B (raw):**
```
{{ retrieved_sources_b }}
```

---

## Rubric (integer score 1–4, applied independently to each set of sources)

Score **1**: None of the sources have anything relevant for the question (wrong crop, wrong domain, off-topic).
Score **2**: Sources are about the **same crop/scheme/topic** but **do not contain** the information needed to answer the question.
Score **3**: Sources are relevant and answer the question **partially** but miss detail needed for a fully comprehensive answer.
Score **4**: Sources contain **all** the information needed to comprehensively answer the question.

---

Score each set of sources independently, then pick the better one. The `reason` fields must always be in **English**.

Return **STRICT JSON only**:
```json
{
  "score_a": <1-4>,
  "reason_a": "<short>",
  "score_b": <1-4>,
  "reason_b": "<short>",
  "better_response": "<response_a | response_b | both>",
  "better_response_reason": "<why one set of sources is better or why there is no difference>"
}
```
