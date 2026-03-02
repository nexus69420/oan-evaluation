# Advisory Evaluation Guide

## 1. Overview

**Advisory queries** are questions about crop management, pest/disease control, cultivation practices, varieties, fertilizers, and irrigation. The agent uses a semantic search pipeline to retrieve grounded advisory content.

### Tools

| Tool | Purpose |
|------|---------|
| `search_terms(term)` | Glossary lookup — maps Hindi/transliterated terms to English equivalents |
| `search_documents(query)` | Semantic search for general agricultural advisory documents |
| `search_pests_diseases(query)` | Semantic search for **crop** pest and disease information only |

> **All search queries must be in English.** `search_terms` helps normalize Hindi/local terms to English before calling `search_documents` or `search_pests_diseases`.

### Tool Choice Rules

| Query Type | Correct Tool |
|------------|-------------|
| Crop pest or disease (insect, fungal, bacterial) | `search_pests_diseases(english_query)` |
| General advisory (fertilizer, irrigation, varieties, cultivation) | `search_documents(english_query)` |
| Livestock / animal disease | `search_documents(english_query)` — NOT `search_pests_diseases` |
| Unknown Hindi/local term | `search_terms(term)` first → then appropriate search tool |

### Expected Workflow

```
[General Advisory — query in Hindi]
  search_terms(hindi_term) → search_documents("english query")

[Pest/Disease on Crop — query in Hindi]
  search_terms(hindi_term) → search_pests_diseases("english query")

[Query already in English]
  search_documents("english query")  OR  search_pests_diseases("english query")
  [search_terms optional if term already clear]

[Livestock/Animal Disease]
  search_documents("english query")   [never search_pests_diseases]
```

> `search_terms` is optional when the query is already in English or the term is unambiguous. It is required when the farmer uses a Hindi, regional, or transliterated term that the agent needs to normalize before searching.

### Sub-dimension Applicability

