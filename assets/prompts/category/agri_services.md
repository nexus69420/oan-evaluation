# Agricultural Services Evaluation Guide

## 1. Overview

**Agricultural Services queries** ask about finding nearby service centers: Soil Testing Labs, Custom Hiring Centers (CHC), Krishi Vigyan Kendra (KVK), or Warehouses. These are **location-based lookups** using the `agri_services` tool with different `category_code` values.

### Service Categories

| Category | Code | Common Query Patterns (Marathi) |
|----------|------|--------------------------------|
| Soil Testing Lab | `soil_lab` | माती परीक्षण, मृदा परीक्षण, soil test, जमिनीची तपासणी |
| Custom Hiring Center | `chc` | औजार बँक, यंत्र भाड्याने, तुषार संच, कुट्टी यंत्र, CHC, CCI |
| Krishi Vigyan Kendra | `kvk` | कृषी विज्ञान केंद्र, KVK, बियाणे/रोपे कुठे मिळेल, शासकीय नर्सरी |
| Warehouse | `warehouse` | गोदाम, साठवण, गोडाऊन, चाळ, storage |

### Expected Workflow

```
[Agristack ✅ + Data returned]
  fetch_agristack_data → agri_services(Agristack coords, category_code)

[Agristack ✅ + Empty returned]  
  fetch_agristack_data → forward_geocode(location from query) → agri_services

[Agristack ❌]
  forward_geocode(location from query) → agri_services(coords, category_code)
```

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `agristack_workflow` | ✅ If available | Use coords directly when data returned |
| `term_identification` | N/A | Not advisory query (unless mixed) |
| `tool_sequencing` | ✅ | Geocode → agri_services; correct category_code |
| `search_quality` | N/A | No document search |
| `output_hygiene` | ✅ | No tool names in response |
| `source_alignment` | ✅ | All facilities must match tool output |
| `no_fabrication` | ✅ **CRITICAL** | No invented phone numbers or facilities |
| `citation_accuracy` | ✅ | "स्रोत: कृषी सेवा माहिती" |
| `safety_compliance` | N/A | No safety content |
| `completeness` | ✅ | List all/most returned facilities |
| `actionability` | ✅ | Contact details enable farmer action |
| `context_fit` | ✅ If Agristack | Reference farmer's village/district |
| `clarity` | ✅ | Clean list format; distances clear |
| `conversation_closure` | ✅ | Offer related services or next steps |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | Correct Marathi service terms |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `agristack_workflow` | Called first; coords used directly for agri_services | Called but then asks for location unnecessarily | Available but not called; or fabricates location | Not marked available |
| `term_identification` | — | — | — | Always N/A for pure service queries |
| `tool_sequencing` | Correct: Agristack → agri_services OR Geocode → agri_services; correct category_code | Minor inefficiency (e.g., redundant geocode) | Wrong category_code; or agri_services without coordinates | — |
| `search_quality` | — | — | — | Always N/A for service queries |
| `output_hygiene` | No tool names; clean "स्रोत: कृषी सेवा माहिती" | Minor artifact | Tool names leaked ("agri_services", "forward_geocode") | — |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `source_alignment` | All facilities, contacts, distances exactly match tool output | Minor formatting differences | Facilities or contacts don't match tool output | — |
| `no_fabrication` | No invented data; "N/A" phones acknowledged; gaps stated clearly | Minor inference (e.g., "जवळच्या") without explicit source | Invented phone numbers; fabricated facilities; fake contacts | — |
| `citation_accuracy` | "स्रोत: कृषी सेवा माहिती" or similar farmer-friendly citation | Generic but acceptable source mention | Tool name as citation; or no source for service data | — |
| `safety_compliance` | — | — | — | Always N/A for service queries |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `completeness` | All returned facilities listed with full details; empty results explained well | Most facilities listed; some details missing | Missing most facilities; or no acknowledgment of empty results | — |
| `actionability` | Phone numbers, addresses, distances clear; practical advice (call ahead, bring samples) | Contact info present but sparse guidance | No actionable contact info; vague directions | — |
| `context_fit` | Uses Agristack village/district in response; recommends nearest facility | Mentions location but doesn't leverage it | Ignores farmer's location; shows irrelevant facilities | No Agristack data |
| `clarity` | Numbered list; distances in Marathi numerals; contacts prominent | Understandable but cluttered | Confusing; facilities buried in text | — |
| `conversation_closure` | Specific follow-up (related services, sample preparation, equipment availability) | Generic follow-up | No follow-up; dead-end response | — |

