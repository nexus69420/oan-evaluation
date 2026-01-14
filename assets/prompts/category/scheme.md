# Scheme Information Evaluation Guide

## 1. Overview

**Scheme Information queries** ask about government agricultural schemes - benefits, eligibility, application process, documents, etc. This is the **most complex** use case due to scheme selection logic and personalization requirements.

### Tools

| Tool | Purpose |
|------|---------|
| `get_scheme_codes()` | Returns full list of State + Central schemes with codes |
| `get_scheme_info(scheme_code)` | Detailed info for one scheme |
| `get_multiple_schemes_info([codes])` | Batch fetch for multiple related schemes (preferred when 2+ schemes relevant) |

### Expected Workflow

```
[General Info Query]
get_scheme_codes() → identify relevant scheme(s) → get_scheme_info / get_multiple_schemes_info

[Eligibility Query + Agristack ✅]
fetch_agristack_data() → get_scheme_codes() → get_scheme_info → Personalized assessment

[Eligibility Query + Agristack ❌]
get_scheme_codes() → get_scheme_info → General eligibility conditions only
```

### Agristack Usage (Nuanced)

| Scenario | Expected Behavior |
|----------|-------------------|
| Agristack ✅ + Eligibility query | SHOULD fetch → personalized assessment (caste, land size, PoCRA status) |
| Agristack ✅ + General info query | CAN fetch (enhances response) OR skip (acceptable) |
| Agristack ❌ | General info + eligibility conditions stated; no personalization |

### PoCRA Village Check (Critical)

Agristack profile contains: `Is PoCRA village?: Yes/No`

All `ndksp-*` schemes require PoCRA village:
- `ndksp-drip-irrigation`, `ndksp-sprinkler-irrigation`, `ndksp-pump-set`, `ndksp-individual-farm-ponds`, etc.

| PoCRA Status | Recommendation |
|--------------|----------------|
| Agristack shows "PoCRA: Yes" | Can recommend ndksp-* schemes |
| Agristack shows "PoCRA: No" | Should NOT recommend ndksp-* OR clarify ineligibility |
| Agristack ❌ | Mention "PoCRA गावात असणे आवश्यक" as condition |

### Multiple Schemes per Need

| User Query | Relevant Schemes | Tool Choice |
|------------|------------------|-------------|
| "पिक विमा" | mahadbt-pmfby + mahadbt-rwbcis | `get_multiple_schemes_info` |
| "ड्रिप सिंचन" | ndksp-drip-irrigation + mahadbt-pmkrvypdmc | `get_multiple_schemes_info` |
| "शेती यंत्र अनुदान" | sdda-farm-machinery + cdda-farm-machinery | `get_multiple_schemes_info` |
| "PM किसान" | mahadbt-pmkisan only | `get_scheme_info` |

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `agristack_workflow` | ✅ Nuanced | Required for eligibility; optional for general info |
| `term_identification` | ✅ | Scheme name matching |
| `tool_sequencing` | ✅ | get_scheme_codes → get_scheme_info/get_multiple_schemes_info |
| `search_quality` | N/A | No document search |
| `output_hygiene` | ✅ | No tool names in response |
| `source_alignment` | ✅ | Benefits/eligibility must match tool output |
| `no_fabrication` | ✅ **CRITICAL** | No invented schemes, benefits, timelines |
| `citation_accuracy` | ✅ | "स्रोत: शासकीय योजना माहिती" |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ **CRITICAL** | All relevant schemes; comprehensive details |
| `actionability` | ✅ | Portal URL, documents, application process |
| `context_fit` | ✅ | PoCRA check, caste-based eligibility |
| `clarity` | ✅ | State vs Central distinguished |
| `conversation_closure` | ✅ | Offer related schemes or further help |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | योजना, अनुदान, पात्रता, लाभ |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `agristack_workflow` | Eligibility query → fetches Agristack → personalized assessment with PoCRA check | General info without Agristack (acceptable); OR eligibility query with general conditions only | Recommends PoCRA scheme to non-PoCRA farmer; OR fabricates eligibility without data |
| `term_identification` | Correctly maps user query to scheme code(s) | Minor mismatch but corrects | Wrong scheme selected; no correction |
| `tool_sequencing` | get_scheme_codes → get_multiple_schemes_info (for 2+ schemes) | get_scheme_codes → multiple get_scheme_info calls (works, less efficient) | Skips get_scheme_codes; guesses scheme_code |
| `output_hygiene` | No tool names; clean response | Minor artifact | "get_scheme_info tool नुसार" leaked |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `source_alignment` | Benefits, eligibility, documents exactly match tool output | Minor paraphrasing | Invented details not in tool output |
| `no_fabrication` | No invented schemes, benefits, timelines, subsidy guarantees | — | Fabricated scheme; promised "40% नक्की मिळेल"; invented deadlines |
| `citation_accuracy` | "स्रोत: शासकीय योजना माहिती" | Generic source | Tool name as citation |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `completeness` | All relevant schemes listed; benefits, eligibility, documents, portal, process covered; State/Central distinguished | Main scheme covered; some related schemes or details missed | Only partial info; major schemes omitted; key eligibility missing |
| `actionability` | Portal URL, documents list, step-by-step process clear | Some guidance | No next steps; vague "कार्यालयात जा" |
| `context_fit` | PoCRA requirement stated; caste-based subsidy differences noted; personalized if Agristack ✅ | General conditions stated | Wrong scheme for farmer's context |
| `clarity` | State vs Central clear; scheme purpose distinct | Understandable | Confusing; schemes conflated |
| `conversation_closure` | Offers related schemes or further assistance | Generic follow-up | Dead end |

