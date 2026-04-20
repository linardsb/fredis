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

## The never-send boundary

Never in any automated path:
- `slack.postMessage`, `slack send` without `--i-confirm-send`
- `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

See `Fredis/Memory/SOUL.md` for the full never-send rules. This file is the path convention; SOUL
is the policy.
