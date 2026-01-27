# Agri Assistant Contact Evaluation Guide

## 1. Overview

**Agri Assistant Contact queries** ask for contact information of local agricultural staff (कृषी सहाय्यक). Uses the `contact_agricultural_staff` tool which returns village-level agricultural assistant details.

**Important Limitation:** This tool ONLY provides agricultural assistant contacts. NOT Talathi, Tehsildar, NAFED, or District Agriculture Officers (these are different departments).

### Expected Workflow

```
[Agristack ✅ + Data returned]  fetch_agristack_data → contact_agricultural_staff(Agristack coords)
[Agristack ✅ + Empty returned]  fetch_agristack_data → forward_geocode → contact_agricultural_staff
[Agristack ❌]                   forward_geocode → contact_agricultural_staff
```

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `agristack_workflow` | ✅ If available | Use coords directly |
| `term_identification` | N/A | Not advisory |
| `tool_sequencing` | ✅ | Geocode → contact_agricultural_staff |
| `search_quality` | N/A | No document search |
| `output_hygiene` | ✅ | No tool names |
| `source_alignment` | ✅ | Officer details must match tool |
| `no_fabrication` | ✅ **CRITICAL** | No invented contacts |
| `citation_accuracy` | ✅ | "स्रोत: कृषी संस्थापक निर्देशिका" |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ | All details; clarify scope if needed |
| `actionability` | ✅ | Phone + guidance on officer's role |
| `context_fit` | ✅ If Agristack | Reference farmer's village |
| `clarity` | ✅ | Clear presentation |
| `conversation_closure` | ✅ | Offer related help |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | कृषी सहाय्यक, विभाग, तालुका |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `agristack_workflow` | Called first; coords used directly | Called first; coords partially used | Called but asks location unnecessarily | Called very late; location ignored | Available but not called |
| `tool_sequencing` | Correct sequence; valid coordinates | Correct sequence; minor redundancy | Minor inefficiency | Significant inefficiency | No valid coordinates |
| `output_hygiene` | No tool names; clean citation | Clean; minor formatting issue | Minor artifact | Multiple artifacts | Tool names leaked |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `source_alignment` | All details match tool output | Most details match; minor omission | Minor formatting differences | Several mismatches | Details don't match |
| `no_fabrication` | No invented data; gaps acknowledged | All data sourced; small inference | Minor inference | Significant unsupported claims | Fabricated phone/name |
| `citation_accuracy` | "स्रोत: कृषी संस्थापक निर्देशिका" | Correct source; minor format issue | Generic source | Source unclear | Tool name as citation |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `completeness` | All details; scope clarified if out-of-scope query | Most details; scope mentioned | Most details | Significant gaps | Missing phone; no scope clarification |
| `actionability` | Phone clear; explains officer's role | Phone clear; basic guidance | Contact present, sparse guidance | Minimal actionable info | No phone; vague |
| `context_fit` | Uses Agristack village in response | Mostly personalized | Generic location mention | Minimal personalization | Ignores location |
| `clarity` | Clean format; phone prominent | Clear; minor organization issue | Understandable but cluttered | Hard to follow | Confusing |
| `conversation_closure` | Offers related help or higher officer guidance | Good follow-up; slightly generic | Generic follow-up | Weak follow-up | Dead end |

### MARATHI QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---------------|-----------|------|------------|------|--------------|
| `grammar` | Perfect | Minor errors; fully clear | Errors but clear | Several errors; meaning affected | Broken |
| `terminology` | Correct: कृषी सहाय्यक, विभाग, तालुका | Mostly correct; one improvised | Mix | Many improvised terms | Wrong terms |
| `language_purity` | Pure Marathi | Mostly pure; minimal English | Some English | Frequent English | Heavy code-switching |
| `fluency` | Natural, respectful | Natural; minor stilted phrase | Stilted | Often stilted | Unnatural |

---

## 3. Annotated Examples

### Example A: EXCELLENT (Standard Query)

