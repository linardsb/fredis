# Pricing Shaper

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Shape a price point (or a contract structure) that matches willingness-to-pay evidence and the lane's revenue model. Output: pricing canvas (lane-specific) + conversation plan + red-team pass.

## Frameworks applied (sources for follow-up authoring)

- **Van Westendorp Price Sensitivity Meter** (Westendorp, 1976) — four-question survey producing acceptable price range.
- **Gabor-Granger** (Gabor & Granger, 1960s) — direct willingness-to-pay test with step-down / step-up anchoring.
- **Monetizing Innovation** (Madhavan Ramanujam, 2016) — willingness-to-pay conversations *before* build; value-first pricing; tiered design; willingness-to-pay segmentation.
- **Hermann Simon critique** — red-team pass ("is this cost-plus hiding as value-based?").
- **Pricing-page playbook** (ported from alirezarezvani SaaS pricing skill) — framing, anchoring, tier structure.

## Lane canvases (three revenue models)

### B2G contract (VTV)
- Pilot fee (fixed, ~3–6 months, covers integration cost).
- Success-based uplift (KPI-tied, e.g., route efficiency %).
- Production contract year 2 (multi-year, volume-tiered).
- Public-sector procurement constraints per LV Public Transport Act + EU Reg 1370/2007.

### B2C commission (Cab)
- Take-rate on each ride (competitive benchmark: Bolt 15-25%).
- Surge multiplier structure.
- Driver incentive mechanics (sign-on, hours, referrals).
- Rider acquisition unit-cost ceiling.

### SaaS (Email Hub, once IP-clear)
- Seat / tier / usage axis choice.
- Free → pro → scale → enterprise ladder.
- Usage-based addons.
- Annual-vs-monthly anchor.

## Structure (to be filled)

1. **Lane pre-load + canvas selection** — load `_shared/lanes.md`, pick canvas.
2. **Willingness-to-pay conversation plan** — who to ask, what to ask, what evidence counts.
3. **Van Westendorp + Gabor-Granger micro-survey** — 4–6 question block to embed in next customer interviews.
4. **Competitor price teardown** — named comparables, their tiers, their positioning.
5. **Canvas fill** — numbers, anchors, structure.
6. **Red-team pass** — Simon critique + cost-plus check + "is this durable under competitor response?".
7. **Atis £1k gate** — would Atis put £1k on this customer saying yes at this price?
8. **Memory recall** — `memory_search.py --mode hybrid "pricing <lane>"` for prior pricing notes.
9. **Pre-committed gate** — revenue check at defined date (e.g., "VTV — by <date>, one signed pilot fee ≥ €X" → `Fredis/Memory/gates/<lane>-pricing-signal.yaml`).

## Ports / attribution

- SaaS base (pricing-models.md, pricing-page-playbook.md): MIT, ported from `alirezarezvani/claude-skills/marketing-skill/pricing-strategy/`.
- B2G contract + B2C commission canvases: de novo.
