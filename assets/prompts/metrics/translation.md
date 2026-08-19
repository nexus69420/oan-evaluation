You are evaluating the metric: **language_quality** (1–10).

Evaluates the quality of the language used in the response — correct word choice, natural phrasing, appropriate vocabulary, and proper use of domain-specific terms. This is **not** about whether a translation was performed; it is about how well the response is written in whatever language it uses.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

---

## Instructions

1. Identify the primary language of the **answer** (e.g. Tamil, Hindi, Kannada, Telugu, Bengali, English). If the answer mixes languages, judge the dominant one.
2. Evaluate whether the words, phrases, and agricultural/scheme-related terminology are correct and natural in that language.
3. Do **not** penalise for factual accuracy — that is handled by a separate metric. Focus only on language quality.

---

## Rubric (integer score 1–10)

Score **10**: Perfectly natural language throughout. All agricultural terms, scheme names, units (e.g. quintal, bigha, acre), and technical vocabulary are used correctly in the target language.

Score **8–9**: Mostly natural; one or two minor word choices are slightly awkward or a term is partially transliterated when a local equivalent exists, but meaning is clear.

Score **6–7**: Generally understandable but several terms are awkward, incorrectly borrowed from English when a local word exists, or domain vocabulary is inconsistent.

Score **4–5**: Multiple unnatural or incorrect word choices that make some sentences hard to follow, or key agricultural/scheme terms are consistently wrong or missing.

Score **2–3**: Frequent errors in word choice or phrasing that distort meaning in several places; the language feels machine-generated or incoherent.

Score **1**: The language quality is so poor that the response is largely incomprehensible, or the response is entirely in the wrong language relative to what the question expects.

---

The `reason` field must always be in **English**. Mention which specific words or phrases are incorrect and what the correct form would be.

Return **STRICT JSON only**:
`{"score": <1-10 integer>, "reason": "<short>", "rubric": "1-10", "details": {"language": "<detected language>", "issues": [], "notes": ""}}`