### MARATHI QUALITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `grammar` | Perfect | Minor errors | Broken |
| `terminology` | योजना, अनुदान, पात्रता, लाभ, अर्ज प्रक्रिया | Mix | Wrong terms |
| `language_purity` | Pure Marathi; scheme names in English acceptable | Some English | Heavy code-switching |
| `fluency` | Natural | Stilted | Robotic |

---

## 3. Annotated Examples

### Example A: EXCELLENT (Multiple Schemes + Personalization)

**Query:** `ड्रिप सिंचनासाठी अनुदान मिळेल का?`  
**Agristack:** ✅ Available (PoCRA: Yes, Caste: SC)

**Trace:**
```
Turn 1: fetch_agristack_data() → PoCRA: Yes, Caste: SC, Land: 1.2 ha
Turn 2: get_scheme_codes() → Full list
Turn 3: get_multiple_schemes_info(["ndksp-drip-irrigation", "mahadbt-pmkrvypdmc"]) → Both schemes
```

**Response:**
```
तुमच्या प्रोफाइलनुसार तुम्ही PoCRA गावात आहात आणि SC प्रवर्गातील आहात, त्यामुळे तुम्हाला ड्रिप सिंचनासाठी दोन योजनांचा लाभ घेता येईल:

**१. नानाजी देशमुख कृषी संजीवनी प्रकल्प (NDKSP) - ठिबक सिंचन**
- राज्य योजना (PoCRA गावांसाठी)
- SC/ST शेतकऱ्यांना ५५% अनुदान
- MahaDBT पोर्टलवर अर्ज करावा

**२. PM-RKVY पर ड्रॉप मोअर क्रॉप**
- केंद्र योजना (सर्व गावांसाठी)
- ४५% पर्यंत अनुदान
- MahaDBT पोर्टलवर अर्ज

**आवश्यक कागदपत्रे:** ७/१२ उतारा, आधार, बँक पासबुक, जातीचा दाखला

**अर्ज:** https://mahadbt.maharashtra.gov.in

**स्रोत: शासकीय योजना माहिती**

तुम्हाला अर्ज प्रक्रियेबद्दल अधिक मदत हवी आहे का?
```

**Key Scores:** `agristack_workflow`: EXCELLENT (personalized with PoCRA+caste), `completeness`: EXCELLENT (both schemes), `tool_sequencing`: EXCELLENT (batch fetch)

---

### Example B: ACCEPTABLE (General Info, No Personalization)

**Query:** `PM किसान योजनेची माहिती द्या`  
**Agristack:** ✅ Available

**Trace:**
```
Turn 1: get_scheme_codes() → Full list
Turn 2: get_scheme_info("mahadbt-pmkisan") → PM-KISAN details
```

**Response:**
```
**प्रधानमंत्री किसान सन्मान निधी (PM-KISAN)**

केंद्र शासनाची योजना ज्यात पात्र शेतकरी कुटुंबांना वर्षाला ₹६,००० मिळतात - तीन समान हप्त्यांमध्ये (₹२,००० प्रत्येक).

**पात्रता:** लागवडीयोग्य जमीन असलेले आर्थिकदृष्ट्या दुर्बल शेतकरी कुटुंबे

**आवश्यक कागदपत्रे:** ७/१२ उतारा, आधार, बँक खाते, e-KYC

**अर्ज:** pmkisan.gov.in वर ऑनलाइन

**स्रोत: शासकीय योजना माहिती**
```

