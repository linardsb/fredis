# Market Landscape Scan

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Given a product lane, produce a structured read of:
- **Category shape** — who's in it, at what stage, with what funding.
- **Gap hypothesis** — where an underserved segment / unmet job sits.
- **Regulatory + macro frame** — STEEP-P layer specific to the lane (VTV: EU Reg 1370/2007 + LV Public Transport Act; Cab: EU Mobility Package + LV Road Traffic Law).

Output: one draft at `Fredis/Memory/drafts/active/idea-validation/market-landscape-scan/YYYY-MM-DD-<lane>-scan.md` ending with the Atis-£1k gate + one pre-committed gate YAML for `Fredis/Memory/gates/<lane>.yaml`.

## Frameworks applied (sources for follow-up authoring)

- **Porter Five Forces** (Porter, *Competitive Strategy*, 1980) — competitive rivalry, new entrants, substitutes, buyer / supplier power.
- **STEEP (+P)** (Aguilar 1967; Political layer added) — social, technological, economic, environmental, political / regulatory.
- **Blue Ocean Strategy** (Kim & Mauborgne 2005) — four-actions grid (eliminate / reduce / raise / create).
- **April Dunford positioning inputs** (*Obviously Awesome*, 2019) — alternative solutions + unique attributes + true value + the best-fit customer.
- **Geoffrey Moore category design** (*Crossing the Chasm*, 1991) — mainstream vs early-market dynamics.
- **Competitive teardown** — 12-dimension comparison matrix (ported from `alirezarezvani/claude-skills/product-team/competitive-teardown/`).
- **2×2 Threat Matrix + 8 tracking dimensions** (ported from `c-level-advisor/competitive-intel/`).

## Structure (to be filled)

1. **Lane context pre-load** — load `_shared/lanes.md`; name the lane + category + current stage.
2. **Competitive teardown matrix** — 12 dimensions × 5–8 named competitors.
3. **2×2 Threat Matrix** — imminence × severity; produces the named watchlist.
4. **Five Forces read** — 1–2 sentences per force.
5. **STEEP-P calibration** — lane-specific regulatory layer in particular.
6. **Blue-Ocean four-actions** — where can this lane differentiate structurally.
7. **Gap hypothesis** — one paragraph, evidence-first.
8. **Atis £1k gate** — would Atis bet on this gap read?
9. **Pre-committed gate** — writes the first kill criterion for the lane (e.g., "if no named competitor moves in 6 weeks, thesis weakens") to `Fredis/Memory/gates/<lane>-competitive.yaml`.
10. **Hand-off** — "Next: `problem-validation` on lane <X>."

## Ports / attribution

- Competitive teardown spine + 2×2 Threat Matrix + Dunford input excerpts: MIT-licensed, ported from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) (`product-team/competitive-teardown/`, `c-level-advisor/competitive-intel/`, `marketing-skill/marketing-strategy-pmm/references/positioning-frameworks.md`). Fredis adaptation: lane-aware pre-seed, Atis gate, advisor-mode.
