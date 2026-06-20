# Metrics Gate

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.
>
> **Only launch-governance reference with live-code integration.** Writes YAML gates; heartbeat reads them each tick.

## Purpose

Write pre-committed kill criteria as YAML files that the heartbeat evaluates. Protects against zombie-product drift by forcing the "if X by Y, kill" commitment *before* the work begins, and surfacing breaches deterministically rather than relying on Linards to remember the deadline.

## Frameworks applied (sources for follow-up authoring)

- **Annie Duke, *Thinking in Bets* + *Quit*** (2018, 2022) — states-and-dates framing, kill triggers as bets.
- **Gary Klein pre-mortem** (HBR 2007) — failure modes as candidate gates.
- **Dave McClure AARRR** (2007) — acquisition / activation / retention / referral / revenue as gate-candidate metric dimensions.
- **SaaS metrics three-tier status flags** (ported from `alirezarezvani/claude-skills/finance/saas-metrics-coach/`) — green / amber / red benchmarks per segment.
- **Charlie Munger inversion** — gate framing as "what would make me regret continuing?".

## Gate schema

Canonical schema at `.claude/scripts/gate_schema.py`:

```yaml
lane: vtv                      # one of email-hub / vtv / cab / other
metric: signed_loi             # short slug
threshold: "one signed LOI from any LV operator"
deadline: 2026-10-20           # ISO date
observable_source: 'gmail_search:"subject:LOI"'   # how to verify
pre_committed_at: 2026-04-20
status: open                   # open | breached | closed
rationale: "VTV month-6 kill trigger per portfolio plan §9"
invalidator: "a signed LOI invalidates the gate (lane continues)"
```

Files live in `Fredis/Memory/gates/<lane>-<metric>.yaml`.

## Heartbeat integration

Live code in `.claude/scripts/gate_loader.py`:

- `load_gates(gates_dir)` — reads all `*.yaml`, skips invalid with WARNING log.
- `evaluate_gates(gates, today=None)` — returns `GateBreach` for every open gate whose deadline has passed.
- `render_breach_draft(breach, template)` — substitutes fields into `.claude/scripts/templates/gate_breach.md.tmpl`.

`heartbeat.py → surface_gate_breaches()` is called each tick. Breach drafts land at `Fredis/Memory/drafts/active/launch-governance/metrics-gate/<YYYY-MM-DD>-<lane>-<metric>-breach.md`. Idempotent — already-surfaced breaches skip.

## Structure (to be filled)

1. **Lane pre-load** — `_shared/lanes.md`.
2. **Pre-mortem** — 3–5 failure modes per bet.
3. **Candidate metric dimensions** — AARRR + SaaS three-tier + lane-specific.
4. **Gate draft** — one YAML per candidate kill trigger; Linards reviews before committing.
5. **Rationalisation-proof check** — heartbeat flags gate edits within 7 days of deadline as "late-stage rationalisation" (see `bet-review` for the counter-pattern).
6. **Integration with `business-cycle-analyst`** — macro-regime annotation: is this lane's metric tailwind / headwind right now?
7. **Atis £1k gate** — would Atis pre-commit to this kill trigger?
8. **Hand-off** — write the gate file; heartbeat takes over.

## Portfolio-seeded gates

Per portfolio plan §9:

- `email-hub-first-revenue.yaml` — first paying customer / signed commitment by the committed date → paused if breached (IP resolved 2026-06-16; kill criteria are revenue-based, not IP).
- `cab-vtv-traction.yaml` — month 4 VTV B2G conversations → paused if breached.
- `vtv-loi.yaml` — month 6 signed LOI or paid pilot → pivot or pause if breached.

These are the canonical starter gates; `metrics-gate` drafts them on first invocation per lane if they don't already exist.

## Ports / attribution

- SaaS metrics three-tier + benchmarks: MIT, ported from `alirezarezvani/claude-skills/finance/saas-metrics-coach/`.
- States-and-dates + pre-mortem + AARRR framework composition: de novo.
