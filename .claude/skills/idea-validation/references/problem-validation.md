# Problem Validation

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Confirm (or kill) the assumption that the target segment has a problem painful enough to buy away. Output: interview design + synthesis + painkiller-vs-vitamin verdict + gate YAML.

## Frameworks applied (sources for follow-up authoring)

- **The Mom Test** (Rob Fitzpatrick, 2013) — anti-compliment interview discipline + commitment escalation ladder (time → introduction → money).
- **Running Lean** (Ash Maurya, 2022 3rd ed) — problem interview structure + lean canvas context.
- **Jobs-to-be-Done switch interview** (Moesta & Spiek, *Demand-Side Sales*, 2020) — struggling moment / first thought / push / pull / anxieties / habits.
- **Painkiller vs vitamin auto-classifier** — derived from Mom Test commitment-ladder outcomes.
- **Pre-mortem** (Gary Klein, HBR 2007) — what kills this thesis in six months?

## Shared tooling

- Reuse `.claude/skills/product-management/references/pm-toolkit/` → `customer_interview_analyzer.py` for synthesis automation (already ported).
- `_shared/atis-test.md` — Atis gate on the painkiller verdict.
- `_shared/lanes.md` — pre-seeded interview populations per lane:
  - Email Hub: UK/EU MarTech ops leads (ESPs, agencies, ESP adjacent)
  - VTV: LV transport operators, Riga municipality transport ops, Rīgas Satiksme
  - Cab: LV drivers + riders on the Bolt corridor

## Structure (to be filled)

1. **Target segment + recruiting plan** — named people per lane (5–10 conversations target).
2. **Interview guide** — Mom Test + JTBD switch questions, lane-specific language.
3. **Commitment ladder** — what commitment pattern converts the interview to validation (time / introduction / money).
4. **Synthesis template** — themes, painkiller evidence, vitamin evidence, anti-evidence.
5. **Painkiller-vs-vitamin verdict** — evidence-first.
6. **Atis £1k gate** — would Atis bet on this problem read?
7. **Pre-committed kill gate** — e.g., "if 10 interviews across 2 weeks and < 3 painkiller commitments, kill the lane" → writes `Fredis/Memory/gates/<lane>-problem-commitment.yaml`.
8. **Hand-off** — "Next: `minimum-lovable-product` (painkiller) | Decision log kill (vitamin)".

## Kill criteria (default pre-commits)

- 10 conversations in 2 weeks with no painkiller-level commitment → kill.
- 10 conversations in 2 weeks with strong vitamin signals but no painkiller → reframe (not kill), try adjacent segment once.

These get written as gate YAMLs so `launch-governance/metrics-gate` heartbeat surfaces a breach if the timebox elapses without evidence.

## Ports / attribution

- No upstream port — de novo body synthesising primary-source canon above plus reuse of existing `product-manager-toolkit/scripts/customer_interview_analyzer.py` (MIT, already in repo).
