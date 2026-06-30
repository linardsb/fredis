# REPOSITORIES.md — Codebase Index

_Fredis's index of every codebase Linards works in. Always loaded at session start (injected right after USER.md). When Linards names a repo, resolve it here, then read `repositories/<slug>.md` for the deep context._

_**Advisor mode (SOUL boundary):** anything this index informs produces a **draft PR only** — nothing auto-sends, auto-merges, or auto-pushes. See §Default Dispatch Rule._

## Conventions

- **Per-repo pages:** `Fredis/Memory/repositories/<slug>.md`, linked as `[[repositories/<slug>]]`. Only repos that have a page get the link; the rest show `—`.
- **Archon-enabled** = the repo has a `.archon/` directory with at least one custom workflow / command / `config.yaml`. None do yet → every page is `archon_enabled: false`.
- **Auto-promotion:** reflection promotes a repo to its own per-repo page after it appears in **3+ daily logs** (prevents page sprawl). Seed pages can predate that threshold for a designated lane.
- **Never an Archon target:** `Fredis` (this repo) and the `Fredis/Memory/` vault are the command centre — never dispatched against. Marked in the table.
- **No `archon` skill in this repo (24-skill cap).** Dispatch mechanics fold into the `integrations` skill + the planned `query.py workflow` CLI (P2) — not built yet. This index is the addressing layer only; it carries no dispatch code.

## Default Dispatch Rule

> **Status: GATED — Active Pages is empty, so this rule currently matches nothing.**
> No repo becomes dispatch-active until its lane is proven green: **Email Hub at P4**, **client-site at P4b**. Until a lane opens, every coding request stays in-session / advisor-draft, exactly as today.

When (and only when) a repo is listed in **Active Pages** below, Archon is the default coding-dispatch tool for it — even if Linards doesn't say the word "Archon." On a substantive coding request (signal phrases: `fix…`, `implement…`, `add a feature`, `let's work on…`, `build…`, `ship…`, `review PR…`, `resolve conflicts on…`):

1. **Resolve** the repo in **Active Pages**. If it isn't there, it is not dispatch-active — work in-session.
2. **Read** its `repositories/<slug>.md` — `## Archon Configuration` + `## Workflow Preferences` (mind base-branch overrides).
3. **Pick the workflow:** a listed **custom** workflow if one fits, else a bundled **default**. Dispatch mechanics live in the `integrations` skill + `query.py workflow` (P2, not built).
4. **Dispatch** with worktree isolation. **Advisor mode: the result is a draft PR — never auto-merged, never pushed to a protected branch.**
5. **Log** the dispatch to today's daily log so reflection routes it to the per-repo `## Dispatch History`.

**Skip dispatch — work in-session — for:** typos, one-line fixes, formatting, README touch-ups, read-only "explain this" questions, planning conversations, or anything Linards asks me to edit directly.

### Active Pages

_(none yet — gate closed; see Status above)_

| Slug | Lane | Opens when |
|------|------|------------|
| _none_ | — | Email Hub at P4 · client-site at P4b |

## Tracked Repositories

_The index. One row per repo Linards works in; every local path resolves on disk (Cab excepted — see §Planned). The **Page** column links to a per-repo page where one exists._

| Repo | Local path | GitHub | Default branch | Visibility | Archon-target | Page |
|------|-----------|--------|----------------|-----------|---------------|------|
| Fredis | `/Users/Berzins/Desktop/claude-code-second-brain` | `linardsb/fredis` | main | public | **never** (command centre) | — |
| merkle-email-hub | `/Users/Berzins/Desktop/merkle-email-hub` | `linardsb/merkle-email-hub` | main | public | yes — gated (P4) | [[repositories/merkle-email-hub]] |
| saulera-client-starter | `/Users/Berzins/Desktop/saulera-client-starter` | `linardsb/saulera-client-starter` | **master** | private | yes — gated (P4b) | [[repositories/saulera-client-starter]] |
| saulera | `/Users/Berzins/Desktop/saulera` | `linardsb/saulera` | main | public | yes | — |
| VTV | `/Users/Berzins/Desktop/VTV` | `linardsb/VTV` | main | private | yes | — |
| GERBONI | `/Users/Berzins/Desktop/AI/GERBONI` | `linardsb/GERBONI` | main | public | yes | — |
| mission-control | `/Users/Berzins/Desktop/mission-control` | _(local only — no remote)_ | master | — | no | — |
| ugoki | `/Users/Berzins/Desktop/ugoki` | `linardsb/ugoki-iOS-Android-app` | main | public | future | — |

## Planned / not yet cloned

_Active topics with no repo on disk yet. No local path resolves; no page until a repo exists and the 3+ threshold trips._

| Repo | Notes |
|------|-------|
| Cab | Taxi / ride product — "setup in progress" (partner: Atis). 9 daily-log mentions, but no repo yet (`~/Desktop/taxi/` is an empty placeholder). Add a Tracked row + page once the repo is cloned. |

## Excluded from tracking

_On disk but deliberately not indexed._

| Path | Why |
|------|-----|
| `~/Desktop/AI/agentic-coding-course` | Cole's course clone — reference material, not Linards's project. |
| `~/Desktop/cloned_repos/archon` | The Archon engine itself — the dispatch tool, never a dispatch target. |

## Dispatch Cheat Sheet

_Reference for when a lane opens (gate currently closed — see §Default Dispatch Rule)._

1. **Resolve** the repo in **Active Pages**. Not there? Not dispatch-active — work in-session.
2. **Open** `repositories/<slug>.md`; read `## Archon Configuration` + `## Workflow Preferences`. Note base-branch overrides — e.g. `saulera-client-starter` defaults to `master`, not `main`.
3. **Dispatch** with worktree isolation via the `integrations` skill + `query.py workflow` (P2, not built).
4. **Advisor mode:** draft PR only — never auto-merge or push.
5. **Log** the dispatch to today's daily log → reflection routes it to the per-repo `## Dispatch History`.

---

_This file is the always-loaded index. Resolve `[[repositories/<slug>]]` to `Fredis/Memory/repositories/<slug>.md`. Reflection updates per-repo pages from daily logs and auto-promotes new repos after 3+ daily-log mentions. Add a row by hand when starting work in a new repo._