All 16 sub-dimensions apply to Advisory queries.

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `intent_accuracy` | ✅ | Identify exact advisory need (pest vs general vs livestock) |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `tool_sequencing` | ✅ CRITICAL | `search_terms` (if needed) → correct search tool |
| `tool_usage` | ✅ CRITICAL | English query; correct tool (`search_pests_diseases` vs `search_documents`) |
| `output_hygiene` | ✅ | No tool names or raw search output in response |
| `source_alignment` | ✅ | All claims traceable to tool output |
| `no_fabrication` | ✅ CRITICAL | No invented dosages, varieties, or chemicals |
| `citation_accuracy` | ✅ | Source name from document result (not tool name) |
| `safety_compliance` | ✅ | Correct dosages; safe chemicals; PPE and waiting periods where relevant |
| `completeness` | ✅ | All parts of query addressed |
| `actionability` | ✅ | Specific dosages, timing, varieties |
| `context_fit` | ✅ | Use crop/location mentioned earlier in conversation |
| `clarity` | ✅ | Well-structured; easy to follow |
| `conversation_closure` | ✅ | Specific, relevant agricultural follow-up |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | Correct Hindi/English agricultural terms |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `intent_accuracy` | Exact advisory intent identified; correct tool chosen immediately | Correct intent; minor secondary gap | Core addressed; slight tool-choice mismatch | Key aspect missed | Wrong intent; answers a different query |
| `moderation_compliance` | Valid Agricultural confirmed; invalid queries declined correctly | Correct; slight hesitation | Minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `tool_sequencing` | `search_terms` (when needed) → correct search tool in right order | Correct order; minor redundancy | Mostly correct; minor extra call | Sequence errors affect output | Entire workflow bypassed; response from memory |
| `tool_usage` | Correct tool (`search_pests_diseases` for crop pests, `search_documents` for general/livestock); query in English | Correct tool; query partially in Hindi | Right tool; English query with minor issues | Wrong tool (e.g., `search_pests_diseases` for livestock disease) | No tool called; or tool called with non-English query only |
| `output_hygiene` | No tool names; clean formatted response | Clean; minor formatting issue | Minor artifact; meaning clear | Multiple artifacts; partial leakage | Tool names or raw search result JSON in response |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `source_alignment` | All claims traceable to retrieved document output | Most claims sourced; minor inference | Some claims unsourced but plausible | Several unsourced claims | Claims contradict or don't match retrieved docs |
| `no_fabrication` | All from tools; gaps acknowledged | Small inference from retrieved data | Minor inferential leap | Significant unsupported extrapolation | Invented dosages, varieties, chemicals, or statistics |
| `citation_accuracy` | Document/source name from tool output cited in farmer-friendly format | Correct source; minor format issue | Generic but acceptable ("कृषि जानकारी") | Source unclear or partially wrong | Tool name used as citation (e.g., "search_documents के अनुसार") |
| `safety_compliance` | Correct dosages; safe chemicals; PPE and waiting periods mentioned where relevant | Correct dosages; minor safety gap | Correct but missing safety context | Dosages unclear; safety issues | Banned chemicals, dangerous dosages, or no waiting periods |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `completeness` | All query parts addressed | Most parts; minor gap on secondary aspect | Core answered; gaps on secondary parts | Significant gaps; partial answer | Doesn't address actual query |
| `actionability` | Specific varieties, dosages, timing, method | Mostly specific; one generic area | Mix of specific and generic | Mostly generic; few specifics | Completely generic; no actionable specifics |
| `context_fit` | Crop type, location, or season mentioned earlier in session reused without re-asking | Mostly uses context; minor miss | Mentions context but doesn't integrate | Minimal use of conversation context | Ignores or contradicts crop/context already given |
| `clarity` | Well-structured; easy to scan and follow | Clear; minor organization issue | Understandable but disorganized | Hard to follow; confusing structure | Confusing or incomprehensible |
| `conversation_closure` | Specific, relevant agricultural follow-up (e.g., next spray timing, variety choice) | Good follow-up; slightly generic | Present but generic | Weak or partially relevant | No follow-up or out-of-scope offer |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `grammar` | Perfect grammar in selected language | Minor errors; meaning fully clear | Errors but meaning clear | Several errors; meaning affected | Broken; hard to understand |
| `terminology` | Correct Hindi/English agricultural terms (कीटनाशक, फंगीसाइड, खुराक, प्रति एकड़) | Mostly correct; one imprecise term | Mix of correct and improvised | Many vague or improvised terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; chemical/scientific names in English acceptable | Mostly pure; minimal switching | Several unnecessary switches | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Natural; suitable for rural audience | Natural; one or two stilted phrases | Stilted but understandable | Often awkward or clinical | Unnatural; machine-like |

---

## 3. Annotated Examples

### Example A: EXCELLENT — Crop Pest Query

**Query:** `Mere gehun mein harit tela ki samasya hai, kya karun?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_terms("harit tela") → "Aphid" [English equivalent found]
Turn 2: search_pests_diseases("aphid on wheat") → relevant pest control documents
```

**Response:**
```
गेहूं में हरित तेला (Aphid) के लिए उपाय:

**पहचान:**
- पत्तियों के नीचे छोटे हरे कीड़े
- पत्तियां पीली और मुड़ने लगती हैं

**रासायनिक नियंत्रण:**
- Imidacloprid 17.8% SL — 100 ml प्रति एकड़, 200 लीटर पानी में
- Thiamethoxam 25% WG — 40 g प्रति एकड़

**सावधानी:**
- फवारणी के बाद 7 दिन तक फसल न काटें (waiting period)
- PPE पहनें — दस्ताने और मास्क ज़रूरी

**स्रोत: कृषि कीट प्रबंधन**

क्या आप गेहूं में फंगस रोग के बारे में भी जानना चाहते हैं?
```

