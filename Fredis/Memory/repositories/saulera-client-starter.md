---
title: saulera-client-starter
type: entity
category: repository
github: linardsb/saulera-client-starter
visibility: private
default_branch: master
local_path: "/Users/Berzins/Desktop/saulera-client-starter"
archon_enabled: false
tags: [repository, design-system, static-site, css, no-build, productisation-lane]
related:
  - "[[REPOSITORIES]]"
created: 2026-06-30
updated: 2026-06-30
---

# saulera-client-starter (codebase)

A client-agnostic design system for vanilla static marketing sites: one brand-agnostic `base/` + a thin per-client pack. No build step, no framework — CSS custom properties + class-based CSS only. Re-skinning a client = swapping one folder. **Client-site productisation lane P4b.**

## Identity

- **Stack:** Vanilla static — `base/` (semantic token contract + component-catalog modules), `client/` (per-client packs; ships `client/saulera/` as client-zero), `studio/`, `skill/`. No framework, no build. Packaged as the `saulera-design` skill.
- **Purpose:** Spin up a client marketing site by swapping the per-client folder; the base never changes between clients. Lane toward productised client sites.

## Archon Configuration

- **Archon-enabled:** no — no `.archon/` directory.
- **Lane gate:** P4b (not yet green) → **not in Active Pages**; coding stays in-session / advisor-draft for now.
- **Default workflows that will fit when the lane opens:** feature-development (new component modules), issue-fix, PR-review. Dispatch mechanics: `integrations` skill + `query.py workflow` (P2 — not built).

## Workflow Preferences

- **Default branch is `master`, not `main`.** Any dispatch / base-branch override must target `master` here — easy to get wrong, since every other lane repo is `main`.
- **Private repo.**
- **Never edit `base/` to re-skin a client** — re-skinning lives entirely in `client/<name>/`. The base is the contract.
- **Advisor mode:** any dispatch yields a draft PR — never auto-merge or push.

## Dispatch History

_Reflection appends date-prefixed bullets here when daily logs reference dispatches against this repo._

- (2026-06-30) Page created.

## Recent Activity

- Seeded ahead of lane activity (0 distinct daily-log mentions of the full slug as of 2026-06-30). This is the designated P4b lane repo, so the page exists before the lane opens; reflection will fill this in as client-site work begins.

## Related

Ships client-zero for the `saulera` marketing site (separate repo, not yet a tracked page). Index: [[REPOSITORIES]].
