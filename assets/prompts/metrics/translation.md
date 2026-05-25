You are evaluating the metric: **translation_accuracy** (1–4).

Evaluates the accuracy of translations, especially for agriculture-specific terminology.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4)

Score **4**: Everything is translated correctly and uses correct agricultural terms in the target language.

Score **3**: General translation is correct but there are some mistakes for agriculture-specific terms, names of schemes, or technical vocabulary.

Score **2**: There are multiple mistakes that change the meaning of the translation in some parts.

Score **1**: There are major errors that change the overall meaning of the answer.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"translation_issues": [], "notes": ""}}`
