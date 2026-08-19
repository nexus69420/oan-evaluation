{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Conversation closure standard for Advisory queries:**
The follow-up must be specific to the actual query topic — e.g., "आपल्या शेतात किती टक्के झाडांवर प्रादुर्भाव दिसत आहे?" (for a pest query) or "रायझोबियम कुठे मिळेल याबद्दल माहिती हवी आहे का?" (after sowing advice). Generic "आणखी काही प्रश्न असल्यास विचारा" scores POOR. The follow-up should help refine advice or open a natural next step, not just acknowledge the conversation.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Conversation closure standard for Mandi/Market Price queries:**
When the requested crop price is unavailable, EXCELLENT closure names specific alternative markets (by market name, not just "nearby market") known to trade that crop — e.g., "जळगाव किंवा अकोला बाजारात तपासू का?" Generic "इतर काही हवे का?" scores POOR. When prices ARE available, a good closure offers to check prices for related crops or alternative markets.
{% elif "weather" in cat %}
**Conversation closure standard for Weather queries:**
Closure should connect to the farmer's immediate agricultural decision — offering a more detailed day-by-day forecast if a summary was given, or asking about a specific crop activity affected by the weather. "इतर काही माहिती हवी का?" scores POOR.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Conversation closure standard for Government Scheme queries:**
EXCELLENT offers a related scheme the farmer may also qualify for (after drip irrigation → mention crop insurance), or to assist with the application process step by step. A dead-end response with no next step is UNACCEPTABLE — scheme queries frequently lead to application questions.
{% elif "mahadbt" in cat or "status" in cat %}
**Conversation closure standard for MahaDBT Status queries:**
EXCELLENT offers either information about the scheme under which the application was filed, or a related service. For "Wait List" or "Cancelled" statuses especially, the farmer needs next steps — a dead-end response here is UNACCEPTABLE.
{% elif "service" in cat %}
**Conversation closure standard for Agricultural Services queries:**
EXCELLENT offers related service types as follow-up (after soil lab → offer CHC; after KVK → offer warehouse). When results are empty, actively offers to check related service types or a broader area. Ending with just "माहिती नाही" after empty results scores POOR.
{% elif "contact" in cat %}
**Conversation closure standard for Agri Contact queries:**
EXCELLENT either: (a) offers guidance on what the located officer specifically handles, or (b) if the query was out of scope (Talathi/NAFED), clarifies the correct department AND provides the agricultural assistant as a starting point. Simply providing a phone number without any follow-up scores ACCEPTABLE at best.
{% else %}
**Conversation closure for {{ category or "this category" }}:**
The follow-up question or closing statement should be specific and relevant to what was just answered, opening a natural next step for the farmer rather than being generic.
{% endif %}
