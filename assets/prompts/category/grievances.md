# PM Kisan Grievance Evaluation Guide

## 1. Overview

**PM Kisan Grievance queries** cover two flows: filing a new grievance and checking the status of an existing one. Both are PM-KISAN specific.

### Tools

| Tool | Purpose |
|------|---------|
| `submit_grievance(identity_no, grievance_description, grievance_type)` | Files a new PM Kisan grievance |
| `grievance_status(identity_no)` | Checks status of an existing grievance |

### Expected Workflows

```
File Grievance:   Acknowledge empathetically → Ask grievance topic
                  → Ask reg number or Aadhaar → submit_grievance(...) → Share confirmation returned by tool

Check Status:     Ask reg number or Aadhaar → grievance_status(...) → Present status
```

### Key Rules

| Rule | Detail |
|------|--------|
| Empathy first | Acknowledge frustration before collecting any information |
| One step at a time | Ask grievance topic first, then identity number — never both at once |
| No type codes | Never show internal grievance type codes (G001–G010) or raw key names to the farmer |
| No source citation | Do not cite sources for grievance responses |
| Confirmation | Always share the confirmation/reference details returned by the tool, if any |

### Valid Grievance Types (internal keys — never expose to farmer)

| Key (passed to tool) | Backend Code | Human-Friendly Label |
|---|---|---|
| `ACCOUNT_NUMBER_NOT_CORRECT` | G001 | Account number not correct |
| `ONLINE_APPLICATION_PENDING_FOR_APPROVAL` | G002 | Online application pending for approval |
| `INSTALLMENT_NOT_RECEIVED` | G003 | Installment not received |
| `TRANSACTION_FAILED` | G004 | Transaction failed |
| `PROBLEM_IN_AADHAAR_CORRECTION` | G005 | Problem in Aadhaar correction |
| `GENDER_NOT_CORRECT` | G006 | Gender not correct |
| `PAYMENT_RELATED` | G007 | Payment related |
| `PROBLEM_IN_OTP_BASED_EKYC` | G008 | Problem in OTP-based eKYC |
| `PROBLEM_IN_BIO_METRIC_BASED_EKYC` | G009 | Problem in biometric-based eKYC |
| `PROBLEM_IN_FACIAL_BASED_EKYC` | G010 | Problem in facial-based eKYC |

> The agent passes the **Key** to the tool. The **Backend Code** is used internally by the API. The farmer should only ever see the **Human-Friendly Label**.

### Identity Number Rules

| Input | Behaviour |
|---|---|
| 12-digit Aadhaar | Tool internally fetches an Aadhaar token via `/GrievanceAadhaarToken` before submitting — transparent to farmer |
| 11-char alphanumeric PM-KISAN Reg No | Used directly |

### Sub-dimension Applicability

| Sub-dimension | Applicable? | Notes |
|---|---|---|
| `intent_accuracy` | ✅ | Distinguish file grievance vs status check |
| `moderation_compliance` | ✅ | Valid Agricultural check before processing |
| `tool_sequencing` | ✅ | Empathy → collect info → submit/status in order |
| `tool_usage` | ✅ CRITICAL | Correct identity_no, grievance_type key, grievance_description passed in correct order |
| `output_hygiene` | ✅ | No tool names; no type codes or key names exposed |
| `source_alignment` | ✅ | Confirmation and status from tool output only |
| `no_fabrication` | ✅ | No invented confirmation references or status outcomes |
| `citation_accuracy` | N/A | No source citation for grievance responses |
| `safety_compliance` | ✅ | Aadhaar/reg number handled discreetly |
| `completeness` | ✅ | Tool confirmation shared; next steps clear |
| `actionability` | ✅ | Farmer knows what happens next |
| `context_fit` | ✅ | Reuse identity number if already given in session |
| `clarity` | ✅ | Simple, reassuring language |
| `conversation_closure` | ✅ | Offer to help with another agricultural query |
| `grammar` | ✅ | Always |
| `terminology` | ✅ | Always |
| `language_purity` | ✅ | Always |
| `fluency` | ✅ | Always |

---

## 2. Rubrics

