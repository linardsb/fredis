---
name: product-management
description: Product management — OKR cascade, quarterly planning, competitive landscape, vision docs, team-scaling proposals; opportunity validation, assumption mapping, discovery sprints, problem-solution fit testing; RICE prioritisation, customer-interview analysis, PRD templates, discovery frameworks, GTM strategy; plus product-manager persona voice — ships outcomes not features, ruthless prioritisation, kills darlings when data says so. Voice modes default to neutral SOUL; override with "in product-manager voice" to load the persona reference. Use when user says "OKR", "quarterly plan", "competitive analysis", "product vision", "product discovery", "opportunity solution tree", "OST", "assumption mapping", "RICE", "customer interview analysis", "PRD", "GTM", "prioritise features", "roadmap", "in product-manager voice".
---

# product-management

TL;DR — product strategy (what to build), discovery (whether to build it), toolkit (how to specify it), and PM persona voice. Four layered references — start at the level of the question.

## Routing table

| Trigger | Reference |
|---|---|
| "OKR", "quarterly plan", "product vision", "product roadmap", "competitive analysis", "KPIs", "product-team scaling" | `references/product-strategy.md` |
| "product discovery", "opportunity solution tree", "OST", "assumption mapping", "discovery sprint", "problem-solution fit" | `references/discovery-ost.md` |
| "RICE", "customer interview analysis", "PRD", "feature prioritisation", "GTM strategy", "product requirements" | `references/pm-toolkit.md` |
| "in product-manager voice", "ship outcomes not features", "ruthless prioritisation", "kill darlings", "PM perspective" | `references/product-manager.md` |

## Voice modes

Default: neutral SOUL voice.

Override:
- "in product-manager voice" → load `references/product-manager.md` and respond from the PM persona (outcome-first, ruthless, data-driven).

## Hand-off

- Upstream ideation → `idea-validation` (market scan, problem validation, MLP).
- Upstream shape → `product-shape` (pricing, positioning, MVP architecture).
- Upstream launch → `launch-governance` (wedge, metrics-gate, bet-review).

`product-management` is for in-flight product work — the shape once a bet is committed. Early-stage "should we even build this?" belongs in `idea-validation`; late-stage "when do we kill it?" belongs in `launch-governance`.

## Shared assets

- `_shared/lanes.md` — product-management decisions name which lane they apply to.
- `_shared/atis-test.md` — roadmap prioritisation outputs get an Atis-gate.
- `_shared/draft-path-convention.md`

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/product-management/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

## References

| File | Load when |
|---|---|
| `references/product-strategy.md` | OKR cascade, quarterly planning, competitive landscape, vision |
| `references/discovery-ost.md` | Opportunity-solution trees, assumption mapping, discovery sprints |
| `references/pm-toolkit.md` | RICE, customer-interview analysis, PRD, GTM |
| `references/product-manager.md` | Voice-mode switch: PM persona |

## Anti-patterns

- Using `product-strategy` pre-revenue. OKRs without a top-line revenue reality cascade into fiction. For pre-revenue single-founder work, start at `idea-validation` or `product-shape`.
- PM voice on strategic / compliance / board decisions. PM persona is for product trade-offs, not organisational leadership.
