---
name: idea-validation
description: Ideate-to-validate chain for a product lane — Porter / STEEP / Dunford / Blue-Ocean market scan (market-landscape-scan), Mom Test + Running Lean + JTBD-switch problem interviews with commitment extraction (problem-validation), Kniberg MLP + Kano + Patton story mapping + Klein pre-mortem (minimum-lovable-product). Pre-seeds Email Hub / VTV / Cab lanes from _shared/lanes.md. Forces the Atis-£1k smoke test and explicit kill criteria before any shipping work. Use when user says "market scan", "competitive landscape", "who else is in X", "STEEP", "Porter", "Blue Ocean", "validate idea", "Mom Test", "customer interview", "is this a real problem", "painkiller vs vitamin", "jobs to be done", "JTBD", "MVP", "MLP", "minimum lovable", "smallest version", "scope down", "pre-mortem", or before opening a new lane.
---

# idea-validation

TL;DR — structured ideate-to-validate chain. Runs scan → interview → MLP in sequence. Every artefact ends with the Atis-£1k gate; every kill criterion writes a gate YAML that `launch-governance/metrics-gate` picks up.

## When to use

Start here whenever a new lane is on the table, or when an existing lane needs a discipline reset. The chain is sequential:

1. **market-landscape-scan** — who else is in this category, where the gap is.
2. **problem-validation** — is the problem painful enough to buy away, not just complain about.
3. **minimum-lovable-product** — what's the smallest thing that proves the core value.

Outputs feed into `product-shape` (pricing, positioning, architecture) and `launch-governance` (wedge, metrics-gate, bet-review).

## Shared primer

All three references share these disciplines — do not re-explain them in the references, just invoke:

- **Lane registry** — load `_shared/lanes.md`. Every output names its lane explicitly (email-hub / vtv / cab / other) or refuses to generate if the lane is ambiguous.
- **Atis £1k gate** — load `_shared/atis-test.md`. Every output ends with the gate block.
- **Draft path convention** — load `_shared/draft-path-convention.md`. Outputs land at `Fredis/Memory/drafts/active/idea-validation/<sub-skill>/YYYY-MM-DD-<slug>.md`.
- **Kill-criteria pre-commit** — every phase commits at least one gate YAML to `Fredis/Memory/gates/<lane>.yaml`. Heartbeat surfaces breaches.

## Routing table

| Trigger | Reference |
|---|---|
| "market scan", "competitive landscape", "who else is in", "STEEP", "Porter", "Blue Ocean", "TAM/SAM/SOM", "funding landscape" | `references/market-landscape-scan.md` |
| "Mom Test", "customer interview", "validate idea", "painkiller vs vitamin", "JTBD", "jobs to be done", "switch interview", "zombie lead" | `references/problem-validation.md` |
| "MVP", "MLP", "minimum lovable", "smallest version", "scope down", "story map", "pre-mortem", "weeknight slice" | `references/minimum-lovable-product.md` |

## Hand-off contract

When a reference completes, it writes a one-line hand-off note naming the next skill. Examples:
- `market-landscape-scan` → "Next: `problem-validation` on lane <X>."
- `problem-validation` (painkiller found) → "Next: `minimum-lovable-product` on lane <X>."
- `problem-validation` (vitamin, or no commitment) → "Kill. Write the decision in `launch-governance/decision-logger`."
- `minimum-lovable-product` → "Next: `product-shape/mvp-architect` for the stack brief."

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/idea-validation/<sub-skill>/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

**Hard refusal — Email Hub lane.** Refuse to produce product-specific outputs on the Email Hub lane until `ip-overhang-guard` has been invoked in the current or recent session and its output is resolved (clean-room rebuild committed, Merkle carve-out received, or explicit assignment). Surface a one-line refusal naming `ip-overhang-guard` as the blocker.

## References

| File | Load when |
|---|---|
| `references/market-landscape-scan.md` | Competitor matrix, STEEP-P calibration, funding landscape, gap identification |
| `references/problem-validation.md` | Customer-interview design, Mom Test + JTBD + Running Lean synthesis, painkiller-vs-vitamin classification |
| `references/minimum-lovable-product.md` | Single-sentence Lovable Promise, Kano prioritisation, weeknight-slice planning, pre-mortem |

## Anti-patterns

- Skipping a phase. "I'll do market scan after MLP" is how zombie lanes start.
- Generating a scan without pre-loading `_shared/lanes.md`. The lane-registry context is what makes Fredis's scan different from a generic one.
- Painkiller-vs-vitamin declared without commitment evidence. The Mom Test's escalation ladder (time / introduction / money) is the gate, not the author's read of the interview tone.
- Generating an MLP "just to get something out." The Lovable Promise is the constraint that kills bad MVPs before they ship.
