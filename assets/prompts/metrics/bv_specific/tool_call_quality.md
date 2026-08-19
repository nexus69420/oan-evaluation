{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Term identification standard for Advisory queries — CRITICAL metric:**
Before calling `search_documents`, the agent MUST call `search_terms` for EACH relevant concept in the query:
- The **crop name** (e.g., "भुईमूग" → Groundnut)
- The **problem or practice** (e.g., "बोंडअळी" → Bollworm, "पेरणी" → Sowing)
- Secondary aspects where relevant (fertilizer type, irrigation method)

EXCELLENT: All key query concepts searched in parallel before documents.
POOR: Crop name searched but problem/practice omitted.
UNACCEPTABLE: Jumped directly to `search_documents` with no `search_terms` calls — this risks retrieving wrong-crop documents, which is a root cause of factual failures.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Term identification standard for Government Scheme queries:**
Term identification means correctly mapping the user's query language to the right scheme code(s):
- "पिक विमा" → both mahadbt-pmfby AND mahadbt-rwbcis
- "ड्रिप सिंचन" → ndksp-drip-irrigation AND mahadbt-pmkrvypdmc
- "शेती यंत्र / ट्रॅक्टर" → sdda-farm-machinery AND cdda-farm-machinery
- Misconception correction (user asks wrong scheme for their need) = EXCELLENT term identification

UNACCEPTABLE: Selecting a wrong scheme and not recognizing the mismatch.
{% else %}
**Term identification for {{ category or "this category" }}:**
This sub-dimension is N/A for non-advisory, non-scheme queries where no document/term search step is required. Mark as N/A.
{% endif %}