**Query:** `पालम तालुका कृषी अधिकारी कोण आहेत`  
**Agristack:** ✅ (empty) → Geocode fallback

**Trace:** `fetch_agristack_data → forward_geocode("Palam") → contact_agricultural_staff → Ajay Mule, 9021934404`

**Response:**
```
पालम तालुक्यातील कृषी अधिकारी:

• नाव: **अजय मुले** (कृषी सहाय्यक)  
• कार्यालय: पालम, तालुका पालम, जिल्हा परभणी  
• संपर्क: ९०२१९३४४०४

शेतकऱ्यांसाठी कृषि योजना, पीक सल्ला, समस्या निवारण यासाठी संपर्क साधा.

**स्रोत: कृषी संस्थापक निर्देशिका**
```

**Key Scores:** `agristack_workflow`: EXCELLENT (correct fallback), `source_alignment`: EXCELLENT, `actionability`: EXCELLENT

---

### Example B: GOOD (Out-of-Scope Query with Clarification)

**Query:** `सातबारा वेगवेगळ्या करायचे आहे तर कोणत्या डिपार्टमेंट विचारायला लागते`  
**Agristack:** ✅ (Farmer: मांडवा, दिग्रस, यवतमाळ)

**Trace:** `fetch_agristack_data → contact_agricultural_staff → Suresh Jadhao, 9922662537`

**Response:**
```
सातबारा उतारे महसूल विभागाशी (Revenue Department) संबंधित आहे. तलाठी किंवा तहसील कार्यालयात संपर्क साधा.

आपल्या मांडवा गावासाठी कृषी सहाय्यक:
• सुरेश जाधव – 9922662537 (दिग्रस, यवतमाळ)

शेतजमिनीशी संबंधित कामांसाठी ते मार्गदर्शन करू शकतात.

**स्रोत: कृषी संस्थापक निर्देशिका**
```

**Key Scores:** `completeness`: EXCELLENT (clarifies 7/12 is Revenue Dept), `context_fit`: EXCELLENT (uses farmer's village)

---

### Example C: UNACCEPTABLE (Fabricated Contact)

**Query:** `नांदेड जिल्ह्यातील कृषी अधिकारी संपर्क`  
**Agristack:** ❌

**Trace:** `forward_geocode → contact_agricultural_staff → "No officer details found"`

**Response:**
```
नांदेड जिल्ह्यातील कृषी अधिकारी:
• श्री. रामराव पाटील – 9876543210

**स्रोत: कृषी संस्थापक निर्देशिका**
```

**Critical Failures:** `source_alignment`: UNACCEPTABLE, `no_fabrication`: UNACCEPTABLE  
**Why:** Tool returned empty; officer name and phone are completely fabricated.

**Correct Response Should:** Acknowledge "माहिती सध्या उपलब्ध नाही" and suggest taluka/district agriculture office.

---

## 4. Common Pitfalls

| Pitfall | Impact |
|---------|--------|
| **Fabricated phone/name when tool empty** | CRITICAL - `no_fabrication` UNACCEPTABLE |
| **No scope clarification for Talathi/NAFED queries** | `completeness` POOR |
| **Agristack available but not called** | `agristack_workflow` UNACCEPTABLE |
| **Tool name in response** | `output_hygiene` UNACCEPTABLE |
| **No guidance on officer's role** | `actionability` ACCEPTABLE max |

---

## 5. Scope Handling

| Query Type | Correct Handling |
|------------|------------------|
| सातबारा / Talathi | Clarify it's Revenue Dept; provide agri contact as helpful reference |
| NAFED | Explain separate org; agri assistant may have local info |
| District Officer | Tool gives village-level only; suggest taluka office for higher |

---

## 6. Evaluator Checklist

- [ ] Agristack available? → Called first?
- [ ] Tool returned officer? → Name/phone match exactly?
- [ ] Tool returned empty? → Acknowledged without fabrication?
- [ ] Out-of-scope query (Talathi/NAFED)? → Scope clarified?
- [ ] Any tool names in response?
- [ ] Guidance on what officer can help with?
