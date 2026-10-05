# Amul eval: metrics so far

A reading note for the scores already posted on the Gujarati seed run `seed-gu-capture-3` (75 turns, 28 chats, dataset `amul-seed-questions` on dev Langfuse). The run used the eval copy of the agent, not the shared app.

Eight metrics from the original list are still not built. They are at the bottom.

## How to read a score

Judge scores are 1 to 5. 5 is a clean pass. The judge is Gemma, with a written rule for each metric. If the rule says this turn does not apply, nothing is posted. Langfuse then shows an empty cell. An empty cell is not a failure. The screen sometimes draws that empty cell as 0.

Code checks are usually 1 (pass) or 0 (fail). They do not ask a model. They compare the tool call, the tool result, and the reply.

## What is worrying

These are the results worth reading first. High averages elsewhere mostly mean the turn was fine.

1. **The milk total is wrong.** On `milk-week` turn 2 the farmer asked for the week's litres. The reply says 72.7 L. The 15 rows the milk tool returned add up to 68.4 L. `milk_total` is 0 on that turn. The grounding judge still gave the same turn a high score, so do not trust `source_alignment` to catch a bad sum.

2. **Government scheme lookup is broken, and the agent fills the gap from memory.** For PM-KISAN, KCC, and PMFBY the tool comes back with "temporarily unavailable". The reply still describes those schemes (`scheme-all` turn 1 and `scheme-apply` turn 1). `recovery_clarification` is 2 on both. The union-scheme text in the same replies is real tool data. The central-scheme text is not.

   What fails underneath: the eval app asks the dev scheme service. Bharat Vistaar does send a reply. The dev gateway throws that reply away because the signature on it does not check out. The same signature also fails when the production callbacks are checked offline. The dev registry key and the prod registry key are already the same, so copying the prod key will not fix it. Separately, the PM-KISAN body that arrives has an empty scheme list, so a fixed signature still would not fill that answer. This needs Bharat Vistaar / the agriculture department. It is recorded as amul-oan-api issue 350. Do not turn the signature check off, and do not point the eval app at production to get around it.

3. **A pregnant-animal dose is given to animals that are not pregnant.** Five replies tell the farmer to use 25–30 g mineral mixture (sometimes also 30–50 g salt). Those numbers sit in the document under pregnant animals. The animal in the question is not pregnant: `health-anoestrus-2`, `health-conceive` turns 1–3, `health-heat-4`. `safety_compliance` and `search_quality` are both 2 there. The search query itself was on the farmer's topic. The reply picked the wrong passage.

4. **A milk date in the future.** On 2 Oct the farmer asked about "the 14th". The agent fetched 14 Oct instead of 14 Sep (`milk-dates` turn 1). `tool_arguments` fails that turn.

5. **A loan the tools never returned.** `scheme-all` turn 3 describes a Kheda district bank loan. This farmer is in Banaskantha, union Banas. No tool returned that loan. `task_success` is low, and `agristack_workflow` is 2.

6. **Tickets get damaged in translation.** Out of 17 booking tickets, two reached the farmer wrong: `EVAL-NET-0007` was transliterated, and `EVAL-HEALTH-0007` became `EVAL-HEALTH-00007`.

7. **Gujarati fluency looks weak, and it is not calibrated yet.** Fluency averages 3.72, the lowest language score. The judge is reacting to English sentences translated word for word, including "I don't know based on the provided documents", which means little to a farmer. Do not treat 3.72 as a release number until about 15 turns are scored by hand and compared.

Smaller misses, already scored, not the same size as the list above:

- `health-heat` turns 2 and 5 never searched the documents. `scheme-gov` turn 1 searched the union schemes when the farmer asked for government schemes. `expected_tools` is 0 on those.
- `milk-week` turn 4 asks which dairy, after this farmer's Banas milk was already on screen. `context_retention` and `agristack_workflow` are 3.
- `health-visit` turn 2 asks again whether to book a doctor after the farmer already asked for one.
- `ai-home` turn 1 and `ai-seed-en` turn 1 ask for the animal and the technician in one reply. Recovery is 3. One question at a time is the rule.
- Four scheme turns ask the union tool and the document search the same question (`scheme-all` turn 2, `scheme-calf`, `scheme-gap`, `scheme-loan`). Sequencing is 4, not a broken order.
- `scheme-heifer` turn 2 names Vasudhara Dairy. The documents that come back do not include that dairy. Search quality is 4.