### PROCESS FIDELITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `intent_accuracy` | Correctly identifies file vs status; proceeds with correct flow | Correct flow; minor clarification needed | Correct after one follow-up | Wrong flow assumed; corrects when clarified | Wrong flow throughout |
| `moderation_compliance` | Valid Agricultural confirmed; proceeds | Minor hesitation; correct outcome | Minor inconsistency | Bypassed for borderline queries | Invalid query processed without check |
| `tool_sequencing` | Empathy → topic → identity → submit/status in correct order | Correct order; minor redundancy | Slightly out of order but reaches correct outcome | Order issues; farmer confused | Skips empathy; calls tool without collecting info |
| `tool_usage` | Correct identity_no type, grievance_type key, and grievance_description passed in correct parameter order | Correct; one minor issue | One non-critical error | Multiple errors; tool result affected | Wrong tool used, wrong parameter order, or missing required params |
| `output_hygiene` | No tool names, no type codes (G001–G010), no key names (e.g. INSTALLMENT_NOT_RECEIVED), no JSON in response | Clean; minor format issue | Minor artifact | Multiple artifacts | Tool names or type/key codes visible in response |

### FACTUAL GROUNDING

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `source_alignment` | Confirmation details and status exactly match tool output | Mostly matches; minor omission | Core info present; minor gap | Several mismatches | Invented confirmation reference or status |
| `no_fabrication` | All from tool; no-data acknowledged simply | Small inference acceptable | Minor gap | Fills gaps from memory | Invented confirmation references, outcomes, or timelines |
| `citation_accuracy` | N/A — no citation for grievance responses | N/A | N/A | N/A | Source cited unnecessarily; or tool name used as citation |
| `safety_compliance` | Aadhaar/reg number collected and handled discreetly; not repeated unnecessarily | Mostly discreet; minor phrasing gap | One minor exposure | Data unnecessarily repeated | Aadhaar or reg number exposed in response text |

### RESPONSE USEFULNESS

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `completeness` | Tool confirmation shared; grievance type communicated in plain language; next steps clear | Most info shared; minor gap | Core outcome shared; confirmation present | Confirmation missing or incomplete | No outcome communicated; farmer left unclear |
| `actionability` | Farmer knows the confirmation received, what it means, and what happens next | Mostly clear; one generic area | Some guidance | Minimal guidance | No next steps given |
| `context_fit` | Reuses identity number or grievance topic from session without re-asking | Minor re-ask of one known detail | Partially re-asks | Re-asks multiple known details | Re-asks everything; ignores session |
| `clarity` | Simple, reassuring language; short and easy to follow | Clear; minor organization issue | Understandable | Hard to follow | Confusing or overwhelming |
| `conversation_closure` | Offers related agricultural help (e.g., check PM Kisan status or scheme info) | Good follow-up; slightly generic | Generic | Weak or tangential | Dead end or out-of-scope offer |

### LANGUAGE QUALITY

| Sub-dimension | EXCELLENT | GOOD | ACCEPTABLE | POOR | UNACCEPTABLE |
|---|---|---|---|---|---|
| `grammar` | Perfect grammar in selected language | Minor errors; meaning fully clear | Errors; meaning still clear | Several errors; meaning affected | Broken; hard to understand |
| `terminology` | Correct terms (e.g., शिकायत, पंजीकरण नंबर) | Mostly correct | Mix of correct and improvised | Many vague terms | Wrong terms causing confusion |
| `language_purity` | Selected language only; English for proper nouns/IDs only | Mostly pure; minimal switching | Several unnecessary switches | Frequent code-switching | Heavy arbitrary mixing |
| `fluency` | Warm, natural, empathetic tone | Natural; one stilted phrase | Stilted but understandable | Often awkward or clinical | Machine-like or cold |

---

## 3. Annotated Examples

### Example A: EXCELLENT — Filing a PM Kisan Grievance

**Query:** `Mera PM Kisan ka paisa nahi aaya, kya kare?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent acknowledges frustration; asks what specifically the grievance is about]
Turn 2: Farmer: "Teen mahine se installment nahi mili"
        [Agent asks for registration number or Aadhaar]
Turn 3: Farmer gives reg number →
        submit_grievance(
          identity_no="MH123456789",
          grievance_description="Farmer has not received installment for 3 months",
          grievance_type="INSTALLMENT_NOT_RECEIVED"
        )
        → Tool returns confirmation message
```

