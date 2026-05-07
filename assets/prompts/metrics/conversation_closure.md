Metric: conversation_closure.
Question: {{ question }}
Answer: {{ answer }}
Rubric: 0/1. Does answer close interaction well with next step/follow-up.
The `reason` field must always be in English.
Return STRICT JSON only: {"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"closure_quality": ""}}
