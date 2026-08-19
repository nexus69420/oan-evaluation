{% set cat = (category or "") | lower %}
{% if "advisory" in cat %}
**Language purity for Advisory responses:**
EXCELLENT: Pure output language throughout, with English only for:
- Chemical/scientific trade names (e.g., Quinalphos, Bt, NPK, Rhizobium)
- Crop variety codes (e.g., TAG-24, ICGS-11)
- Institution abbreviations (e.g., MPKV, ICAR, CICR)

Unnecessary English mixing — using English words where a native-language equivalent exists for common farming terms (spray, varieties, fertilizer, sowing) — scores POOR.
{% elif "mandi" in cat or "market price" in cat or "price" in cat %}
**Language purity for Mandi/Market Price responses:**
EXCELLENT: Pure output language with English only for:
- Market proper nouns (APMC), currency symbol (₹)
- Variety names that are proper nouns

Using English "price" or "market" where output-language equivalents exist scores POOR.
{% elif "weather" in cat %}
**Language purity for Weather responses:**
EXCELLENT: Pure output language with English acceptable for:
- Measurement units (°C, mm, km/h, %)
- Source names (IMD, Skymet)

Using "weather forecast" or "temperature" where output-language equivalents exist scores POOR. Numeral format (local vs Arabic) is a minor issue, not critical.
{% elif "scheme" in cat and "mahadbt" not in cat and "status" not in cat %}
**Language purity for Government Scheme responses:**
EXCELLENT: Pure output language with English acceptable for:
- Official scheme names (PM-KISAN, PMFBY, NDKSP, RWBCIS)
- Portal names (MahaDBT)
- Standard category abbreviations (SC/ST)

Using English vocabulary for common words like "eligibility" or "benefit" where output-language equivalents exist scores POOR.
{% elif "mahadbt" in cat or "status" in cat %}
**Language purity for MahaDBT Status responses:**
EXCELLENT: Pure output language with English acceptable for:
- Portal name (MahaDBT), financial year format (e.g., 2025-2026)
- Masked application IDs

Using "status" or "portal" as English words in an otherwise non-English response scores POOR.
{% elif "service" in cat %}
**Language purity for Agricultural Services responses:**
EXCELLENT: Pure output language with English acceptable for:
- Service abbreviations (KVK, CHC, MSWC), PIN codes, distance units

Using English terms for service types that have standard output-language equivalents scores POOR.
{% elif "contact" in cat %}
**Language purity for Agri Contact responses:**
EXCELLENT: Pure output language throughout. Officer titles and department names should be in the output language. Unnecessary English mixing scores POOR.
{% else %}
**Language purity for {{ category or "this category" }} responses:**
The response should stay in the output language. Technical proper nouns and standard abbreviations in English are acceptable. Unnecessary code-switching or using English where output-language equivalents exist should be penalised proportionally to the frequency.
{% endif %}
