# Minimum Lovable Product

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Cut scope to the single slice that proves core value. Force the "what's the smallest thing the segment would love?" question before writing code or burning a weekend. Output: one-page MLP brief + weeknight-slice plan + pre-mortem + gate YAML.

## Frameworks applied (sources for follow-up authoring)

- **Minimum Lovable Product** (Henrik Kniberg, 2016) — the skateboard-bike-car illustration; every stage lovable in its own right.
- **Kano model** (Noriaki Kano, 1984) — must-haves / performance / delighters; shows what not to bother with in MVP.
- **User Story Mapping** (Jeff Patton, 2014) — spine of user activities; slice vertically, not feature-by-feature.
- **Pre-mortem** (Gary Klein, HBR 2007) — "it's six months from now and this failed — why?"

## Lane-specific lovable definitions

Pre-seeded from portfolio plan + `_shared/lanes.md`:

- **Email Hub** — lovable = a MarTech dev opens one campaign and the tool saves > 2 h on the next one. (Runs only after `ip-overhang-guard` clears the lane.)
- **VTV** — lovable = a transport planner watches the demo and says "I can show this to my director tomorrow." (B2G credibility test, not feature test.)
- **Cab** — lovable = riders join a waitlist AND a match-simulation demo produces a plausible ride in < 10 s.

## Structure (to be filled)

1. **Lane pre-load** — load `_shared/lanes.md`.
2. **Lovable Promise** — one sentence the target user would believe.
3. **Kano classification of candidate features** — must-have / performance / delighter / don't-bother.
4. **Weeknight-slice plan** — 4–8 hour build budget; what ships this week.
5. **Pre-mortem** — 3–5 failure modes + pre-commit mitigation.
6. **Atis £1k gate** — would Atis bet on this MLP brief?
7. **Pre-committed kill gate** — e.g., "MLP demo shown to 5 target users by <date>, < 2 say 'when can I use this?' → kill or reframe" → writes `Fredis/Memory/gates/<lane>-mlp-reception.yaml`.
8. **Hand-off** — "Next: `product-shape/mvp-architect` for the stack brief."

## Ports / attribution

- No upstream port — de novo body synthesising primary-source canon above.
