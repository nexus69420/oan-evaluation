# Mandi Prices Evaluation Guide

## 1. Overview

**Mandi/Market Price queries** are questions about commodity prices at agricultural markets (APMCs). Farmers ask about current prices for their crops to make sell/store decisions.

### Tools

| Tool | Purpose |
|------|---------|
| `search_commodity(query)` | Fuzzy-matches commodity name (any language/script) → returns integer commodity code |
| `forward_geocode(place_name)` | Converts place name to latitude/longitude |
| `get_mandi_prices(latitude, longitude, commodity_code, days_back=30)` | Fetches mandi price data for a commodity near a location |

> `get_mandi_prices` **requires a `commodity_code` (integer)**. The agent must always call `search_commodity` first to find the correct code. Skipping this step and passing an invented or guessed code is a critical failure.

### Function Signatures

```python
search_commodity(query: str, max_results: int = 5) -> str         # Returns matched commodity codes
forward_geocode(place_name: str) -> str                            # Returns location with lat/lon
get_mandi_prices(latitude: float, longitude: float,
                 commodity_code: int, days_back: int = 30) -> str  # Fetches mandi prices
```

### Expected Workflow

```
[Location + commodity in query]
  search_commodity(commodity_name) + forward_geocode(place_name)  [parallel]
  → get_mandi_prices(latitude, longitude, commodity_code)

[No location in query]
  search_commodity(commodity_name) → Ask for location
  → forward_geocode(place_name) → get_mandi_prices(...)

[Commodity not found by search_commodity]
  Acknowledge → Ask farmer to clarify crop name
```

### Tool Sequencing Rules

| Step | Action | Notes |
|------|--------|-------|
| 1 | `search_commodity(crop_name)` | Always required; provides integer `commodity_code` |
| 2 | `forward_geocode(place_name)` | Required if location not already known; can run parallel with step 1 |
| 3 | `get_mandi_prices(lat, lon, code)` | Only after steps 1 and 2 complete |

### Date in Tool Output

The tool converts arrival dates to **relative time strings** automatically:
- "today", "1 day ago", "10 days ago", etc.

| Tool Output | Correct Agent Response | Incorrect Agent Response |
|-------------|----------------------|--------------------------|
| "1 day ago" | "कल के भाव: ₹5,000" or just show price | "आज के भाव: ₹5,000" |
| "10 days ago" | "10 दिन पहले के भाव: ₹4,800" | "ताजे भाव: ₹5,000" |
| No date in output | Show price without date claim | "आजचे भाव: ₹5,000" |

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `intent_accuracy` | ✅ | Identify commodity and location from query |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `tool_sequencing` | ✅ CRITICAL | `search_commodity` → `forward_geocode` → `get_mandi_prices` in order |
| `tool_usage` | ✅ CRITICAL | Correct commodity_code (integer) from `search_commodity`; no invented codes |
| `output_hygiene` | ✅ | No tool names in response |
| `source_alignment` | ✅ | Prices must match tool output exactly |
| `no_fabrication` | ✅ CRITICAL | No invented prices, dates, or arrival volumes |
| `citation_accuracy` | ✅ | "स्रोत: मंडी भाव" or market name from tool output |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ | Address requested crop + market; show min/modal/max |
| `actionability` | ✅ | Sell/store guidance if appropriate |
| `context_fit` | ✅ | Reference the farmer's stated location |
| `clarity` | ✅ | Clear price presentation |
| `conversation_closure` | ✅ | Offer alternatives or nearby markets |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | क्विंटल, भाव, आवक, मॉडल प्राइस |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `intent_accuracy` | Correctly identifies commodity and location; proceeds immediately | Correct intent; minor clarification needed | Correct after one follow-up | Partial identification; corrects when clarified | Wrong commodity or location assumed; never corrects |
| `moderation_compliance` | Valid Agricultural confirmed; proceeds | Minor hesitation; correct outcome | Minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `tool_sequencing` | `search_commodity` + `forward_geocode` (parallel) → `get_mandi_prices` in correct order | Correct order; minor redundancy | Sequential instead of parallel (works, less efficient) | Out of order; `get_mandi_prices` before commodity code obtained | `get_mandi_prices` called without `search_commodity`; code invented or guessed |
| `tool_usage` | Correct integer `commodity_code` from `search_commodity` passed to `get_mandi_prices` | Correct; minor precision issue in coordinates | One non-critical parameter issue | Clearly wrong commodity code used | No `search_commodity` called; code fabricated |
| `output_hygiene` | No tool names; clean response | Clean; minor formatting issue | Minor artifact | Multiple artifacts | Tool names leaked ("search_commodity के अनुसार", "get_mandi_prices") |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `source_alignment` | All prices (min/modal/max) exactly match tool output; variety/grade distinctions preserved | Most prices match; minor omission | Prices correct; variety distinction missing | Several mismatches | Prices don't match tool output |
| `no_fabrication` | No invented prices; no fabricated dates; gaps clearly acknowledged | All sourced; small inference (e.g., "prices stable") | Minor inference without explicit source | Significant unsupported claims | Invented prices when tool returned empty; fake "आज के भाव" |
| `citation_accuracy` | "स्रोत: मंडी भाव" or market name from tool output | Correct source; minor format issue | Generic but acceptable ("बाजार भाव") | Source unclear | Tool name as citation OR no source for price data |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `completeness` | Requested commodity + market; min/modal/max shown; arrival date relative time preserved | Most info; minor gap | Partial info (only one price point) | Significant gaps | Doesn't address requested crop or market |
| `actionability` | Prices translated to sell/store guidance; or notes trend | Good guidance; one generic area | Prices given; minimal practical context | Minimal guidance | Raw data only; no framing |
| `context_fit` | Response references farmer's specific location by name | Mostly personalized; minor miss | Generic location reference | Minimal location reference | Ignores stated location entirely |
| `clarity` | Clear price table; min/modal/max easy to scan | Clear; minor organization issue | Understandable but cluttered | Hard to follow | Confusing; prices buried in text |
| `conversation_closure` | Offers nearby markets or related commodity prices | Good follow-up; slightly generic | Generic follow-up | Weak follow-up | Dead end when crop unavailable |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `grammar` | Perfect grammar in selected language | Minor errors; meaning fully clear | Errors; meaning still clear | Several errors; meaning affected | Broken; hard to understand |
| `terminology` | Correct terms (भाव, क्विंटल, आवक, मॉडल प्राइस, न्यूनतम/अधिकतम) | Mostly correct; one improvised | Mix of correct and improvised | Many improvised terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; market names/units in English acceptable | Mostly pure; minimal switching | Some unnecessary switching | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Natural, farmer-friendly tone | Natural; minor stilted phrase | Stilted but understandable | Often awkward | Robotic or overly technical |

