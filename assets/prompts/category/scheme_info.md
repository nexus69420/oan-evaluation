# Scheme Information Evaluation Guide

## 1. Overview

**Scheme Information queries** ask about government agricultural schemes — benefits, eligibility, application process, documents, etc. The agent identifies the relevant scheme(s) from a fixed set of 10 central government schemes and fetches detailed information.

### Tools

| Tool | Purpose |
|------|---------|
| `get_scheme_info(scheme_name)` | Fetches detailed info for one scheme; call once per scheme (parallel calls if multiple schemes relevant) |

### Supported Scheme Codes

| Code | Scheme Name |
|------|-------------|
| `kcc` | Kisan Credit Card |
| `pmkisan` | Pradhan Mantri Kisan Samman Nidhi |
| `pmfby` | Pradhan Mantri Fasal Bima Yojana |
| `shc` | Soil Health Card |
| `pmksy` | Pradhan Mantri Krishi Sinchayee Yojana |
| `sathi` | Seed Authentication, Traceability & Holistic Inventory |
| `pmasha` | Pradhan Mantri Annadata Aay Sanrakshan Abhiyan |
| `aif` | Agriculture Infrastructure Fund |
| `smam` | Sub-Mission on Agricultural Mechanization |
| `pdmc` | Per Drop More Crop |

### Expected Workflow

```
[Single Scheme Query]
Identify scheme name → get_scheme_info(scheme_name) → Present formatted result


### Multiple Schemes per Need

| User Query | Relevant Codes | Tool Calls |
|------------|----------------|------------|
| "फसल बीमा / crop insurance" | `pmfby` | Single call |
| "ड्रिप सिंचन / drip irrigation subsidy" | `pdmc`, `pmksy` | Two parallel calls |
| "कृषि यंत्र / farm machinery" | `smam` | Single call |
| "किसान क्रेडिट / farmer loan" | `kcc` | Single call |
| "आय सहायता / income support" | `pmkisan` | Single call |
| "बीज प्रमाणीकरण / seed authentication" | `sathi` | Single call |
| "मूल्य समर्थन / price support" | `pmasha` | Single call |
| "सिंचाई अनुदान / irrigation subsidy" | `pdmc`, `pmksy` | Two parallel calls |
| "कृषि अवसंरचना / agri infrastructure" | `aif` | Single call |
| "मिट्टी स्वास्थ्य / soil health" | `shc` | Single call |

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `intent_accuracy` | ✅ | Must identify which scheme(s) the user is asking about |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `term_identification` | ✅ | Map user query to correct scheme code(s) |
| `tool_sequencing` | ✅ | Single or parallel calls to get_scheme_info |
| `tool_usage` | ✅ CRITICAL | Correct scheme code passed; no invented codes |
| `output_hygiene` | ✅ | No tool names in response |
| `source_alignment` | ✅ | Benefits/eligibility must match tool output exactly |
| `no_fabrication` | ✅ CRITICAL | No invented schemes, benefits, timelines, or subsidy amounts |
| `citation_accuracy` | ✅ | No invented sources; info sourced from tool output |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ CRITICAL | All relevant schemes called; comprehensive details presented |
| `actionability` | ✅ | Application process, documents, portal link from tool output |
| `context_fit` | ✅ | If user specifies crop/need, match to right scheme |
| `clarity` | ✅ | Scheme purpose clearly explained |
| `conversation_closure` | ✅ | Offer related schemes or further help |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | योजना, अनुदान, पात्रता, लाभ |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `intent_accuracy` | Correctly identifies the scheme(s) the user is asking about; proceeds immediately | Correct scheme; minor clarification needed | Correct scheme identified after one follow-up | Wrong scheme assumed; corrects when clarified | Wrong scheme throughout; never corrects |
| `moderation_compliance` | Valid Agricultural confirmed; proceeds | Minor hesitation; correct outcome | Minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `term_identification` | Correctly maps user query to the right scheme code(s) | Correct mapping; minor terminology gap | Minor mismatch but corrects | Significant mismatch; partial correction | Wrong scheme code used; no correction |
| `tool_sequencing` | Parallel calls for multi-scheme queries; single call for single scheme | Correct; minor redundancy (sequential instead of parallel) | Sequential calls instead of parallel (works, less efficient) | Inefficient but arrives at correct answer | Skips tool; makes up scheme details |
| `tool_usage` | Correct scheme code(s) from the known list of 10; no invented codes | Correct; one minor spelling issue | One non-critical error | Multiple errors; result affected | Invented scheme code; tool returns error or wrong data |
| `output_hygiene` | No tool names; clean, readable response | Clean; minor formatting issue | Minor artifact | Multiple artifacts | Tool name leaked (e.g., "get_scheme_info के अनुसार") |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `source_alignment` | Benefits, eligibility, documents exactly match tool output | Most details match; minor omission | Minor paraphrasing | Several mismatches | Invented details not in tool output |
| `no_fabrication` | No invented schemes, benefits, subsidy %, or deadlines | All data sourced; small inference acceptable | Minor inference | Significant unsupported claims | Invented scheme; promised "40% नक्की मिळेल"; invented deadlines |
| `citation_accuracy` | Info grounded in tool output; no false sources cited | Mostly grounded; minor generic phrasing | Acceptable phrasing | Source unclear | Tool name used as citation OR scheme not in list but details fabricated |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `completeness` | All relevant schemes fetched and presented; benefits, eligibility, documents, application process covered | Most schemes and details; minor gap | Main scheme covered; one related scheme or detail missed | Significant gaps | Only partial info; key schemes omitted; eligibility missing |
| `actionability` | Application process, documents list, and portal link from tool output clearly stated | Clear guidance; minor gap | Some guidance | Minimal guidance | No next steps; vague "office जाएं" |
| `context_fit` | If user specifies crop/need, agent selects the most relevant scheme(s); misconceptions corrected | Mostly correct scheme for context | General info; correct scheme but not tailored | Partially correct | Wrong scheme for stated need |
| `clarity` | Scheme purpose clearly explained; easy to act on | Clear; minor organization issue | Understandable | Hard to follow | Confusing; multiple schemes conflated |
| `conversation_closure` | Offers related schemes (e.g., if asked about irrigation, offer pdmc + pmksy) or further assistance | Good follow-up; slightly generic | Generic follow-up | Weak follow-up | Dead end |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `grammar` | Perfect grammar in selected language | Minor errors; fully clear | Minor errors | Several errors; meaning affected | Broken |
| `terminology` | Correct terms (e.g., योजना, अनुदान, पात्रता, लाभ, आवेदन प्रक्रिया) | Mostly correct; one improvised | Mix of correct and improvised | Many improvised terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; scheme names/codes in English acceptable | Mostly pure; minimal switching | Some unnecessary switching | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Natural, farmer-friendly tone | Natural; minor stilted phrase | Stilted but understandable | Often awkward | Robotic or overly technical |

---

## 3. Annotated Examples

### Example A: EXCELLENT — Multi-Scheme Query (Irrigation)

**Query:** `ड्रिप सिंचन के लिए कोई सरकारी योजना है?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent identifies two relevant codes: pdmc, pmksy]
         get_scheme_info("pdmc") + get_scheme_info("pmksy")  [parallel calls]
         → Both schemes returned with details
