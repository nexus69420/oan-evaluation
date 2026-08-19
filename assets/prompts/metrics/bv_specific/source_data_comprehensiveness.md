{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Source data comprehensiveness for Advisory queries:**
EXCELLENT: The response uses all major useful claims available in the retrieved documents — varieties, dosages, timing, safety precautions. If the document contains specific safety data (PPE, waiting period) that protects the farmer, omitting it scores POOR. Selectively extracting only the "easy" parts of a document while omitting the critical safety or dosage details is not comprehensive.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Source data comprehensiveness for Government Scheme queries:**
EXCELLENT: The response covers benefits, eligibility conditions, required documents, portal link, AND personalization signals from Agristack. Omitting key scheme details (benefit amount, PoCRA requirement, subsidy %) when they are present in tool output scores POOR. When `get_multiple_schemes_info` is called, ALL returned schemes should be reflected in the response.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Source data comprehensiveness for Mandi/Market Price queries:**
EXCELLENT: Shows the full price range (min/max/modal) AND variety distinctions if the tool returned them (e.g., Jyoti vs Local varieties at different prices). Omitting the min/max distinction when both are available scores ACCEPTABLE at best. All available crops at the market should be surfaced when the requested crop is unavailable.
{% elif "weather" in cat %}
**Source data comprehensiveness for Weather queries:**
EXCELLENT: Covers all weather parameters the tool returned that are relevant to farming decisions — temperature range, rainfall probability/amount, humidity, wind speed. Omitting rainfall (critical for spray and irrigation decisions) while reporting only temperature scores POOR. All days in the requested forecast window should be covered (at minimum as ranges).
{% elif "mahadbt" in cat or "status" in cat %}
**Source data comprehensiveness for MahaDBT Status queries:**
EXCELLENT: All applications returned by the tool are reported (not just one if multiple exist), each with its masked ID, status, and financial year. Omitting applications from the response when the tool returned them scores POOR.
{% else %}
**Source data comprehensiveness for {{ category or "this category" }}:**
Evaluate whether the response uses all the relevant data returned by the tool(s). Missing information that was available and useful to the farmer scores lower. The response should not selectively report only convenient or positive data.
{% endif %}