---

## 3. Annotated Examples

### Example A: EXCELLENT — Crop Available

**Query:** `Ludhiana mandi mein gehun ka bhav kya hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_commodity("gehun") → Wheat, code: 27
         forward_geocode("Ludhiana, Punjab") → (30.901, 75.857)  [parallel]
Turn 2: get_mandi_prices(30.901, 75.857, commodity_code=27) →
         Commodity: Wheat | Market: Ludhiana, Punjab
         Price: Rs 2100 (Min: 2000, Max: 2200) | 1 day ago
         Variety: Sharbati | Grade: FAQ
```

**Response:**
```
लुधियाना मंडी (पंजाब) में गेहूं के भाव:

| विवरण | मूल्य |
|-------|-------|
| न्यूनतम भाव | ₹2,000/क्विंटल |
| मॉडल भाव | ₹2,100/क्विंटल |
| अधिकतम भाव | ₹2,200/क्विंटल |
| किस्म | शरबती |
| ग्रेड | FAQ |
| आवक | कल |

**किसान सलाह:** भाव MSP के करीब हैं — तुरंत बेचने या थोड़ा इंतज़ार करने में से निर्णय बाजार की आवक देखकर करें।

**स्रोत: मंडी भाव**

क्या मैं आसपास की किसी अन्य मंडी के भाव भी बता सकता हूं?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — `search_commodity` + `forward_geocode` in parallel, then `get_mandi_prices`
- `tool_usage`: EXCELLENT — Correct integer code `27` used
- `source_alignment`: EXCELLENT — All min/modal/max, variety, grade match tool output
- `actionability`: EXCELLENT — MSP comparison guidance given
- `no_fabrication`: EXCELLENT — Date shown as relative ("कल") matching tool's "1 day ago"

---

### Example B: UNACCEPTABLE — Commodity Code Invented (No `search_commodity` Called)

**Query:** `Indore mein soyabean ka bhav batao`
(User selected language: Hindi)

**Trace:**
```
Turn 1: forward_geocode("Indore, Madhya Pradesh") → (22.719, 75.857)
Turn 2: get_mandi_prices(22.719, 75.857, commodity_code=999)  ← WRONG: code invented, search_commodity not called
         → "No mandi price data found..."
Turn 3: [Agent fabricates prices]
```

**Response:**
```
इंदौर मंडी में सोयाबीन के आज के भाव:
- न्यूनतम: ₹4,500/क्विंटल
- अधिकतम: ₹5,200/क्विंटल

बेचने के लिए अच्छा समय है।

