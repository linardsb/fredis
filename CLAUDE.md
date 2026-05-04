## Project Overview

Fredis is a personal AI advisor for Linards. This repo is the runtime — a 24-skill stack, an Obsidian vault for persistent memory (`Fredis/Memory/`), heartbeat / reflection / synthesis SDK loops, and Slack / Gmail / Google Workspace / HubSpot / GitHub integrations. **Nothing is auto-sent**: every output lands in `Fredis/Memory/drafts/active/` and the HubSpot Review pipeline for Linards to action himself (see §Advisor Mode).

## Quick Reference

| Resource | Purpose |
|----------|---------|
| `README.md` | Setup, scheduling cron lines, configuration, daily ops |
| `setup_workspace.py` | One-shot workspace bootstrap (vault skeleton, env wiring) |
| `master.env.example` | Consolidated env template (Slack, Gmail, HubSpot, OpenAI/Anthropic, …) |
| `docker-compose.yml` | Local supporting services |
| `.claude/scripts/CLAUDE.md` | Subsystem detail — heartbeat, chat, memory search/index, reflection, synthesis, vault sync, `query.py` integrations CLI, threat models, MCP/Zapier fallback. **Auto-loads only when Claude's cwd is at or below `.claude/scripts/`** — keep runtime-only detail there so SDK callers running with `cwd=PROJECT_ROOT` don't load it. |

## Behavioral Guardrails

The four principles in `~/.claude/CLAUDE.md` (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) apply by default. How they bind in this repo:

