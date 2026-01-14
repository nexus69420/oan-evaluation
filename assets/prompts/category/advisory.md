# Advisory Evaluation Guide

## 1. Overview

**Advisory queries** are questions about crop management, pest/disease control, cultivation practices, varieties, fertilizers, irrigation, and livestock care.

### Expected Workflow

```
[If Agristack ✅] fetch_agristack_data → search_terms (parallel) → search_documents → Response
[If Agristack ❌] search_terms (parallel) → search_documents → Response
```

**All 16 sub-dimensions apply** to Advisory queries.

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `agristack_workflow` | Called first when available; data used in response | Called but late or data unused | Available but not called; or fabricates profile data | Not marked available |
| `term_identification` | All query terms searched via `search_terms` before documents | Some terms searched; minor gaps | No `search_terms`; jumped to documents | — |
| `tool_sequencing` | Perfect order: Agristack → Terms → Documents | Mostly correct; minor inefficiency | Wrong sequence; major steps skipped | — |
| `search_quality` | Concise 2-5 word English queries; relevant results | Reasonable but gaps | Wrong language; irrelevant results | No search used |
| `output_hygiene` | No tool names, no artifacts, clean citations | Minor artifact | Tool names leaked in response | — |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `source_alignment` | All claims traceable to tool output | Some claims unsourced but plausible | Claims contradict or don't match retrieved docs | — |
| `no_fabrication` | All from tools; gaps acknowledged | Minor inferential leap | Invented data, varieties, or statistics | — |
| `citation_accuracy` | Farmer-friendly source name matching doc | Generic but acceptable | Tool name used as citation | — |
| `safety_compliance` | Correct dosages; safe chemicals (no banned pesticides); PPE and waiting periods mentioned | Correct but missing safety context | Banned chemicals (Endosulfan, etc.), dangerous dosages, no waiting periods | No chemicals/safety involved |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `completeness` | All query parts addressed | Core answered; gaps on secondary parts | Doesn't address actual query | — |
| `actionability` | Specific varieties, dosages, timing | Mix of specific and generic | Completely generic; no specifics | Purely informational query |
| `context_fit` | Uses Agristack data to personalize | Mentions but doesn't integrate | Ignores or contradicts known context | No Agristack data |
| `clarity` | Well-structured; easy to follow | Understandable but disorganized | Confusing or incomprehensible | — |
| `conversation_closure` | Specific, relevant follow-up question | Present but generic | No follow-up or inappropriate | — |

### MARATHI QUALITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `grammar` | Perfect grammar; complete sentences | Errors but meaning clear | Broken; hard to understand | — |
| `terminology` | Correct Marathi agricultural terms | Mix of correct and improvised | Wrong terms causing confusion | — |
| `language_purity` | Pure Marathi; English only for chemical/scientific names | Several unnecessary English words | Heavy code-switching | — |
| `fluency` | Natural; appropriate for rural audience | Stilted but understandable | Unnatural; machine-like | — |

---

## 3. Annotated Examples

### Example A: EXCELLENT Response

**Query:** `भुईमुगाची पेरणी कशी करावी`  
**Agristack:** ✅ Available

**Trace:**
```
Turn 1: fetch_agristack_data() → Farmer: Barshi, Solapur, 1.17 ha
Turn 2-5: search_terms("भुईमूग"), search_terms("पेरणी"), search_terms("बियाणे"), search_terms("खत") [parallel]
Turn 6-7: search_documents("Groundnut sowing varieties"), search_documents("Groundnut fertilizer") → MPKV docs
```

