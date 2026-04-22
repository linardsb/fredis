---
name: launch-governance
description: Launch wedge + kill gates + monthly portfolio review per lane. Bullseye + do-things-that-don't-scale + Four Fits wedge; states-and-dates + pre-mortem + AARRR + SaaS-metrics status flags for metrics gates; Thinking-in-Bets + pivot-or-persevere + Munger inversion monthly review; two-layer decision journal with DO_NOT_RESURFACE. Heartbeat reads Fredis/Memory/gates/*.yaml each tick and writes breach drafts to drafts/active/launch-governance/metrics-gate/. Use when user says "first 10 users", "launch plan", "which channel", "wedge", "GTM for X", "Bullseye", "do things that don't scale", "kill criteria", "metrics gate", "pre-mortem", "when do I shut this down", "states and dates", "monthly review", "portfolio check", "bet review", "continue or kill", "Thinking in Bets", "Munger invert", "pivot or persevere", "decision log", "DO_NOT_RESURFACE", "stale decision", "zombie check".
---

# launch-governance

TL;DR — the "decide, ship, review, kill" layer. Four references: launch-wedge (first 10 users), metrics-gate (pre-committed kill criteria wired into heartbeat), bet-review (monthly portfolio verdict), decision-logger (audit trail + DO_NOT_RESURFACE).

## When to use

Runs after `idea-validation` + `product-shape` clear. The launch-governance chain is the *only* skill that has live-code integration: `metrics-gate` writes YAML gates that `heartbeat.py` reads each tick and surfaces breaches to `Fredis/Memory/drafts/active/launch-governance/metrics-gate/`.

## Shared primer

- **Lane registry** — `_shared/lanes.md`. Every bet is a lane.
- **Atis £1k gate** — `_shared/atis-test.md`. Monthly review verdicts include an Atis gate.
- **Chris-Lori voice** — `_shared/chris-lori-voice.md`. Bet-review verdicts use Lori rhythm.
- **Draft path convention** — `_shared/draft-path-convention.md`.
- **Portfolio kill triggers (pre-seeded 2026-04-19):**
  - Email Hub — no IP answer by end of month 2 → paused.
  - Cab — no VTV B2G conversations by end of month 4 → paused.
  - VTV — no signed LOI or paid pilot discussion by end of month 6 → pivot or pause.

## Routing table

| Trigger | Reference |
|---|---|
| "first 10 users", "launch plan", "wedge", "GTM for X", "Bullseye", "channel selection", "do things that don't scale", "Four Fits" | `references/launch-wedge.md` |
| "kill criteria", "metrics gate", "pre-mortem", "states and dates", "AARRR", "zombie check", "SaaS metrics" | `references/metrics-gate.md` |
| "monthly review", "bet review", "continue or kill", "Thinking in Bets", "Munger invert", "pivot or persevere", "portfolio check" | `references/bet-review.md` |
| "decision log", "DO_NOT_RESURFACE", "stale decision", "reversible / irreversible decision" | `references/decision-logger.md` |

## Heartbeat wiring (live code, not just doc)

`metrics-gate` is the only launch-governance sub-skill with live-code integration:

- **Write path:** `metrics-gate` outputs a YAML file to `Fredis/Memory/gates/<lane>-<metric>.yaml` with the schema in `.claude/scripts/gate_schema.py`.
- **Read path:** `heartbeat.py` calls `gate_loader.evaluate_gates` every tick. Breached gates render the template at `.claude/scripts/templates/gate_breach.md.tmpl` and land at `Fredis/Memory/drafts/active/launch-governance/metrics-gate/<YYYY-MM-DD>-<lane>-<metric>-breach.md`.
- **Test:** `.claude/scripts/tests/test_gate_loader.py` covers parse, evaluate, render.

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/launch-governance/<sub-skill>/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

**Hard refusal — Email Hub launch-wedge:** refuse to emit a wedge plan for the Email Hub lane until `ip-overhang-guard` output is resolved. The kill trigger already captured in `metrics-gate` for Email Hub (month 2 IP gate) is the canonical lever here — surface breaches, don't design launches.

## References

| File | Load when |
|---|---|
| `references/launch-wedge.md` | First-10-users plan, channel selection, Bullseye, Four Fits |
| `references/metrics-gate.md` | Writing pre-committed kill criteria as YAML gates + three-tier SaaS status flags |
| `references/bet-review.md` | Monthly portfolio verdict per lane with Thinking-in-Bets discipline |
| `references/decision-logger.md` | Two-layer decision journal with DO_NOT_RESURFACE |

## Anti-patterns

- Extending a gate deadline silently. Heartbeat surfaces breaches — the gate YAML is a contract. If the gate should move, write a `decision-logger` entry; that's the audit trail.
- `launch-wedge` with personas instead of named humans. 10 named rows. Real names, real channels, real phone numbers / emails.
- `bet-review` verdict "continue" three months running with no new evidence. That's a zombie — `bet-review` auto-flags this via the DO_NOT_RESURFACE + prior-review-loading rules.
- Starting `launch-wedge` without `idea-validation/problem-validation` → painkiller painkiller commitment evidence. Launching a wedge on a vitamin is wasted credibility.