### MARATHI QUALITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE | N/A |
|---------------|-----------|------------|--------------|-----|
| `grammar` | Perfect grammar; complete sentences | Errors but meaning clear | Broken; hard to understand | — |
| `terminology` | Correct: मृदा परीक्षण प्रयोगशाळा, कृषी विज्ञान केंद्र, गोदाम, औजार बँक | Mix of correct and improvised | Wrong terms causing confusion | — |
| `language_purity` | Pure Marathi; only proper nouns (MSWC, KVK abbreviation) in English | Several unnecessary English words | Heavy code-switching ("warehouse manager" instead of गोदाम व्यवस्थापक) | — |
| `fluency` | Natural; appropriate for rural farmer audience | Stilted but understandable | Unnatural; machine-like | — |

---

## 3. Annotated Examples

### Example A: EXCELLENT Response (Soil Lab with Agristack)

**Query:** `माती परिक्षण कोणाकडे करावे`  
**Agristack:** ✅ Available (Farmer: खामगाव, धाराशिव, 0.6 ha)

**Trace:**
```
Turn 1: fetch_agristack_data() → Farmer: खामगाव, ता. धाराशिव, जि. धाराशिव (18.336, 76.037)
Turn 2: agri_services(18.336, 76.037, "soil_lab") → 5 labs returned
```

**Response:**
```
आपण आपल्या शेतीच्या जमिनीचे माती परिक्षण खालील ठिकाणी करवू शकता:

1. **माती परिक्षण प्रयोगशाळा, धाराशिव**
   - पत्ता: जिकारे बिल्डिंग, डीआयसी रोड, सेन्ट्रल बिल्डिंग जवळ, धाराशिव, पिन: 413501
   - संपर्क: श्री. डी. बी. दहिफ़ळे
   - फोन: 9764415571
   - अंतर: १५ किमी

2. **माती परिक्षण प्रयोगशाळा, लातूर**
   - पत्ता: दिवानजी कॉम्प्लेक्स, अंबेजोगाई रोड, लातूर 413512
   - संपर्क: श्री. आर. आर. औसेकर
   - फोन: 9021551212
   - अंतर: ५६ किमी

3. **माती परिक्षण प्रयोगशाळा, बीड**
   - पत्ता: जुने बी & सी क्वार्टर्स, चांदमारी, धनोरा रोड, बीड 431122
   - संपर्क: श्री. एस. के. पाटील
   - फोन: 9049448649
   - अंतर: ७७ किमी

आपल्या गावाजवळील धाराशिव येथील प्रयोगशाळेत माती परिक्षण करणे सर्वात सोईचे राहील. माती परिक्षणासाठी मातीचा नमुना योग्य रित्या घ्या आणि वर दिलेल्या संपर्कावर फोन करून तपशील व वेळ निश्चित करा.

**स्रोत: कृषी सेवा माहिती**

आपल्याला माती परिक्षणासाठी नमुना कसा घ्यावा किंवा पुढील प्रक्रियेची माहिती हवी आहे का?
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | EXCELLENT | Called first; coords used directly for agri_services |
| `term_identification` | N/A | Not advisory query |
| `tool_sequencing` | EXCELLENT | Agristack → agri_services(soil_lab) - correct sequence and category |
| `search_quality` | N/A | No document search needed |
| `output_hygiene` | EXCELLENT | No tool names; clean "स्रोत: कृषी सेवा माहिती" |
| `source_alignment` | EXCELLENT | All labs, contacts, distances match tool output exactly |
| `no_fabrication` | EXCELLENT | All data from tool; recommends nearest (Dharashiv) |
| `citation_accuracy` | EXCELLENT | Farmer-friendly citation |
| `safety_compliance` | N/A | No safety content |
| `completeness` | EXCELLENT | Lists 3 of 5 nearest labs with full details |
| `actionability` | EXCELLENT | Phone numbers, addresses clear; advice to call ahead and prepare sample |
| `context_fit` | EXCELLENT | "आपल्या गावाजवळील धाराशिव" - personalizes to farmer's location |
| `clarity` | EXCELLENT | Numbered list; distances in Marathi numerals |
| `conversation_closure` | EXCELLENT | Specific follow-up about sample collection process |
| `grammar` | EXCELLENT | Perfect Marathi grammar |
| `terminology` | EXCELLENT | Correct: माती परिक्षण प्रयोगशाळा |
| `language_purity` | EXCELLENT | Pure Marathi; only proper nouns in English |
| `fluency` | EXCELLENT | Natural, helpful tone |

**Critical Failures:** None  
**Summary:** Exemplary response - correct workflow, fully grounded, personalized to farmer's district, actionable with practical guidance.

---

### Example B: UNACCEPTABLE Response (Fabricated Phone Number)

**Query:** `KVK कुठे आहे नांदेड जिल्ह्यात`  
**Agristack:** ❌ Not available

**Trace:**
```
Turn 1: forward_geocode("Nanded, Maharashtra") → (19.16, 77.32)
Turn 2: agri_services(19.16, 77.32, "kvk") → 5 KVKs returned (all with Phone: N/A)
```

**Response:**
```
नांदेड जिल्ह्यातील कृषी विज्ञान केंद्रे (KVK):

