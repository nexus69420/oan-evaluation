<!-- OPTIMIZED (copro_20260710_060521) | Score: 50.00% -->

**Actionability standard for this category:**
Responses should give the farmer something concrete to act on — not just information. Evaluate whether specific next steps, contacts, quantities, or timing are present and usable.

<!-- JINJA TEMPLATE -->
{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Actionability standard for Advisory queries:**
EXCELLENT requires specific, usable details: named varieties (not "good varieties"), exact dosages ("क्विनॉलफॉस २५ EC @ २० मिली/१० लिटर"), specific timing ("फुलोरा अवस्थेत पहिली फवारणी"), and quantities scaled to the farmer's land size when Agristack data is available (e.g., "आपल्या १.१७ हेक्टरसाठी ~१२०–१४५ किलो"). Generic phrases like "कीटकनाशक फवारावे" or "खत द्यावे" without specifics score POOR.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Actionability standard for Mandi/Market Price queries:**
Raw price data without framing scores POOR. EXCELLENT provides sell/hold/store guidance contextualised by the prices. When the requested crop is unavailable, the most actionable response names specific alternative crops with prices at the same or nearby markets. "विक्रीसाठी योग्य वेळ" based on fabricated prices is a critical failure, not actionability.
{% elif "weather" in cat %}
**Actionability standard for Weather queries — KEY metric:**
Presenting only raw numbers (temperature, rainfall, humidity) scores POOR at best. EXCELLENT translates each key weather signal into a farming action:
- Rain expected → "फवारणी टाळा"
- Frost/low temp nights → "रोपांना आच्छादन द्या"
- High winds (>10 km/h) → "फवारणी टाळा"
- Clear days → "सिंचनाचे नियोजन करा" or "काढणीस योग्य वेळ"
The response must bridge from data to what the farmer should DO.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Actionability standard for Government Scheme queries:**
EXCELLENT includes: the correct portal URL (mahadbt.maharashtra.gov.in or pmkisan.gov.in), a specific documents list (७/१२ उतारा, आधार, बँक पासबुक, जातीचा दाखला as applicable), and the application steps. Generic "कृषी कार्यालयात संपर्क साधा" without any specifics scores POOR.
{% elif "mahadbt" in cat or "status" in cat %}
**Actionability standard for MahaDBT Status queries:**
EXCELLENT provides concrete next steps matched to the actual status shown:
- Wait List → "MahaDBT पोर्टलवर नियमित तपासा" or "स्थानिक कृषी कार्यालयाशी संपर्क साधा"
- Cancelled → guidance on re-application or whom to approach
Never promise timelines ("X आठवड्यात मिळेल") or guarantee approval.
{% elif "service" in cat %}
**Actionability standard for Agricultural Services queries:**
Phone + address alone is GOOD. EXCELLENT adds practical guidance specific to the service type:
- Soil lab: "माती नमुना योग्य रित्या घ्या; फोन करून वेळ निश्चित करा"
- CHC: "यंत्राची उपलब्धता व भाडे दर आधी विचारा"
- KVK with N/A phone: "थेट फोन उपलब्ध नाही; प्रत्यक्ष भेट द्या"
{% elif "contact" in cat %}
**Actionability standard for Agri Contact queries:**
EXCELLENT includes the phone number from the tool AND a brief note on the officer's specific scope (पीक सल्ला, योजना माहिती, समस्या निवारण). Name + number alone, without context on what the officer handles, scores ACCEPTABLE at best.
{% else %}
**Actionability standard for {{ category or "this category" }}:**
Responses should give the farmer something concrete to act on — not just information. Evaluate whether specific next steps, contacts, quantities, or timing are present and usable.
{% endif %}
