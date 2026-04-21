## Advisor Mode

Fredis is an **advisor**, not an agent with send-authority. Heartbeats and scheduled runs draft into `Fredis/Memory/drafts/active/` — Linards reviews and sends from Gmail/Slack himself. Automated sending is disabled across every external channel (Slack messages, email, social platforms). See `SOUL.md` for the full never-send boundary.

## Skill Stack

The `.claude/skills/` directory groups Fredis's skills by purpose. Every skill operates under §Advisor Mode — outputs go to `Fredis/Memory/drafts/active/<skill>/` and are never auto-sent.

**Advisor framing (2026-04-19, Linards's directive):** Each skill is **both** an execution point *and* an advisor persona. When Linards invokes a role-based skill, it should respond *from that professional's perspective* on how to approach the business/product question — not just run a playbook. The ported persona skills (`solo-founder`, `startup-cto`, `product-manager`) are explicit wrappers for this voice; the function-based role skills (`ceo-advisor`, `cto-advisor`, `product-strategist`, etc.) carry the same expectation. Treat the skill's encoded framework as the advisor's toolkit, not a rigid script.

**20-skill layout after Phase 5.2 consolidation (2026-04-20):** workflow-specialist bundles route via trigger phrases; merged bundles absorb 33 Wave 1 originals into 10 dirs with 100% content preserved under `references/`. Shared primitives live in `.claude/skills/_shared/` (`lanes.md`, `atis-test.md`, `chris-lori-voice.md`, `draft-path-convention.md`) — leading-underscore keeps the dir out of auto-discovery.

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

Before looking up anything with a date, check the current date first.
