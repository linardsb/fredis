# Draft-Path Convention

Every Fredis skill writes to `Fredis/Memory/drafts/active/`. Never direct to `drafts/sent/`. Never
to an external system (Gmail, Slack, Monday, GitHub). Linards reviews and sends manually.

## Path shape

### Single-purpose skill
```
Fredis/Memory/drafts/active/<skill-name>/YYYY-MM-DD-<slug>.md
```

Example — `ip-overhang-guard` writing the Merkle letter draft:
```
Fredis/Memory/drafts/active/ip-overhang-guard/2026-04-20-merkle-ip-letter.md
```

### Merged bundle skill (a skill containing multiple sub-skills)
```
Fredis/Memory/drafts/active/<bundle-name>/<sub-skill>/YYYY-MM-DD-<slug>.md
```

Example — `launch-governance/metrics-gate` writing a breach draft for VTV:
```
Fredis/Memory/drafts/active/launch-governance/metrics-gate/2026-04-20-vtv-loi-breach.md
```

Example — `idea-validation/minimum-lovable-product` writing an MLP brief for Cab:
```
Fredis/Memory/drafts/active/idea-validation/minimum-lovable-product/2026-04-20-cab-mlp-brief.md
```

## Slug rules

- Kebab-case, lowercase, ASCII.
- 2–5 words — enough to disambiguate but scannable in `ls`.
- Include the lane name when the draft is lane-specific (`cab-*`, `vtv-*`, `email-hub-*`).
- Include the artefact type when the skill emits multiple types (`-brief`, `-letter`, `-canvas`, `-scan`).

## Front-matter

Every draft starts with:

```markdown
---
skill: <skill-or-bundle/sub-skill>
lane: <email-hub | vtv | cab | other | na>
created: YYYY-MM-DD
status: draft
---
```

`status: draft` is the default. Linards changes it to `sent` when he moves the file to
`drafts/sent/`, or `expired` when it stops being relevant.

## Review lifecycle

- `drafts/active/` — waiting for Linards review.
- `drafts/sent/` — Linards sent a version (manually); file moved here as the record.
- `drafts/expired/` — draft went stale or was rejected.

The heartbeat reads `drafts/active/` to flag inbox build-up. Keeping that folder tidy is part of
advisor-mode hygiene — stale drafts mean the inbox is a pile.

## Capture-mode exceptions

A narrow set of skills writes directly to a topical folder rather than `drafts/active/`. These are
**capture-mode** skills — their output is not a send-candidate awaiting review, so routing through
`drafts/active/` would add a pointless manual-move step and bury the files under a retrieval prefix
that means "unsent reply drafts".

| Skill | Writes to | Why |
|---|---|---|
| `meeting-notes` | `Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md` | Meeting captures never send. Retrieval via `--path-prefix meetings/`. |
| `client-log` | `Fredis/Memory/retainers/<client-slug>.md` | Permanent client record, appended. Retrieval via `--path-prefix retainers/`. |

Capture-mode skills MUST document this exception explicitly in their own SKILL.md under a §Path
heading. New capture-mode skills require this file's table to be updated at the same time.

`draft-reply` is NOT a capture-mode exception — it follows the standard `drafts/active/draft-reply/`
path because its output is a send-candidate, even though `heartbeat.py:1086` reconciles the state
field automatically on send. The automatic reconciler is the reason `draft-reply` uses
`status: active` instead of the default `status: draft` — see its SKILL.md for the full rationale.

## Grounding discipline (lane-chain handoffs)

The lane chain runs `idea-validation → product-shape → launch-governance` (with `engineering`
branching off `product-shape/mvp-architect`). Each upstream skill writes its artefact to
`drafts/active/<skill>/...` and ends with a forward hand-off note naming the next skill — see each
skill's "Hand-off contract". This is the *backward* half of that handoff: what the downstream skill
owes the artefact it builds on.

Before a downstream skill runs, it:

1. **Names its inputs.** States which upstream artefact(s) it is building on, by path — e.g.
   `product-shape/mvp-architect` reads the MLP brief at
   `Fredis/Memory/drafts/active/idea-validation/minimum-lovable-product/<date>-<lane>-mlp-brief.md`.
2. **Reads and cites them.** Facts carried forward — the validated problem, the painkiller verdict,
   the agreed price point — are cited back to the upstream draft as a vault-file source (`V1`) per
   [[citation-and-provenance]], so a number never appears downstream without its origin.
3. **STOPs if an input is missing.** If the named upstream artefact does not exist, the downstream
   skill does not invent it. It stops, says which artefact is missing and which skill produces it,
   and asks for that step first — it does not fabricate a validated problem or a price to keep going.

Worked example: `launch-governance/launch-wedge` depends on `idea-validation/problem-validation`'s
painkiller-commitment evidence (its anti-patterns already forbid launching a wedge on a vitamin).
Under this discipline that dependency is *explicit*: launch-wedge cites the problem-validation draft
as its input, and if no such draft exists it stops and asks for validation first rather than
assuming a painkiller.

This mirrors ArcKit's read-upstream-or-stop handoff without porting its recipe engine — a convention
the lane skills follow, not a new orchestrator. It pairs with [[citation-and-provenance]] (cite the
upstream artefact) and [[atis-test]] (the downstream bet must clear the £1k gate on grounded inputs,
not assumed ones).

## The never-send boundary

Never in any automated path:
- `slack.postMessage`, `slack send` without `--i-confirm-send`
- `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

See `Fredis/Memory/SOUL.md` for the full never-send rules. This file is the path convention; SOUL
is the policy.
