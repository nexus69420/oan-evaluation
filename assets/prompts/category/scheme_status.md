# Scheme Status Evaluation Guide

## 1. Overview

**Scheme Status queries** are multi-turn flows where a farmer checks their benefit status for PMFBY, PM Kisan, or Soil Health Card. Each scheme has a distinct tool flow and required data sequence.

### Tools

| Tool | Purpose |
|------|---------|
| `initiate_pmfby_status_check(phone_number)` | Sends OTP to farmer's phone for PMFBY verification |
| `check_pmfby_status_with_otp(otp, phone_number, inquiry_type, year, season)` | Fetches PMFBY policy or claim status |
| `initiate_pm_kisan_status_check(reg_no)` | Sends OTP to registered mobile for PM Kisan verification |
| `check_pm_kisan_status_with_otp(otp, reg_no)` | Fetches PM Kisan payment status |
| `check_shc_status(phone_number, cycle)` | Fetches Soil Health Card report directly |

### Expected Workflows

```
PMFBY Status:    Ask phone → initiate_pmfby_status_check(phone_number)
                 → Ask OTP (6 digits) → check_pmfby_status_with_otp(otp, phone_number, inquiry_type, year, season)

PM Kisan Status: Ask reg_no → initiate_pm_kisan_status_check(reg_no)
                 → Ask OTP (4 digits) → check_pm_kisan_status_with_otp(otp, reg_no)

SHC Status:      Ask phone + cycle year → check_shc_status(phone_number, cycle)
```

### Key Rules per Scheme

| Scheme | Required Inputs | Special Rules |
|--------|----------------|---------------|
| PMFBY | Phone → OTP (6 digits) → inquiry_type + year + season | Never echo OTP digits; reuse inquiry type if stated earlier in session |
| PM Kisan | Registration number → OTP (4 digits, auto-sent to registered mobile) | Do NOT ask for phone — OTP sent automatically to registered mobile; OTP is exactly 4 digits |
| SHC | Phone + cycle year | Ask naturally; do not expose YYYY-YY format to farmer; agent converts plain year to YYYY-YY before calling tool |

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---|---|---|
| `intent_accuracy` | ✅ | Must identify which scheme status is being requested |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `tool_sequencing` | ✅ CRITICAL | Two-step flows for PMFBY and PM Kisan; wrong order breaks flow |
| `tool_usage` | ✅ CRITICAL | Correct parameters (reg_no vs phone_number, inquiry_type, year, season, cycle) |
| `output_hygiene` | ✅ | No tool names or artifacts in response |
| `source_alignment` | ✅ | Status data must match tool output exactly |
| `no_fabrication` | ✅ | No invented status, UTR numbers, or payment dates |
| `citation_accuracy` | N/A | No source citation needed for status responses |
| `safety_compliance` | ✅ CRITICAL | OTP never echoed; sensitive data handled discreetly |
| `completeness` | ✅ | All relevant status fields shown |
| `actionability` | ✅ | Clear next steps (e.g., UTR for payment issues) |
| `context_fit` | ✅ CRITICAL | Reuse phone, OTP, scheme, year/season from session — never re-ask |
| `clarity` | ✅ | Status presented clearly |
| `conversation_closure` | ✅ | Offer related follow-up within tool scope |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | Always |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `intent_accuracy` | Identifies exact scheme and status type; proceeds with correct flow immediately | Correct scheme; minor clarification needed | Correct scheme identified after one follow-up | Wrong scheme assumed; corrects when clarified | Wrong scheme throughout; never corrects |
| `moderation_compliance` | Valid Agricultural confirmed; proceeds | Minor hesitation; correct outcome | Processed with minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `tool_sequencing` | Perfect two-step flow (initiate → check); single-step for SHC | Correct flow; minor redundancy | Correct but slight sequence delay | Step order issues affecting experience | Skips initiate step; jumps directly to check tool |
| `tool_usage` | Correct parameters: right phone_number/reg_no, inquiry_type, year, season, cycle | Correct; one minor formatting error | One non-critical parameter error | Multiple errors; result affected | Wrong input type (e.g., phone_number for PM Kisan instead of reg_no; wrong OTP digit count) |
| `output_hygiene` | No tool names, JSON, or artifacts in response | Clean; minor format issue | Minor artifact; meaning clear | Multiple artifacts | Tool names or raw function syntax visible in response |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `source_alignment` | All status fields match tool output exactly | Most match; minor omission | Core status shown; some fields omitted | Several mismatches | Invented status not in tool output |
| `no_fabrication` | All from tool; no-data acknowledged simply | Small inference from returned data | Minor gap | Fills gaps from memory | Invented UTR numbers, payment dates, or claim status |
| `citation_accuracy` | N/A — no citation needed for status responses | N/A | N/A | N/A | Tool name used as citation |
| `safety_compliance` | OTP never echoed; phone/reg number handled discreetly | Mostly secure; minor phrasing gap | One minor data exposure | Sensitive data unnecessarily repeated | OTP echoed verbatim; reg numbers unnecessarily exposed |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `completeness` | All status fields shown (payment, UTR, crop, season, dates) | Most shown; minor gap | Core status shown; some fields missed | Significant gaps | Status not shown; only error message returned |
| `actionability` | Clear next step (e.g., share UTR with bank; re-initiate if OTP expired) | Mostly clear; one generic area | Some guidance | Minimal guidance | No next steps |
| `context_fit` | Reuses all session data (phone, OTP, scheme, year/season) without re-asking | Minor re-ask of one already-given detail | Partially re-asks known info | Re-asks multiple known details | Re-asks everything; ignores session history |
| `clarity` | Status in simple, readable format; easy to act on | Clear; minor organization issue | Understandable | Hard to follow | Confusing or overloaded |
| `conversation_closure` | Specific offer (e.g., check claim vs policy; check another scheme or year) | Good follow-up; slightly generic | Generic | Weak or tangentially related | Dead end or out-of-scope offer |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `grammar` | Perfect grammar in selected language | Minor errors; meaning fully clear | Errors; meaning still clear | Several errors; meaning affected | Broken; hard to understand |
| `terminology` | Correct Hindi/English terms (e.g., किश्त, पॉलिसी, UTR, बीमित राशि) | Mostly correct; one imprecise term | Mix of correct and improvised | Many vague terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; English for proper nouns/scheme names only | Mostly pure; minimal switching | Several unnecessary switches | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Natural, conversational tone suitable for farmer | Natural; one or two stilted phrases | Stilted but understandable | Often awkward or clinical | Machine-like or overly technical |

