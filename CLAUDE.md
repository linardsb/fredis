## Advisor Mode

Fredis is an **advisor**, not an agent with send-authority. Heartbeats and scheduled runs draft into `Fredis/Memory/drafts/active/` — Linards reviews and sends from Gmail/Slack himself. No `slack.postMessage`, no `drafts.send`, no social-media POSTs in any automated path. See `SOUL.md` for the full never-send boundary.

## Completed Phases

- **Phase 1** — Memory-layer personalisation (SOUL/USER/MEMORY/HABITS/HEARTBEAT drafting via `phase1-ready` skill).
- **Phase 2** — Heartbeat + draft loop (scheduled gather → reconcile → prompt → Slack).
- **Phase 3** — Hybrid memory search (SQLite/Postgres + FastEmbed) + Slack chat interface.
- **Phase 4** — Integrations reconciliation: added Monday.com + GitHub; advisor-mode belt tightened; heartbeat defaults set to Europe/London 05:00–20:00, 120 min interval.
- **Phase 5.1** — Skill stack Wave 1 (`.agent/plans/phase5-skill-stack.md`): ported 25 MIT-licensed skills from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) covering C-level advisors, engineering roles, stats/experimentation, product, and personas (solo-founder, startup-cto, product-manager); authored 3 de novo — `ip-overhang-guard` (UK employer-IP), `business-cycle-analyst` (Dalio + Lori voice), `robotics-engineer` (ROS2 + ISO safety + motion planning). Archon sub-agent port deferred to post-Fredis-completion.
- **Phase 5.2** — Workflow-specialist bundles + 20-skill consolidation (`.agent/plans/phase5-2-skill-consolidation.md`): authored 3 new bundles (`idea-validation`, `product-shape`, `launch-governance`) encoding 10 workflow-specialist frameworks (market-landscape-scan, problem-validation, minimum-lovable-product, pricing-shaper, positioning-sharpener, mvp-architect, launch-wedge, metrics-gate, bet-review, decision-logger) as structural skeletons with source lists; consolidated 33 existing skills into 10 merged bundles (`integrations`, `executive-leadership`, `technical-leadership`, `org-design`, `security-engineering`, `engineering`, `data-and-experimentation`, `product-management`, `content-social`, `content-artifacts`) with 100% content preserved in `references/`; `ciso-advisor` kept standalone; shared assets in `_shared/` (lanes, Atis-£1k test, Chris-Lori voice, draft-path convention); `metrics-gate` wired into heartbeat for proactive kill-trigger breach surfacing via `Fredis/Memory/gates/*.yaml`. Final: 20 Fredis skills + 7 Claude Code built-ins.

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

## Memory Files

This project uses an Obsidian vault (`Fredis/Memory/`) as persistent memory across sessions. These files are auto-loaded into context via the `SessionStart` hook — no manual reading required.

| File | Contains | Update When |
|------|----------|-------------|
| `SOUL.md` | AI personality, behavioral rules, communication style, boundaries | Changing how the assistant should behave |
| `USER.md` | User profile, account IDs, integration config, preferences, team info | Learning something about the user or adding an integration account |
| `MEMORY.md` | Key decisions, lessons learned, active projects, important facts | Making a significant decision or learning a reusable lesson |
| `daily/YYYY-MM-DD.md` | Session logs, heartbeat entries, daily context | End of meaningful sessions (also written automatically by hooks) |

This file (CLAUDE.md) is **project documentation** — how the system works and how its components fit together. It should not contain user-specific preferences, personality rules, or behavioral instructions. Those belong in `SOUL.md`.

> For setup, scheduling, and configuration instructions, see `README.md`.

### Hooks