## Process: did the agent use its tools properly

### `output_hygiene` — code — 75/75 pass

The farmer's Gujarati reply must not show the machinery. The check scans the reply for tool names, code-style words, raw JSON, internal web addresses, file names such as `.docx` or `.pdf`, technician user ids, and English reasoning that leaked through. Any one of those is a fail. None of the 75 replies had them. The farmer's own society code is allowed.

### `search_quality` — judge — 17 searches, mean 4.06

Only turns that called `search_documents`. The judge reads the query, the passages that came back, and what the reply actually used. A query on the farmer's problem with a matching passage is a 5. Using a pregnant-animal passage for an animal that is not pregnant is a 2, even when the query was on topic. A search that never happened is left blank here and failed on `expected_tools` instead.

### `agristack_workflow` — judge — 66 turns, mean 4.92

There is no Agristack tool in prod, in dev, or in the eval app. The name is kept from the original metric list. What is scored is the signed-in farmer profile: union Banas, Banaskantha, one cow, one buffalo, and two AI technicians. A 5 uses the profile fact the answer needs, or correctly ignores the profile on general advice. Asking for something the profile already has is a 3 (`milk-week` turn 4 asks which dairy). Inventing a fact that fights the profile is a 2 (the Kheda loan). Asking cow or buffalo is a 5, because the profile has both. The AI technicians are for insemination only, not the vet.

### `term_identification` — judge — 22 turns, mean 5.00

This agent has no separate "find the search terms" step. The score is the words sent into `search_documents`, `get_vistaar_scheme_info`, or `get_union_scheme_data`. A 5 names the animal, the problem, or the scheme the farmer asked about. Booking and milk calls are left blank. A wrong passage is `search_quality`, not this score. Every scored lookup named the farmer's term.

### `tool_sequencing` — judge — 44 turns, mean 4.91

Order, and whether a booking waited. Insemination should not be booked until the farmer has named cow or buffalo and chosen a technician. A health visit should not be booked twice. Lookups that do not depend on each other can run in any order. Sending the same scheme question to the union tool and then to document search is a 4. One lookup on its own is left blank. A wrong single tool is `expected_tools`. A bad date or a wrong species is `tool_arguments`.

## Facts: is the reply true and safe

### `source_alignment` — judge — 69 turns, mean 4.96

Every factual claim in the reply should match the tool result or the farmer profile. Clarifying questions and the thank-you are left blank. This judge missed the 72.7 L milk total. Use `milk_total` for sums.

### `no_fabrication` — judge — 75 turns, mean 4.87

The agent must not invent a dose, a price, a scheme rule, a contact, or a farmer fact. General husbandry advice is allowed when it is short and tells the farmer to ask a vet. Specific claims have to come from a tool or a document. The same rules as the agent's own prompt.

### `citation_accuracy` — judge — 9 turns, mean 4.78

Scored only when the reply names where a fact came from: a brochure, a circular, the farmer's own records, a link. Not naming a source is allowed, and those 66 turns are blank. A 5 is a real source in farmer-friendly words. A tool name or a source that was never retrieved is a 1. Eight of the nine were 5s. One was a 3.

### `safety_compliance` — judge — 9 turns, mean 3.22

Scored only when the reply names a medicine, a brand, a dose, or a procedure. "Talk to a vet" with no dose is left blank. The low average is the pregnant-animal mineral dose used on animals that are not pregnant.

## Language

One judge call scores grammar, terminology, language purity, fluency, and an overall `gujarati_language` (mean 4.05, kept so older charts still line up). The judge sees the Gujarati the farmer got, plus the short glossary that the translator was given for that answer.

| Score | Mean | What it is |
|---|---|---|
| `grammar` | 4.77 | Complete, correct Gujarati sentences. |
| `terminology` | 4.69 | Dairy, vet, and scheme words match the glossary when the glossary has them. |
| `language_purity` | 4.59 | Hindi or English mixed in where a Gujarati word would do. A short form such as AI or PD is tolerated. |
| `fluency` | 3.72 | Sounds like a person talking to a farmer, not like English translated line by line. Not calibrated yet. |

