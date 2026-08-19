{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Context fit standard for Advisory queries:**
Agristack data enables full personalization. EXCELLENT uses ALL applicable data:
- **Location** → references farmer's village/district; informs variety recommendations (region-appropriate varieties)
- **Land size** → scales quantities to actual holding (e.g., "आपल्या १.१७ हेक्टरसाठी ~१२०–१४५ किलो")
- **District** → tailors timing (sowing windows differ by region)
Fetching Agristack but using none of its data in the response scores POOR. Not calling Agristack when it is marked available scores UNACCEPTABLE.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Context fit standard for Mandi/Market Price queries:**
Agristack enables: (1) using the farmer's GPS coordinates directly for the nearest mandi without asking, (2) mentioning the farmer's home location when offering alternative market suggestions. Asking "कोणत्या बाजारातील भाव हवे?" when Agristack has coordinates is UNACCEPTABLE — the agent has the location and should use it.
{% elif "weather" in cat %}
**Context fit standard for Weather queries:**
Agristack GPS coordinates should feed directly into the weather tool — no geocoding step needed when Agristack returns data. EXCELLENT names the specific village in the response ("आपल्या आसराचीवाडी भागासाठी"). When Agristack returns "No farmer information found", correctly fall back to geocoding — do NOT penalize the agent for asking for location in that case.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Context fit standard for Government Scheme queries:**
Agristack enables critical personalization. Check these fields:
- **PoCRA village** → required for ALL ndksp-* schemes. Recommending a PoCRA scheme to a non-PoCRA farmer is UNACCEPTABLE.
- **Caste category** → SC/ST receive higher subsidy % in most schemes; this should be stated.
- **Land size** → small/marginal farmer classification affects eligibility.
- **Gender** → women farmers get higher subsidy in some schemes.
For general info queries (not eligibility-specific), Agristack usage is ACCEPTABLE to skip.
{% elif "mahadbt" in cat or "status" in cat %}
**Context fit standard for MahaDBT Status queries:**
Context fit is N/A for MahaDBT — this tool uses farmer_id from authentication context, not location. Do not penalize for absence of location personalization here.
{% elif "service" in cat %}
**Context fit standard for Agricultural Services queries:**
Agristack coordinates should be used directly to find nearby services — no need to ask the farmer for their location. EXCELLENT uses the farmer's village name when presenting results ("आपल्या खामगाव परिसरात"). UNACCEPTABLE: asking for location when Agristack has returned valid coordinates.
{% elif "contact" in cat %}
**Context fit standard for Agri Contact queries:**
Agristack location directly determines which agricultural assistant has jurisdiction over the farmer's village. EXCELLENT references the farmer's village in the response. If Agristack returns empty, correctly fall back to geocoding the location from the query.
{% else %}
**Context fit for {{ category or "this category" }}:**
Evaluate whether the response uses any available Agristack data (farmer's location, land size, crop profile) to personalize the answer. Generic responses that ignore available profile data score lower.
{% endif %}