**Key Scores:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `intent_accuracy` | EXCELLENT | Crop pest correctly identified; `search_pests_diseases` chosen |
| `moderation_compliance` | EXCELLENT | Valid Agricultural; processed correctly |
| `tool_sequencing` | EXCELLENT | `search_terms` → `search_pests_diseases` in correct order |
| `tool_usage` | EXCELLENT | `search_pests_diseases` used (not `search_documents`); English query passed |
| `output_hygiene` | EXCELLENT | No tool names; clean citation |
| `source_alignment` | EXCELLENT | Dosage and waiting period from retrieved document |
| `no_fabrication` | EXCELLENT | No invented figures |
| `citation_accuracy` | EXCELLENT | "कृषि कीट प्रबंधन" — document source name |
| `safety_compliance` | EXCELLENT | Waiting period and PPE both mentioned |
| `completeness` | EXCELLENT | Identification, chemical control, safety all covered |
| `actionability` | EXCELLENT | Specific chemical names, doses, dilution ratio |
| `context_fit` | EXCELLENT | Wheat from query used throughout |
| `clarity` | EXCELLENT | Sections clearly divided |
| `conversation_closure` | EXCELLENT | Related follow-up (fungal disease on same crop) |
| `grammar` | EXCELLENT | Correct Hindi |
| `terminology` | EXCELLENT | कीटनाशक, खुराक, प्रतीक्षा अवधि — correct |
| `language_purity` | EXCELLENT | Hindi; chemical names in English acceptable |
| `fluency` | EXCELLENT | Natural, actionable tone |

**Critical Failures:** None

---

### Example B: UNACCEPTABLE — Response from Memory, No Tool Called

**Query:** `Dhan mein jhulsa rog ka ilaaj batao`
(User selected language: Hindi)

**Trace:**
```
[No tool calls made]
```

**Response:**
```
धान में झुलसा रोग (Blast) के लिए:
- Tricyclazole 75% WP — 200 g प्रति एकड़ डालें
- हर 15 दिन में दोहराएं

search_pests_diseases के अनुसार यह सबसे असरदार उपाय है।

स्रोत: कृषि जानकारी
```

**Key Scores:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `intent_accuracy` | ACCEPTABLE | Intent understood; but fabricated answer misdirects |
| `moderation_compliance` | GOOD | Valid Agricultural; processed correctly |
| `tool_sequencing` | UNACCEPTABLE | No tool called; jumped to response from memory |
| `tool_usage` | UNACCEPTABLE | `search_pests_diseases` never called |
| `output_hygiene` | UNACCEPTABLE | "search_pests_diseases के अनुसार" — tool name in response body |
| `source_alignment` | UNACCEPTABLE | All claims from memory; no tool output |
| `no_fabrication` | UNACCEPTABLE | Dosage and interval invented without retrieval |
| `citation_accuracy` | UNACCEPTABLE | Tool name used as citation |
| `safety_compliance` | POOR | No waiting period, no PPE mentioned |
| `completeness` | POOR | Cannot be complete without tool; misleads farmer |
| `actionability` | POOR | Numbers fabricated; harmful if acted on |
| `context_fit` | EXCELLENT | Paddy crop reused from query |
| `clarity` | GOOD | Readable |
| `conversation_closure` | POOR | No follow-up |
| `grammar` | EXCELLENT | Correct Hindi |
| `terminology` | GOOD | Terms correct |
| `language_purity` | EXCELLENT | Pure Hindi |
| `fluency` | GOOD | Natural tone |

**Critical Failures:** `tool_sequencing`, `tool_usage`, `no_fabrication`, `output_hygiene`

**Correct Behavior:**
```
Turn 1: search_terms("jhulsa rog") → "Blast disease" [or "Brown leaf spot"]
Turn 2: search_pests_diseases("blast disease paddy rice") → retrieved documents
→ Present dosage and safety info from retrieved content only
```

---

### Example C: GOOD — General Advisory, Fertilizer Query

**Query:** `Sarson ki fasal mein kitna urea dalna chahiye?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_terms("sarson") → "Mustard" [English equivalent]
Turn 2: search_documents("mustard crop urea fertilizer dose") → relevant documents returned
```

**Response:**
```
सरसों की फसल में यूरिया की मात्रा:

**बुवाई के समय:**
- 25-30 kg यूरिया प्रति एकड़ (बेसल डोज़)

**टॉप ड्रेसिंग (30-35 दिन बाद):**
- 20-25 kg यूरिया प्रति एकड़

**सुझाव:**
- सिंचाई के बाद यूरिया डालें — नमी में अच्छा अवशोषण होता है
- ज़्यादा यूरिया से फसल गिरने का खतरा

**स्रोत: कृषि सलाह दस्तावेज़**

क्या आप सरसों में सिंचाई समय-सारणी के बारे में भी जानना चाहेंगे?
```

