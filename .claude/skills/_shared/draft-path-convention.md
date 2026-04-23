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

## The never-send boundary

Never in any automated path:
- `slack.postMessage`, `slack send` without `--i-confirm-send`
- `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

See `Fredis/Memory/SOUL.md` for the full never-send rules. This file is the path convention; SOUL
is the policy.
