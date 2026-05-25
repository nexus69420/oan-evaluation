You are evaluating the metric: **grammar_fluency** (1–4).

Evaluates grammatical correctness in the target language. The response tone should be friendly while speaking in perfect language and style that the farmer can understand easily.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4)

Score **4**: Sounds like a native speaker wrote it — perfect structure, grammar, and a friendly tone.

Score **3**: Grammar and structure are overall correct but the language is too cold/technical, or some parts of the answer don't read very naturally.

Score **2**: Feels word-by-word translated; grammar doesn't make sense in multiple places.

Score **1**: The answer is grammatically completely incorrect.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"grammar_issues": [], "notes": ""}}`
