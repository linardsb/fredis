---
name: product-shape
description: Shape a validated idea into a priced, positioned, stack-ready MVP — Van Westendorp + Gabor-Granger + Ramanujam monetisation (pricing-shaper), April Dunford + Geoffrey Moore positioning with one-tweet test (positioning-sharpener), Ries + Kniberg + Wardley build-vs-buy stack architecture (mvp-architect). Three pre-built lane canvases — B2G contract (VTV), B2C commission (Cab), SaaS (Email Hub gated on ip-overhang-guard). Use when user says "price this", "what should I charge", "willingness to pay", "Van Westendorp", "Gabor Granger", "position Cab/VTV/Email Hub", "who are we for", "Dunford", "Moore positioning template", "why us not them", "MVP architecture", "stack for X", "build vs buy", "Wardley", "first sprint".
---

# product-shape

TL;DR — runs after `idea-validation` clears. Takes a validated problem and shapes the product: price, position, stack. Three references cover each; outputs are durable artefacts (canvases, briefs) that feed into `launch-governance`.

## When to use

After `idea-validation/problem-validation` returns a painkiller verdict. Sequence inside `product-shape`:

1. **pricing-shaper** — willingness-to-pay conversation plan + canvas per revenue model.
2. **positioning-sharpener** — one-sentence + five-bullet Dunford.
3. **mvp-architect** — stack brief with build-vs-buy grid and first-commit checklist.

Outputs feed `launch-governance/launch-wedge` (first-10-users plan) and `launch-governance/metrics-gate` (kill criteria on revenue / pricing / usage).

## Shared primer

- **Lane registry** — load `_shared/lanes.md`. Each reference picks the lane-appropriate canvas (B2G / B2C / SaaS).
- **Atis £1k gate** — load `_shared/atis-test.md`. Every output ends with the gate.
- **Chris-Lori voice** — load `_shared/chris-lori-voice.md` for positioning drafts (forces evidence-first, kills "we empower X to unlock Y" fluff).
- **Draft path convention** — outputs to `Fredis/Memory/drafts/active/product-shape/<sub-skill>/`.

## Routing table

| Trigger | Reference |
|---|---|
| "price", "pricing", "Van Westendorp", "Gabor Granger", "willingness to pay", "charge", "pricing canvas" | `references/pricing-shaper.md` |
| "positioning", "who are we for", "Dunford", "Moore template", "why us not them", "one-sentence positioning" | `references/positioning-sharpener.md` |
| "MVP architecture", "stack", "build vs buy", "Wardley", "C4 diagram", "first sprint", "first-commit" | `references/mvp-architect.md` |

## Hand-off contract

- `pricing-shaper` → "Next: `positioning-sharpener` (you can't position what you can't price)".
- `positioning-sharpener` → "Next: `mvp-architect` — unique attributes drive architecture choices."
- `mvp-architect` → "Next: `engineering` (deep ADRs/C4) + `launch-governance/launch-wedge` (first 10 users)."

## Voice modes

Positioning defaults to Chris-Lori evidence-first voice. Other references stay SOUL-neutral. No persona voices in this bundle.

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/product-shape/<sub-skill>/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

**Hard refusal — Email Hub lane.** Refuse to produce product-specific outputs on the Email Hub lane until `ip-overhang-guard` output is resolved. `mvp-architect` in particular must invoke `ip-overhang-guard` at the top of any Email Hub stack brief.

## References

| File | Load when |
|---|---|
| `references/pricing-shaper.md` | Van Westendorp + Gabor-Granger + Ramanujam pricing; three lane canvases |
| `references/positioning-sharpener.md` | Dunford + Moore positioning; one-sentence + five-bullet output with Chris-Lori gate |
| `references/mvp-architect.md` | Ries + Kniberg + Wardley; three stack templates; build-vs-buy grid; first-commit checklist |

## Anti-patterns

- Pricing before problem-validation. Willingness-to-pay questions only produce signal once the segment has committed to *a* solution being worth solving.
- Positioning with "we help companies…" openers. Load `_shared/chris-lori-voice.md` and kill fluff.
- MVP architecture that leaps to microservices pre-revenue. First-commit checklist = monolith + Postgres + one deploy target until it's validated.