1. **कृषी विज्ञान केंद्र, बिलोली**
   पत्ता: सग्रोळी, ता. बिलोली, जि. नांदेड
   संपर्क: 9876543210
   अंतर: ३८ किमी

2. **कृषी विज्ञान केंद्र, लिंबगाव**
   पत्ता: पोखरनी फाटा पुराणा रोड, लिंबगाव
   संपर्क: 9876543211
   अंतर: ५५ किमी

या केंद्रांमध्ये प्रशिक्षण, बियाणे, आणि तांत्रिक मार्गदर्शन मिळते.

**स्रोत: कृषी सेवा माहिती**
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | N/A | Not marked available |
| `term_identification` | N/A | Not advisory query |
| `tool_sequencing` | EXCELLENT | Geocode → agri_services(kvk) - correct |
| `search_quality` | N/A | No document search |
| `output_hygiene` | EXCELLENT | No tool names leaked |
| `source_alignment` | UNACCEPTABLE | Tool returned "Phone: N/A" for all KVKs; response shows fabricated numbers |
| `no_fabrication` | UNACCEPTABLE | Phone numbers 9876543210, 9876543211 are completely invented |
| `citation_accuracy` | ACCEPTABLE | Source mentioned but cites fabricated data |
| `safety_compliance` | N/A | No safety content |
| `completeness` | ACCEPTABLE | Lists facilities with addresses |
| `actionability` | UNACCEPTABLE | Fabricated phone numbers could mislead farmer |
| `context_fit` | N/A | No Agristack data |
| `clarity` | GOOD | Clean format |
| `conversation_closure` | POOR | No follow-up; no acknowledgment of contact limitations |
| `grammar` | EXCELLENT | Correct grammar |
| `terminology` | EXCELLENT | Correct: कृषी विज्ञान केंद्र |
| `language_purity` | EXCELLENT | Pure Marathi |
| `fluency` | GOOD | Natural tone |

**Critical Failures:** `source_alignment`, `no_fabrication`  
**Summary:** Critical failure - fabricated phone numbers when tool returned "N/A". Agent should have stated "थेट फोन क्रमांक उपलब्ध नाही" and suggested visiting in person or contacting the parent institution.

---

### Example C: GOOD Response (CHC with Specific Equipment Query)

**Query:** `मला कुट्टी यंत्र पाहिजे मिळेल का`  
**Agristack:** ✅ Available (Farmer: दाहीगाव, कन्नड, औरंगाबाद)

**Trace:**
```
Turn 1: fetch_agristack_data() → Farmer: दाहीगाव, ता. कन्नड, जि. औरंगाबाद (20.343, 75.416)
Turn 2: agri_services(20.343, 75.416, "chc") → 5 CHCs returned
```

