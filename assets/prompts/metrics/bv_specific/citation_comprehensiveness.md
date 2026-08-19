{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Citation comprehensiveness for Advisory queries:**
Every major factual claim should be traceable to a retrieved source document: variety recommendations, fertilizer dosages, pesticide rates, timing, safety instructions. EXCELLENT: all claims cited or clearly derived from tool output. POOR: multiple claims lack sourcing. UNACCEPTABLE: safety-critical claims (pesticide dosages, waiting periods) are unsourced, which puts the farmer at risk.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Citation comprehensiveness for Government Scheme queries:**
Scheme details (benefit amounts, eligibility conditions, required documents) should all be sourced to the tool output. A response that invents details but attaches a citation label is NOT comprehensive — that is fabrication. EXCELLENT means all tool-provided data is present, accurately reflected, and attributed.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Citation comprehensiveness for Mandi/Market Price queries:**
All price data must be attributable to the mandi_prices tool output. If the tool provided variety-level breakdowns (e.g., Jyoti ₹1000–1100, Local ₹700–800), the response should include them — omitting variety distinctions when available scores ACCEPTABLE at best. A single "स्रोत: बाजारभाव" at the end is sufficient citation structure.
{% elif "weather" in cat %}
**Citation comprehensiveness for Weather queries:**
All weather values must come from the tool (IMD forecast or Skymet historical). If both tools were called (combined query), both should be cited and their data clearly attributed to the correct source. Using IMD data as if it were Skymet (or vice versa) is a citation failure.
{% elif "service" in cat %}
**Citation comprehensiveness for Agricultural Services queries:**
Facility details (names, addresses, distances) must come from the agri_services tool. Phone numbers not in the tool output must NOT be cited as if they came from it. A single "स्रोत: कृषी सेवा माहिती" covers the entire facility list; individual citation per facility is not required.
{% else %}
**Citation comprehensiveness for {{ category or "this category" }}:**
All factual claims in the response should have a basis in tool output. Evaluate how completely the response attributes its information to the data sources used, and whether any key claims are floating without a traceable source.
{% endif %}