- **`SessionStart`** — injects SOUL.md, USER.md, MEMORY.md, and the last 3 days of daily logs into context at session start
- **`PreCompact`** — saves important conversation context to the daily log before Claude Code auto-compacts (safety net)
- **`SessionEnd`** — saves important conversation context when the session ends
- Agent SDK callers (`heartbeat`, `memory_flush`, `memory_reflect`, `chat`) set `CLAUDE_INVOKED_BY` at module top; `PreCompact`/`SessionEnd` hooks skip when it is set (prevents recursive flushes when SDK sub-sessions exit).

---

## Onboarding

First-run personalisation is a TUI + skill pair that converts the 103-question interview at `.agent/plans/phase1-onboarding-interview.md` into the five personalised memory files.

- **TUI:** `cd .claude/scripts && uv run python onboard.py [--tier core|rich|all] [--from A1] [--dry-run]`. One question per terminal screen with a multi-line `TextArea`. Answers are written back into the interview file in place — no sidecar state. `Ctrl+N` / `Ctrl+P` navigate, `Ctrl+S` saves and exits, `Ctrl+E` drops into `$EDITOR` for ★★★ long-form questions, `Ctrl+J` jumps to a section by letter, `Ctrl+Q` quits. Resumes automatically at the first unanswered question. Requires the `textual>=0.85.0` dep (already in `pyproject.toml`).
- **Trigger phrase:** say "phase 1 answers ready" (or "phase 1 complete" / "onboarding interview done") in any session. The `phase1-ready` skill (`.claude/skills/phase1-ready/`) reads the interview, drafts SOUL/USER/MEMORY/HABITS/HEARTBEAT, shows each draft for review, writes only after approval, scaffolds `Fredis/Memory/{research,competitors,retainers,case-studies}/`, appends a `## Addendum — Context Deltas` section to `.agent/plans/second-brain-prd.md`, and deletes `Fredis/Memory/BOOTSTRAP.md`. The skill's per-file mapping lives in `.claude/skills/phase1-ready/runbook.md`; the write-allowlist reference is `drafting_hook.py`.

---

## Heartbeat System (Proactive Second Brain)

The heartbeat is a scheduled script that proactively checks the user's draft inbox, overdue tasks across Asana + Monday.com, calendar, email, Slack, market/policy/AI research signals, and habit pillars using the Claude Agent SDK. It runs every 120 minutes during active hours (Europe/London, 05:00–20:00) and sends a Slack DM + native macOS notification when something needs attention.

**Location:** `.claude/scripts/`

### Key Files

| File | Purpose |
|------|---------|
| `heartbeat.py` | Main script - gathers API data, runs Claude for reasoning |
| `config.py` | Path constants, active hours, timezone config |
| `notifications.py` | Cross-platform notifications (Windows toast / macOS osascript / Linux notify-send) |
| `shared.py` | State management, daily log helpers, file locking, bash validation |

### How It Works

1. OS scheduler runs the wrapper script every 120 minutes
2. Wrapper runs `uv run python heartbeat.py` in `.claude/scripts/`
3. `heartbeat.py` gathers data from Gmail, Calendar, Asana, Slack, Monday.com, and GitHub via direct Python API calls
4. State diffing compares current data against the previous snapshot — only new/changed items get full context
5. Guardrail pre-filter (deterministic pattern matching + Haiku LLM) checks for prompt injection in external data
6. Pre-fetched, diff-annotated data is injected into Claude's prompt; Claude reasons over it and decides what needs attention
7. If something needs attention → Slack notification + daily log entry
8. If nothing needs attention → `HEARTBEAT_OK` logged silently

**Authentication:** Uses Claude Code CLI credentials automatically (`~/.claude/.credentials.json`). No API key needed.

### State & Logs

- **State:** `.claude/data/state/heartbeat-state.json` - tracks `last_run`, snapshot, alert history (per-machine, not synced)
- **Guardrail state:** `.claude/data/state/guardrail-state.json` - tracks last guardrail verdict
- **Daily log:** `Fredis/Memory/daily/YYYY-MM-DD.md` - heartbeat entries appended here
- **Checklist:** `Fredis/Memory/HEARTBEAT.md` - defines what to check each heartbeat