```

**Response:**
```
ड्रिप सिंचन के लिए दो केंद्र सरकारी योजनाएं उपलब्ध हैं:

**१. Per Drop More Crop (PDMC)**
- प्रधानमंत्री कृषि सिंचाई योजना के अंतर्गत
- ड्रिप और स्प्रिंकलर सिंचाई पर अनुदान
- [tool से प्राप्त पात्रता और आवेदन विवरण]

**२. प्रधानमंत्री कृषि सिंचाई योजना (PMKSY)**
- जल उपयोग दक्षता बढ़ाने के लिए
- [tool से प्राप्त लाभ और आवेदन विवरण]

क्या आप किसी एक योजना के बारे में विस्तार से जानना चाहेंगे?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Both relevant schemes fetched in parallel; no invented codes
- `completeness`: EXCELLENT — Both irrigation schemes covered
- `tool_usage`: EXCELLENT — Correct codes `pdmc` and `pmksy` used
- `conversation_closure`: EXCELLENT — Offers deeper dive into either scheme

---

### Example B: EXCELLENT — Misconception Correction

**Query:** `PMFBY में ट्रैक्टर सब्सिडी कैसे मिलेगी?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent recognizes PMFBY is crop insurance, not machinery; also identifies smam for machinery]
         get_scheme_info("pmfby") + get_scheme_info("smam")  [parallel calls]
```

**Response:**
```
**PMFBY (प्रधानमंत्री फसल बीमा योजना)** फसल बीमा योजना है — इसमें ट्रैक्टर या यंत्र अनुदान नहीं मिलता। इस योजना में प्राकृतिक आपदा से फसल नुकसान पर बीमा कवर मिलता है।

**ट्रैक्टर/यंत्र अनुदान के लिए सही योजना:**

**Sub-Mission on Agricultural Mechanization (SMAM)**
- कृषि यंत्रों पर अनुदान
- [tool से प्राप्त पात्रता और आवेदन विवरण]

क्या आप SMAM योजना के बारे में और जानकारी चाहते हैं?
```

**Key Scores:**
- `term_identification`: EXCELLENT — Misconception corrected; right scheme identified
- `completeness`: EXCELLENT — Both PMFBY (clarification) and SMAM (correct scheme) covered
- `no_fabrication`: EXCELLENT — All details from tool output

---

### Example C: ACCEPTABLE — General Single Scheme Query

**Query:** `PM Kisan योजना की जानकारी दें`
(User selected language: Hindi)

**Trace:**
```
Turn 1: get_scheme_info("pmkisan") → PM-KISAN details
```

**Response:**
```
**प्रधानमंत्री किसान सन्मान निधी (PM-KISAN)**

केंद्र सरकार की इस योजना में पात्र किसान परिवारों को सालाना ₹6,000 मिलते हैं — तीन समान किस्तों में।

**पात्रता:** [tool से प्राप्त विवरण]

**आवश्यक दस्तावेज़:** [tool से प्राप्त विवरण]

**आवेदन:** [tool से प्राप्त portal link]
```