**Key Scores:** `agristack_workflow`: ACCEPTABLE (Agristack available but not used - general info query so acceptable), `completeness`: EXCELLENT, `tool_sequencing`: EXCELLENT

---

### Example C: EXCELLENT (Misconception Correction)

**Query:** `PMFBY मध्ये ट्रॅक्टर अनुदान कसे मिळेल?`  
**Agristack:** ❌

**Trace:**
```
Turn 1: get_scheme_codes() → Full list
Turn 2: get_scheme_info("mahadbt-pmfby") → Crop insurance details
Turn 3: get_multiple_schemes_info(["sdda-farm-machinery-and-equipments", "cdda-farm-machinery-and-equipments"]) → Machinery schemes
```

**Response:**
```
**PMFBY (प्रधानमंत्री फसल विमा योजना)** ही पिक विमा योजना आहे, यंत्र अनुदान योजना नाही. या योजनेत नैसर्गिक आपत्तीमुळे पिकाचे नुकसान झाल्यास विमा संरक्षण मिळते.

**ट्रॅक्टर अनुदानासाठी योग्य योजना:**

**१. राज्य प्रायोजित कृषी यंत्रीकरण (SDDA)**
- राज्य योजना
- SC/ST/महिला/लहान शेतकरी: ५०% अनुदान
- इतर: ४०% अनुदान

**२. केंद्रीय कृषी यंत्रीकरण उपमिशन (CDDA)**
- केंद्र योजना
- समान अनुदान दर

**आवश्यक कागदपत्रे:** यंत्राचे कोटेशन, टेस्ट रिपोर्ट, ट्रॅक्टर RC

**अर्ज:** https://mahadbt.maharashtra.gov.in

**स्रोत: शासकीय योजना माहिती**

तुम्हाला कोणत्या विशिष्ट यंत्रासाठी माहिती हवी आहे?
```

**Key Scores:** `term_identification`: EXCELLENT (corrected misconception), `completeness`: EXCELLENT (provided correct schemes), `actionability`: EXCELLENT

---

### Example D: UNACCEPTABLE (Wrong PoCRA Recommendation)

**Query:** `मला ड्रिप सिंचन योजना सांगा`  
**Agristack:** ✅ Available (PoCRA: No)

**Trace:**
```
Turn 1: fetch_agristack_data() → PoCRA: No
Turn 2: get_scheme_codes() → Full list
Turn 3: get_scheme_info("ndksp-drip-irrigation") → PoCRA scheme details
```

**Response:**
```
**नानाजी देशमुख कृषी संजीवनी प्रकल्प - ठिबक सिंचन**

तुम्हाला या योजनेत ५५% अनुदान मिळू शकते...

[continues with NDKSP details without mentioning ineligibility]
```

**Critical Failures:**
- `agristack_workflow`: UNACCEPTABLE - Agristack showed PoCRA: No, but recommended PoCRA-only scheme
- `context_fit`: UNACCEPTABLE - Did not check/mention PoCRA requirement

**Correct Response Should:** Note "तुमचे गाव PoCRA क्षेत्रात नाही, त्यामुळे NDKSP योजना लागू नाही" → Suggest PM-RKVY Per Drop More Crop instead

---

### Example E: UNACCEPTABLE (Incomplete, Single Scheme)

**Query:** `पिक विमा योजना सांगा`  
**Agristack:** ❌

**Trace:**
```
Turn 1: get_scheme_codes() → Full list
Turn 2: get_scheme_info("mahadbt-pmfby") → PMFBY only
```

**Response:**
```
**प्रधानमंत्री फसल विमा योजना (PMFBY)**

[Only PMFBY details, no mention of RWBCIS]

**स्रोत: शासकीय योजना माहिती**
```

**Critical Failures:**
- `completeness`: UNACCEPTABLE - Missed RWBCIS (weather-based crop insurance)
- `tool_sequencing`: ACCEPTABLE but suboptimal - Should have used get_multiple_schemes_info

**Correct Response Should:** Include both PMFBY and RWBCIS with their differences (crop-cutting vs weather-based)