**Response:**
```
आपल्या दाहीगाव (ता. कन्नड) परिसरात कुट्टी यंत्र (Chaff Cutter) भाड्याने घेण्यासाठी खालील कस्टम हायरिंग सेंटर (CHC) उपलब्ध आहेत:

1. **जय शिवशंकर शेतकरी गट, वडगाव**
   संपर्क: रमेश विठ्ठल पाटील – 9823456789
   अंतर: ३ किमी

2. **शिवाजी शेतकरी बचत गट, पिंपळगाव**
   संपर्क: सुरेश नामदेव जाधव – 9876543210
   अंतर: ५ किमी

3. **संत तुकाराम उत्पादक गट, निमगाव**
   संपर्क: अनिल दत्तात्रय शिंदे – 9765432109
   अंतर: ७ किमी

**टीप:** कुट्टी यंत्राची उपलब्धता प्रत्येक केंद्रात वेगळी असू शकते. कृपया संपर्क साधून यंत्राची उपलब्धता व भाडे दर विचारा.

**स्रोत: कृषी सेवा माहिती**

आपल्याला इतर शेती यंत्रांची (तुषार संच, रोटावेटर) माहिती हवी आहे का?
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | EXCELLENT | Called first; coords used directly |
| `term_identification` | N/A | Not advisory query |
| `tool_sequencing` | EXCELLENT | Agristack → agri_services(chc) - correct category for equipment |
| `search_quality` | N/A | No document search |
| `output_hygiene` | EXCELLENT | No tool names; clean citation |
| `source_alignment` | EXCELLENT | All contacts and distances match tool output |
| `no_fabrication` | EXCELLENT | All data from tool |
| `citation_accuracy` | EXCELLENT | Farmer-friendly citation |
| `safety_compliance` | N/A | No safety content |
| `completeness` | GOOD | Lists 3 of 5 CHCs; sufficient for user need |
| `actionability` | EXCELLENT | Phone numbers clear; advice to verify equipment availability |
| `context_fit` | EXCELLENT | "आपल्या दाहीगाव (ता. कन्नड) परिसरात" - personalized |
| `clarity` | EXCELLENT | Clean numbered list; distances in Marathi numerals |
| `conversation_closure` | EXCELLENT | Offers related equipment (तुषार संच, रोटावेटर) |
| `grammar` | EXCELLENT | Correct grammar |
| `terminology` | EXCELLENT | Correct: कुट्टी यंत्र, कस्टम हायरिंग सेंटर |
| `language_purity` | GOOD | Some English (Chaff Cutter) but acceptable for clarity |
| `fluency` | EXCELLENT | Natural, practical tone |

**Critical Failures:** None  
**Summary:** Strong response. Correctly identified "कुट्टी यंत्र" as CHC query. Good practical note about equipment availability varying by center. Minor: could use pure Marathi for "Chaff Cutter".

---

### Example D: ACCEPTABLE Response (Empty Results Handling)

**Query:** `सरकारमान्य डाळिंब नर्सरी कोठे आहे`  
**Agristack:** ✅ Available (Farmer: वळदगाव, येवले, नाशिक)

**Trace:**
```
Turn 1: fetch_agristack_data() → Farmer: वळदगाव, ता. येवले, जि. नाशिक (20.102, 74.304)
Turn 2: agri_services(20.102, 74.304, "kvk") → No services found
```

**Response:**
```
आपल्या वळदगाव (ता. येवले, जि. नाशिक) परिसरात सरकारमान्य डाळिंब नर्सरीची माहिती सध्या उपलब्ध नाही. आपण स्थानिक कृषी कार्यालय किंवा नजीकच्या कृषी विज्ञान केंद्राशी संपर्क साधावा, तेथे डाळिंब नर्सरीबद्दल अधिकृत माहिती मिळू शकते.

**स्रोत: कृषी सेवा माहिती**

