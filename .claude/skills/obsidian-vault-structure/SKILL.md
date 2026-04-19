---
name: obsidian-vault-structure
description: |
  Reference for the Fredis Obsidian vault organization and file structure.
  Use when Claude needs to understand where content is stored, how files are organized,
  or where to save new content. Helpful for: (1) Finding existing notes, drafts, or
  research, (2) Understanding date-based conventions in daily logs and sent drafts,
  (3) Knowing where new research, drafts, or domain entities belong, (4) Understanding
  the relationship between the top-level Phase-1 memory files and the topical folders.
---

# Fredis Obsidian Vault Structure

**Location:** `Fredis/Memory/` (relative to project root).

The vault is a single tree rooted at `Fredis/Memory/`. Everything persistent the
assistant reads or writes lives here. The vault is sync'd across machines by
`git-sync` (see `CLAUDE.md` → Vault Sync).

## Directory Overview

```
Fredis/Memory/
├── SOUL.md                    # Personality, communication style, never-send boundary
├── USER.md                    # User profile, account IDs, integrations, preferences
├── MEMORY.md                  # Decisions, lessons, active projects, durable facts
├── HABITS.md                  # Habit pillars tracked by heartbeat
├── HEARTBEAT.md               # Checklist of what each heartbeat should check
│
├── daily/                     # Daily logs (YYYY-MM-DD.md) — heartbeat + session entries
│   ├── 2026-04-19.md
│   └── 2026-04-19.md.lock     # File locks written by heartbeat/reflection
│
├── drafts/                    # Outbound drafts — advisor mode, Linards sends manually
│   ├── active/                # Awaiting review/send
│   │   └── research/          # Research topic drafts (ai.md, markets.md, …)
│   ├── sent/                  # Archived after send, grouped by campaign
│   │   └── lv-seed/           # e.g. YYYY-MM-DD_slug.md
│   └── expired/               # Drafts that aged out without being sent
│
├── research/                  # Long-lived topic research (one folder per domain)
│   ├── ai/          {README.md, papers/}
│   ├── markets/     {README.md, watchlist-tickers.md, papers/}
│   ├── agriculture/ {README.md, latvia-landscape.md, papers/}
│   ├── materials/   {README.md, 3d_printing/, mycelium/, papers/}
│   ├── policy/      {README.md, papers/}
│   └── robotics/    {README.md, papers/}
│
├── competitors/               # Competitive landscape notes
│   ├── README.md
│   ├── _summary.md
│   └── ai-consultancy-landscape.md
│
├── collaborators/             # People Linards partners with
│   ├── README.md
│   ├── _network.md
│   └── <firstname-lastname>.md
│
├── investors/                 # Investor pipeline + per-person notes
│   ├── README.md
│   ├── _pipeline.md
│   └── <firstname-lastname>.md
│
├── retainers/                 # Active retainer clients (README.md placeholder today)
└── case-studies/              # Published/shipped work writeups (README.md placeholder today)
```

## Top-Level Memory Files

Auto-loaded into context by the `SessionStart` hook — Claude does not need to read them manually.

| File | Contains | Update When |
|------|----------|-------------|
| `SOUL.md` | Personality, behavioral rules, communication style, never-send boundary | Changing how the assistant should behave |
| `USER.md` | User profile, account IDs, integration config, preferences, team info | Learning about the user or adding an integration account |
| `MEMORY.md` | Key decisions, lessons learned, active projects, important facts | Making a significant decision or learning a reusable lesson |
| `HABITS.md` | Habit pillars + cadence, used by heartbeat | Changing what the assistant nudges on |
| `HEARTBEAT.md` | Checklist of what each heartbeat should check | Adjusting the heartbeat's scope |

## Daily Logs

- Filename: `daily/YYYY-MM-DD.md`
- Written by: heartbeat, reflection, `PreCompact`/`SessionEnd` hooks, and ad-hoc Claude sessions
- `.lock` sidecars are file locks (`shared.py`) — never edit or commit them; git ignores them via `.gitignore`
- Daily logs use the `concat-both` merge driver so simultaneous appends from multiple machines auto-merge (see `CLAUDE.md` → Vault Sync)

## Drafts (Advisor Mode)

Fredis is an **advisor**, not a sender. Scheduled/automated flows write drafts here; Linards reviews and sends from Gmail/Slack himself.

```
drafts/
├── active/    # pending review — safe target for new drafts
├── sent/      # archive after send, grouped by campaign folder
│   └── <campaign-slug>/YYYY-MM-DD_<kebab-slug>.md
└── expired/   # drafts that aged out without being sent
```

- Sent-draft filenames: `YYYY-MM-DD_<kebab-case-subject>.md`
- `drafts/sent/` doubles as the voice-matching corpus — `memory_search.py --path-prefix drafts/sent` pulls examples when drafting new replies
- New research-topic drafts go in `drafts/active/research/<topic>.md`

## Research

Each domain folder is self-contained:

- `README.md` — overview / running index of what lives in this topic
- `papers/` — downloaded papers, notes on them
- Topic-specific files at the folder root (e.g. `markets/watchlist-tickers.md`, `agriculture/latvia-landscape.md`)

When adding a new research domain, scaffold `<domain>/README.md` + `<domain>/papers/` to match the existing pattern.

## Relationship Folders

`competitors/`, `collaborators/`, `investors/`, `retainers/`, `case-studies/` all follow the same shape:

- `README.md` — what the folder is for, index of entries
- `_<aggregate>.md` — rollup file (e.g. `_summary.md`, `_network.md`, `_pipeline.md`)
- `<firstname-lastname>.md` or `<entity-slug>.md` — one file per person/entity

## Naming Conventions

| Thing | Pattern |
|-------|---------|
| Daily logs | `YYYY-MM-DD.md` |
| Sent drafts | `YYYY-MM-DD_<kebab-slug>.md` |
| People | `<firstname-lastname>.md` |
| Topics / entities | `kebab-case.md` |
| Rollup files | `_<name>.md` (underscore prefix sorts them to top) |
| Folder READMEs | `README.md` (one per topical folder) |

## Common Operations

| Task | Location |
|------|----------|
| Today's daily log | `Fredis/Memory/daily/YYYY-MM-DD.md` |
| Draft a reply Linards will send | `Fredis/Memory/drafts/active/<slug>.md` |
| Look up past sent phrasing for voice-match | `memory_search.py "<topic>" --path-prefix drafts/sent` |
| Add a new research note | `Fredis/Memory/research/<domain>/<slug>.md` (or `papers/`) |
| Add a person (investor/collab) | `Fredis/Memory/<folder>/<firstname-lastname>.md` + link from `_pipeline.md` / `_network.md` |
| Record a durable decision | Append to `Fredis/Memory/MEMORY.md` |

## What Is *Not* In The Vault

These live elsewhere in the repo and should not be duplicated into `Fredis/Memory/`:

- Onboarding interview → `.agent/plans/phase1-onboarding-interview.md`
- Project PRD → `.agent/plans/second-brain-prd.md`
- Heartbeat / reflection / chat state → `.claude/data/state/*.json`
- Memory search index → `.claude/data/memory.db` (regenerable)
- Skills, hooks, scripts → `.claude/`