### `language_mixing` — code — mean 4.84

A second, mechanical pass on the same idea. Other scripts score 1. English words in the sentence score 2. English in brackets scores 3. Only short forms such as AI or PD score 4. Clean Gujarati scores 5. The judge is the one that also catches Hindi written in Gujarati letters.

### `glossary_adherence` — code — 59 turns

Share of that answer's glossary terms whose approved Gujarati actually appears. It checks that the word is present, not that the sentence means the right thing. Meaning is `translation_meaning`. Sixteen answers had no glossary terms, so they are blank.

### `translation_meaning` — judge — 75 turns, mean 4.79

The English answer and the Gujarati reply should say the same thing. A ticket that gets transliterated, "Soil Health Card" turned into a generic health card, or union help called a central-government scheme, scores down.

## Amul jobs: did the farmer get what they asked for

### `expected_tool_called` — code — 28/28

Once per chat, on the last turn. Did this chat ever call the tool the seed sheet named (`create_ai_call`, `create_health_call`, the milk tool, or the union-scheme tool)? All 28 did. Earlier turns are blank on purpose.

### `expected_tools` — code — 53 turns, mean 0.94

This turn, not the whole chat. The seed sheet lists the tool that should run. A cell marked `prior:...` passes if that tool already ran earlier in the chat. An empty cell (a clarifying question) is not scored. Fails: `health-heat` turns 2 and 5 called no document search, and `scheme-gov` turn 1 called the union tool instead of the government-scheme tool.

### `tool_arguments` — code — 20 of 21 pass

Booking and milk calls only. Booking must use this farmer's union, society, and farmer code. The species must match what the farmer said. The AI technician must be one of the two on the list. An emergency must be marked emergency. A milk date range must be real dates, end after it starts, stay within 31 days, and not end after the day of the question. The fail is `milk-dates` turn 1, the future 14 Oct.

### `ticket_consistency` — code — booking turns that returned a ticket

The ticket in the English answer and in the Gujarati reply must be the ticket the booking tool returned. The two mangled tickets above are the misses.

### `milk_total` — code — 2 turns

When the farmer asks for a litre total or an earnings total, add the milk rows already fetched in that chat. Litres must match within 0.05. Rupees must match within ₹0.50. `milk-week` turn 2 is 0 (72.7 L against 68.4 L). Turn 3, the earnings total, passes.

### `task_success` — judge — 74 turns, mean 4.96

Did this turn do the thing the farmer asked? A thank-you is left blank. The low one is `scheme-all` turn 3, the loan that no tool returned.

### `recovery_clarification` — judge — 29 turns, mean 4.66

When something is missing or a tool fails, the agent should ask one clear question or say plainly that it does not have the information. Filling in scheme benefits after the tool said unavailable is a 2. Asking for the animal and the technician in the same breath is a 3. A finished booking, a thank-you, and a turn whose tools already returned usable data are left blank.

### `context_retention` — judge — 47 turns, mean 4.91

From the second turn on, the reply should keep facts the farmer already gave. The first turn of each chat is blank. Asking again for something already answered is a 3. A brand-new question that names its own animal replaces the earlier one and can still be a 5. A general "how do I book?" after a ticket exists can be a 5. It does not have to repeat the ticket.

## Extra numbers, not in the original metric list

### `latency_s` — code — mean 13.6 seconds

How long the turn took. Not a quality score. The previous capture was faster only because the content tools failed immediately.

### `reference_agreement` — judge — 2 turns

Used when a knowledge tool failed. The reply is compared with a successful answer to a similar question from other Amul Agent Dev chats. Only two turns on this run had that kind of reference.

## Not built yet

Usefulness: completeness, actionability, context fit, clarity, conversation closure.

Amul-specific: persona, brevity (especially voice), and content gap (the documents did not have the answer, as opposed to the model getting it wrong).

Golden answers are still out of scope. Fluency still needs a hand-scored sample before it is used as a release signal.