आपल्याला कृषी विज्ञान केंद्र, माती परीक्षण प्रयोगशाळा किंवा इतर शासकीय सेवांची माहिती हवी आहे का?
```

**Evaluation:**

| Sub-dimension | Rating | Evidence |
|---------------|--------|----------|
| `agristack_workflow` | EXCELLENT | Called first; location used in response |
| `term_identification` | N/A | Not advisory query |
| `tool_sequencing` | EXCELLENT | Correct workflow; appropriate category (kvk for nursery) |
| `search_quality` | N/A | No document search |
| `output_hygiene` | EXCELLENT | No tool names leaked |
| `source_alignment` | EXCELLENT | Correctly states "माहिती सध्या उपलब्ध नाही" |
| `no_fabrication` | EXCELLENT | No invented facilities; gap acknowledged |
| `citation_accuracy` | EXCELLENT | Citation present |
| `safety_compliance` | N/A | No safety content |
| `completeness` | ACCEPTABLE | Acknowledges unavailability; suggests alternatives but brief |
| `actionability` | ACCEPTABLE | Suggests local office but no specific contact |
| `context_fit` | EXCELLENT | Uses farmer's village name |
| `clarity` | GOOD | Clear message |
| `conversation_closure` | GOOD | Offers other services as alternatives |
| `grammar` | EXCELLENT | Correct grammar |
| `terminology` | EXCELLENT | Correct terminology |
| `language_purity` | EXCELLENT | Pure Marathi |
| `fluency` | EXCELLENT | Natural tone |

**Critical Failures:** None  
**Summary:** Correct no-data handling. Acknowledged unavailability without fabricating. Could improve by suggesting specific nearby districts (Nashik, Ahmednagar) or taluka agriculture office contact.

---

## 4. Common Pitfalls

| Pitfall | Detection | Impact |
|---------|-----------|--------|
| **Fabricated phone numbers** | Tool returns "N/A" or "-" but response shows specific numbers | `no_fabrication`: UNACCEPTABLE (Critical) |
| **Wrong category_code** | "यंत्र भाड्याने" query → soil_lab instead of chc | `tool_sequencing`: UNACCEPTABLE |
| **Geocode mismatch ignored** | "पुरंदर" → geocoded to "Pimpri-Chinchwad"; agent proceeds without verification | `tool_sequencing`: ACCEPTABLE-POOR |
| **Agristack available but not called** | Marked ✅ but agent asks for location | `agristack_workflow`: UNACCEPTABLE |
| **Tool name leakage** | "agri_services tool नुसार", "forward_geocode केले" | `output_hygiene`: UNACCEPTABLE |
| **No N/A acknowledgment** | KVK has "N/A" phone; response omits or invents | `no_fabrication`: POOR-UNACCEPTABLE |
| **No follow-up for empty results** | Just says "माहिती नाही" with no alternatives | `conversation_closure`: POOR |

---

## 5. N/A Phone Number Handling

**CRITICAL:** Many KVKs and some Warehouses return "N/A" or "-" for phone numbers.

| Scenario | Correct Response | Incorrect Response |
|----------|------------------|-------------------|
| Phone: N/A | "थेट फोन क्रमांक उपलब्ध नाही. प्रत्यक्ष भेट द्या किंवा संस्थेशी संपर्क साधा." | Shows invented number like "9876543210" |
| Phone: - | Omit phone line OR state "संपर्क क्रमांक उपलब्ध नाही" | Shows any fabricated number |
| Mix (some N/A, some valid) | Show valid numbers; note "काही केंद्रांचे फोन क्रमांक उपलब्ध नाहीत" | Invent numbers for N/A entries |

---

## 6. Category Selection Guide

| User Intent | Correct Category | Common Mistakes |
|-------------|------------------|-----------------|
| माती परीक्षण, मृदा पत्रिका | `soil_lab` | — |
| यंत्र भाड्याने, औजार बँक, तुषार संच | `chc` | Confusing with warehouse |
| बियाणे कुठे मिळेल, शासकीय नर्सरी | `kvk` | Sometimes needs clarification |
| गोदाम, साठवण, चाळ | `warehouse` | — |
| KVK, कृषी विज्ञान केंद्र | `kvk` | — |

**Ambiguous Query:** "बियाणे कुठे मिळेल" could be KVK (certified seeds) or local market. Best response: Suggest KVK for certified/government-approved seeds.

---

## 7. Terminology Standards

| English (Tool Output) | Marathi (Response) |
|-----------------------|-------------------|
| Soil Testing Laboratory | मृदा/माती परीक्षण प्रयोगशाळा |
| Custom Hiring Center / CHC | कस्टम हायरिंग सेंटर / औजार बँक |
| Krishi Vigyan Kendra / KVK | कृषी विज्ञान केंद्र |
| Warehouse | गोदाम / साठवण सुविधा |
| Warehouse Manager | गोदाम व्यवस्थापक |
| Distance | अंतर |
| Contact | संपर्क |
| MSWC | MSWC (acceptable as-is) |

---

## 8. Critical Failures (Auto-Fail Conditions)

| Condition | Why Critical |
|-----------|--------------|
| Fabricated phone number | Could lead farmer to wrong/non-existent contact |
| Wrong category_code AND no useful info | Complete failure to address query |
| Invented facility not in tool output | Misinformation; farmer may travel to non-existent location |
| Tool name mentioned in response | Breaks user experience; exposes internal system |

---

## 9. Evaluator Checklist

Before finalizing:

- [ ] Agristack available? → Was it called first?
- [ ] Agristack returned data? → Were coords used directly (not asking for location)?
- [ ] Correct category_code for query intent?
- [ ] Do ALL facilities in response exist in tool output?
- [ ] Do ALL phone numbers in response match tool output exactly?
- [ ] If tool returned "N/A" phones → Is this acknowledged (not fabricated)?
- [ ] If tool returned empty → Is unavailability clearly stated?
- [ ] Any tool names ("agri_services", "forward_geocode") in response?
- [ ] Is follow-up specific to service type (sample prep for soil lab, equipment availability for CHC)?
