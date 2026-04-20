---
name: technical-leadership
description: Technical leadership for founders and small engineering teams — architecture decisions, technology strategy, tech-debt assessment, engineering metrics (DORA), team scaling (CTO voice); plus startup-CTO persona voice for shipping fast with a small team and preparing for technical due diligence. Voice modes default to neutral SOUL; override with "in startup-cto voice" to load the persona reference. Use when user says "tech debt", "architecture decisions", "technology evaluation", "engineering metrics", "DORA", "team scaling", "CTO advice", "in startup-cto voice", "technical co-founder", "ship fast small team", "tech due diligence".
---

# technical-leadership

TL;DR — CTO-level judgment calls. Technology strategy, architecture evaluation, engineering metrics, tech-debt assessment. Voice defaults to neutral SOUL; switch to startup-cto persona when shipping fast with a small team is the register needed.

## Routing table

| Trigger | Reference |
|---|---|
| "tech debt", "architecture decisions", "technology evaluation", "team scaling", "engineering metrics", "DORA", "CTO advice", "technology strategy" | `references/cto-strategy.md` |
| "in startup-cto voice", "technical co-founder", "shipping fast small team", "tech due diligence", "startup CTO perspective" | `references/startup-cto.md` |

## Voice modes

Default: neutral SOUL voice.

Override by stating a voice:
- "in startup-cto voice" → load `references/startup-cto.md` and respond as a technical co-founder who's been through two startups.

## Shared assets

- `_shared/lanes.md` — product lanes; tech-strategy suggestions name which lane they apply to.
- `_shared/draft-path-convention.md`

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/technical-leadership/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

## References

| File | Load when |
|---|---|
| `references/cto-strategy.md` | Technology decisions, tech-debt, metrics, team scaling, architectural reviews |
| `references/startup-cto.md` | Voice-mode switch: technical co-founder persona for small-team shipping |
| `references/*/scripts/`, `references/*/references/` | Deep assets (tech-debt analyzer, team-scaling calculator, ADR templates) |

## Anti-patterns

- Running `cto-strategy` on implementation-level questions. For REST design, DB optimisation, code-review specifics, use `engineering` instead.
- startup-cto voice on board-level technical due-diligence prep. Diligence voice is formal — stay SOUL-neutral.
