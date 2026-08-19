You are evaluating the metric: **language_purity** (1–5).

Evaluates whether the response stays in the target language without mixing scripts or words from another language.

**Question:** {{ question }}

**Answer:** {{ answer }}

**Category:** {{ category }}

{% if output_language %}**Expected output language:** {{ output_language }}{% endif %}

---

## Instructions

1. {% if output_language %}The answer should be in **{{ output_language }}**. Evaluate it against that standard.{% else %}Identify the target language by looking at the majority script/language used in the answer. Use that as the standard.{% endif %}
2. Scan the answer for any mixing of foreign scripts or languages.
3. Apply the rubric below — foreign script mixing (non-target, non-English scripts) is the most critical failure.

---

## Rubric (integer score 1–5)

Score **5** (Pure): Entirely in the target language script. No foreign script mixing. No English words at all.

Score **4** (Minimal English): Only rare, universally-accepted technical abbreviations in English are present (e.g. ICAR, IMD, NPSS, PMFBY, APMC, URL, chemical formulae). No English inline words or numerals.

Score **3** (English Technical Terms — Acceptable): English abbreviations, chemical names, scheme acronyms (PMFBY, ICAR, NPSS), English in parentheses for clarification of rare technical terms (e.g. "(Cauliflower)", "(Biosecurity)"), or English numerals used instead of target-script numerals. Acceptable for technical agricultural content. The rest of the response is in the target language.

Score **2** (Unnecessary Code-switching — Problematic): English words used inline where a target-language equivalent is already present in the same sentence (e.g. "Deworming", "Natural farming", "Heat Stress" used alongside their target-language translation). This is avoidable and degrades quality.

Score **1** (CRITICAL — Foreign Script Mixing): A non-target, non-English script appears directly in the text — e.g. Hindi/Devanagari words embedded in a Gujarati or Tamil response, or Malayalam script in a Gujarati response. This is random broken mixing that severely impacts comprehensibility. Examples: "तना छेदक" in Gujarati text, "गोबर" in Gujarati text, "ആക്രമണ" in Gujarati text.

---

## Acceptable vs Problematic (quick reference)

- ✅ **Acceptable**: ICAR, IMD, NPSS, PMFBY, APMC — standard technical acronyms in English
- ✅ **Acceptable**: English in parentheses for rare technical clarification — e.g. "(Cauliflower)", "(Biosecurity)"
- ⚠️ **Borderline / Score 2**: English inline words where the target-language term is already used in the same sentence
- 🚫 **Critical / Score 1**: Hindi/Devanagari, Malayalam, or any other non-target, non-English script mixed directly into sentences

---

The `reason` field must always be in **English**. Mention the specific mixed words/scripts found.

Return **STRICT JSON only**:
`{"score": <1-5 integer>, "reason": "<short>", "rubric": "1-5", "details": {"target_language": "{{ output_language }}", "mixed_language_examples": [], "foreign_script_found": false, "notes": ""}}`
