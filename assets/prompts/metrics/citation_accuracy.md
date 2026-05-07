Metric: citation_accuracy.
Question: {{ question }}
Answer: {{ answer }}
Agent turns: {{ agent_turns }}
Rubric: 1-4. Correctness of cited references.
The `reason` field must always be in English.
Return STRICT JSON only: {"score": <number>, "reason": "<short>", "rubric": "1-4", "details": {"incorrect_citations": []}}
