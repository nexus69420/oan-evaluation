# MahaDBT Status Evaluation Guide

## 1. Overview

**MahaDBT Status queries** ask about farmer's scheme application status on the MahaDBT portal. Uses `get_scheme_status` which takes **NO arguments** - it automatically uses farmer_id from context.

**Critical Requirement:** This tool requires farmer authentication. If Agristack is marked ❌ (not available), the agent CANNOT use this tool and must ask user to login.

### Tool Behavior
- Returns: Application ID (masked), status, financial year, scheme name
- Scheme name often shows "Unknown Scheme" (data limitation)
- Application IDs are PII-masked: `***3214` (shows only last 4 digits)

### Common Statuses
| Status | Meaning |
|--------|---------|
| ⏳ Wait List | Application in queue (most common) |
| ✅ Fund Disbursed | Money transferred |
| ✅ Approved | Approved, pending disbursement |
| 🚫 Department Cancelled | Rejected by department |
| 📄 Auto cancelled | Cancelled due to document/timeline issue |

### Expected Workflow

```
[Agristack ✅]  get_scheme_status() → Show results
[Agristack ❌]  DO NOT call tool → Ask user to login with Agristack
```

**Note:** Unlike other use cases, Agristack data fetch is NOT required before calling this tool. Calling `fetch_agristack_data` first is unnecessary and should be penalized as inefficiency.

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---------------|-------------|-------|
| `agristack_workflow` | ✅ Special | Calling Agristack = inefficiency; ❌ = must ask login |
| `term_identification` | N/A | Not advisory |
| `tool_sequencing` | ✅ | Direct get_scheme_status; no geocode needed |
| `search_quality` | N/A | No document search |
| `output_hygiene` | ✅ | No tool names; keep IDs masked |
| `source_alignment` | ✅ | Status/ID/year must match exactly |
| `no_fabrication` | ✅ **CRITICAL** | No fake statuses, timelines, scheme names, or unmasked IDs |
| `citation_accuracy` | ✅ | "स्रोत: महाडीबीटी अर्ज स्थिती" |
| `safety_compliance` | N/A | — |
| `completeness` | ✅ | All applications shown; empty acknowledged |
| `actionability` | ✅ | Next steps (contact office, check portal) |
| `context_fit` | N/A | No location context needed |
| `clarity` | ✅ | Status prominent; IDs masked |
| `conversation_closure` | ✅ | Offer scheme info or other help |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | प्रतीक्षा यादी, अर्ज रद्द, etc. |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `agristack_workflow` | Direct get_scheme_status (no Agristack call) | Calls Agristack first (unnecessary but works) | Agristack ❌ but tries get_scheme_status anyway |
| `tool_sequencing` | Single get_scheme_status call | Minor inefficiency | Wrong tool; or no tool when Agristack ✅ |
| `output_hygiene` | No tool names; IDs stay masked (***3214) | Minor artifact | Tool names leaked; or unmasked full application ID |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `source_alignment` | Status, ID, year exactly match tool output | Minor formatting | Details don't match tool output |
| `no_fabrication` | No invented data; "Unknown Scheme" kept as-is; no timeline promises | Minor inference | Invented scheme name, status, timeline, or unmasked ID |
| `citation_accuracy` | "स्रोत: महाडीबीटी अर्ज स्थिती" | Generic source | Tool name as citation |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `completeness` | All applications listed; empty results clearly stated | Most info present | Missing applications; or fabricates when empty |
| `actionability` | Clear next steps (contact कृषी कार्यालय, check portal) | Some guidance | No guidance; or false promises ("2 सप्ताहात मिळेल") |
| `clarity` | Status prominent; financial year clear; masked ID shown | Understandable | Confusing; buried info |
| `conversation_closure` | Offers related help (scheme info, other queries) | Generic follow-up | Dead end |

### MARATHI QUALITY

| Sub-dimension | EXCELLENT | ACCEPTABLE | UNACCEPTABLE |
|---------------|-----------|------------|--------------|
| `grammar` | Perfect | Errors but clear | Broken |
| `terminology` | Correct: प्रतीक्षा यादी, अर्ज रद्द, निधी वितरण | Mix | Wrong terms |
| `language_purity` | Pure Marathi; MahaDBT/portal acceptable | Some English | Heavy code-switching |
| `fluency` | Natural | Stilted | Unnatural |

---

## 3. Annotated Examples

### Example A: EXCELLENT (Direct Tool Call)

**Query:** `अर्ज स्थिती`  
**Agristack:** ✅ Available

**Trace:**
```
Turn 1: get_scheme_status() → 1 application, Wait List, ***3709, FY 2025-2026
```

**Response:**
```
आपल्या MahaDBT अर्जाची स्थिती:

• अर्ज क्रमांक: ***3709
• आर्थिक वर्ष: 2025-2026
• स्थिती: प्रतीक्षा यादीत आहे

आपला अर्ज सध्या प्रक्रियेत आहे. स्थानिक कृषी कार्यालयाशी संपर्क साधा किंवा MahaDBT पोर्टलवर नियमित तपासा.

**स्रोत: महाडीबीटी अर्ज स्थिती**
```

**Key Scores:** `agristack_workflow`: EXCELLENT (no unnecessary Agristack call), `no_fabrication`: EXCELLENT (ID kept masked), `actionability`: EXCELLENT