---

## 3. Annotated Examples

### Example A: EXCELLENT — PMFBY Policy Status

**Query (Turn 1):** `Mujhe PMFBY mein apni policy ka status check karna hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for phone number]
Turn 2: Farmer gives phone → initiate_pmfby_status_check(phone_number) → OTP sent
Turn 3: [Agent says "OTP sent, please share it" — does not echo digits]
Turn 4: Farmer gives 6-digit OTP → Agent: "OTP received" → asks year + season (inquiry_type=policy_status already known)
Turn 5: Farmer gives year + season → check_pmfby_status_with_otp(otp, phone_number, "policy_status", "2024", "Kharif")
```

**Response:**
```
आपकी PMFBY पॉलिसी का विवरण:

- **फसल:** धान
- **सीज़न:** खरीफ 2024
- **बीमित राशि:** ₹45,000
- **प्रीमियम:** ₹900
- **स्थिति:** पॉलिसी सक्रिय है

क्या आप अपने दावे (claim) की स्थिति भी जांचना चाहेंगे?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Two-step flow followed correctly in order
- `safety_compliance`: EXCELLENT — OTP not echoed; confirmed simply as "OTP received"
- `context_fit`: EXCELLENT — inquiry_type (policy_status) reused from Turn 1 without re-asking
- `conversation_closure`: EXCELLENT — Specific offer to check claim using same phone and OTP

---

### Example B: UNACCEPTABLE — OTP Echoed + Wrong Input for PM Kisan

**Query:** `PM Kisan ka status check karna hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for phone number ← WRONG; should ask for registration number]
Turn 2: Farmer gives phone → initiate_pm_kisan_status_check(phone) ← WRONG parameter type
Turn 3: Farmer gives 4-digit OTP "4567" → Agent: "Your OTP 4567 is verified." ← OTP echoed
Turn 4: [Registration number was given earlier in session — agent asks again]
```

**Response:**
```
आपका OTP 4567 verified हो गया है।

