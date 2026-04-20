---
name: org-design
description: Organisational design — strategy cascade from boardroom to IC, OKR alignment, silo detection, orphan-goal surfacing (strategic alignment) plus operating-system selection (EOS / Scaling Up / OKR-native / hybrid), meeting pulse (L10), accountability charts, scorecards, 90-day rocks (company OS). Use when user says "teams pulling in different directions", "OKRs don't connect", "strategy cascade", "silo", "conflicting OKRs", "EOS", "Scaling Up", "operating system", "L10 meetings", "rocks", "accountability chart", "quarterly planning", "meeting rhythms".
---

# org-design

TL;DR — how the organisation runs and how strategy flows through it. For solo/pre-revenue, this is design-for-later; for multi-person teams, this is active. Two references: strategy cascade (OKRs and alignment) + operating-system shape (meeting rhythms, accountability).

## Routing table

| Trigger | Reference |
|---|---|
| "strategy cascade", "orphan goals", "silo", "conflicting OKRs", "teams pulling apart", "local optimisation", "realignment", "strategy communication gap" | `references/strategic-alignment.md` |
| "EOS", "Scaling Up", "operating system", "L10 meetings", "rocks", "scorecard", "accountability chart", "quarterly planning", "meeting pulse" | `references/company-os.md` |

## Shared assets

- `_shared/lanes.md` — lane-level goals feed the cascade when OKRs apply to specific product lanes.
- `_shared/draft-path-convention.md`

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/org-design/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

## References

| File | Load when |
|---|---|
| `references/strategic-alignment.md` | Cascade mapping, orphan-goal detection, communication-gap analysis, realignment protocols |
| `references/company-os.md` | Selecting an operating framework, designing meeting rhythms, building accountability systems |

## Anti-patterns

- Full EOS/Scaling-Up rollout on a solo founder. Save operating-system selection for post-first-hire; until then, just a scorecard and weekly review suffices.
- Cascading OKRs from a made-up company goal. Cascade only when the top goal is real and revenue-linked.
