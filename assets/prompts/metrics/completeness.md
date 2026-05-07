Metric: completeness.
Question: {{ question }}
Answer: {{ answer }}
Rubric: 1-4. Whether answer fully addresses user query.
The `reason` field must always be in English.
Return STRICT JSON only: {"score": <number>, "reason": "<short>", "rubric": "1-4", "details": {"missing_parts": []}}