### State Diffing

The heartbeat snapshots integration data (email IDs, event IDs, task GIDs, Slack message timestamps) after each run and stores it in the heartbeat state file. On the next run, `diff_snapshot()` compares the current data against the previous snapshot:

- **New items** get full context and are annotated as "NEW" in Claude's prompt
- **Unchanged items** get a one-line summary marked "unchanged (already reported)"
- **Removed items** (e.g., completed tasks) are noted so Claude can acknowledge them

This prevents the agent from repeatedly alerting about the same emails/tasks across consecutive heartbeats.

### Security: Guardrail Pre-Filter

Before external data reaches the main Claude agent, it passes through a two-stage guardrail:

1. **Deterministic pre-check** (`sanitize.py → check_injection_patterns`) — 12 regex categories catch known injection patterns (role-play attacks, instruction overrides, XML escape attempts, tool invocations)
2. **LLM semantic evaluation** (Haiku) — catches obfuscated or novel injection attempts that regex misses

Verdicts:
- `pass` → data is safe, proceed normally
- `suspicious` → warning logged, proceed with caution
- `fail` → heartbeat blocked, Slack alert sent, data never reaches the main agent

The 3-layer sanitization system (`sanitize.py`) also wraps all external data in XML trust boundaries (`<external_data>` tags) and escapes markdown structure (headings, code fences, horizontal rules) to prevent content from breaking Claude's context formatting.

---

## Vault Sync (Git-Based)

