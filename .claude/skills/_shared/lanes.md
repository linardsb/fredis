# Lane Registry — Email Hub / VTV / Cab

Single source of truth for the three product lanes Fredis's workflow-specialist skills operate on.
Skills under `idea-validation/`, `product-shape/`, and `launch-governance/` load this file to seed
lane-specific context.

Source: `docs/product-portfolio-plan.md` §5 + §9, `Fredis/Memory/MEMORY.md` §Key Decisions + §Active Projects + J5 lessons, `Fredis/Memory/USER.md`.

---

## Lane 1 — Email Hub

- **Category:** B2B MarTech / SaaS (commercial model still TBD — SaaS vs one-off-sale)
- **Market:** UK + EU agencies, ESPs, CMSs; Merkle/Dentsu-adjacent mid-market as warm segment
- **Stage:** MVP / pitching (paused)
- **Warm-network contacts:** Tim Jackson (Walking Ventures, 2018 context), Gavin Hughes (Ometria — conflict node, keep warm, keep boundary clean)
- **Sensitive segment / conflict:** Ometria (email-tech peer) — never source recent internal details for pitches
- **IP-gate status (BLOCKING):** UK CDPA 1988 s.11(2) + Patents Act 1977 s.39 overhang. Built outside
  Merkle hours but scope + department-head instruction test likely failed. No product-specific work
  until `ip-overhang-guard` output is resolved (Merkle written carve-out, clean-room rebuild, or
  explicit assignment).
- **Kill trigger:** no IP answer from Merkle by end of month 2 → paused indefinitely (agreed 2026-04-19).
- **Skill hand-off rule:** every `idea-validation`, `product-shape`, `launch-governance` invocation on
  Email Hub MUST call `ip-overhang-guard` first. Refuse to emit product artefacts while IP-gate open.

## Lane 2 — VTV (B2G public-transport optimisation, Latvia)

- **Category:** B2G (public-sector contract)
- **Market:** Riga municipality + LV transport operators (Rīgas Satiksme + regional); EU transport-innovation funding as secondary
- **Stage:** MVP / inbound LPV warm interest (**ships first**)
- **Warm-network contacts:** Šlesers (ex-Transport Minister), Krištopans, wider LPV network; Atis Vīķis (cousin, LV technical partner), Juris Ņefedovs (LV partner)
- **Distribution caveat:** LPV channel is an accelerator, not a foundation. Must work without LPV influence.
- **Regulatory layer:** EU Regulation 1370/2007 (public passenger transport services), LV Public Transport Act; procurement rules apply.
- **Sales cycle:** 6–18 months realistic for B2G.
- **Credibility gap flagged:** VTV ROI claim (€2.4–4.4M) needs one transit-CFO in the room before public re-use. Founder-built math reads optimistic without third-party stamp.
- **Kill trigger:** no signed LOI or paid pilot discussion by end of month 6 → pivot or pause.

## Lane 3 — Cab (B2C ride-hailing)

- **Category:** B2C marketplace (two-sided — drivers + riders)
- **Market:** Latvia first (Bolt-replacement angle), potentially broader EU
- **Stage:** concept / **shares VTV codebase** (sequenced after VTV traction)
- **Warm-network contacts:** Atis Vīķis + Juris Ņefedovs (shared with VTV — same LV partners)
- **Regulatory layer:** EU Mobility Package (VHC/taxi directives), LV Road Traffic Law licensing, local municipal licensing.
- **Structural difficulty:** two-sided marketplace cold-start; capital-intensive rider + driver acquisition; Bolt has ~decade head start.
- **Distribution dependency:** rides on VTV's operator + government relationships. Parallel push only if a distinct Cab partner is pulling separately.
- **Kill trigger:** VTV has no real B2G conversations by end of month 4 → Cab paused (no distribution base).

---

## Cross-lane rules

- **VTV first, Cab second, Email Hub gated on IP** — sequencing locked 2026-04-19 (MEMORY.md).
- **Paused lanes are paused, not backlogged** — UGOKI, GERBONI, agri×AI, robotics, mycelium, 3d-printing are out of scope for `idea-validation` / `product-shape` / `launch-governance` invocations until a paid-user signal unlocks one.
- **UK + LV dual-identity positioning is the moat** — MarTech veteran + Latvian-native + AI-agentic build. Skills should surface this where applicable.

---

## How to use this file

- `idea-validation/market-landscape-scan.md` — pre-populates lane-starter competitor matrices from the categories above.
- `product-shape/pricing-shaper.md` — routes to the correct canvas: B2G contract (VTV), B2C commission (Cab), SaaS (Email Hub).
- `product-shape/positioning-sharpener.md` — loads the weak-starting-position list for each lane.
- `product-shape/mvp-architect.md` — loads the pre-built stack template for the lane's category.
- `launch-governance/launch-wedge.md` — seeds Bullseye 19-channel starter per lane.
- `launch-governance/metrics-gate.md` — seeds kill-trigger YAML per lane.
- `launch-governance/bet-review.md` — monthly review loads all three lanes, flags zombie-status on "continue" without new evidence for 3 months.

If a lane's data above is stale, update this file — not the individual skill bodies.