**Response:**
```
मैं समझता हूं कि यह बहुत परेशान करने वाली बात है — तीन महीने से किश्त न आना सच में चिंता की बात है।

आपकी शिकायत दर्ज हो गई है।

संबंधित विभाग जल्द इस पर कार्रवाई करेगा।

क्या आप अपने PM Kisan पंजीकरण की वर्तमान स्थिति भी जांचना चाहेंगे?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Empathy first, topic collected, identity collected, then tool called with correct parameter order
- `tool_usage`: EXCELLENT — `identity_no`, `grievance_description`, `grievance_type` passed correctly; correct key `INSTALLMENT_NOT_RECEIVED` used
- `output_hygiene`: EXCELLENT — No type codes, no key names, no tool names; confirmation shared in plain language
- `actionability`: EXCELLENT — Farmer informed of submission and next steps
- `conversation_closure`: EXCELLENT — Specific offer to check PM Kisan status within tool scope

---

### Example B: UNACCEPTABLE — Empathy Skipped, Type Code Exposed

**Query:** `Mera PM Kisan ka paisa band ho gaya hai`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent immediately asks for Aadhaar — no empathy, no topic clarification]
Turn 2: Farmer gives Aadhaar →
        submit_grievance(
          identity_no="123456789012",
          grievance_description="payment stopped",
          grievance_type="INSTALLMENT_NOT_RECEIVED"
        )
        → Tool returns confirmation
```

**Response:**
```
आपकी शिकायत type INSTALLMENT_NOT_RECEIVED (G003) के लिए दर्ज हो गई है।
```

**Key Scores:**
- `tool_sequencing`: UNACCEPTABLE — Jumped straight to identity collection; no empathy, no topic clarification
- `output_hygiene`: UNACCEPTABLE — Internal key name `INSTALLMENT_NOT_RECEIVED` and backend code `G003` exposed to farmer
- `actionability`: POOR — Farmer doesn't know what happens next

**Correct Behavior:** Acknowledge frustration first → ask what the issue is → ask for identity number → submit with correct parameter order → share confirmation in plain language without type codes or key names.

---

### Example C: GOOD — Grievance Status Check

**Query:** `Maine pehle shikayat ki thi, uska kya hua?`
(User selected language: Hindi)

**Trace:**
```
Turn 1: [Agent asks for reg number or Aadhaar]
Turn 2: Farmer gives reg number →
        grievance_status(identity_no="MH123456789")
        → Returns status with GrievanceDate, GrievanceDescription, OfficerReply
```

**Response:**
```
आपकी शिकायत की स्थिति:

- **विषय:** किश्त नहीं मिली
- **दर्ज तिथि:** 12 मार्च 2024
- **अधिकारी का जवाब:** अभी तक जवाब नहीं आया है

संबंधित विभाग इस पर काम कर रहा है।

क्या आप PM Kisan की किश्त की स्थिति भी जांचना चाहेंगे?
```

**Key Scores:**
- `tool_sequencing`: EXCELLENT — Direct single-step status flow used correctly
- `completeness`: GOOD — Status shown clearly from tool fields (`GrievanceDate`, `GrievanceDescription`, `OfficerReply`)
- `conversation_closure`: GOOD — PM Kisan status offer is relevant; could also offer to file a follow-up if needed

---

## 4. Common Pitfalls

| Pitfall | Impact | Sub-dimension |
|---------|--------|---------------|
| **Skipping empathy; jumping straight to data collection** | HIGH | `fluency`, `tool_sequencing` |
| **Showing grievance type codes (G001–G010) or key names to farmer** | HIGH | `output_hygiene` |
| **Not sharing confirmation after submission** | HIGH | `completeness`, `actionability` |
| **Wrong parameter order in submit_grievance call** | HIGH | `tool_usage` |
| **Using wrong or lowercase grievance_type key** | HIGH | `tool_usage` |
| **Re-asking identity number already given in session** | MEDIUM | `context_fit` |
| **Citing a source for grievance responses** | MEDIUM | `citation_accuracy` |
| **Tool name leakage in response** | MEDIUM | `output_hygiene` |
| **Generic follow-up unrelated to PM Kisan** | LOW | `conversation_closure` |

---

## 5. Evaluator Checklist

- [ ] Did agent acknowledge frustration empathetically before collecting info?
- [ ] Was grievance topic collected before identity number?
- [ ] Was `submit_grievance` called with correct parameter order: `(identity_no, grievance_description, grievance_type)`?
- [ ] Was a valid ALL-CAPS grievance type key (e.g. `INSTALLMENT_NOT_RECEIVED`) used — not a lowercase or invented value?
- [ ] Was the tool confirmation/reference shared with the farmer in plain language?
- [ ] For status check: `grievance_status` called with `identity_no` (reg number or Aadhaar)?
- [ ] No grievance type codes (G001–G010) or key names visible in response?
- [ ] No source citation added to grievance response?
- [ ] Identity number (Aadhaar/reg_no) handled discreetly?
- [ ] Session context reused (identity number, grievance topic) without re-asking?
- [ ] Response in correct selected language (Hindi or English)?