The Obsidian vault (`Fredis/`) syncs between machines via Git using [simonthum/git-sync](https://github.com/simonthum/git-sync) (CC0 license) on a 2-minute timer. This replaces Obsidian Sync, which can't detect file changes made by external processes (heartbeat, reflection, Claude Code).

**Location:** `.claude/scripts/` (sync scripts), `Fredis/` (vault repo)

### Key Files

| File | Purpose |
|------|---------|
| `git-sync` | The simonthum/git-sync script (CC0 license, modified to use merge) |
| `git-merge-concat` | Custom merge driver - concatenates append-only files instead of conflicting |
| `run_vault_sync.bat` | Windows Task Scheduler wrapper |
| `run_vault_sync.sh` | Linux systemd timer wrapper |
| `setup_vault_sync.ps1` | Windows Task Scheduler setup script |
| `Fredis/.gitignore` | Excludes workspace.json, .trash/, lock files |
| `Fredis/.gitattributes` | Forces LF line endings + concat-both merge driver for daily logs |

### How It Works

1. OS scheduler triggers `run_vault_sync` every 2 minutes
2. Wrapper runs `git-sync` inside `Fredis/` (the vault directory)
3. `git-sync` auto-commits local changes, fetches from origin, merges if diverged
4. Daily log conflicts are auto-resolved by the `concat-both` merge driver (concatenates both sides)
5. If a non-daily-log conflict occurs, merge is aborted to keep the repo clean (fails gracefully, retries next cycle)
6. Results logged to `vault_sync_runs.log`

### Scheduling

- **Windows:** Task Scheduler task `SecondBrain-VaultSync` (every 2 min)
- **VPS:** systemd timer `vault-sync.timer` (every 2 min after previous run completes)

### Management Commands

```powershell
# Windows
Get-ScheduledTask -TaskName "SecondBrain-VaultSync"         # check status
Start-ScheduledTask -TaskName "SecondBrain-VaultSync"       # run now
Disable-ScheduledTask -TaskName "SecondBrain-VaultSync"     # pause
Enable-ScheduledTask -TaskName "SecondBrain-VaultSync"      # resume
```

```bash
# VPS (via SSH)
systemctl status vault-sync.timer          # check status
systemctl list-timers | grep vault         # see next run time
systemctl start vault-sync.service         # run now
journalctl -u vault-sync.service -n 20    # view recent logs
```

### Merge Strategy

git-sync uses **merge** (not rebase) when local and remote diverge. This prevents the repo from getting stuck in a broken rebase state if a conflict occurs.

For daily log files (`Memory/daily/*.md`), a custom merge driver (`concat-both`) automatically concatenates additions from both sides instead of conflicting. This handles the most common conflict source: multiple machines appending heartbeat entries and session logs to the same daily file.

**How the merge driver works:**
1. `.gitattributes` maps `Memory/daily/*.md` to the `concat-both` driver
2. On conflict, git invokes `.claude/scripts/git-merge-concat` with the ancestor, local, and remote versions
3. The script takes the remote version as base, then appends any lines the local side added that aren't already present
4. Result: both sides' entries are preserved, no manual intervention needed

**Exit codes:**
- **git-sync exit 0:** Success, everything synced
- **git-sync exit 1:** Merge conflict on a non-daily-log file (merge aborted, repo stays clean, retries next cycle)
- **git-sync exit 2:** Repo in an unexpected state (check for stuck rebase/merge)
- **git-sync exit 3:** Network error (transient, retries next cycle)

### Git Config (Required on Every Machine)

```bash
git config core.autocrlf false
git config --bool branch.main.sync true
git config --bool branch.main.syncNewFiles true

# Register the concat-both merge driver (path varies by machine)
git config merge.concat-both.name "Concatenate both sides for append-only files"
git config merge.concat-both.driver "bash /path/to/your-repo/.claude/scripts/git-merge-concat %O %A %B"
```

---

## Memory Search

Hybrid search (keyword + semantic) over all Second Brain memory files. Fully local — no API calls.

### How It Works

1. Markdown files in `Fredis/Memory/` are chunked into ~400-token overlapping segments
2. Each chunk is indexed for keyword search (FTS5 in SQLite, tsvector in Postgres) and vector search (sqlite-vec or pgvector)
3. Embeddings generated locally via FastEmbed (ONNX, all-MiniLM-L6-v2, 384-dim)
4. Incremental indexing — only changed files are re-indexed
5. Hybrid search combines vector similarity (0.7) with keyword score (0.3)

### Key Files

| File | Purpose |
|------|---------|
| `db.py` | Database abstraction — SQLiteMemoryDB or PostgresMemoryDB |
| `memory_index.py` | Chunks markdown, generates embeddings, stores via db.py |
| `memory_search.py` | Keyword/semantic/hybrid search with CLI |
| `embeddings.py` | FastEmbed wrapper with lazy model loading |

### Search Commands

```bash
# Quick keyword search (instant, no embedding)
cd .claude/scripts && uv run python memory_search.py "query" --mode keyword --limit 5

# Deep hybrid search (embeds query, ~1 sec, finds conceptually related content)
cd .claude/scripts && uv run python memory_search.py "query" --mode hybrid --limit 10

# Search only sent drafts (for voice-matching when drafting new replies)
cd .claude/scripts && uv run python memory_search.py "topic" --mode hybrid --path-prefix drafts/sent --limit 3
```

If the database doesn't exist (first run on a new machine):
```bash
cd .claude/scripts && uv run python memory_index.py
```

### Data Locations

- **SQLite database:** `.claude/data/memory.db` (git-ignored, regenerable via `memory_index.py`)
- **Postgres:** Set `DATABASE_URL` in `.claude/scripts/.env` (pgvector required)
- **Model cache:** `.claude/data/models/` (auto-downloaded ~80MB on first run)
- **Auto-indexing:** Heartbeat re-indexes every 120 minutes (unchanged files skipped)

### SSH Tunnel for Postgres (Required on Local Machine)

Memory search and chat sessions use Postgres on the VPS. The local `.env` has `DATABASE_URL` pointing to `localhost:5432`, which requires a persistent SSH tunnel.

#### macOS (launchd, primary)

The launchd plist lives at `.claude/scripts/schedule/com.linards.ssh-tunnel.plist`.
It respawns the tunnel on exit (including laptop wake) and throttles restarts on auth failure.
Full install/check/unload commands are in `.claude/scripts/schedule/README.md`.

```bash
# Install + load
cp .claude/scripts/schedule/com.linards.ssh-tunnel.plist ~/Library/LaunchAgents/
# (substitute __HOME__/__KEY_PATH__/__VPS_USER__/__VPS_HOST__ placeholders first — see schedule/README.md)
launchctl load ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist

# Check
launchctl list | grep com.linards.ssh-tunnel
nc -z localhost 5432 && echo TUNNEL_OK

# Unload
launchctl unload ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist
```

Skip this plist entirely if `DATABASE_URL` is unset or points at SQLite — the tunnel is only needed in VPS Postgres mode.

#### Windows (Task Scheduler)

```powershell
# Creates a persistent tunnel that starts at logon and auto-restarts on failure
$action = New-ScheduledTaskAction -Execute "ssh.exe" `
    -Argument "-N -i C:\Users\you\.ssh\your-key -L 5432:localhost:5432 user@your-vps-ip"
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask `
    -TaskName "SecondBrain-SSH-Tunnel" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "SSH tunnel to VPS Postgres"
```

Manage the tunnel:
```powershell
Start-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel"      # start now
Stop-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel"       # stop
Get-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel"        # check status
```

**If `memory_search.py` fails with a connection error**, the tunnel is probably down. The SSH key is passphrase-protected, so automated restarts only work once the key is loaded in `ssh-agent`:
- macOS: `ssh-add ~/.ssh/your-key` then `launchctl kickstart -k "gui/$(id -u)/com.linards.ssh-tunnel"`
- Windows: `ssh-add C:\Users\you\.ssh\your-key` then `Start-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel"`

### SSH to VPS from Claude Code

On macOS, just use `ssh` directly — no Git-SSH-vs-Windows-SSH conflict.

On Windows, Claude Code's bash shell uses Git's bundled SSH (`/usr/bin/ssh`), which does **not** connect to the Windows SSH agent. Always use the Windows OpenSSH binary instead:

```bash
# SSH
/c/Windows/System32/OpenSSH/ssh.exe -i C:/Users/you/.ssh/your-key user@your-vps-ip "command"

# SCP
/c/Windows/System32/OpenSSH/scp.exe -i C:/Users/you/.ssh/your-key local_file user@your-vps-ip:/remote/path
```

The Windows SSH agent service is set to `Automatic` start and persists loaded keys across reboots. If SSH fails with "Permission denied (publickey)", ask the user to run `ssh-add C:\Users\you\.ssh\your-key` in a terminal.

**VPS notes:**
- `uv` may need to be added to PATH — run `export PATH=$HOME/.local/bin:$PATH` before using it
- Clone the repo on the VPS and configure the same `.env` values

See `SOUL.md` → Memory Recall for behavioral rules on when to search.

---

## Daily Reflection (Automated Memory Curation)

A scheduled script that uses Claude Agent SDK to review yesterday's daily log and promote important items to MEMORY.md. Runs daily at 8 AM via OS scheduler.

**Location:** `.claude/scripts/`

### Key Files

| File | Purpose |
|------|---------|
| `memory_reflect.py` | Main script - reviews logs and updates MEMORY.md |
| `run_reflect.bat` | Wrapper for Windows Task Scheduler |
| `run_reflect.sh` | Wrapper for cron/launchd (macOS/Linux) |

### How It Works

1. OS scheduler runs the wrapper script daily at 8 AM
2. Wrapper runs `uv run python memory_reflect.py` in `.claude/scripts/`
3. Script loads yesterday's daily log and current MEMORY.md
4. Claude Agent SDK reviews the log and identifies items worth promoting
5. Claude uses Edit tool to update MEMORY.md directly (decisions, lessons, facts)
6. If nothing to promote → `REFLECTION_OK` logged to daily log

### State & Logs

- **State:** `.claude/data/state/reflection-state.json` - tracks `last_run`, days reviewed, result (per-machine)
- **Daily log:** `Fredis/Memory/daily/YYYY-MM-DD.md` - reflection entries appended here
- **Config:** `REFLECTION_HOUR` in `.env` (default: 8 AM)

---

## Direct Platform Integrations

The `direct-integrations` skill provides direct API access to Gmail, Calendar, Asana, Slack, Google Sheets, Google Docs, and Google Drive without going through Zapier MCP. **Always prefer direct integrations over Zapier.** The CLI wrapper lives at `.claude/scripts/query.py` (moved from the skill directory in Phase 4 so it sits sibling to `integrations/`).

### Usage

```bash
# Gmail
python .claude/scripts/query.py gmail list --max 5
python .claude/scripts/query.py gmail urgent --hours 2
python .claude/scripts/query.py gmail unread
python .claude/scripts/query.py gmail read <message_id>
python .claude/scripts/query.py gmail thread <thread_id>
python .claude/scripts/query.py gmail search "subject or query"
python .claude/scripts/query.py gmail attachments <message_id>
python .claude/scripts/query.py gmail download-attachment <message_id> --attachment-id <id> [--output-dir <path>]
python .claude/scripts/query.py gmail create-draft --from-file "Fredis/Memory/drafts/active/<draft>.md"
python .claude/scripts/query.py gmail create-draft --to "Name <email>" --subject "Re: Subject" --body "Reply text" --thread-id <thread_id> <message_id>

# Calendar
python .claude/scripts/query.py calendar today
python .claude/scripts/query.py calendar upcoming --hours 48
python .claude/scripts/query.py calendar soon

# Asana
python .claude/scripts/query.py asana my-tasks --max 10
python .claude/scripts/query.py asana my-tasks --assignee <name> --max 10
python .claude/scripts/query.py asana project <project_id>
python .claude/scripts/query.py asana overdue
python .claude/scripts/query.py asana due-soon --days 3
python .claude/scripts/query.py asana create --name "Task name" --due 2026-03-01 --project <project_id> --notes "Details"
python .claude/scripts/query.py asana comment <task_gid> --comment "Comment text"
python .claude/scripts/query.py asana complete <task_gid>
python .claude/scripts/query.py asana move <task_gid> --to-project <project_id> --from-project <project_id>

# Slack (`send` gated behind --i-confirm-send — advisor mode refuses otherwise)
python .claude/scripts/query.py slack channels
python .claude/scripts/query.py slack messages <channel> --hours 2
python .claude/scripts/query.py slack update <channel> "new text" --ts <message_ts>
python .claude/scripts/query.py slack check

# Google Sheets
python .claude/scripts/query.py sheets read <spreadsheet_id>
python .claude/scripts/query.py sheets read <spreadsheet_id> --range "Sheet1!A1:Z100"
python .claude/scripts/query.py sheets info <spreadsheet_id>
python .claude/scripts/query.py sheets write <spreadsheet_id> --range "A1" --values '[["a","b"]]'
python .claude/scripts/query.py sheets append <spreadsheet_id> --range "A:Z" --values '[["new","row"]]'

# Google Docs
python .claude/scripts/query.py docs read <document_id>
python .claude/scripts/query.py docs info <document_id>

# Google Drive
python .claude/scripts/query.py drive find "search term"
python .claude/scripts/query.py drive find "search term" --type spreadsheet
python .claude/scripts/query.py drive list --type document --max 10
python .claude/scripts/query.py drive get <file_id>

# Monday.com (read-only — GraphQL)
python .claude/scripts/query.py monday boards
python .claude/scripts/query.py monday board <board_id> --max 25
python .claude/scripts/query.py monday my-items --max 25
python .claude/scripts/query.py monday overdue
python .claude/scripts/query.py monday search --query "invoice"

# GitHub (read-only — REST)
python .claude/scripts/query.py github recent --hours 24
python .claude/scripts/query.py github review-requests
python .claude/scripts/query.py github mentions --hours 168
python .claude/scripts/query.py github ship
```

### Authentication

- **Gmail + Calendar + Sheets + Docs + Drive:** Google OAuth2 (shared token, `gmail.readonly` + `gmail.compose` + `calendar.readonly` + `spreadsheets` + `documents.readonly` + `drive.readonly` scopes)
- **Asana:** Personal Access Token in `.env` (`ASANA_ACCESS_TOKEN`)
- **Slack:** Bot Token in `.env` (`SLACK_BOT_TOKEN`)
- **Monday.com:** API v2 token in `.env` (`MONDAY_API_TOKEN`) — note: header is `Authorization: <token>`, NO `Bearer ` prefix. Board IDs in `MONDAY_BOARD_IDS` (Name:ID pairs), user ID in `MONDAY_USER_ID`.
- **GitHub:** PAT in `.env` (`GITHUB_TOKEN`, reused from the shared top-of-env var), username in `GITHUB_USERNAME`.
- **Setup:** `cd .claude/scripts && uv run python setup_auth.py`
- **Re-auth after scope changes:** Delete `google_token.json` and re-run `setup_auth.py`

### Key Details

All account IDs, project GIDs, and service preferences are in `Fredis/Memory/USER.md`. Refer there for specific values when running commands.

### Heartbeat Architecture

The heartbeat gathers data from all integrations in Python BEFORE invoking Claude:
```
heartbeat.py → Python calls APIs → snapshot + diff → guardrail check → results fed into Claude prompt → Claude reasons
```
Claude no longer needs Skill/MCP tools for heartbeat — data is pre-loaded as context. External data is wrapped in XML trust boundaries and checked for prompt injection before Claude sees it.

---

## Slack Chat Interface

Chat with the Second Brain through Slack DMs or @mentions. Each Slack thread is a separate, persistent conversation backed by the Agent SDK — survives restarts.

**Location:** `.claude/chat/`

**Start it:**
```bash
cd .claude/scripts && uv run python ../chat/main.py
```

**Test without connecting to Slack:**
```bash
cd .claude/scripts && uv run python ../chat/main.py --test
```

The process needs to stay running — it connects via Socket Mode (outbound WebSocket, no public URL needed). Run the start command in the background.

**How it works:** Slack event → platform-agnostic message → Agent SDK conversation (with full skills, memory, tools) → response posted back to the thread. Sessions stored in `.claude/data/chat.db`.

**Config:** `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` in `.claude/scripts/.env`. Only the authorized Slack user ID (see `USER.md` → Integrations) can trigger responses.

---

## Pre-Commit Workflow

Before committing changes under `.claude/scripts/`, run the lint, type, and
test checks. The baseline is clean (0 ruff errors, 0 mypy errors,
≥249 tests passing as of 2026-04-18) — keep it that way.

```bash
cd .claude/scripts
uv run ruff check .                         # 0 errors expected
uv run --with mypy mypy . --ignore-missing-imports  # 0 errors expected
uv run pytest tests/                        # all green expected
```

Notes:
- `heartbeat.py` has a per-file E501 ignore (see `pyproject.toml`) because
  it contains a 200-line Claude prompt template inside a triple-quoted
  string. Every other rule still applies.
- mypy is invoked with `--with mypy` because it isn't in the project's
  default dependency set; the dev extra (`pip install -e .[dev]`) declares
  it for editor integrations but the CLI invocation is self-contained.

---

## Legacy: MCP/Zapier (Fallback)

MCP servers available through the mcp-client skill (use only if direct integrations are unavailable):

- Zapier (Gmail, Asana, Google Calendar, Slack) — higher latency, uses Zapier quota
- Sequential Thinking (think deeply about something) - **Only use when explicitly requested**

Before looking up anything with a date, check the current date first.
