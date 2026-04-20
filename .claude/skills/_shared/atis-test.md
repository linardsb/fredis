# Atis £1k Test — The Smoke Test

Before any `idea-validation`, `product-shape`, or `launch-governance` output leaves draft status,
run the Atis gate.

## The question

> Would Atis (Linards's cousin, engineer, no cheerleader) put **£1k of his own money** on this bet
> after reading the current draft? If **no** — what specifically would flip him to yes?

## Why Atis

- Cousin = cares about the outcome, not about being polite.
- Engineer = scans for weakness in the logic, not the prose.
- No cheerleader = no "great stuff mate" motivator bias.
- £1k = small enough to actually risk, large enough to force an honest read.

## How to apply

Every skill that emits a product-bet artefact — a market scan, a positioning statement, a pricing
canvas, a launch wedge, a metrics gate, a bet review verdict — writes an **Atis-gate block** at the
bottom of the draft:

```markdown
## Atis £1k gate

- **Verdict (Atis would bet £1k?):** yes / no / not yet
- **If no / not yet — what would flip him:**
  - [specific evidence or change needed]
  - [specific evidence or change needed]
- **What I'm NOT going to do about it yet (and why):**
  - [honest note on which flips are out of scope right now]
```

## Example invocations

- `idea-validation/minimum-lovable-product.md` — Atis-gate on the Lovable Promise sentence.
- `product-shape/pricing-shaper.md` — Atis-gate on the price-point + acquisition-cost math.
- `launch-governance/launch-wedge.md` — Atis-gate on the 10-named-humans table.
- `launch-governance/bet-review.md` — Atis-gate is the verdict itself (monthly).

## Anti-pattern

- Skipping the gate because the draft "feels right." The gate exists to catch drafts that feel right
  to the author and look thin to an engineer who'd lose real money on them.
- Writing the Atis-gate block for the skill. Fredis writes the first pass; Linards rewrites it in
  his own read of what Atis would actually say.