---

### Example B: ACCEPTABLE (Unnecessary Agristack Call)

**Query:** `ट्रॅक्टर अनुदान कधी मिळेल`  
**Agristack:** ✅ Available

**Trace:**
```
Turn 1: fetch_agristack_data() → Farmer info returned
Turn 2: get_scheme_status() → 2 applications (1 Cancelled, 1 Wait List)
```

**Response:**
```
आपल्या ट्रॅक्टर अनुदान अर्जाची स्थिती:

• एक अर्ज: विभागाने रद्द केला
• दुसरा अर्ज: प्रतीक्षा यादीत आहे (आर्थिक वर्ष 2022-2023)

प्रतीक्षा यादीतील अर्ज मंजूर झाल्यावर अनुदान मिळेल. कृषी कार्यालयात संपर्क साधा.

**स्रोत: महाडीबीटी अर्ज स्थिती**
```

**Key Scores:** `agristack_workflow`: ACCEPTABLE (unnecessary fetch_agristack_data), `no_fabrication`: EXCELLENT (no timeline promised), `source_alignment`: EXCELLENT

---

### Example C: UNACCEPTABLE (Fabrication)

**Query:** `माझ्या पंप संच अर्जाचे काय झाले`  
**Agristack:** ✅ Available

**Trace:**
```
Turn 1: get_scheme_status() → "No scheme application information found"
```

**Response:**
```
आपल्या पंप संच अर्जाची स्थिती:

• अर्ज क्रमांक: 252620001234567
• योजना: राष्ट्रीय कृषी विकास योजना - पंप संच
• स्थिती: मंजूर - अनुदान 2 आठवड्यात मिळेल

**स्रोत: महाडीबीटी अर्ज स्थिती**
```

**Critical Failures:** 
- `no_fabrication`: UNACCEPTABLE - Tool returned empty, but response shows invented application
- `no_fabrication`: UNACCEPTABLE - Unmasked full application ID (should be ***4567)
- `no_fabrication`: UNACCEPTABLE - Promised timeline ("2 आठवड्यात")
- `source_alignment`: UNACCEPTABLE - Invented scheme name

**Correct Response Should:** State "आपल्या प्रोफाइलमध्ये पंप संच अर्ज सापडला नाही" and suggest checking with local office or verifying application was submitted.

---

### Example D: UNACCEPTABLE (Agristack ❌ But Proceeds)

**Query:** `माझा अर्ज कुठपर्यंत आला`  
**Agristack:** ❌ Not available

**Trace:**
```
Turn 1: get_scheme_status() → "Farmer ID is not available in the context"
```

**Response:**
```
आपल्या अर्जाची स्थिती तपासण्यासाठी प्रणालीत समस्या आली. कृपया पुन्हा प्रयत्न करा.

**स्रोत: महाडीबीटी अर्ज स्थिती**
```

**Critical Failures:**
- `agristack_workflow`: UNACCEPTABLE - Should not have attempted tool when Agristack ❌

**Correct Response Should:** "MahaDBT अर्ज स्थिती पाहण्यासाठी आपल्याला Agristack द्वारे लॉगिन करणे आवश्यक आहे. कृपया आपल्या शेतकरी ID सह लॉगिन करा."

---

## 4. Common Pitfalls

| Pitfall | Impact |
|---------|--------|
| **Fabricated status when tool returns empty** | CRITICAL - `no_fabrication` UNACCEPTABLE |
| **Invented scheme name for "Unknown Scheme"** | CRITICAL - `no_fabrication` UNACCEPTABLE |
| **Unmasking application ID** (showing full number) | CRITICAL - `output_hygiene` UNACCEPTABLE |
| **Promising timelines** ("2 सप्ताहात मिळेल") | CRITICAL - `no_fabrication` UNACCEPTABLE |
| **Calling fetch_agristack_data first** | `agristack_workflow` ACCEPTABLE (penalty) |
| **Attempting tool when Agristack ❌** | `agristack_workflow` UNACCEPTABLE |
| **Tool name in response** | `output_hygiene` UNACCEPTABLE |

---

## 5. No-Data Handling

| Scenario | Correct Response |
|----------|------------------|
| Agristack ❌ | "MahaDBT स्थिती पाहण्यासाठी Agristack लॉगिन आवश्यक आहे" |
| Tool returns empty | "आपल्या प्रोफाइलमध्ये अर्ज सापडला नाही. स्थानिक कृषी कार्यालयात तपासा." |
| "Unknown Scheme" | Keep as-is OR say "योजनेचे नाव उपलब्ध नाही"; do NOT invent name |

---

## 6. Evaluator Checklist

- [ ] Agristack ❌? → Did agent ask for login (not attempt tool)?
- [ ] Agristack ✅? → Did agent skip unnecessary fetch_agristack_data?
- [ ] Tool returned data? → Do status/ID/year match exactly?
- [ ] Tool returned empty? → Is this acknowledged (not fabricated)?
- [ ] Application ID masked in response (***XXXX)?
- [ ] Any timeline promises ("X दिवसात मिळेल")?
- [ ] "Unknown Scheme" → Was scheme name invented?
- [ ] Any tool names in response?
