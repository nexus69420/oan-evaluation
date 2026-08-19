You are evaluating the metric: **terminology** (1–4).

Evaluates whether the response uses correct agricultural and domain-specific terminology. This includes crop names, pest/disease names, fertilizer and chemical names, government scheme names, and any technical terms relevant to Indian agriculture.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 1–4)

Score **4**: All domain-specific terms are correct — crop varieties, pesticide/fertiliser names, scheme names, and dosages are accurate and used appropriately.

Score **3**: Most terminology is correct but there are **minor** errors, such as an imprecise chemical name, wrong dosage unit, or an informal rather than standard term.

Score **2**: Several domain terms are incorrect or confused — e.g., wrong scheme name, incorrect pesticide name, or generic words used where specific terms are required.

Score **1**: Terminology is **consistently wrong or misleading** — incorrect scheme/crop/chemical names that could cause the farmer to take the wrong action.

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <1-4 integer>, "reason": "<short>", "rubric": "1-4", "details": {"incorrect_terms": [], "notes": ""}}`
