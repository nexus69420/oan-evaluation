You are checking whether the Amul dairy assistant's Gujarati reply still means the same thing as the English answer it was translated from. Farmers see only the Gujarati.

Your task: score **translation_meaning**. Do not grade grammar, fluency, or whether the English answer was factually right.

---

**Farmer's message (Gujarati):** {{ question_gu }}

**English answer (the source):**
```
{{ answer }}
```

**Gujarati reply (what the farmer received):**
```
{{ answer_gu }}
```

---

## translation_meaning
- 5: the same request is answered. Numbers, dates, amounts, names, ticket ids, yes/no, and the question asked of the farmer all match.
- 4: the meaning matches. One harmless wording change, and no fact, number, name, or ticket changed.
- 3: the main point matches, but a secondary detail was dropped or softened.
- 2: a number, date, amount, name, ticket id, or yes/no changed, or a ticket was transliterated so the farmer cannot use it.
- 1: the Gujarati reply is a different answer from the English.
- null: there is no English answer, or no Gujarati reply.

Ticket ids such as EVAL-NET-0007 must appear unchanged. A Gujarati spelling of the same id, or an extra digit, is a 2.

## Rules
- Compare the two answers only. Do not use outside knowledge.
- Whole numbers 1-5 or null only.
- `evidence`: one English sentence quoting the English fact and the Gujarati wording that matches or changes it.

Return **STRICT JSON only**, no markdown:
{"translation_meaning": {"score": <1-5 or null>, "evidence": "..."}}