- **Think Before Coding → run §Audit Conventions before claiming anything is "open", "still not done", "pending", or "needs fixing".** The four checks (git log since the doc's write time, run the live CLI that proves or disproves the claim, grep the full daily-log window, read SKILL.md + references for any skill the audit touches) prevent re-proposing already-done or explicitly-deferred work.
- **Simplicity First → consolidate, don't proliferate skills.** New behaviour belongs inside an existing skill bundle (see §Skill Stack — the 24-skill layout already absorbed 20 specialists into 14 bundles in Phase 5.2) or as a shared primitive in `.claude/skills/_shared/`. Spinning up a 25th top-level skill needs explicit approval.
- **Surgical Changes → `Fredis/Memory/` is read-mostly for code edits.** SOUL.md is hook-blocked (`block-soul-edit.py`); template-residue paths are hook-blocked (`block-template-residue.py`); daily logs are written by hooks/SDK callers, not by hand. To suggest a behaviour change, append to today's daily log — don't edit SOUL.md.
- **Goal-Driven Execution → before declaring a task done, name the artifact Linards reviews — not "I implemented X".** Drafts go to `Fredis/Memory/drafts/active/<skill>/`; the matching HubSpot ticket in the Fredis Review pipeline is the inbox; the `[DRAFT]` Slack notice is the heads-up. No artifact = task isn't done.

When uncertain about a phase boundary, deferred scope, or whether a feature has already shipped, **stop and check `.agent/plans/` + `.agent/audits/` + grep the daily logs** before proceeding. Audit Conventions exists because every shortcut around it has cost tokens and trust.

## Advisor Mode

Fredis is an **advisor**, not an agent with send-authority. Heartbeats and scheduled runs draft into `Fredis/Memory/drafts/active/` — Linards reviews and sends from Gmail/Slack himself. Automated sending is disabled across every external channel (Slack messages, email, social platforms). See `SOUL.md` for the full never-send boundary.

**Review queue (HubSpot tickets).** Every actionable draft Fredis produces also creates a ticket in the HubSpot `Fredis Review` pipeline (5 stages: Drafted → In review → Needs send → Actioned / Rejected) and posts a `[DRAFT] ...` notice to `#hubspot` in Slack. The ticket is the inbox; the draft file is the content. DM Fredis "what's in my queue" to scan, or use the `hubspot queue` / `hubspot create-ticket` / `hubspot move-ticket` / `hubspot close-ticket` CLI. Flag-gated on `HUBSPOT_TICKETS_ENABLED`. Plan: `.agent/plans/fredis-hubspot-tickets-slack.md`.

## Audit Conventions

Before claiming anything in this repo is "open", "still not done", "pending", or "needs fixing":

1. **Check `git log` since the reference doc's write time** — plan docs and audit reports in `.agent/plans/` and `.agent/audits/` are historical snapshots, never current state. A doc written yesterday afternoon doesn't know about yesterday evening's commits.
2. **Run the live CLI that proves or disproves the claim.** Examples: `git status` for uncommitted work, `query.py lanes list` for GitHub Projects scope, `query.py hubspot pipelines` for stage names, `uv run python heartbeat.py --test` for integration health. Every audit claim must trace to output produced in *this* session, not to a doc string.
3. **Grep the full daily-log window, not just the last 3 days.** The `SessionStart` hook loads only the last 3 daily logs, so scope decisions older than that are invisible unless `memory_reflect.py` promoted them to MEMORY.md. Run `grep -rni 'deferred\|dropped\|out of scope\|won.?t build\|not shipping' Fredis/Memory/daily/` before treating any gap as open.
4. **Read the `SKILL.md` + `references/*.md` of any skill the audit touches.** Skill reference docs (e.g. `.claude/skills/draft-reply/references/slack-integration.md`) frequently encode scope decisions ("Future phase", "out of Phase X scope") that never reach MEMORY.md.

An audit that skips these four checks will re-propose work that's already done, deferred, or explicitly dropped — wasting Linards's tokens and trust. If a finding survives all four, then it's real; only then list it.

## Skill Stack

The `.claude/skills/` directory groups Fredis's skills by purpose. Every skill operates under §Advisor Mode — outputs go to `Fredis/Memory/drafts/active/<skill>/` and are never auto-sent.

**Advisor framing (2026-04-19, Linards's directive):** Each skill is **both** an execution point *and* an advisor persona. When Linards invokes a role-based skill, it should respond *from that professional's perspective* on how to approach the business/product question — not just run a playbook. The ported persona skills (`solo-founder`, `startup-cto`, `product-manager`) are explicit wrappers for this voice; the function-based role skills (`ceo-advisor`, `cto-advisor`, `product-strategist`, etc.) carry the same expectation. Treat the skill's encoded framework as the advisor's toolkit, not a rigid script.

**24-skill layout after Phase 12 starter-pack additions (2026-04-23):** Phase 5.2 consolidation added 20 workflow-specialist bundles; Phase 12 adds 4 manual-invocation starter-pack skills (`draft-reply`, `meeting-notes`, `client-log`, `uk-latvia-context`) covering everyday chat-invoked flows. Shared primitives live in `.claude/skills/_shared/` (`lanes.md`, `atis-test.md`, `chris-lori-voice.md`, `draft-path-convention.md`) — leading-underscore keeps the dir out of auto-discovery.

| # | Skill | Absorbs / Purpose |
|---|-------|--------------------|
| 1 | `ip-overhang-guard` | UK CDPA s.11(2) + Patents Act s.39 + clean-room + Merkle-letter |
| 2 | `business-cycle-analyst` | Dalio cycles + Kondratieff + Chris-Lori voice |
| 3 | `robotics-engineer` | ROS2 + ISO safety + motion planning |
| 4 | `phase1-ready` | Onboarding pipeline |
| 5 | `skill-creator` | Meta — scaffold + validate skills |
| 6 | `obsidian-vault-structure` | Vault layout reference |
| 7 | `ciso-advisor` | Strategic/compliance security (kept separate from hands-on security-engineering) |
| 8 | `integrations` | `direct-integrations` + `mcp-client` |
| 9 | `executive-leadership` | `ceo-advisor` + `founder-coach` + `solo-founder` + `scenario-war-room` |
| 10 | `technical-leadership` | `cto-advisor` + `startup-cto` |
| 11 | `org-design` | `strategic-alignment` + `company-os` |
| 12 | `security-engineering` | `senior-security` + `senior-secops` + `security-pen-testing` + `cloud-security` + `ai-security` |
| 13 | `engineering` | `senior-architect` + `senior-backend` + `senior-qa` + `tdd-guide` |
| 14 | `data-and-experimentation` | `senior-data-scientist` + `statistical-analyst` + `experiment-designer` |
| 15 | `product-management` | `product-strategist` + `product-discovery` + `product-manager-toolkit` + `product-manager` |
| 16 | `content-social` | `linkedin-post` + `x-post` + `instagram-post` |
| 17 | `content-artifacts` | `pptx-generator` + `excalidraw-diagram` + `pdf` + `sop-creator` |
| 18 | **`idea-validation`** | market-landscape-scan + problem-validation + minimum-lovable-product (new) |
| 19 | **`product-shape`** | pricing-shaper + positioning-sharpener + mvp-architect (new) |
| 20 | **`launch-governance`** | launch-wedge + metrics-gate + bet-review + decision-logger (new, heartbeat-wired) |
| 21 | **`draft-reply`** | Voice-matched email/Slack reply drafting — retrieves 3 past replies from `drafts/sent/`, creates native Gmail draft via `query.py gmail create-draft --from-file` (Phase 12) |
| 22 | **`meeting-notes`** | Structured meeting capture to `Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md` (capture-mode carve-out; Phase 12) |
| 23 | **`client-log`** | Appender for `Fredis/Memory/retainers/<client>.md` — dated entries with context/decisions/open-items (capture-mode carve-out; Phase 12) |
| 24 | **`uk-latvia-context`** | Reference pack for UK + Latvian admin (Companies House, HMRC, Lursoft, VID, cross-border). Grows organically — structure seeded, Q&A added on demand (Phase 12) |

**Voice modes** — merged skills with persona references surface them via invocation ("in solo-founder voice", "in startup-cto voice", "in product-manager voice"). Default is neutral SOUL voice.

## Memory Layout

Fredis's persistent memory is an Obsidian vault at `Fredis/Memory/`. Top-level files are auto-loaded into context by the `SessionStart` hook — no manual reading required.

| File | Contains | Update When |
|------|----------|-------------|
| `SOUL.md` | AI personality, behavioural rules, communication style, boundaries | Changing how the assistant should behave |
| `USER.md` | User profile, account IDs, integration config, preferences, team info | Learning something about the user or adding an integration account |
| `MEMORY.md` | Key decisions, lessons learned, active projects, important facts | Making a significant decision or learning a reusable lesson |
| `HABITS.md` | Habit pillars checked during heartbeat | Changing the habit pillars |
| `HEARTBEAT.md` | What the heartbeat scans each tick | Changing heartbeat behaviour |
| `daily/YYYY-MM-DD.md` | Session logs, heartbeat entries, reflection / synthesis notes | Session end or heartbeat (written automatically by hooks) |

### Vault subdirectories

| Path | Contains |
|------|----------|
| `Fredis/Memory/drafts/active/` | Pending drafts awaiting Linards's review — every skill, heartbeat, chat, and synthesis output lands here |
| `Fredis/Memory/drafts/sent/` | Historical sent drafts — use for voice-matching when drafting new replies |
| `Fredis/Memory/research/` | Research notes on topics under investigation |
| `Fredis/Memory/competitors/` | Competitor analysis per market / product lane |
| `Fredis/Memory/retainers/` | Retainer-specific client context |
| `Fredis/Memory/case-studies/` | Case studies for positioning |
| `Fredis/Memory/gates/*.yaml` | Launch-governance kill-trigger gates (read by heartbeat's `metrics-gate` bundle from the `launch-governance` skill) |

### Outside the vault

| Path | Contains |
|------|----------|
| `.claude/skills/` | Skill definitions (see §Skill Stack above) |
| `.claude/skills/_shared/` | Shared primitives — `lanes.md`, `atis-test.md`, `chris-lori-voice.md`, `draft-path-convention.md` |
| `.claude/scripts/` | Runtime scripts (heartbeat, reflection, synthesis, memory search/index, chat engine, integrations CLI) |
| `.claude/chat/` | Slack chat interface (engine, session store, Slack adapter) |
| `.claude/hooks/` | `PreToolUse` / `SessionStart` / `SessionEnd` / `PreCompact` hooks |
| `.agent/plans/` | Planning docs (onboarding interview, phase plans) |
| `.agent/audits/` | Audit / review docs |
| `docs/` | Durable documentation — phase history, deployment records, research decisions |

This file (CLAUDE.md) is **project documentation** — how the system works and how its components fit together. It should not contain user-specific preferences, personality rules, or behavioural instructions. Those belong in `SOUL.md`.

> For setup, scheduling, and configuration instructions, see `README.md`.

### Hooks

- **`SessionStart`** — injects SOUL.md, USER.md, MEMORY.md, and the last 3 days of daily logs into context at session start
- **`PreCompact`** — saves important conversation context to the daily log before Claude Code auto-compacts (safety net)
- **`SessionEnd`** — saves important conversation context when the session ends
- **`PreToolUse → block-soul-edit.py`** — blocks Edit/Write to `Fredis/Memory/SOUL.md` across every surface (normal Claude Code sessions + heartbeat / reflection / chat SDK sessions via `setting_sources=["user","project"]`). SOUL edits go through Linards by hand — append suggestions to today's daily log instead.
- **`PreToolUse → block-template-residue.py`** — blocks Edit/Write that re-introduce scrubbed template strings outside the allowlisted paths (`.agent/plans/`, `.agent/audits/`, `Fredis/Memory/daily/`, `Fredis/Memory/USER.md`).
- Agent SDK callers (`heartbeat`, `memory_flush`, `memory_reflect`, `chat`) set `CLAUDE_INVOKED_BY` at module top; `PreCompact`/`SessionEnd` hooks skip when it is set (prevents recursive flushes when SDK sub-sessions exit).

---

## Architecture & Operations

Subsystem implementation detail is split out of this file so every SDK caller (heartbeat, chat, reflection, synthesis) loads a smaller `/CLAUDE.md` each run.

- **`.claude/scripts/CLAUDE.md`** — heartbeat, chat engine, memory search + index, reflection, synthesis, vault sync, integrations CLI (`query.py`), pre-commit workflow, threat models, secrets rotation, dependency audit, MCP/Zapier fallback. Auto-loads when Claude's cwd is at or below `.claude/scripts/`; invisible to SDK callers that run with `cwd=PROJECT_ROOT`.
- **`docs/phases.md`** — completed-phase history (Phases 1 through 10.5).
- **`docs/vps-deployment-and-vault-sync.md`** — VPS deployment + vault-sync operational detail.
- **`docs/phase10-deploy-progress.md`** — Phase 10 deployment log.
- **`docs/llm-and-vps-swapping.md`** — how to swap front-end clients (easy, post-OB1-Phase-1) vs swapping the autonomous-services LLM (hard, full SDK rewrite). Read first before changing which LLM talks to Fredis.

## Compact instructions

When compacting, preserve:
- Active task + plan path under `.agent/plans/`
- Modified files + outcome of any tool runs
- Active draft path under `Fredis/Memory/drafts/active/<skill>/` (and matching HubSpot ticket id, if any)
- Skill currently invoked + voice mode (e.g. `solo-founder`, `startup-cto`, `product-manager`)
- Decisions worth promoting to `MEMORY.md` (don't write SOUL.md — blocked by `PreToolUse` hook; append to today's daily log instead)

Before looking up anything with a date, check the current date first.
