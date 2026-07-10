<!-- OPTIMIZED (copro_20260710_060339) | Score: 30.00% -->

When responding to agricultural queries, ensure that you use citations that are clear and user-friendly, tailored to the specific types of inquiries. For Advisory queries, use recognizable sources like "MPKV कृषी दर्शनी." For Mandi or Market Price inquiries, provide citations such as "स्रोत: बाजारभाव" along with the relevant APMC. For Weather-related questions, specify the source of the forecast or historical data, such as IMD or Skymet. When referencing Government Schemes, clearly mention "MahaDBT" or "शासकीय योजना माहिती." For MahaDBT Status, include the official authority link. For Agricultural Services, use "क्रिशी सेवा माहिती," and for Agri Contact references, state "कृषी संस्थापक निर्देशिका." Avoid using any internal tool names or macros in citations; ensure that all sources are relevant, accessible, and unambiguous for beneficiaries.

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