**स्रोत: मंडी भाव**
```

**Key Scores:**
- `tool_sequencing`: UNACCEPTABLE — `search_commodity` skipped entirely; commodity code invented
- `tool_usage`: UNACCEPTABLE — Fabricated `commodity_code=999`; tool returned empty
- `no_fabrication`: UNACCEPTABLE — Prices invented when tool returned no data
- `citation_accuracy`: POOR — Cites "मंडी भाव" for fabricated data

**Correct Response Should:**
```
Turn 1: search_commodity("soyabean") → Soybean, code: 43
Turn 2: forward_geocode("Indore, Madhya Pradesh") → (22.719, 75.857)
Turn 3: get_mandi_prices(22.719, 75.857, commodity_code=43)
```

---

### Example C: GOOD — Crop Unavailable, Correct Handling

**Query:** `Jaipur mein sarson ka rate kya hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_commodity("sarson") → Mustard, code: 52
         forward_geocode("Jaipur, Rajasthan") → (26.912, 75.787)  [parallel]
Turn 2: get_mandi_prices(26.912, 75.787, commodity_code=52) →
         "No mandi price data found for the requested location and commodity."
```

**Response:**
```
जयपुर मंडी में सरसों के भाव अभी उपलब्ध नहीं हैं।

क्या मैं अलवर या कोटा मंडी के भाव देखूं? राजस्थान में इन मंडियों में सरसों की अच्छी आवक रहती है।

**स्रोत: मंडी भाव**
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — `search_commodity` called correctly before `get_mandi_prices`
- `no_fabrication`: EXCELLENT — Empty result clearly acknowledged
- `conversation_closure`: EXCELLENT — Specific nearby markets (Alwar, Kota) offered with reasoning
- `completeness`: GOOD — Unavailability handled; could also mention `days_back` can be extended

---

### Example D: UNACCEPTABLE — Date Fabrication

**Query:** `Amritsar mandi mein dhan ka bhav`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_commodity("dhan") → Paddy, code: 2
         forward_geocode("Amritsar, Punjab") → (31.634, 74.872)  [parallel]
Turn 2: get_mandi_prices(31.634, 74.872, commodity_code=2) →
         Price: Rs 1900 | 10 days ago
```

**Response:**
```
अमृतसर मंडी में धान के आज के ताजे भाव:
- भाव: ₹1,900/क्विंटल

**स्रोत: मंडी भाव**
```

**Key Scores:**
- `no_fabrication`: UNACCEPTABLE — Tool output says "10 days ago"; response says "आज के ताजे भाव" — date fabricated
- `source_alignment`: POOR — Data is 10 days old but presented as today's price; misleading

**Correct Response Should:** "अमृतसर मंडी में धान का भाव (10 दिन पहले): ₹1,900/क्विंटल। ताजा भाव के लिए कृपया दोबारा जांचें।"

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Skipping `search_commodity`; inventing commodity_code** | CRITICAL | `tool_sequencing`, `tool_usage` |
| **Fabricating prices when tool returns empty** | CRITICAL | `no_fabrication`, `source_alignment` |
| **Presenting old data (e.g., "10 days ago") as "आज के भाव"** | HIGH | `no_fabrication` |
| **No alternatives offered when crop unavailable** | HIGH | `conversation_closure` |
| **Wrong market geocoded (different district/state)** | HIGH | `tool_usage`, `context_fit` |
| **Tool name leakage in response** | MEDIUM | `output_hygiene` |
| **Missing min/max; only modal price shown** | MEDIUM | `completeness` |
| **Generic follow-up (not nearby mandi or related crop)** | LOW | `conversation_closure` |

### NOT Pitfalls (Do Not Penalize)

| Scenario | Reason |
|----------|--------|
| `search_commodity` and `forward_geocode` called sequentially instead of parallel | Correct outcome; minor inefficiency only |
| Arrival date shown as relative ("10 दिन पहले") not absolute | Tool returns relative time; this is correct |
| `days_back` not explicitly set (uses default 30) | Default is appropriate for most queries |
| Variety/grade not shown when tool doesn't return them | Only present when available in tool output |

---

## 5. Evaluator Checklist

- [ ] `search_commodity` called before `get_mandi_prices` to obtain commodity code?
- [ ] `forward_geocode` called to obtain coordinates (not guessed)?
- [ ] Integer `commodity_code` from `search_commodity` passed to `get_mandi_prices`?
- [ ] All prices in response (min/modal/max) match tool output exactly?
- [ ] Arrival date shown as relative time matching tool output (not fabricated as "आज")?
- [ ] Crop unavailable → acknowledged clearly without fabricating prices?
- [ ] Crop unavailable → nearby markets or alternative crops offered?
- [ ] No tool names visible in response?
- [ ] Citation present ("स्रोत: मंडी भाव" or market name from tool)?
- [ ] Follow-up relevant to farmer's need (nearby markets, related commodity)?
- [ ] Response in correct selected language (Hindi or English)?
