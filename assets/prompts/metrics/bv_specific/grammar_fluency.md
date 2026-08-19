{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Grammar & fluency for Advisory responses:**
Evaluate the response prose for correctness and natural flow appropriate for a rural farmer audience. Technical content (chemical trade names, variety codes like TAG-24, institution abbreviations like MPKV) may appear in English within an otherwise non-English response — this is acceptable and should not be counted as a grammar error. Focus on sentence completeness, grammatical agreement, and natural phrasing in the output language.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Grammar & fluency for Mandi/Market Price responses:**
Mandi responses are typically structured with bullet points for price data. Evaluate grammar in the prose sections — the opening statement, any alternative suggestions, and the follow-up question. Minor number formatting inconsistency (currency symbol placement, numeral style) is a minor fluency issue, not a critical error.
{% elif "weather" in cat %}
**Grammar & fluency for Weather responses:**
The translation of weather data into farming advice should read naturally and conversationally in the output language. Stilted, over-literal phrasing scores lower than fluid, natural guidance. Measurement units (°C, mm, km/h, %) in English are not grammar errors. Evaluate the connecting prose that bridges weather data to actionable farming recommendations.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Grammar & fluency for Government Scheme responses:**
Scheme responses typically use structured lists and headers. Evaluate grammar in the connecting prose, eligibility explanations, and closing question. Official scheme names in English (PM-KISAN, PMFBY, MahaDBT) are proper nouns — not grammar errors.
{% elif "mahadbt" in cat or "status" in cat %}
**Grammar & fluency for MahaDBT Status responses:**
These are typically short, factual responses. Evaluate clarity and naturalness. Status descriptions should flow naturally in the output language rather than importing English status labels untranslated into non-English prose.
{% elif "service" in cat %}
**Grammar & fluency for Agricultural Services responses:**
Evaluate the prose that introduces and closes the facility list, not just the list entries themselves. Numeral format for distances (local vs Arabic numerals) is a minor style preference, not a grammar error.
{% elif "contact" in cat %}
**Grammar & fluency for Agri Contact responses:**
These are short structured responses. Evaluate the prose framing the contact details and any explanatory sentences. The tone should be respectful and natural for a farmer seeking official assistance.
{% else %}
**Grammar & fluency for {{ category or "this category" }} responses:**
Evaluate whether the response reads naturally and correctly in the output language. Minor errors that do not affect meaning score GOOD. Multiple errors that affect comprehension score POOR.
{% endif %}

{# --- terminology --- #}
{% if "advisory" in cat %}
**Domain terminology for Advisory responses:**
Verify correct use of agricultural domain terms in the output language:
- Crop stages: seed treatment, germination, flowering stage, grain/pod filling, harvest
- Practices: sowing, transplanting, inter-cultivation, weed control, spraying
- Inputs: fertilizer, insecticide, fungicide, herbicide, bio-control agent
- Units: kg/ha, ml/10 litre water, g/kg seed

Chemical trade names and variety codes in English are acceptable regardless of output language. Using generic or improvised terms where precise domain terms exist scores POOR.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Domain terminology for Mandi/Market Price responses:**
Key domain terms to verify (in the output language):
- Price / market price
- Quintal (standard mandi weight unit)
- Arrivals (आवक — crop supply volume at market)
- Minimum support price / MSP
- Min / max / modal price
- Variety (used when prices differ by crop variety)

Using imprecise or improvised substitutes where standard market-price terms exist scores POOR.
{% elif "weather" in cat %}
**Domain terminology for Weather responses:**
Key weather terms to verify (in the output language):
- Temperature, minimum temperature, maximum temperature
- Humidity
- Rainfall / precipitation
- Weather forecast / weather history
- Wind speed

Measurement units (°C, mm, km/h, %) in English are acceptable regardless of output language. Using informal or imprecise weather vocabulary scores POOR.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Domain terminology for Government Scheme responses:**
Key scheme terms (in the output language):
- Scheme, subsidy/grant, eligibility, benefit
- Application process, required documents
- PoCRA (proper noun — use as-is)
- Insurance / guarantee

Official scheme names (PM-KISAN, PMFBY, NDKSP, MahaDBT) are acceptable in English as proper nouns. Using informal substitutes for standard scheme terminology scores POOR.
{% elif "mahadbt" in cat or "status" in cat %}
**Domain terminology for MahaDBT Status responses:**
Key status terms (in the output language):
- Wait list / queue (application in queue)
- Fund disbursed
- Approved
- Department cancelled / auto cancelled
- Financial year

Status terms should be expressed naturally in the output language — mixing English status labels into a non-English response without adaptation scores POOR.
{% elif "service" in cat %}
**Domain terminology for Agricultural Services responses:**
Key service-type terms (in the output language):
- Soil testing laboratory (not abbreviated informally)
- Custom Hiring Centre / equipment bank (CHC acceptable as abbreviation)
- Krishi Vigyan Kendra (KVK acceptable)
- Warehouse / storage facility

Using informal English service names where output-language equivalents exist scores POOR.
{% elif "contact" in cat %}
**Domain terminology for Agri Contact responses:**
- Agricultural assistant (the specific role this tool covers — village level)
- Taluka agriculture officer (higher level, different role)
- Revenue department (for Talathi/7-12 matters — out of scope for this tool)

Do NOT conflate an agricultural assistant with a taluka agriculture officer — different ranks and jurisdictions.
{% else %}
**Terminology for {{ category or "this category" }}:**
Evaluate whether the response uses correct domain-specific agricultural terminology in the output language. Generic or improvised terms where precise domain terms exist should score lower.
{% endif %}