**Key Scores:**
- `tool_usage`: EXCELLENT — Correct code `pmkisan` used
- `completeness`: ACCEPTABLE — Single scheme correctly covered; could offer to check PM-KISAN payment status as a follow-up
- `conversation_closure`: ACCEPTABLE — Could offer `check_pm_kisan_status` as a related next step

---

### Example D: UNACCEPTABLE — Invented Scheme Code

**Query:** `आत्मा योजना की जानकारी दें`
(User selected language: Hindi)

**Trace:**
```
Turn 1: get_scheme_info("atma") ← WRONG — "atma" is not a valid scheme code
         → Tool returns error or empty response
Turn 2: [Agent fabricates scheme details instead of acknowledging]
```

**Response:**
```
**आत्मा योजना (ATMA)**

इस योजना में किसानों को प्रशिक्षण और तकनीक के लिए ₹50,000 तक का अनुदान मिलता है...

[fabricated details with no tool basis]
```

**Critical Failures:**
- `tool_usage`: UNACCEPTABLE — Invented scheme code `"atma"` not in the 10 valid codes
- `no_fabrication`: UNACCEPTABLE — Scheme not available but details invented
- `source_alignment`: UNACCEPTABLE — Response has no tool basis

**Correct Response Should:** "आत्मा योजना की जानकारी फिलहाल उपलब्ध नहीं है। अगर आप कृषि प्रशिक्षण या अनुदान के बारे में जानना चाहते हैं, तो AIF (Agriculture Infrastructure Fund) या SMAM (Agricultural Mechanization) की जानकारी ले सकते हैं।"

---

### Example E: UNACCEPTABLE — Missing Relevant Scheme

**Query:** `सिंचाई के लिए कोई योजना बताएं`
(User selected language: Hindi)

**Trace:**
```
Turn 1: get_scheme_info("pmksy") only ← Misses pdmc
```

**Response:**
```
**PMKSY (प्रधानमंत्री कृषि सिंचाई योजना)**
[Only PMKSY details — no mention of PDMC]
```

**Critical Failures:**
- `completeness`: UNACCEPTABLE — Missed `pdmc` (Per Drop More Crop) which is directly relevant to irrigation subsidy
- `tool_sequencing`: POOR — Should have called both `pmksy` and `pdmc` in parallel

**Correct Response Should:** Include both PMKSY and PDMC with their respective focus areas.

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Using an invented scheme code not in the 10 valid codes** | CRITICAL | `tool_usage` |
| **Fabricating scheme details when scheme is not available** | CRITICAL | `no_fabrication` |
| **Missing a relevant scheme** (only one called when multiple apply) | HIGH | `completeness` |
| **No misconception correction** (e.g., PMFBY for machinery subsidy) | HIGH | `term_identification` |
| **Promising exact subsidy amounts** without tool data to support | HIGH | `no_fabrication` |
| **Missing eligibility conditions or documents** from tool output | MEDIUM | `completeness` |
| **No portal link or application process** when tool provides it | MEDIUM | `actionability` |
| **Tool name leakage in response** | MEDIUM | `output_hygiene` |
| **Sequential calls instead of parallel** for multi-scheme queries | LOW | `tool_sequencing` (minor inefficiency) |

---

## 5. Scheme Quick Reference

| User Query Pattern | Relevant Code(s) |
|--------------------|-----------------|
| फसल बीमा, crop insurance | `pmfby` |
| ड्रिप/स्प्रिंकलर सिंचन, drip/sprinkler irrigation | `pdmc`, `pmksy` |
| सिंचाई सब्सिडी, irrigation subsidy | `pdmc`, `pmksy` |
| कृषि यंत्र, ट्रैक्टर, farm machinery | `smam` |
| किसान लोन, कृषि ऋण, farmer credit | `kcc` |
| आय सहायता, ₹6000, income support | `pmkisan` |
| मिट्टी जांच, soil health | `shc` |
| बीज प्रमाणीकरण, seed quality | `sathi` |
| MSP, मूल्य समर्थन, price support | `pmasha` |
| कृषि अवसंरचना, storage, agri infrastructure | `aif` |

---

## 6. Evaluator Checklist

- [ ] Correct scheme code(s) identified from the valid list of 10?
- [ ] If user asked about wrong scheme → misconception corrected and right scheme provided?
- [ ] All relevant schemes covered (not just one when multiple apply)?
- [ ] For multi-scheme queries: were calls made in parallel (not sequential)?
- [ ] Benefits, eligibility, and documents match tool output — not fabricated?
- [ ] Portal link and application process included when available from tool?
- [ ] No subsidy amounts or deadlines invented beyond what tool returned?
- [ ] Scheme not in the 10 codes → acknowledged, not fabricated?
- [ ] Tool name absent from response?
- [ ] Follow-up offer relevant to the user's need (e.g., related scheme or status check)?
- [ ] Response in correct selected language (Hindi or English)?
