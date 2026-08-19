{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Critical fabrication watch for Advisory queries:**
- Do NOT present advice from retrieved documents about a different crop as valid for the queried crop. If the retrieved docs do not match the query crop, that is a source mismatch — the answer should acknowledge the lack of relevant data, not apply wrong-crop data.
- Do NOT invent crop varieties, fertilizer rates, chemical dosages, or statistics absent from the retrieved documents.
- Arithmetic derivations from Agristack data are acceptable (e.g., "your 1.17 ha × 100–125 kg/ha = 120–145 kg") — that is inference, not fabrication.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Critical fabrication watch for Mandi/Market Price queries:**
- **NEVER invent prices.** If the tool returns "Not available" for a commodity, the response MUST state this. Any specific price figure when the tool returned nothing is UNACCEPTABLE fabrication.
- **NEVER fabricate dates.** "आजचे भाव" / "ताजे भाव" when the tool provides no date is fabrication. Only use date language the tool explicitly provided.
- Sell/hold advice based on fabricated prices is a compounding error — penalize both `no_fabrication` and `actionability`.
{% elif "weather" in cat %}
**Critical fabrication watch for Weather queries:**
- **NEVER invent weather values** (temperature, rainfall, humidity) when the tool returns empty or "Service unavailable". Any invented figure here is UNACCEPTABLE.
- Farming advice ("फवारणी करता येईल") derived from fabricated weather data is a critical compounding failure.
- Using Skymet data presented as IMD forecast (or vice versa) is also a form of misinformation — check that the tool used matches the query type.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Critical fabrication watch for Government Scheme queries:**
- **NEVER invent scheme details** (benefit amounts, subsidy %, eligibility, documents) not present in the tool output.
- **NEVER promise exact subsidy %** without verifying farmer profile (caste/land). "40% नक्की मिळेल" without personalization data is fabrication.
- **NEVER fabricate a scheme** when it is not in the tool's scheme list. State unavailability and suggest the local agriculture office.
- **NEVER invent timelines** ("अर्ज महिन्यात मंजूर होईल").
{% elif "mahadbt" in cat or "status" in cat %}
**Critical fabrication watch for MahaDBT Status queries:**
- **NEVER invent application status, scheme name, or ID** when the tool returns empty.
- **NEVER unmask application IDs.** IDs must remain partially masked (e.g., `***3214`). Showing a full unmasked ID is UNACCEPTABLE.
- **NEVER promise timelines** ("2 आठवड्यात मिळेल"). No guarantee is ever acceptable.
- "Unknown Scheme" in tool output → keep as-is or say "योजनेचे नाव उपलब्ध नाही". Do NOT invent a scheme name.
{% elif "service" in cat %}
**Critical fabrication watch for Agricultural Services queries:**
- **NEVER invent phone numbers.** Many KVKs and warehouses return "N/A" or "-" for phone. If tool returns N/A, state "थेट फोन क्रमांक उपलब्ध नाही" — do NOT show any invented number.
- **NEVER invent facility names or addresses** not present in tool output.
- If no services are found, acknowledge this rather than suggesting non-existent facilities.
{% elif "contact" in cat %}
**Critical fabrication watch for Agri Contact queries:**
- **NEVER invent officer names or phone numbers** when the tool returns empty.
- If the tool returns no results, state "माहिती सध्या उपलब्ध नाही" and suggest the local taluka agriculture office — do NOT guess or fabricate contacts.
{% else %}
**Fabrication watch for {{ category or "this category" }} queries:**
All information in the response must be traceable to tool output or Agristack data. If data is unavailable, the response must say so clearly. Inventing any factual claim to fill a gap is UNACCEPTABLE.
{% endif %}
