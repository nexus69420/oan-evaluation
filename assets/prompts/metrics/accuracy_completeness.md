You are evaluating the metric: **accuracy_completeness** (1–4).

Evaluates whether the response accurately and fully answers the user's query. The model is allowed to say that it doesn't have the data to respond to the question if that's the case.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4)

Score **4**: Fully answers **all** aspects of the query with necessary detail (e.g., identifies the pest, provides mechanical control, and lists chemical dosages).

Score **3**: Answers the **main** question but leaves out a **minor** detail (e.g., mentions the pesticide but forgets the water dilution ratio).

Score **2**: Provides a **partial** answer or answers something related to the crop but **not** answering the actual question.

Score **1**: The response is **incorrect** or talks about a **different** scheme/crop/topic than what was asked.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"missing_parts": [], "notes": ""}}`
