# Decision Logger

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Two-layer decision journal with a DO_NOT_RESURFACE primitive. Layer 1 captures raw transcripts of deliberations; Layer 2 captures founder-approved decisions with review dates. Prevents revisiting decisions that have already been made — "let's talk about pricing again" gets caught against the prior pricing decision.

## Frameworks applied (sources for follow-up authoring)

- **Annie Duke decision-journal discipline** (*Thinking in Bets*, 2018) — capture state-at-decision-time to separate decision quality from outcome quality.
- **Reversible / one-way-door framing** (Bezos) — mark decisions accordingly; irreversible ones get heavier review.
- **DO_NOT_RESURFACE primitive** — decisions tagged `status: locked` don't resurface on the same trigger for N days unless new evidence is explicitly logged.
- **Port basis:** `alirezarezvani/claude-skills/c-level-advisor/decision-logger/` (MIT) — includes `templates/decision-entry.md` which moves to `assets/decision-entry-template.md`.

## Two-layer structure

### Layer 1 — raw transcripts
`Fredis/Memory/daily/*.md` already captures raw reasoning. Decision-logger references these but doesn't duplicate.

### Layer 2 — founder-approved decisions
`Fredis/Memory/decisions/YYYY-MM-DD-<slug>.md` (new directory — scaffolded on first invocation). Each entry:

```markdown
---
status: locked | provisional | retired
reversibility: one-way | two-way
review_date: YYYY-MM-DD
do_not_resurface_until: YYYY-MM-DD (optional)
lane: <lane or na>
---

## Decision
<one sentence>

## Context (what was happening)
...

## Alternatives considered
...

## Expected outcome (falsifiable)
...

## Evidence that would cause reconsideration
...

## Linked gate YAMLs
- ...
```

## DO_NOT_RESURFACE rule

When a chat / heartbeat invocation surfaces a topic matching a `status: locked` decision with `do_not_resurface_until` in the future:
- Don't re-run the deliberation.
- Echo the prior decision with a link.
- Only proceed if new evidence is explicitly flagged — and if so, add evidence to the decision file before re-deliberating.

## Cross-linking

- `metrics-gate` — every gate YAML references the decision entry that committed it.
- `bet-review` — monthly review references the decision entries it's evaluating against.
- `ip-overhang-guard` — employer-IP decisions land as one-way-door entries (Email Hub IP resolved 2026-06-16; the guard stays available for other lanes).

## Structure (to be filled)

1. **Gather context** — what decision is being made, what's driving the ask.
2. **Check existing decisions** — `memory_search.py --mode hybrid "<topic>"` for DO_NOT_RESURFACE matches.
3. **If existing match is active** — echo, don't re-deliberate.
4. **Draft entry** — schema above.
5. **Atis £1k gate** — would Atis bet on this decision (given the evidence + alternatives considered)?
6. **Link to gate YAMLs and bet-review cadence.**

## Ports / attribution

- Port spine + `decision-entry.md` template: MIT, ported from `alirezarezvani/claude-skills/c-level-advisor/decision-logger/`.
- DO_NOT_RESURFACE primitive + Fredis cross-linking: de novo.
