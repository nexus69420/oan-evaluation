You are evaluating the metric: **actionability** (0/1).

Measures how easily a user (a farmer) can implement the advice provided in the response.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1)

Score **1**: The answer mentions clearly what the farmer can do — clear, concrete action points (e.g., "Install yellow sticky traps 1 foot above the crop canopy and space them 20 meters apart.").

Score **0**: Theoretical or vague advice that provides no clear starting point for the farmer (e.g., "Pest control is important for better yields.").

---

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"actionable_steps": [], "notes": ""}}`
