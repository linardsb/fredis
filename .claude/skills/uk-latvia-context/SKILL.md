---
name: uk-latvia-context
description: |
  Reference pack for UK and Latvian administrative context — Companies House, HMRC,
  Lursoft, VID, VAT thresholds, filing deadlines, cross-border tax. Reference only —
  no API calls, no writes. Cites sources; flags when an answer needs a human advisor.
  Use when user asks about: "VAT threshold", "Companies House", "HMRC deadline",
  "Lursoft", "VID", "SIA", "Latvian tax", "UK filing deadline", "cross-border tax",
  "invoice in EUR or GBP", "permanent establishment", "double tax UK Latvia".
---

# uk-latvia-context

Reference pack for UK and Latvian administrative questions. Not a full tax
adviser — a cheatsheet that (a) covers the questions Linards actually asks,
(b) cites primary sources so he can verify, (c) flags when the answer needs
a real accountant / solicitor.

## When to use

- Linards has a Companies House / HMRC / Lursoft / VID question and wants a
  pointer before going to his accountant.
- A retainer conversation is about to touch cross-border invoicing (GBP vs EUR,
  VAT reverse-charge, permanent-establishment risk).
- Writing a client-log or retainer entry that references filing deadlines.

## How this skill answers

Every answer cites the section of the reference pack it came from and includes a
`confidence:` line:

- `confidence: reference` — answer is directly from the reference pack section cited.
- `confidence: inferred` — answer combines reference facts with situational
  reasoning; verify with a human advisor before acting.
- `confidence: needs advisor` — the question touches law / tax that Fredis is
  not authoritative on. Surface the relevant-looking section, then point at
  Linards's accountant or solicitor.

When the question touches **specific numbers** (VAT thresholds, filing deadlines,
rates), always append: *"Verify current value on gov.uk / vid.gov.lv — these
figures change; the reference pack can go stale."*

## Growth model — seed structure, fill on demand

The reference files (`uk-admin.md`, `latvia-admin.md`, `cross-border.md`) are
seeded with section headers for the likely topics but mostly empty bodies.
**This is deliberate.**

- Authoring all three upfront with 2026 numbers risks stale data the day Linards
  first reads it — VAT thresholds, Companies House filing rules, and VID
  procedures change every 1–2 years.
- Filling entries only when Linards actually asks means the pack accumulates
  *questions he's had*, not *questions he might have*. Higher retrieval signal
  over time.

When Linards asks a question whose topic matches an empty section:

1. Answer using web-research or `integrations` skill (read-only) to pull current
   primary-source data.
2. Add the Q&A to the appropriate reference file under the existing section
   header:
   ```markdown
   ### <Short question>

   <Answer — 2–6 sentences. Cite the primary source URL.>

   *Asked: 2026-04-23. Source: gov.uk/vat/thresholds. Verify before acting.*
   ```
3. Flag the entry with the date asked so Linards can see which entries are
   fresh vs a year old.

When Linards asks a question that doesn't match any existing section header,
add a new header and fill the first Q&A under it.

## Maintenance cadence

Annual review — re-verify the top 5 most-cited entries against primary sources.
Set an anchor of **April 2027** for the first review (one year from the pack's
creation on 2026-04-23). Add a reminder to `launch-governance/bet-review`
month-anchored gates or surface it via heartbeat in April 2027.

## References

| File | Contains |
|---|---|
| `references/uk-admin.md` | Companies House, HMRC, VAT, PAYE, director duties |
| `references/latvia-admin.md` | Lursoft, VID, VAT, SIA, EDS portal, individual trader rules |
| `references/cross-border.md` | UK–Latvia double-tax treaty, permanent establishment, invoicing currency |

## Boundary — what this skill does not do

- No API calls to Companies House / HMRC / Lursoft / VID. The skill is purely a
  reference pack; real-time lookups are out of scope.
- No writes to the vault outside its own references folder. Never touches
  retainer files, MEMORY.md, or drafts.
- No financial / legal advice. Every answer is information, not a decision.
  Where law or tax is involved, the answer routes to "needs advisor".
- No reliance on memory alone when answering specific-number questions. If a
  filing deadline or threshold hasn't been verified within the last 12 months,
  the answer says so and points Linards at the current primary source.
