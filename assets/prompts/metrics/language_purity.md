You are evaluating the metric: **language_purity** (1–4).

Evaluates whether the response stays in the target language without mixing scripts or words from another language. For example, if the answer is in Gujarati, it should not add English full forms or English numerals.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4)

Score **4**: No language code-switching at all — the answer stays fully in the target language.

Score **3**: Only English full forms are being used, or English numerals are being used (e.g., writing numbers in English script instead of the target script).

Score **2**: Randomly switches to English/Marathi/other-language words in some places.

Score **1**: Entire sections or a large chunk of the answer are in a different language.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"mixed_language_examples": [], "notes": ""}}`