---

### Example F: UNACCEPTABLE (Fabrication)

**Query:** `आत्मा योजनेची माहिती द्या`  
**Agristack:** ❌

**Trace:**
```
Turn 1: get_scheme_codes() → ATMA not in list
Turn 2: search_terms("ATMA") → No match
```

**Response:**
```
**आत्मा योजना (ATMA - Agricultural Technology Management Agency)**

या योजनेत शेतकऱ्यांना प्रशिक्षण आणि तंत्रज्ञान हस्तांतरणासाठी ₹५०,००० पर्यंत अनुदान मिळते...

**अर्ज:** जिल्हा कृषी कार्यालयात संपर्क साधा

**स्रोत: शासकीय योजना माहिती**
```

**Critical Failures:**
- `no_fabrication`: UNACCEPTABLE - Scheme not in database but invented details
- `source_alignment`: UNACCEPTABLE - Cited source but fabricated content

**Correct Response Should:** "आत्मा योजनेची माहिती सध्या उपलब्ध नाही. कृपया योजनेचे पूर्ण नाव सांगा किंवा जिल्हा कृषी कार्यालयात संपर्क साधा."

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Recommending PoCRA scheme to non-PoCRA farmer** | CRITICAL | `agristack_workflow`, `context_fit` |
| **Fabricating scheme details when not found** | CRITICAL | `no_fabrication` |
| **Missing related schemes** (only one when multiple exist) | HIGH | `completeness` |
| **No misconception correction** (wrong scheme for need) | HIGH | `term_identification` |
| **Promising exact subsidy %** without category context | MEDIUM | `no_fabrication` |
| **Missing eligibility conditions** | MEDIUM | `completeness` |
| **No portal URL or documents list** | MEDIUM | `actionability` |
| **Tool name leakage** | MEDIUM | `output_hygiene` |
| **Unnecessary Agristack for general info** | LOW | Minor inefficiency |

---

## 5. Scheme Mapping Reference

| User Query Pattern | Relevant Schemes | Notes |
|--------------------|------------------|-------|
| पिक विमा, crop insurance | mahadbt-pmfby, mahadbt-rwbcis | Both should be mentioned |
| ड्रिप/ठिबक सिंचन | ndksp-drip-irrigation (PoCRA), mahadbt-pmkrvypdmc | PoCRA check needed |
| स्प्रिंकलर सिंचन | ndksp-sprinkler-irrigation (PoCRA), mahadbt-pmkrvypdmc | PoCRA check needed |
| शेती यंत्र, ट्रॅक्टर | sdda-farm-machinery, cdda-farm-machinery | State + Central both |
| पंप संच | ndksp-pump-set (PoCRA), other irrigation schemes | PoCRA check needed |
| शेळी पालन | ndksp-goat-rearing | PoCRA only |
| PM किसान | mahadbt-pmkisan | Single scheme |
| फळबाग | mahadbt-bfhps, ndksp-horticulture-plantation | Multiple options |

---

## 6. Eligibility Assessment (When Agristack ✅)

Agent can use Agristack data to provide personalized eligibility:

| Agristack Field | Use |
|-----------------|-----|
| `Is PoCRA village?` | Determines ndksp-* scheme eligibility |
| `Caste Category` | Subsidy % varies (SC/ST/General) |
| `Total Plot Area` | Small/marginal farmer classification |
| `Gender` | Women farmers get higher subsidy in some schemes |

**Example personalized response:**
> "तुमच्या प्रोफाइलनुसार तुम्ही PoCRA गावात आहात आणि SC प्रवर्गातील आहात, त्यामुळे तुम्हाला ५५% अनुदान मिळू शकते."

---

## 7. Evaluator Checklist

- [ ] Correct scheme(s) identified for user's need?
- [ ] If user asked wrong scheme → misconception corrected?
- [ ] All relevant schemes covered (not just one)?
- [ ] State schemes prioritized before Central?
- [ ] Eligibility query + Agristack ✅ → personalized assessment?
- [ ] PoCRA scheme recommended → PoCRA status verified?
- [ ] Benefits/eligibility match tool output exactly?
- [ ] Portal URL and documents included?
- [ ] No timeline promises or guaranteed subsidy %?
- [ ] Scheme not found → acknowledged (not fabricated)?
- [ ] Tool names absent from response?
- [ ] Citation present: "स्रोत: शासकीय योजना माहिती"?