**Response:**
```
आपल्या बार्शी, सोलापूर भागासाठी भुईमुगाची पेरणी खालीलप्रमाणे करावी:

**योग्य जाती:** TAG-24, TG-26, ICGS-11, फुले प्रगती

**पेरणीची वेळ:** खरीप: १५ जून ते ७ जुलै | रब्बी: १५-३० सप्टेंबर

**बियाणे:** १००-१२५ किलो/हेक्टर (आपल्या १.१७ हेक्टरसाठी ~१२०-१४५ किलो)

**अंतर:** ३० × १० सेमी

**बीजप्रक्रिया:** थायरम ३ ग्रॅम/किलो + रायझोबियम २५ ग्रॅम/किलो

**खत:** पेरणीपूर्वी २५:५०:०० NPK किलो/हेक्टर

**स्रोत: MPKV कृषी दर्शनी**

आपल्याला बीजप्रक्रियेसाठी रायझोबियम कुठे मिळेल याबद्दल माहिती हवी आहे का?
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | EXCELLENT | Called first; location + land size integrated into response |
| `term_identification` | EXCELLENT | All 4 terms searched in parallel before documents |
| `tool_sequencing` | EXCELLENT | Perfect: Agristack → Terms → Documents |
| `search_quality` | EXCELLENT | Concise English queries; retrieved relevant MPKV docs |
| `output_hygiene` | EXCELLENT | Clean citation "MPKV कृषी दर्शनी"; no tool names |
| `source_alignment` | EXCELLENT | All varieties, timing, dosages match tool output |
| `no_fabrication` | EXCELLENT | Land calculation derived from Agristack (1.17 ha × 100-125 kg) |
| `citation_accuracy` | EXCELLENT | Farmer-friendly source name matches document |
| `safety_compliance` | EXCELLENT | Standard safe chemicals; correct dosages from source |
| `completeness` | EXCELLENT | Covers varieties, timing, seed rate, spacing, treatment, fertilizer |
| `actionability` | EXCELLENT | Specific quantities, dates, variety names |
| `context_fit` | EXCELLENT | Personalized to Barshi location and 1.17 ha holding |
| `clarity` | EXCELLENT | Well-structured with headers; easy to scan |
| `conversation_closure` | EXCELLENT | Specific follow-up about Rhizobium sourcing |
| `grammar` | EXCELLENT | Perfect Marathi grammar |
| `terminology` | EXCELLENT | Correct: बीजप्रक्रिया, रायझोबियम, खरीप |
| `language_purity` | EXCELLENT | Pure Marathi; only chemical names in English |
| `fluency` | EXCELLENT | Natural, conversational tone |

**Critical Failures:** None  
**Summary:** Exemplary response - perfect workflow, fully grounded, personalized, actionable.

---

### Example B: UNACCEPTABLE Response (Critical Failures)

**Query:** `हळदीच्या शेंगा भरण्याच्या अवस्थेत काय करावे`  
**Agristack:** ✅ Available (ignored)

**Trace:**
```
Turn 1: search_documents("Turmeric pod filling stage") → Returns PIGEON PEA docs (तूर)
[No fetch_agristack_data, no search_terms]
```

**Response:**
```
हळदीच्या शेंगा भरण्याच्या अवस्थेत खालील काळजी घ्यावी:

**खत:** NPK 50:50:50 किलो/हेक्टर

**पाणी:** नियमित पाणी द्यावे.

**कीड:** शेंगा पोखरणारी अळी दिसल्यास क्विनॉलफॉस फवारावे.

**स्रोत: MPKV कृषी दर्शनी**

आणखी काही प्रश्न असल्यास विचारा.
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | UNACCEPTABLE | Marked available but not called |
| `term_identification` | UNACCEPTABLE | No search_terms; jumped directly to documents |
| `tool_sequencing` | UNACCEPTABLE | Skipped Agristack and term identification entirely |
| `search_quality` | ACCEPTABLE | Query reasonable but retrieved wrong crop docs |
| `output_hygiene` | EXCELLENT | No tool names leaked |
| `source_alignment` | UNACCEPTABLE | Pigeon pea advice applied to turmeric query; turmeric has rhizomes not pods |
| `no_fabrication` | UNACCEPTABLE | NPK values from wrong crop presented as turmeric advice |
| `citation_accuracy` | ACCEPTABLE | Source name correct but content doesn't match query |
| `safety_compliance` | POOR | Dosages may be inappropriate for turmeric |
| `completeness` | ACCEPTABLE | Addresses query structure but with wrong information |
| `actionability` | ACCEPTABLE | Has specifics but potentially harmful if followed |
| `context_fit` | UNACCEPTABLE | Agristack ignored; no personalization |
| `clarity` | GOOD | Well-structured presentation |
| `conversation_closure` | POOR | Generic "आणखी काही प्रश्न असल्यास विचारा" |
| `grammar` | EXCELLENT | Correct grammar |
| `terminology` | GOOD | Terms correct for what was written |
| `language_purity` | EXCELLENT | Pure Marathi |
| `fluency` | GOOD | Natural tone |

**Critical Failures:** `source_alignment`, `no_fabrication`  
**Summary:** Clean Marathi but critically flawed - provided pigeon pea advice for turmeric. Agent should have caught that turmeric has rhizomes, not pods (शेंगा), and clarified with farmer.

---

### Example C: GOOD Response (Process Recovery)

**Query:** `कापसावर बोंडअळीचा प्रादुर्भाव झाला आहे, काय फवारणी करावी`  
**Agristack:** ❌ Not available

