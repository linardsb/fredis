# Scripts & Chat Architecture

Subsystem deep-dives for code under `.claude/scripts/` and `.claude/chat/`. Auto-loads when Claude Code's cwd is at or below `.claude/scripts/`; NOT loaded by Agent SDK callers (heartbeat, chat, `memory_reflect`, `memory_synthesis`) which run with `cwd=PROJECT_ROOT` — they only see the root `/CLAUDE.md`.

For advisor-mode rules, skill routing, memory files, and hook boundaries, see the project root `CLAUDE.md`.

---

## Onboarding

First-run personalisation is a TUI + skill pair that converts the 103-question interview at `.agent/plans/phase1-onboarding-interview.md` into the five personalised memory files.

- **TUI:** `cd .claude/scripts && uv run python onboard.py [--tier core|rich|all] [--from A1] [--dry-run]`. One question per terminal screen with a multi-line `TextArea`. Answers are written back into the interview file in place — no sidecar state. `Ctrl+N` / `Ctrl+P` navigate, `Ctrl+S` saves and exits, `Ctrl+E` drops into `$EDITOR` for ★★★ long-form questions, `Ctrl+J` jumps to a section by letter, `Ctrl+Q` quits. Resumes automatically at the first unanswered question. Requires the `textual>=0.85.0` dep (already in `pyproject.toml`).
- **Trigger phrase:** say "phase 1 answers ready" (or "phase 1 complete" / "onboarding interview done") in any session. The `phase1-ready` skill (`.claude/skills/phase1-ready/`) reads the interview, drafts SOUL/USER/MEMORY/HABITS/HEARTBEAT, shows each draft for review, writes only after approval, scaffolds `Fredis/Memory/{research,competitors,retainers,case-studies}/`, appends a `## Addendum — Context Deltas` section to `.agent/plans/second-brain-prd.md`, and deletes `Fredis/Memory/BOOTSTRAP.md`. The skill's per-file mapping lives in `.claude/skills/phase1-ready/runbook.md`; the write-allowlist reference is `drafting_hook.py`.

---

## Heartbeat System (Proactive Second Brain)

The heartbeat is a scheduled script that proactively checks the user's draft inbox, HubSpot CRM scans (overdue invoices, silent contacts, stale deals), GitHub Projects lane kill-gate breaches, calendar, email, Slack, market/policy/AI research signals, and habit pillars using the Claude Agent SDK. It runs every 120 minutes during active hours (Europe/London, 05:00–20:00) and sends a Slack DM + native macOS notification when something needs attention.

Three scheduled modes share the same pipeline: the plain 2-hourly heartbeat, `--summary` (17:00 UK transparency recap, `fredis-summary.timer`), and `--brief` (07:00 UK morning brief, `fredis-brief.timer`). Summary and brief always produce a digest — never a silent `HEARTBEAT_OK` — and the 2-hourly cadence itself never changes. The active-drafts context also appends a stale-draft note (recursive scan of skill subfolders, threshold `STALE_DRAFT_DAYS`, default 14; `research/` and `memory-synthesis/` excluded) so long-lived drafts surface in the digest instead of rotting silently.

A deterministic companion, `meeting_prep.py` (`fredis-meeting-prep.timer`, every 10 min 05:00–20:00 UK), sends a Slack prep pack ~15 minutes before each calendar event — event details + memory-search hits for attendees + last Gmail thread. No Claude call; per-event dedupe state in `.claude/data/state/meeting-prep-state.json`.

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
3. `heartbeat.py` gathers data from Gmail, Calendar, Slack, HubSpot CRM, GitHub Projects (lanes), and GitHub (commits/PRs) via direct Python API calls
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

