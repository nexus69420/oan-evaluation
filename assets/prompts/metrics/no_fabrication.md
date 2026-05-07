You are evaluating the metric: no_fabrication.
Question: {{ question }}
Answer: {{ answer }}
Agent turns: {{ agent_turns }}
Rubric: 0 or 1. 1 means no hallucinated/unsupported claims.
The `reason` field must always be in English.
Return STRICT JSON only: {"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"fabricated_claims": []}}
