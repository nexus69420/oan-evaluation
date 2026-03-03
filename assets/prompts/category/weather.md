# Weather Evaluation Guide

## 1. Overview

**Weather queries** ask about upcoming weather conditions. Farmers need this for irrigation planning, spraying decisions, harvest timing, and crop protection.

### Tools

| Tool | Purpose | Source Citation |
|------|---------|-----------------|
| `forward_geocode(place_name)` | Converts place name to latitude/longitude | — |
| `weather_forecast(latitude, longitude)` | Upcoming weather forecast for a location | IMD |

### Function Signatures

```python
forward_geocode(place_name: str) -> str         
weather_forecast(latitude: float, longitude: float) -> str  
```

### Expected Workflow

```
[Location in query]       forward_geocode(place_name) → weather_forecast(latitude, longitude)

[No location in query]    Ask user for district/village → forward_geocode → weather_forecast

[Location not found]      Inform user; ask for alternate spelling or nearby district name
```

### Geocode Verification

`forward_geocode` can occasionally return wrong locations (e.g., a village name matches an unrelated place):

| Agent Behaviour | Rating |
|-----------------|--------|
| Notices mismatch and clarifies with user | EXCELLENT |
| Proceeds with plausible location | ACCEPTABLE |
| Proceeds with obviously wrong location (e.g., village in Punjab → unrelated state returned) | POOR |

---

## 2. Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `intent_accuracy` | ✅ | Identify weather query; extract or ask for location |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `tool_sequencing` | ✅ | `forward_geocode` → `weather_forecast` in correct order |
| `tool_usage` | ✅ | Correct lat/lon passed to `weather_forecast`; no invented params |
| `output_hygiene` | ✅ | No tool names in response |
| `source_alignment` | ✅ | Data must match tool output exactly |
| `no_fabrication` | ✅ CRITICAL | No invented temperature, rainfall, or humidity values |
| `citation_accuracy` | ✅ | IMD for weather forecast |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ | Cover all parameters returned by tool |
| `actionability` | ✅ KEY | Translate weather data to farming advice |
| `context_fit` | ✅ | Reference the farmer's specific location |
| `clarity` | ✅ | Clear day-by-day or range-based presentation |
| `conversation_closure` | ✅ | Offer related help |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | तापमान, आर्द्रता, वर्षा, हवा |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 3. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `intent_accuracy` | Identifies weather query; extracts or asks for location immediately | Correct intent; minor clarification needed | Correct after one follow-up | Partial identification; corrects when clarified | Misidentifies query; wrong tool used |
| `moderation_compliance` | Valid Agricultural confirmed; proceeds | Minor hesitation; correct outcome | Minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `tool_sequencing` | `forward_geocode` → `weather_forecast` in correct order | Correct order; minor redundancy | Minor sequence gap | Out of order; causes confusion | `weather_forecast` called with guessed/invented coordinates |
| `tool_usage` | Correct `latitude` and `longitude` from geocode result passed to `weather_forecast` | Correct; minor precision issue | One non-critical parameter issue | Coordinates clearly wrong | No geocoding; coordinates fabricated |
| `output_hygiene` | No tool names; clean response | Clean; minor formatting issue | Minor artifact | Multiple artifacts | Tool names leaked ("forward_geocode के अनुसार") |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `source_alignment` | All values (temperature, humidity, rainfall, wind) match tool output | Most values match; minor omission | Minor paraphrasing | Several mismatches | Values don't match tool output |
| `no_fabrication` | All data from tool; no data acknowledged simply | All sourced; small inference | Minor inference | Significant unsupported claims | Invented temperature, rainfall, or wind data |
| `citation_accuracy` | "IMD" cited for weather forecast | Correct source; minor format issue | Generic "मौसम विभाग" | Source unclear | Wrong source OR no source at all |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `completeness` | All tool-returned parameters covered (temperature min/max, rainfall, humidity, wind) | Most parameters; minor gap | Main parameters (temperature, rain); minor gaps | Significant gaps | Key parameters missing |
| `actionability` | Weather translated to farming advice (e.g., spray timing, irrigation, frost protection) | Good guidance; one generic area | Some guidance present | Minimal guidance; mostly raw data | Raw data only; no farming relevance |
| `context_fit` | Response references farmer's specific location by name | Mostly personalized; minor miss | Generic location reference | Minimal location reference | Ignores stated location |
| `clarity` | Day-by-day OR clear ranges; easy to read | Clear; minor organization issue | Understandable | Hard to follow | Confusing or overloaded |
| `conversation_closure` | Specific follow-up (e.g., "क्या मैं मंडी भाव या फसल सलाह भी बता सकता हूं?") | Good follow-up; slightly generic | Generic offer | Weak follow-up | Dead end |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `grammar` | Perfect grammar in selected language | Minor errors; meaning fully clear | Errors; meaning still clear | Several errors; meaning affected | Broken; hard to understand |
| `terminology` | Correct terms (तापमान, किमान/अधिकतम, आर्द्रता, वर्षा, हवा की गति) | Mostly correct; one improvised term | Mix of correct and improvised | Many improvised terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; units (°C, mm, km/h) in English acceptable | Mostly pure; minimal switching | Some unnecessary switching | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Natural, farmer-friendly tone | Natural; minor stilted phrase | Stilted but understandable | Often awkward | Robotic or overly technical |