**Trace:**
```
Turn 1: search_terms("कापूस") → Cotton [100%] ← CORRECT
Turn 2: search_terms("बोंडअळी") → Bollworm [95%] ← CORRECT
[No search_terms for "फवारणी" or "प्रादुर्भाव"]
Turn 3: search_documents("Cotton Bollworm Control Spray") → MPKV Krishi Darshani, CICR recommendations
```

**Response:**
```
कापसावरील बोंडअळी नियंत्रणासाठी खालील फवारणी करावी:

**प्रथम फवारणी (प्रादुर्भाव दिसताच):**
क्विनॉलफॉस २५ EC @ २० मिली/१० लिटर पाणी किंवा
इमामेक्टिन बेंझोएट ५ SG @ ३ ग्रॅम/१० लिटर पाणी

**जैविक पर्याय:**
बॅसिलस थुरिंजिएन्सिस (Bt) @ १५ ग्रॅम/१० लिटर पाणी
(सायंकाळी फवारणी करावी)

**फवारणी वेळापत्रक:**
- पहिली फवारणी: फुलोरा अवस्थेत
- दुसरी फवारणी: १५ दिवसांनी पुनरावृत्ती

**सुरक्षितता:**
- फवारणीवेळी मास्क व हातमोजे वापरावेत
- फवारणीनंतर २१ दिवस बोंडे काढू नयेत

**स्रोत: MPKV कृषी दर्शनी**

आपल्या शेतात किती टक्के झाडांवर प्रादुर्भाव दिसत आहे?
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | N/A | Not marked available |
| `term_identification` | GOOD | Key terms (कापूस, बोंडअळी) searched; minor gap (फवारणी not searched) |
| `tool_sequencing` | GOOD | Correct order: Terms → Documents |
| `search_quality` | EXCELLENT | "Cotton Bollworm Control Spray" - precise, correct results |
| `output_hygiene` | EXCELLENT | No tool names; clean citation |
| `source_alignment` | EXCELLENT | All dosages and chemicals match MPKV/CICR docs |
| `no_fabrication` | EXCELLENT | Only sourced information provided |
| `citation_accuracy` | EXCELLENT | Farmer-friendly "MPKV कृषी दर्शनी" |
| `safety_compliance` | EXCELLENT | Correct dosages; includes PPE (mask, gloves); waiting period (21 days) before harvest |
| `completeness` | EXCELLENT | Covers chemical options, bio-control, timing, safety |
| `actionability` | EXCELLENT | Specific dosages (20ml/10L, 3g/10L), timing, application method |
| `context_fit` | N/A | No Agristack data available |
| `clarity` | EXCELLENT | Well-organized with clear sections |
| `conversation_closure` | EXCELLENT | Asks infestation percentage to refine advice |
| `grammar` | EXCELLENT | Correct grammar |
| `terminology` | EXCELLENT | Correct: बोंडअळी, फवारणी, फुलोरा अवस्था |
| `language_purity` | EXCELLENT | Pure Marathi; only chemical names in English (appropriate) |
| `fluency` | EXCELLENT | Natural, practical tone |

**Critical Failures:** None  
**Summary:** Strong response with minor process gap (not all terms searched). Excellent grounding with proper pesticide dosages, safety precautions (PPE, waiting period), and specific actionable advice.

---

## 4. Common Pitfalls

| Pitfall | Detection | Impact |
|---------|-----------|--------|
| **Document-Query Mismatch** | Compare query topic vs. doc content in trace | `source_alignment`: UNACCEPTABLE, `no_fabrication`: POOR-UNACCEPTABLE |
| **Term Search Fails but Recovers** | Wrong term matches but correct doc search | `term_identification`: ACCEPTABLE, but other scores can be high |
| **Generic When Specifics Available** | Doc has varieties/dosages; response is vague | `actionability`: POOR-ACCEPTABLE |
| **Agristack Fetched but Unused** | Data in trace but not in response | `context_fit`: POOR-ACCEPTABLE |
| **Tool Name Leakage** | "search_documents मधून", "get_scheme_info" in response | `output_hygiene`: UNACCEPTABLE-POOR, `citation_accuracy`: UNACCEPTABLE |

---

## 5. Evaluator Checklist

Before finalizing:

- [ ] Agristack available? → Was it called first?
- [ ] Were `search_terms` called before `search_documents`?
- [ ] Do retrieved docs match the query topic?
- [ ] Are all claims in response traceable to tool output?
- [ ] Any tool names or artifacts in response?
- [ ] Are dosages/chemicals safe and sourced?
- [ ] Is follow-up question specific to the query?
