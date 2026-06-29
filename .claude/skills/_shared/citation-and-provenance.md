# Citation and Provenance Convention

Advisor-mode means Linards *acts* on drafts — sends the email, files the bid, makes the call. So
"where did this number come from?" and "what produced this draft?" must be answerable before he
acts. This file is the convention that makes both answerable. It is dependency-free: a writing
discipline plus an optional helper, not a validator to install.

Two mechanisms, used together:

1. **Inline citations + a Source Register** — trace each *claim* in the body back to the source it
   came from.
2. **A provenance block** — record how the *draft itself* was produced (skill, model, inputs, when).

Borrowed in principle from [tractorjuice/arc-kit](https://github.com/tractorjuice/arc-kit)'s
citation system and provenance stamp, stripped to what a single-user advisor actually needs.

---

## Source IDs

Give every source a short ID: a fixed channel prefix plus an index. Fredis's real sources:

| Prefix | Source channel | Record as the origin |
|--------|----------------|----------------------|
| `GM` | Gmail | thread/message id + subject (or the `query.py gmail` command) |
| `SL` | Slack | channel + message timestamp (or the `query.py slack` command) |
| `WEB` | Web research (WebFetch / `deep-research`) | the full URL fetched |
| `GH` | GitHub | repo + PR/issue number (or the `query.py github` command) |
| `HS` | HubSpot | object type + id (contact / deal / ticket) |
| `V` | Vault file | the vault-relative path |
| `GS` / `GD` / `DR` / `CAL` | Google Sheets / Docs / Drive / Calendar | object id or title (+ tab / range) |

Index in order of first use: `GM1`, `GM2`, `WEB1`, `V1`. **One ID per unique source** — re-reading
the same thread does not earn a second ID. WebSearch that was never fetched is exploratory and is
not a citable source; cite a URL only once it has actually been fetched.

---

## Inline citation markers

Format: `[<SourceID>-C<N>]` — the source ID, then `C` for citation, then a number sequential **per
source** from 1. So a draft reads `[GM1-C1]`, `[GM1-C2]`, `[WEB1-C1]`, `[V1-C1]`.

Place the marker **immediately after the specific claim** it supports — not grouped at the end of a
paragraph. Attach it to the figure, quote, name, date, or finding that came from the source.

```text
Tim Jackson confirmed the pilot can start in Q3 [GM1-C1], at the £4k/month figure he quoted last
year [GM1-C2]. Innovate UK Smart Grants close on 24 September [WEB1-C1].
```

---

## Source Register

One table near the foot of the draft listing every source consulted, cited or not.

| Source ID | Origin | Retrieved | Description |
|-----------|--------|-----------|-------------|
| `GM1` | thread `18f2a…`, subject "Re: Email Hub pilot" | 2026-06-29 | Tim Jackson reply confirming Q3 + £4k/mo |
| `WEB1` | https://www.gov.uk/guidance/innovate-uk-smart-grants | 2026-06-29 | Smart Grants eligibility + deadline |
| `V1` | `Fredis/Memory/research/cab-market.md` | 2026-06-28 | Cab competitor pricing notes |

**Retrieved** is the date the source was pulled — and it matters here in a way it does not for
ArcKit. Gmail, Slack, HubSpot, and web pages are *live and mutable*: a thread read today may read
differently next week, and a vault file is the committed version at that date. The date is what lets
Linards re-check a claim against what the source says *now*.

If the draft asserts nothing from retrieved material — pure synthesis or opinion — omit the register
and let the provenance block's `Inputs` line say `none — synthesis only`.

---

## Provenance block

A `## Provenance` block as the final section of the draft, mirroring the `## Atis £1k gate` block
convention ([[atis-test]]). Four fields:

```markdown
## Provenance

- **Skill:** product-shape/pricing-shaper
- **Model:** claude-opus-4-8
- **Inputs:** GM1, WEB1, V1  (see Source Register)
- **Generated:** 2026-06-29
```

`Inputs` is the list of Source IDs the draft was built on — the one-glance answer to "what did this
read?". Optional extra lines where they matter: `**Voice:**` (neutral / solo-founder / startup-cto /
product-manager) and `**Effort:**`. Front-matter already carries `skill` and `created`; the block's
real value-add over front-matter is **model** and **inputs**.

A future helper may wrap the block in `<!-- provenance:start -->` / `<!-- provenance:end -->` markers
so it can be re-stamped idempotently — not required when the block is written by hand.

### Optional helper (not built)

A dependency-free `provenance.py` in `.claude/scripts/` could later (a) append or refresh the
provenance block and (b) check every inline `[ID-Cn]` marker resolves to a Source Register row. It
stays a convention until that earns its keep — Fredis does **not** port ArcKit's Node validator.

---

## When to cite

The grounding rule at the claim level:

- **Every external fact a reader could act on carries a marker** — figures, quotes, names, dates,
  prices, deadlines, claims about a person or market.
- **If you cannot attribute it, do not assert it as fact.** Either retrieve a source, flag it
  explicitly as Fredis's own inference, or drop it.
- **Synthesis and opinion are allowed and need no marker** — but they must read as Fredis's view, not
  as sourced fact. The Atis gate ([[atis-test]]) judges the bet; citations judge the facts under it.

The lane-chain version of this rule — read the upstream artefact, cite it, STOP if it is missing —
lives in [[draft-path-convention]] under "Grounding discipline".

---

## Where it goes in a draft

Foot of the draft, after the body, in this order: `## Atis £1k gate` (for bet artefacts, if
applicable) → `## Source Register` → `## Provenance`.

## Which skills use this

Research- and decision-grade drafts cite per this file: `deep-research`, `idea-validation`,
`product-shape`, `launch-governance`, `draft-reply`, `uk-latvia-context`, `security-engineering`.
Capture-mode skills ([[draft-path-convention]] — `meeting-notes`, `client-log`) record their own
source inline and do not need the full register.

**Related:** [[draft-path-convention]] · [[atis-test]] · [[lanes]] · plan `.agent/plans/arckit-borrows.md` (item C1).