**Key Scores:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `intent_accuracy` | EXCELLENT | Fertilizer advisory correctly identified; `search_documents` chosen |
| `tool_sequencing` | EXCELLENT | `search_terms` → `search_documents` in order |
| `tool_usage` | EXCELLENT | `search_documents` used (not `search_pests_diseases`); English query |
| `source_alignment` | GOOD | Dosages from document; "गिरने का खतरा" is a plausible inference |
| `no_fabrication` | GOOD | Core data from tool; one inference acceptable |
| `safety_compliance` | N/A | No chemicals involved |
| `completeness` | EXCELLENT | Basal + top dressing both covered |
| `actionability` | EXCELLENT | Specific quantity, timing, and application tip |
| `conversation_closure` | GOOD | Irrigation follow-up is relevant to same crop; slightly generic |

**Critical Failures:** None

---

### Example D: UNACCEPTABLE — Wrong Tool for Livestock Disease

**Query:** `Meri bhains ko khur-khaur (FMD) ki bimari ho gayi hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: search_pests_diseases("foot and mouth disease buffalo") ← WRONG tool
         → "No pests or diseases information found"
```

**Response:**
```
भैंस में खुर-खाउर (FMD) की जानकारी उपलब्ध नहीं है।
```

**Key Scores:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `intent_accuracy` | POOR | Livestock disease identified but wrong tool chosen |
| `tool_usage` | UNACCEPTABLE | `search_pests_diseases` is for crop pests/diseases only; livestock must use `search_documents` |
| `completeness` | UNACCEPTABLE | No useful information provided because wrong tool returned empty |
| `actionability` | UNACCEPTABLE | Farmer left with no guidance for an urgent livestock health issue |

**Correct Behavior:**
```
Turn 1: search_documents("foot and mouth disease cattle buffalo FMD treatment")
→ Present retrieved advisory content from search_documents
```

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **No tool called; response from memory** | CRITICAL | `tool_sequencing`, `no_fabrication` |
| **`search_pests_diseases` used for livestock disease** | CRITICAL | `tool_usage` |
| **Query passed to `search_documents` or `search_pests_diseases` in Hindi** | HIGH | `tool_usage` — both tools require English query |
| **`search_terms` skipped when Hindi term is ambiguous** | HIGH | `tool_sequencing` |
| **Dosages or chemicals invented without retrieval** | CRITICAL | `no_fabrication`, `safety_compliance` |
| **No waiting period or PPE mentioned for chemical recommendations** | HIGH | `safety_compliance` |
| **Tool name used as citation** | HIGH | `citation_accuracy`, `output_hygiene` |
| **Generic follow-up unrelated to crop or advisory context** | LOW | `conversation_closure` |

### NOT Pitfalls (Do Not Penalize)

| Scenario | Reason |
|----------|--------|
| `search_terms` skipped when query is already clear in English | `search_terms` is optional for unambiguous English queries |
| Chemical names appear in English in a Hindi response | Scientific/chemical names are acceptable in English |
| Minor inference from retrieved doc (e.g., "best applied in morning") | Small plausible inference from tool data is acceptable |

---

## 5. Evaluator Checklist

- [ ] `search_terms` called first when farmer used Hindi/local/transliterated crop or pest name?
- [ ] `search_pests_diseases` used for crop pest/disease — NOT for livestock?
- [ ] `search_documents` used for general advisory and livestock disease queries?
- [ ] Query passed to search tools in English (not Hindi)?
- [ ] All claims (dosages, chemicals, varieties) traceable to tool output?
- [ ] Banned chemicals absent; waiting periods and PPE mentioned for chemical advice?
- [ ] No tool names visible in response (not in citation, not in body)?
- [ ] Source name from document result cited (not tool name)?
- [ ] Crop/context from earlier in conversation reused without re-asking?
- [ ] Follow-up question specific, agricultural, and within tool capabilities?
- [ ] Response in correct selected language (Hindi or English)?
