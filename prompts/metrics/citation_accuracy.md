<!-- OPTIMIZED (stage2_20260708_032813) | Score: 85.19% -->

In providing responses for different types of queries regarding agricultural information, use the proper citation format that aligns with the specified categories. For Advisory queries, cite using user-friendly source names like "MPKV कृषी दर्शनी" or similar recognized entities. For Mandi/Market Price queries, include citations such as "स्रोत: बाजारभाव" or an appropriate market name with APMC. For Weather queries, state the forecast or historical source specifically as noted (e.g., IMD or Skymet). Government Scheme references should unambiguously mention "MahaDBT" or "शासकीय योजना माहिती". For MahaDBT Status, ensure to cite the authority link. Agricultural Services references should succinctly note "क्रिशी सेवा माहिती", while Agri Contact citations should name "कृषी संस्थापक निर्देशिका". Remember, attaching any internal tool names or any macros is strictly unacceptable; the sources need to be relevant and accessible to the beneficiaries, resistant to ambiguity.

<!-- JINJA TEMPLATE -->
{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Expected citation format for Advisory queries:**
Source name should be a farmer-friendly label matching the retrieved document — e.g., "MPKV कृषी दर्शनी", "ICAR प्रकाशन", "कृषी विद्यापीठ मार्गदर्शन". Using internal tool names ("search_documents", "search_terms") as citations is UNACCEPTABLE. Generic "स्रोत: इंटरनेट" is POOR.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Expected citation format for Mandi/Market Price queries:**
Correct: "स्रोत: बाजारभाव" or "स्रोत: [Market Name] APMC" (e.g., "स्रोत: मुंबई APMC बाजारभाव"). Using "mandi_prices", "forward_geocode", or any tool name as citation is UNACCEPTABLE.
{% elif "weather" in cat %}
**Expected citation format for Weather queries:**
- Forecast queries: "स्रोत: हवामान अंदाज (IMD)"
- Historical queries: "स्रोत: हवामान इतिहास (Skymet)"
- Combined queries: both sources cited
Using "weather_forecast" or "weather_historical" as citations is UNACCEPTABLE. Generic "हवामान विभाग" without naming IMD or Skymet is POOR.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Expected citation format for Government Scheme queries:**
Correct: "स्रोत: शासकीय योजना माहिती" or "स्रोत: MahaDBT". Using "get_scheme_info", "get_scheme_codes", "get_multiple_schemes_info" as citations is UNACCEPTABLE.
{% elif "mahadbt" in cat or "status" in cat %}
**Expected citation format for MahaDBT Status queries:**
Correct: "स्रोत: महाडीबीटी अर्ज स्थिती". Using "get_scheme_status" as citation is UNACCEPTABLE.
{% elif "service" in cat %}
**Expected citation format for Agricultural Services queries:**
Correct: "स्रोत: कृषी सेवा माहिती". Using "agri_services" or "forward_geocode" as citation is UNACCEPTABLE.
{% elif "contact" in cat %}
**Expected citation format for Agri Contact queries:**
Correct: "स्रोत: कृषी संस्थापक निर्देशिका". Using "contact_agricultural_staff" as citation is UNACCEPTABLE.
{% else %}
**Citation format for {{ category or "this category" }}:**
The citation should be a farmer-friendly label for the data source, not an internal tool name. Tool names ("get_*", "fetch_*", "search_*", "forward_geocode") in citations are always UNACCEPTABLE.
{% endif %}
