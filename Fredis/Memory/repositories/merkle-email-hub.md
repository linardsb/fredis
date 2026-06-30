---
title: merkle-email-hub
type: entity
category: repository
github: linardsb/merkle-email-hub
visibility: public
default_branch: main
local_path: "/Users/Berzins/Desktop/merkle-email-hub"
archon_enabled: false
tags: [repository, email-platform, fastapi, nextjs, postgres, python, productisation-lane]
related:
  - "[[REPOSITORIES]]"
created: 2026-06-30
updated: 2026-06-30
---

# merkle-email-hub (codebase)

Email Innovation Hub — a centralised email-development platform with AI agents. Build, preview, QA, and export HTML emails from one workspace; CMS-agnostic, security-first, GDPR-compliant. Linards's own IP. **Productisation lane P4.**

## Identity

- **Stack:** FastAPI (Python, `uv`) + Next.js 16 / React 19 / Tailwind / shadcn-ui; PostgreSQL + pgvector; Redis. Vertical Slice Architecture — each feature owns its models / schemas / routes / logic under `app/{feature}/`. Docker Compose for local services; Alembic migrations; CI via GitHub Actions (`ci.yml`).
- **Purpose:** Email engine + AI orchestrator + QA engine + CMS / Figma / Litmus connectors. ~95% built; ship-first lane toward revenue.

## Archon Configuration

- **Archon-enabled:** no — no `.archon/` directory. Stays `archon_enabled: false` until a lane build adds one.
- **Lane gate:** P4 (not yet green) → **not in Active Pages**; coding stays in-session / advisor-draft for now.
- **Default workflows that will fit when the lane opens:** issue-fix, feature-development, PIV-loop, comprehensive-PR-review. Dispatch mechanics: `integrations` skill + `query.py workflow` (P2 — not built).

## Workflow Preferences

- **Default branch `main`.** When the lane opens, dispatch on a worktree branch — never on `main` directly.
- **IP is Linards's, owned outright** — no IP-overhang / clean-room gate applies here. The Email Hub IP question is settled; don't re-raise it.
- **VSA discipline:** new work lands self-contained under `app/{feature}/`.
- **Advisor mode:** any dispatch yields a draft PR — never auto-merge or push.

## Dispatch History

_Reflection appends date-prefixed bullets here when daily logs reference dispatches against this repo._

- (2026-06-30) Page created.

## Recent Activity

- Most-referenced repo across the daily logs (28 distinct days as of 2026-06-30). Active build toward ship; primary income candidate.

## Related

Gated behind the `product-shape` SaaS canvas and the now-settled IP question. Index: [[REPOSITORIES]].