**False-positive guards (June 2026 incident).** `check_injection_patterns` strips the system's own line-exact `<external_data>` wrapper tags before scanning (the wrapper's closing tag used to flag `xml_escape_attempt` on every pass); the `dan_jailbreak` regex matches the upper-case acronym only (the name "Dan" in the guardrail's own abort entries re-triggered it daily); and reflection/synthesis abort entries log pattern names only, never the matched text. Any reflection/synthesis abort or crash also fires a Slack alert via `notifications.send_loop_failure_alert` — the memory loops never fail silently again.

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

The `direct-integrations` skill provides direct API access to Gmail, Calendar, Slack, Google Sheets, Google Docs, and Google Drive without going through Zapier MCP. **Always prefer direct integrations over Zapier.** The CLI wrapper lives at `.claude/scripts/query.py` (moved from the skill directory in Phase 4 so it sits sibling to `integrations/`).

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

# HubSpot CRM — reads (REST)
python .claude/scripts/query.py hubspot contacts --max 10
python .claude/scripts/query.py hubspot companies --max 10
python .claude/scripts/query.py hubspot deals --max 10 [--stage <stage_id>]
python .claude/scripts/query.py hubspot overdue-invoices
python .claude/scripts/query.py hubspot silent-contacts
python .claude/scripts/query.py hubspot stale-deals
python .claude/scripts/query.py hubspot search --query "example.com"
python .claude/scripts/query.py hubspot pipelines
python .claude/scripts/query.py hubspot properties contacts

# HubSpot CRM — writes (internal CRM mutations only — Advisor-mode allows direct writes)
# Contacts / companies / deals
python .claude/scripts/query.py hubspot create-contact --email tim@walking.vc [--firstname Tim] [--lastname Jackson] [--phone P] [--company-domain walking.vc] [--urgent true|false] [--conflict true|false] [--conflict-reason "..."] [--preferred-channel email|whatsapp|slack|facebook_dm] [--lifecyclestage lead|...]
python .claude/scripts/query.py hubspot update-contact <id|email> [--urgent ...] [--phone ...] [--firstname ...] [--lifecyclestage ...]
python .claude/scripts/query.py hubspot archive-contact <id|email>
python .claude/scripts/query.py hubspot create-company --name "..." --domain D [--engagement retainer|project|prospect|dormant] [--retainer-gbp N] [--contract-end YYYY-MM-DD]
python .claude/scripts/query.py hubspot update-company <id|domain> [...]
python .claude/scripts/query.py hubspot archive-company <id|domain>
python .claude/scripts/query.py hubspot create-deal --name "..." --amount N --stage <label> [--pipeline Consultancy] [--currency GBP|EUR|USD] [--contact-email X] [--company-domain D] [--service-line ai_agentic|custom_app|saas|marketing_ops|agri_ai|advisory] [--source cold|inbound|referral|content] [--close-date YYYY-MM-DD] [--probability 0..1]
python .claude/scripts/query.py hubspot move-deal <id> --to-stage <label>
python .claude/scripts/query.py hubspot update-deal <id> [--amount N] [--close-date ...] [--probability ...] [--service-line ...] [--source ...]
python .claude/scripts/query.py hubspot close-deal <id> --as won|lost
python .claude/scripts/query.py hubspot archive-deal <id>
# Engagements (logging — never sends external comms)
python .claude/scripts/query.py hubspot add-note --about <type>:<id|key> --text "..."
python .claude/scripts/query.py hubspot create-task --about <type>:<id|key> --title "..." --due YYYY-MM-DD [--notes "..."] [--status not_started|in_progress|waiting|completed]
python .claude/scripts/query.py hubspot log-call --with contact:<id|email> --summary "..." [--duration-min N] [--disposition "..."] [--direction in|out]
python .claude/scripts/query.py hubspot log-meeting --with contact:<id|email> --title "..." --start <iso> --end <iso> [--notes "..."]
python .claude/scripts/query.py hubspot log-email --with contact:<id|email> --subject "..." --direction in|out --sent-at <iso> [--body "..."]
# Associations
python .claude/scripts/query.py hubspot associate --from <type>:<id|key> --to <type>:<id|key> [--type-id N]
python .claude/scripts/query.py hubspot unassociate --from <type>:<id> --to <type>:<id>
# Tickets — Fredis Review queue (unified review inbox; heartbeat auto-creates + posts to #hubspot)
python .claude/scripts/query.py hubspot create-ticket --subject "..." [--lane email_hub|vtv|cab|content|ops|client|admin] [--urgency today|this_week|whenever] [--skill <name>] [--draft-path "Fredis/Memory/drafts/active/<skill>/<file>.md"] [--contact-id <id>] [--company-id <id>] [--deal-id <id>] [--content "..."]
python .claude/scripts/query.py hubspot get-ticket <ticket_id>
python .claude/scripts/query.py hubspot move-ticket <ticket_id> --to-stage "Drafted|In review|Needs send"
python .claude/scripts/query.py hubspot close-ticket <ticket_id> --as actioned|rejected [--note "..."]
python .claude/scripts/query.py hubspot list-tickets [--lane ...] [--urgency ...] [--max N]
python .claude/scripts/query.py hubspot queue   # shortcut: open tickets grouped by urgency

# GitHub Projects v2 — Lanes & Features (read-only — GraphQL)
python .claude/scripts/query.py lanes list
python .claude/scripts/query.py lanes breached

# GitHub (read-only — REST)
python .claude/scripts/query.py github recent --hours 24
python .claude/scripts/query.py github review-requests
python .claude/scripts/query.py github mentions --hours 168
python .claude/scripts/query.py github ship
```

### Authentication

- **Gmail + Calendar + Sheets + Docs + Drive:** Google OAuth2 (shared token, `gmail.readonly` + `gmail.compose` + `calendar.readonly` + `spreadsheets` + `documents.readonly` + `drive.readonly` scopes)
- **Slack:** Bot Token in `.env` (`SLACK_BOT_TOKEN`)
- **HubSpot CRM:** Private App token in `.env` (`HUBSPOT_API_TOKEN`) — header is `Authorization: Bearer <token>`. Rate limit: 110 req/10s + 250k/day. Hub ID in `HUBSPOT_HUB_ID`. Heartbeat scans gated on `HUBSPOT_SCANS_ENABLED=true`.
- **GitHub Projects v2:** Reuses `GITHUB_TOKEN` (GraphQL only — REST doesn't cover v2 Projects). Set `GITHUB_PROJECT_LANES_ID` to the project's node id.
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

The process needs to stay running — it connects via Socket Mode (outbound WebSocket, no public URL needed). For local use, run the start command in the background. On the VPS it runs as `secondbrain-chat.service` (systemd, `Restart=always`); unit file tracked at `.claude/scripts/schedule/secondbrain-chat.service`, install instructions in README §10.

**How it works:**

1. **Socket Mode** — uses `SLACK_BOT_TOKEN` + `SLACK_APP_TOKEN` you already have. No public URL or ngrok needed. The bot connects outbound to Slack via WebSocket.
2. **Message routing** — listens for DMs and @mentions. Sessions are keyed by `platform:channel_id:thread_ts`, so each Slack thread maps to one Agent SDK conversation. A top-level DM (no thread) uses `channel_id` as the thread id, so the whole DM stays one continuous session; replying inside a thread spawns a separate one.
3. **Persistent sessions** — `chat.db` stores the mapping of `platform:channel:thread` → Agent SDK `session_id`, so conversations survive bot restarts and long gaps. The engine passes `resume=agent_session_id` into `ClaudeAgentOptions` on the next message and the SDK rehydrates full history.
4. **Bot capabilities** — anything the second brain can do today:
   - Memory search ("What did we decide about X?")
   - Integration queries ("Any overdue HubSpot invoices?", "Check my email")
   - Draft review ("Show active drafts", "Approve the draft for John")
   - Habit check-ins ("Mark God as done", "How are my habits?")

**Config:** `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` in `.claude/scripts/.env`. Only the authorized Slack user ID (see `USER.md` → Integrations) can trigger responses.

### Per-Channel Scoping (Tools / MCP / Skills)

Each Slack channel exposes only the tools, MCP servers, and skills relevant to its work. Reduces per-turn context floor and prevents the model from invoking, say, `Bash` in `#legal` or the `engineering` skill in `#gmail`.

- **Config:** `.claude/config/channel-routing.yaml` under `tools:`, `mcp_servers:`, `skills:`. Resolvers live in `channel_router.py:resolve_tools/resolve_mcp_servers/resolve_skills`.
- **Always-on base palette:** `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Skill` — every channel including DMs.
- **DMs:** universal surface — full tool palette, every MCP server, every skill (`skills.defaults.dm: ALL`).
- **Skills enforcement is prompt-level**, not a hard SDK filter. The SDK has no clean per-call skill-discovery override (`setting_sources` only accepts the `user|project|local` enum, not arbitrary paths). The engine appends a `# Skill scope (per-channel)` rule to the system prompt naming the allowed subset; non-listed skills must be refused with a redirect to DMs.
- **Tools and MCP servers ARE hard-filtered** via `allowed_tools` and `mcp_servers` on `ClaudeAgentOptions` — these are real SDK gates.
- **Per-turn observability:** every turn logs `[scoping] channel=#X model=Y tools=N mcp=N skills=N` to stdout. Grep chat logs to verify scoping took effect.

**Kill switch.** Set `scoping_enabled: false` at the top level of `channel-routing.yaml` to revert every channel to the legacy "everything everywhere" behaviour without a code revert. Restart the chat engine to pick up the change. Use this for emergency rollback if scoping breaks a channel.

**Adding a new MCP server.** Register the server in `mcp_tools.py:_SERVER_SPECS`, then add its name to the relevant `mcp_servers.by_channel` lists in YAML. The engine picks up the registry at startup; per-channel mounts are computed per turn.

**Promoting/demoting a channel's model.** Add or remove the channel name under `models.opus` / `models.haiku` in YAML. Default is Sonnet. Concrete model IDs are pinned in `channel_router.MODEL_IDS` (intentionally code-side so version pins go through review).

### Thread Degradation Nudges (Phase A)

Long Slack threads degrade as context fills — the SDK eventually auto-compacts older turns into a lossy summary, and "lost in the middle" effects mean Fredis attends less reliably to mid-thread content even before that. Phase A surfaces this passively: each turn the engine reads the latest `ResultMessage.usage` and appends a one-line markdown italic to the outgoing Slack reply when the thread first crosses a soft or hard threshold. The nudge text is **not** persisted to the SDK conversation history — the model never sees its own nudge on the next turn (so it can't echo or treat it as an instruction).

| Tier | Turn count OR | Tokens | Nudge wording |
|---|---|---|---|
| Soft | ≥ 30 | ≥ 120 000 | _say "consolidate" when you want me to lock canon to a file before context gets noisy_ |
| Hard | ≥ 50 | ≥ 180 000 | _context is now degrading. Strongly recommend "consolidate" before the next round of work._ |

- **Token metric:** `input_tokens + cache_read_input_tokens + cache_creation_input_tokens` from the latest turn's usage — the *current* attention surface, not a running sum (each resumed turn's input already includes prior turns once).
- **Single-fire guarantee:** `chat_sessions.nudged_soft_at` and `nudged_hard_at` are ISO timestamps set the first time each tier fires for a thread. A hard fire from cold (no prior soft) consumes the soft slot too so soft can't fire afterwards.
- **Where it's wired:** `engine.py:compute_thread_nudge` (pure decision function, fully unit-tested in `tests/test_chat_thread_nudge.py`); persisted via `Session.last_turn_context_tokens` / `nudged_soft_at` / `nudged_hard_at` (`session.py`).
- **Per-turn observability:** `[thread-nudge] tier=<soft|hard> turns=N tokens=N` printed to stdout the turn a nudge fires. Grep chat logs to verify firing is happening (or not, when you'd expect it).
- **Tuning the thresholds:** edit `NUDGE_SOFT_TURNS / NUDGE_SOFT_TOKENS / NUDGE_HARD_TURNS / NUDGE_HARD_TOKENS` constants at the top of `engine.py`. Restart the chat engine to pick up the change. Phase B (`/consolidate` directive) is gated on observing these in production for 3+ days before tuning.

---

## Pre-Commit Workflow

Before committing changes under `.claude/scripts/`, run the lint, type, and
test checks. The baseline is clean (0 ruff errors, 0 mypy errors,
≥770 tests passing as of 2026-04-23) — keep it that way.

```bash
cd .claude/scripts
uv run ruff check .                         # 0 errors expected
uv run --with mypy --with types-requests --with types-PyYAML mypy . --ignore-missing-imports  # 0 errors expected
uv run pytest tests/                        # all green expected
```

Notes:
- `heartbeat.py` has a per-file E501 ignore (see `pyproject.toml`) because
  it contains a 200-line Claude prompt template inside a triple-quoted
  string. Every other rule still applies.
- mypy is invoked with `--with mypy --with types-requests --with types-PyYAML` because
  these aren't in the project's default runtime dependency set; they're declared
  under the dev extra (`pip install -e .[dev]`) for editor integrations, but the
  CLI invocation is self-contained so Claude / CI can run it without `uv sync --extra dev`.
- Third-party HTTP/YAML lib stubs are required because `--ignore-missing-imports`
  silences `[import-not-found]` but NOT `[import-untyped]` (module found, stubs
  missing). Without the stubs, mypy flags `import requests` / `import yaml` as
  untyped and `# type: ignore[import-untyped]` becomes a needed crutch.

---

## CI & Local Fallback

`.github/workflows/ci.yml` runs the same trio (ruff, mypy, pytest) on every push/PR that touches `.claude/scripts/**`, `.claude/chat/**`, or the workflow itself — vault-sync commits never trigger it. The local mirror is `bash .claude/scripts/check.sh`.

When GitHub Actions is unavailable (billing/quota — detected as the most recent completed run having executed zero steps), the pre-push hook runs `check.sh` locally before allowing a code push; vault-only pushes always skip instantly. Ported from merkle-email-hub `scripts/ci-local-fallback.sh`. Bypass with `git push --no-verify`; force with `LOCAL_CI=1`, skip with `LOCAL_CI=0`. Install once per dev machine:

```bash
cp .claude/scripts/ci-local-fallback.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push
```

---

## Threat Models

Per-agent threat models colocated with code at `.claude/scripts/threat-models/` — one page per SDK caller (`heartbeat.md`, `chat.md`, `reflection.md`, `memory_flush.md`) using the §7 checklist from `.claude/skills/security-engineering/references/agent-guardrails.md`. Revisit when `allowed_tools` changes, a new integration is added to the gather path, or a new hook is registered. Start with the README index.

---

## Secrets Management

Token rotation procedures for every secret in `.env.example` live at `.claude/scripts/schedule/rotation-runbooks.md`. Rotate on a 90-day cadence or immediately on suspected leak. The runbook covers Slack bot / app tokens, Anthropic / GitHub / HubSpot PATs, Google OAuth (refresh token + client secret rotation paths), Postgres password, and SSH keys (VPS + vault git remote).

---

## Dependency Audit (Phase 9.5)

Weekly `pip-audit` + `safety check` run via `.claude/scripts/deps_audit.py` (wrapper: `run_deps_audit.sh` / `.bat`). Results append to today's daily log under `## Memory Maintenance` → `### Dependency Audit`. Scheduler units live under `.claude/scripts/schedule/`:

- **macOS** — `com.linards.fredis-deps-audit.plist` (launchd, every Monday 09:00 local). Install by copying to `~/Library/LaunchAgents/` and `launchctl load`.
- **Linux VPS** — `deps-audit.service` + `deps-audit.timer` (systemd, `OnCalendar=Mon *-*-* 09:00:00`). Install into `/etc/systemd/system/` and `systemctl enable --now deps-audit.timer`.

Non-zero exit on any HIGH/CRITICAL finding so the scheduler surfaces the alert.

---

## Legacy: MCP/Zapier (Fallback)

MCP servers available through the mcp-client skill (use only if direct integrations are unavailable):

- Zapier (Gmail, Google Calendar, Slack) — higher latency, uses Zapier quota
- Sequential Thinking (think deeply about something) - **Only use when explicitly requested**
