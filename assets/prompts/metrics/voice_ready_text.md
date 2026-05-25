You are evaluating the metric: **voice_ready_text** (0/1).

Output should be pure speech text, devoid of any text/chat artifacts like `:`, `*`, `#`, `|`, `[`, `]`, `**`, `- `, markdown headers, bullet-point symbols, or any formatting that a TTS system would read aloud literally (e.g., the AI saying "Asterisk," "Bullet point," "Bold," "Hash," "Colon," etc.).

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Rubric (integer score 0 or 1)

Score **1**: The text is clean — no markdown, no bullet-point markers, no formatting symbols. Everything in the answer is naturally speakable without the TTS reading out artifacts.

Score **0**: The answer contains symbols or formatting that a TTS system would speak aloud literally (e.g., asterisks read as "Asterisk," colons read as "Colon," bullet markers read as "Bullet point," etc.).

---

**Important:** In the `details` field, list every specific word or symbol that would be spoken as an artifact by the TTS (e.g., `"*"`, `"**"`, `"#"`, `":"`, `"- "`, `"|"`, `"```"`).

The `reason` field must always be in **English**.

Return **STRICT JSON only**:
`{"score": <0_or_1>, "reason": "<short>", "rubric": "0/1", "details": {"spoken_artifacts": ["<symbol_or_word>", "..."], "notes": ""}}`
