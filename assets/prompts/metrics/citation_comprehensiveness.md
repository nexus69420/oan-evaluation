You are evaluating the metric: citation_comprehensiveness.
Question: {{ question }}
Answer: {{ answer }}
Category: {{ category }}
Agent turns: {{ agent_turns }}
Rubric: 1-4. Score if sources pulled are sufficient for comprehensive answer.
The `reason` field must always be in English.
Return STRICT JSON only: {"score": <number>, "reason": "<short>", "rubric": "1-4", "details": {"missing_sources": [], "notes": ""}}
