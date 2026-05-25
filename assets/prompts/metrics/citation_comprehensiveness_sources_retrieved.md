You are evaluating the metric: **citation_comprehensiveness** (retrieved sources only).

You must score **only** whether the **retrieved sources** (below) are comprehensive enough to answer the **question**. Do **not** use or judge the assistant’s final answer; it may be omitted from your reasoning. If the sources block is empty or unusable, explain that and assign the lowest appropriate score.

**Question:** {{ question }}

**Category:** {{ category }}

**Retrieved sources (raw):**
```
{{ retrieved_sources }}
```

---

## Rubric (integer score 1–4)

Score **1** if none of the sources have anything relevant for the question (e.g. wrong crop, wrong domain, unrelated scheme, or off-topic).

Score **2** if the sources are about the **same crop / scheme / topic** as the question but **do not contain** the information needed to answer the question (only general background in the right area).

Score **3** if the sources are relevant and answer the question **partially** but **miss detail** that would be needed for a **fully** comprehensive answer.

Score **4** if the sources contain **all** the information that would be needed to comprehensively answer the question (for the topic as asked). It can have irrelevant sources as long as relevant info is covered in others

### Scoring logic (examples)

- Question: *How do I manage whiteflies in cotton?*
  - **4**: Sources include cotton + whitefly management specifics (e.g. control practices for whiteflies on cotton).
  - **3**: e.g. pesticide/cotton management is covered but whiteflies specifically are thin or missing.
  - **2**: Only general cotton information, nothing that answers whitefly management.
  - **1**: None of the sources are really about cotton (or are entirely irrelevant).

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4 sources-only", "details": {"missing_or_irrelevant": "", "notes": ""}}`

If there are truly no usable retrieved sources, use score **1** and state that in `reason`.