कृपया अपना पंजीकरण नंबर फिर से दें।
```

**Key Scores:**
- `tool_usage`: UNACCEPTABLE — Phone used instead of registration number; PM Kisan requires reg_no
- `safety_compliance`: UNACCEPTABLE — OTP digits "4567" echoed verbatim in response
- `context_fit`: UNACCEPTABLE — Registration number already given in session; asked again unnecessarily

**Correct Behavior:** Ask for registration number → `initiate_pm_kisan_status_check(reg_no)` → tell farmer OTP sent to registered mobile → ask for 4-digit OTP → confirm receipt without echoing digits.

---

### Example C: GOOD — SHC Status with Minor Gap

**Query:** `Mera soil health card dekhna hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for phone and cycle year naturally (e.g., "Which year's card do you want?")]
Turn 2: Farmer gives phone + "2023" → agent converts to "2023-24" →
        check_shc_status(phone_number="9876543210", cycle="2023-24")
```

**Response:**
```
🧾 **[Click here for Soil Health Card](report-url)**

**किसान:** रमेश पाटील | **जिला:** नागपुर

**मिट्टी की स्थिति:** तटस्थ (neutral pH)
**जैविक कार्बन:** कम — खाद या FYM डालें

**कम पोषक तत्व:** नाइट्रोजन, फॉस्फोरस
- Combo-1: DAP 17 kg + Urea 45 kg प्रति एकड़

**सुझाई गई फसलें:** गेहूं, चना, सोयाबीन

क्या आप मिट्टी सुधार के बारे में और जानना चाहेंगे?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Single-step SHC flow used correctly; YYYY-YY format handled internally by agent without exposing to farmer
- `completeness`: GOOD — Report link, soil condition, nutrients shown; fertilizer combos present for only one crop instead of 2–3
- `conversation_closure`: GOOD — Relevant follow-up on soil improvement; could be more specific (e.g., "for wheat or chana specifically?")

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Asking phone instead of reg_no for PM Kisan** | CRITICAL | `tool_usage` |
| **Echoing OTP digits in response** | CRITICAL | `safety_compliance` |
| **Skipping initiate step; calling check tool directly** | CRITICAL | `tool_sequencing` |
| **Accepting 6-digit OTP for PM Kisan (expects exactly 4 digits)** | CRITICAL | `tool_usage` |
| **Re-asking phone/OTP/scheme already given in session** | HIGH | `context_fit` |
| **Fabricating UTR or payment dates when tool returns empty** | HIGH | `no_fabrication` |
| **Exposing YYYY-YY cycle year format to farmer for SHC** | MEDIUM | `output_hygiene` |
| **Tool name leakage in response** | MEDIUM | `output_hygiene` |
| **Generic follow-up instead of scheme-specific offer** | LOW | `conversation_closure` |

---

## 5. Evaluator Checklist

- [ ] Correct scheme status flow identified (PMFBY / PM Kisan / SHC)?
- [ ] PMFBY: Two-step flow used (initiate → check with OTP)?
- [ ] PMFBY: OTP collected is 6 digits?
- [ ] PM Kisan: Registration number used (not phone) to initiate?
- [ ] PM Kisan: OTP collected is exactly 4 digits?
- [ ] SHC: Both phone_number and cycle year collected before calling tool?
- [ ] SHC: Agent converted plain year from farmer to YYYY-YY format without exposing format to farmer?
- [ ] OTP never echoed verbatim in any response?
- [ ] Sensitive data (phone, reg_no) handled discreetly?
- [ ] Session context reused (phone, OTP, year/season) without re-asking?
- [ ] Status fields presented from tool output only (no fabrication)?
- [ ] No tool names visible in response?
- [ ] Follow-up offer within tool capabilities (e.g., check claim vs policy; another year)?
- [ ] Response in correct selected language (Hindi or English)?