---

## 4. Annotated Examples

### Example A: EXCELLENT — Forecast with Location in Query

**Query:** `Ludhiana mein agle 5 din ka mausam batao`
(User selected language: Hindi)

**Trace:**
```
Turn 1: forward_geocode("Ludhiana, Punjab") → Ludhiana (30.901, 75.857)
Turn 2: weather_forecast(30.901, 75.857) → 5 days data: min 14-17°C, max 27-30°C, 0mm rain
```

**Response:**
```
लुधियाना (पंजाब) के लिए अगले 5 दिनों का मौसम पूर्वानुमान:

- **बारिश:** कोई बारिश की संभावना नहीं — सभी दिन सूखे रहेंगे
- **न्यूनतम तापमान:** 14°C से 17°C
- **अधिकतम तापमान:** 27°C से 30°C
- **आर्द्रता:** 20% से 55%
- **हवा:** 5 से 12 किमी/घंटा

**किसान सलाह:**
- बारिश न होने से खेत में नमी कम होगी — ज़रूरत के अनुसार सिंचाई करें
- तापमान सामान्य है — सुबह के समय फवारणी करें

**स्रोत: मौसम पूर्वानुमान (IMD)**

क्या मैं मंडी भाव या किसी योजना की जानकारी भी दे सकता हूं?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — `forward_geocode` → `weather_forecast` in correct order
- `actionability`: EXCELLENT — Weather translated to irrigation and spray timing advice
- `citation_accuracy`: EXCELLENT — IMD cited correctly
- `context_fit`: EXCELLENT — Ludhiana named explicitly in response

---

### Example B: UNACCEPTABLE — Fabrication When Tool Returns Empty

**Query:** `Agra mein aaj ka mausam kaisa hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: forward_geocode("Agra, Uttar Pradesh") → (27.176, 78.008)
Turn 2: weather_forecast(27.176, 78.008) → "No weather forecast data found for the requested location."
```

**Response:**
```
आगरा जिले में आज का मौसम:
- तापमान: न्यूनतम 12°C, अधिकतम 28°C
- आर्द्रता: 55%
- बारिश: कोई संभावना नहीं

मौसम फसल के लिए अनुकूल है। फवारणी कर सकते हैं।

**स्रोत: मौसम पूर्वानुमान (IMD)**
```

**Key Scores:**
- `no_fabrication`: UNACCEPTABLE — Tool returned empty; all values (12°C, 28°C, 55%) invented
- `source_alignment`: UNACCEPTABLE — Cites IMD but data has no tool basis
- `actionability`: UNACCEPTABLE — Farming advice ("फवारणी करें") based on fabricated data; potentially harmful

**Correct Response Should:** "आगरा के लिए अभी मौसम डेटा उपलब्ध नहीं है। कृपया थोड़ी देर बाद पुनः प्रयास करें या नज़दीकी जिले का नाम बताएं।"

---

### Example C: GOOD — No Location in Query

**Query:** `कल बारिश होगी?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for location — no location in query]
Turn 2: User: "Hisar" → forward_geocode("Hisar, Haryana") → (29.151, 75.722)
Turn 3: weather_forecast(29.151, 75.722) → Tomorrow: 0mm rain, 20-31°C
```

**Response:**
```
हिसार (हरियाणा) के लिए कल का मौसम पूर्वानुमान:

- **बारिश:** कोई बारिश नहीं (0 मिमी)
- **न्यूनतम तापमान:** 20°C
- **अधिकतम तापमान:** 31°C
- **आर्द्रता:** 40-65%

कल फवारणी के लिए अच्छा दिन रहेगा।

**स्रोत: मौसम पूर्वानुमान (IMD)**
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Correctly asked for location first, then geocoded, then forecast
- `completeness`: GOOD — Core parameters present; wind data from tool not included
- `actionability`: GOOD — Spray advice given; could also mention irrigation guidance
- `conversation_closure`: ACCEPTABLE — Could offer related help (mandi, scheme)

---

### Example D: ACCEPTABLE — Tool Empty, No Fabrication

**Query:** `मेरे गाँव का मौसम बताओ`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for location]
Turn 2: User: "Rajgarh, Madhya Pradesh" → forward_geocode("Rajgarh, Madhya Pradesh") → (24.023, 76.727)
Turn 3: weather_forecast(24.023, 76.727) → "No weather forecast data found for the requested location."
```

**Response:**
```
माफ़ करें, राजगढ़ (मध्य प्रदेश) के लिए अभी मौसम डेटा उपलब्ध नहीं है।

क्या आप नज़दीकी बड़े जिले (जैसे भोपाल या इंदौर) का मौसम जानना चाहेंगे?
```

**Key Scores:**
- `no_fabrication`: EXCELLENT — Acknowledged unavailability without inventing data
- `actionability`: ACCEPTABLE — Offered alternative but could suggest retry timing
- `conversation_closure`: GOOD — Specific alternate locations offered

---

## 5. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Fabricating weather values when tool returns empty or unavailable** | CRITICAL | `no_fabrication`, `source_alignment` |
| **Calling `weather_forecast` with guessed/invented coordinates** | CRITICAL | `tool_usage`, `tool_sequencing` |
| **No farming advice — raw data only** | HIGH | `actionability` |
| **Missing IMD citation** | MEDIUM | `citation_accuracy` |
| **Proceeding with obviously wrong geocode result** | MEDIUM | `tool_usage`, `context_fit` |
| **Tool name leakage in response** | MEDIUM | `output_hygiene` |
| **Not asking for location when none is in query** | MEDIUM | `tool_sequencing` |
| **Generic follow-up unrelated to agriculture** | LOW | `conversation_closure` |

### NOT Pitfalls (Do Not Penalize)

| Scenario | Reason |
|----------|--------|
| User asks about past weather → forecast used → acknowledged as future data | Only `weather_forecast` exists; correct fallback behavior |
| Summarized ranges instead of day-by-day breakdown | Both formats acceptable |
| Location asked before geocoding when no location in query | Correct protocol |
| Coordinates have minor precision difference from geocode output | Acceptable rounding |

---

## 6. Actionability Examples

**EXCELLENT** — Translates weather to farming decisions:
```
- कल बारिश की संभावना है — फवारणी आज ही करें
- रात का तापमान 10°C से नीचे — छोटे पौधों को ढकें
- तेज़ हवा (15+ किमी/घंटा) — ड्रोन फवारणी न करें
```

**POOR** — Raw data only, no farming relevance:
```
तापमान: 13-30°C, आर्द्रता: 50%, वर्षा: 0.2 मिमी
```

---

## 7. Evaluator Checklist

- [ ] Location extracted from query OR asked before calling tools?
- [ ] `forward_geocode` called before `weather_forecast` (not skipped)?
- [ ] Coordinates from geocode result passed correctly to `weather_forecast`?
- [ ] Geocode result verified as plausible (correct state/region)?
- [ ] All tool-returned values present in response (temperature, rainfall, humidity, wind)?
- [ ] Tool returned empty → acknowledged without fabrication?
- [ ] Farming advice derived from actual tool data (not generic)?
- [ ] IMD cited as source?
- [ ] No tool names visible in response?
- [ ] Follow-up offer relevant to farmer's agricultural context?
- [ ] Response in correct selected language (Hindi or English)?
