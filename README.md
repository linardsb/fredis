# Second Brain — Personal AI Assistant on Claude Code

A proactive AI assistant built on Claude Code that monitors your email, calendar, tasks (Asana + Monday.com), Slack, and GitHub activity. It runs scheduled heartbeats, maintains long-term memory across sessions, manages drafts, tracks habits, and can respond to chat via Slack DMs. Everything is configurable — use the integrations you want, skip the ones you don't.

> **This is my personal system** — not a framework to install and run as-is. The skills, brand references, and workflow patterns are tuned to my content creation process. The goal is for you to see the architecture and patterns, then build something that's truly yours. Each piece (memory, hooks, heartbeat, integrations) is independently useful.

### Want to Build Your Own?

This repo is a reference implementation rather than a framework to install and run. To build your own Second Brain, clone or fork it, then work through the phases in `.agent/plans/second-brain-prd.md` — tweaking each piece for your own stack, integrations, and preferences. The memory scaffolding, hooks, heartbeat loop, and integration adapters are independently reusable.

## What It Does

- **Proactive heartbeats** — Checks email, calendar, tasks (Asana + Monday.com), and Slack on a schedule. Sends a Slack DM + native desktop notification when something needs your attention.
- **Long-term memory** — Remembers decisions, preferences, and context across sessions via markdown files in an Obsidian vault (synced via Git between machines).
- **Hybrid memory search** — Find anything in your memory with keyword + semantic vector search. Fully local, no API calls. Scope searches to specific folders (sent drafts, daily logs, etc.) for voice-matching when drafting replies.
- **Chat interface** — Talk to your Second Brain through Slack DMs or @mentions. Each thread is a separate persistent conversation backed by the Agent SDK.
- **Daily reflection** — Automatically reviews daily logs and promotes important items to long-term memory.
- **Draft management** — Tracks email and message drafts through active, sent, and expired states so nothing falls through the cracks.
- **Habit tracking** — Monitors recurring habits defined in `HABITS.md` and surfaces reminders during heartbeat runs.
- **Heartbeat thread replies** — Slack thread replies to heartbeat alerts open a full conversation with the assistant in context.
- **Security guardrail** — Two-stage prompt injection defense (deterministic pattern matching + LLM semantic evaluation) checks all external data before it reaches the main agent. 3-layer sanitization with XML trust boundaries.
- **State diffing** — Heartbeat snapshots integration data between runs so only new/changed items are surfaced — no repeat alerts.
- **Vault sync** — Git-based sync between machines with a custom merge driver that auto-resolves daily log conflicts.
- **Onboarding conversation** — On first run, Claude interviews you to personalize memory files, heartbeat checks, and communication style.

## Architecture Overview

| Component | Location | Purpose |
|-----------|----------|---------|
| **Memory files** | `Fredis/Memory/` | SOUL.md, USER.md, MEMORY.md, daily logs (synced via Git) |
| **Heartbeat** | `.claude/scripts/heartbeat.py` | Scheduled check of email, calendar, Asana + Monday.com tasks, Slack |
| **Memory search** | `.claude/scripts/memory_search.py` | Hybrid keyword + vector search over memory |
| **Chat interface** | `.claude/chat/main.py` | Slack DM/mention handler using Agent SDK |
| **Integrations** | `.claude/scripts/integrations/` | Gmail, Calendar, Asana, Slack, Sheets, Docs, Drive wrappers |
| **Integration registry** | `.claude/scripts/integrations/registry.py` | Discovers which integrations are configured |
| **Draft management** | `Fredis/Memory/drafts/` | Active, sent, and expired draft tracking |
| **Habit tracking** | `Fredis/Memory/HABITS.md` | Recurring habit checklist surfaced during heartbeats |
| **Database** | SQLite (local) or Postgres (VPS) | Search index + chat sessions |
| **State files** | `.claude/data/state/` | Per-machine operational state (not synced) |
| **Sanitization** | `.claude/scripts/sanitize.py` | 3-layer prompt injection defense (pattern detection, markdown escaping, XML wrapping) |
| **Vault sync** | `.claude/scripts/git-sync` | Git-based vault sync with custom merge driver for daily logs |

## Quick Start (Local)

### Prerequisites

- Python 3.12+
- [UV](https://docs.astral.sh/uv/) (Python package manager)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (logged in)

### 1. Clone and Configure

```bash
git clone https://github.com/linardsb/fredis.git
cd fredis

# Create your master env file
cp master.env.example master.env
# Edit master.env — fill in your API keys and IDs (see Configuration Reference below)

# Run workspace setup
python setup_workspace.py
```

`setup_workspace.py` runs four steps:

1. Reads your `master.env`
2. Clones companion repositories (content-engine, video-processor, obsidian-ai-agent) — skips any that fail (they're optional)
3. Writes `.env` files to each project from your `master.env`
4. Generates platform-specific Claude Code hooks in `.claude/settings.local.json`

### 2. Install Dependencies

```bash
cd .claude/scripts
uv sync
```

### 3. Personalize the Memory Layer

The memory files under `Fredis/Memory/` (`SOUL.md`, `USER.md`, `MEMORY.md`, `HEARTBEAT.md`, `HABITS.md`) are the agent's long-term context — edit them directly with your name, timezones, integration IDs, and voice.

For a guided fill-in, run the onboarding TUI against the 103-question interview at `.agent/plans/phase1-onboarding-interview.md`:

```bash
cd .claude/scripts && uv run python onboard.py
```

Once you've answered the interview, say `phase 1 answers ready` in a Claude Code session and the `phase1-ready` skill drafts the five memory files from your answers (see `.claude/skills/phase1-ready/` for details).

### 4. Choose Your Integrations

All integrations are optional. Configure the ones you want — the system detects what's available via the integration registry and automatically skips unconfigured ones.

| Integration | Config Needed | Auth Type | What It Does |
|-------------|--------------|-----------|--------------|
| Gmail | Google OAuth credentials file | Google OAuth | Read emails, check for urgent messages |
| Google Calendar | `GOOGLE_CALENDAR_ID` + OAuth | Google OAuth | Check today's events, upcoming meetings |
| Asana | `ASANA_ACCESS_TOKEN` | Personal Access Token | Track tasks, create/comment/move tasks |
| Slack | `SLACK_BOT_TOKEN` | Bot Token | Monitor channels, send notifications, chat interface |
| Google Sheets | Google OAuth credentials file | Google OAuth | Read/write spreadsheets |
| Google Docs | Google OAuth credentials file | Google OAuth | Read documents |
| Google Drive | Google OAuth credentials file | Google OAuth | Search and list files |

**Google integrations** (Gmail, Calendar, Sheets, Docs, Drive) share a single OAuth token. Set up once, access all five.

```bash
cd .claude/scripts
uv run python setup_auth.py           # Walk through auth for each integration
uv run python setup_auth.py --check   # Verify without re-authenticating
```

### 5. Test

```bash
cd .claude/scripts
uv run python heartbeat.py --test           # Test heartbeat (no notifications sent)
uv run python memory_index.py --rebuild     # Build the search index (~80MB model download on first run)
uv run python memory_search.py "test"       # Test search
```

### 6. Schedule the Heartbeat

**Windows** — run PowerShell as Admin:
```powershell
& ".claude\scripts\setup_scheduler.ps1"
```

<details>
<summary>macOS / Linux setup</summary>

**macOS** — create `~/Library/LaunchAgents/com.secondbrain.heartbeat.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.secondbrain.heartbeat</string>
    <key>ProgramArguments</key>
    <array><string>/path/to/fredis/.claude/scripts/run_heartbeat.sh</string></array>
    <key>StartInterval</key><integer>7200</integer>
    <key>RunAtLoad</key><true/>
</dict>
</plist>
```

```bash
chmod +x .claude/scripts/run_heartbeat.sh
# Update the path in the plist above, then:
launchctl load ~/Library/LaunchAgents/com.secondbrain.heartbeat.plist
```

**Linux** — add a cron job:
```bash
chmod +x .claude/scripts/run_heartbeat.sh
(crontab -l 2>/dev/null; echo "0 */2 * * * /path/to/fredis/.claude/scripts/run_heartbeat.sh") | crontab -
```

</details>

### 7. Schedule Vault Sync (Optional — for multi-machine setups)

If you run your Second Brain on multiple machines (e.g., local PC + VPS), set up vault sync to keep the Obsidian vault in sync via Git:

**Windows:**
```powershell
& ".claude\scripts\setup_vault_sync.ps1"
```

**Linux:**
```bash
chmod +x .claude/scripts/run_vault_sync.sh
# Runs every 2 minutes via systemd timer or cron
```

The sync uses git-sync with a custom merge driver that auto-resolves daily log conflicts by concatenating both sides.

### 8. Schedule the Daily Reflection (Optional)

**Windows** — run PowerShell as Admin:
```powershell
& ".claude\scripts\setup_reflect_scheduler.ps1"
```

<details>
<summary>macOS / Linux setup</summary>

**macOS** — create `~/Library/LaunchAgents/com.secondbrain.reflection.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.secondbrain.reflection</string>
    <key>ProgramArguments</key>
    <array><string>/path/to/fredis/.claude/scripts/run_reflect.sh</string></array>
    <key>StartCalendarInterval</key>
    <dict><key>Hour</key><integer>8</integer><key>Minute</key><integer>0</integer></dict>
</dict>
</plist>
```

```bash
chmod +x .claude/scripts/run_reflect.sh
launchctl load ~/Library/LaunchAgents/com.secondbrain.reflection.plist
```

**Linux:**
```bash
chmod +x .claude/scripts/run_reflect.sh
(crontab -l 2>/dev/null; echo "0 8 * * * /path/to/fredis/.claude/scripts/run_reflect.sh") | crontab -
```

</details>

---

## Personalizing Your Second Brain

### Memory Files

Your Second Brain's personality and knowledge live in `Fredis/Memory/`. The onboarding conversation fills in the essentials. You can also edit these files directly at any time:

| File | Purpose |
|------|---------|
| `SOUL.md` | The AI's personality, values, and behavioral guidelines. Defines *how* it communicates. |
| `USER.md` | Information about you — projects, preferences, team, integrations, account IDs. |
| `MEMORY.md` | Long-term memory. Decisions, lessons learned, important facts. Grows over time. |
| `HEARTBEAT.md` | Checklist for heartbeat runs. Add or remove checks based on what you want monitored. |
| `HABITS.md` | Recurring habits the assistant tracks and surfaces during heartbeat runs. |
| `drafts/active/` | In-progress email and message drafts. |
| `drafts/sent/` | Sent drafts (used for voice-matching when drafting future replies). |
| `drafts/expired/` | Drafts that were never sent and have passed `DRAFT_EXPIRY_HOURS`. |
| `daily/` | Daily log entries. Heartbeat results, session summaries, and reflections are appended here. |

### Adding and Removing Integrations

Integrations are controlled by your `.env` file. To add one:
1. Set the required env vars in `.claude/scripts/.env`
2. Run `uv run python setup_auth.py` for OAuth-based integrations
3. Run `uv run python setup_auth.py --check` to verify all integrations

To remove one, clear its env vars. The integration registry and heartbeat automatically skip unconfigured integrations.

<details>
<summary>Memory search CLI examples</summary>

```bash
cd .claude/scripts

# Hybrid search (recommended — combines keyword + semantic)
uv run python memory_search.py "query"

# Specific modes
uv run python memory_search.py "query" --mode keyword     # Fast, exact matches
uv run python memory_search.py "query" --mode semantic    # Conceptual similarity
uv run python memory_search.py "query" --mode hybrid      # Weighted: 0.7 vector + 0.3 keyword

# Scoped search — filter by folder prefix
uv run python memory_search.py "topic" --path-prefix drafts/sent    # Voice-match against sent drafts
uv run python memory_search.py "topic" --path-prefix daily/         # Search daily logs only
uv run python memory_search.py "topic" --mode hybrid --limit 5

# Utilities
uv run python memory_index.py --stats       # File/chunk/vector counts
uv run python memory_index.py --rebuild     # Force full reindex
```

</details>

<details>
<summary>Direct integrations CLI reference</summary>

The `direct-integrations` skill gives Claude (and you) a CLI for querying all integrations directly. This is the same data source the heartbeat uses — you can run any of these ad hoc:

```bash
# Gmail
python .claude/scripts/query.py gmail list --max 5
python .claude/scripts/query.py gmail urgent --hours 2
python .claude/scripts/query.py gmail unread
python .claude/scripts/query.py gmail read <message_id>

# Calendar
python .claude/scripts/query.py calendar today
python .claude/scripts/query.py calendar upcoming --hours 48
python .claude/scripts/query.py calendar soon

# Asana — read and write
python .claude/scripts/query.py asana my-tasks --max 10
python .claude/scripts/query.py asana my-tasks --assignee <name> --max 10
python .claude/scripts/query.py asana project <project_id>
python .claude/scripts/query.py asana overdue
python .claude/scripts/query.py asana overdue --assignee <name>
python .claude/scripts/query.py asana due-soon --days 3
python .claude/scripts/query.py asana create --name "Task name" --due 2026-03-01 --assignee <name> --project <project_id> --notes "Details"
python .claude/scripts/query.py asana comment <task_gid> --comment "Comment text"
python .claude/scripts/query.py asana complete <task_gid>
python .claude/scripts/query.py asana move <task_gid> --to-project <project_id> --from-project <project_id>

# Slack (read-only; `send` is gated behind --i-confirm-send — advisor mode)
python .claude/scripts/query.py slack channels
python .claude/scripts/query.py slack messages <channel> --hours 2
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

</details>

---

<details>
<summary>VPS Deployment</summary>

Deploy to a VPS for a persistent Second Brain that runs when your PC is off. Uses Postgres instead of SQLite and runs the Slack chat bot as a systemd service.

### Prerequisites

A VPS running Ubuntu (or similar) with Docker installed.

```bash
sudo apt update && sudo apt install -y build-essential
```

### 1. Install UV

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv --version
```

### 2. Install Claude Code CLI

```bash
curl -fsSL https://claude.ai/install.sh | bash
source $HOME/.local/bin/env
claude --version
```

### 3. Log in to Claude Code

```bash
claude
# Follow the OAuth prompt in your browser.
# If headless (no local browser on the VPS), use an API key instead:
# export ANTHROPIC_API_KEY=sk-ant-...
```

Once authenticated, credentials are stored in `~/.claude/.credentials.json`. The heartbeat and Slack bot use these automatically — no API key needed in normal operation.

### 4. Set Up Git SSH Access

```bash
ssh-keygen -t ed25519 -C "vps-secondbrain"
cat ~/.ssh/id_ed25519.pub    # Add this to GitHub: Settings -> SSH and GPG keys -> New SSH key
eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519
echo -e '\neval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519' >> ~/.bashrc
```

### 5. Clone and Configure

```bash
git clone https://github.com/linardsb/fredis.git
cd fredis
cp master.env.example master.env
# Fill in your API keys and IDs
python3 setup_workspace.py
```

After setup, run `claude` to start the onboarding conversation (same as local — see Quick Start step 3 above).

### 6. Start Postgres and Obsidian

```bash
# Fix permissions for the vault mount (Docker creates it as root otherwise)
mkdir -p ./Fredis
sudo chown -R 1000:1000 ./Fredis

docker compose up -d
```

This starts two services:
- **Postgres 17 + pgvector** on `127.0.0.1:5432` (search index and chat sessions)
- **Headless Obsidian** on port `8080` (for vault sync via the Obsidian UI)

The Obsidian UI is bound to localhost only. Access it via SSH tunnel from your local machine:
```bash
ssh -N -L 8080:localhost:8080 user@your-vps
```

Then open `https://localhost:8080` in your browser (accept the self-signed certificate), open `/Fredis` as a vault, and enable Obsidian Sync to connect your remote vault.

### 7. Configure the Database

```bash
echo 'DATABASE_URL=postgresql://secondbrain:changeme@localhost:5432/secondbrain' >> .claude/scripts/.env
```

### 8. Install Dependencies and Build the Search Index

```bash
cd .claude/scripts
uv sync
uv run python setup_auth.py              # Google OAuth + verify integrations
uv run python memory_index.py --rebuild  # Index vault into Postgres
```

For Google OAuth on a headless VPS:
```bash
uv run python setup_auth.py --headless
```

### 9. Schedule the Heartbeat

```bash
chmod +x .claude/scripts/run_heartbeat.sh
(crontab -l 2>/dev/null; echo "0 */2 * * * $(pwd)/.claude/scripts/run_heartbeat.sh") | crontab -
```

> **Note:** Cron uses a minimal `PATH`. The `run_heartbeat.sh` script adds `~/.local/bin` to `PATH` for `uv`. If your `uv` is installed elsewhere, update the `export PATH` line in that script accordingly.

### 10. Start the Slack Chat Bot as a Persistent Service

Create the systemd service file:

```
[Unit]
Description=Second Brain Slack Chat Bot
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/fredis/.claude/scripts
ExecStart=/root/.local/bin/uv run python ../chat/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save to `/etc/systemd/system/secondbrain-chat.service`, update the `WorkingDirectory` path to match your install location, then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable secondbrain-chat
sudo systemctl start secondbrain-chat
sudo systemctl status secondbrain-chat
```

View logs:
```bash
sudo journalctl -u secondbrain-chat -f
```

### Managing Schedulers on the VPS

```bash
# Heartbeat (cron)
crontab -l | grep heartbeat    # View
crontab -e                     # Edit or remove

# Chat service (systemd)
sudo systemctl status secondbrain-chat
sudo systemctl restart secondbrain-chat
sudo systemctl stop secondbrain-chat
```

</details>

<details>
<summary>PC to VPS: Persistent SSH Tunnel (Windows)</summary>

Share the VPS Postgres with your local PC so both use the same search index and chat history:

```powershell
# Run PowerShell as Admin — update the key path and VPS IP
$action = New-ScheduledTaskAction -Execute "ssh.exe" `
    -Argument "-N -i C:\Users\you\.ssh\your_key -L 5432:localhost:5432 root@your-vps-ip"
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
Disable-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel"    # pause
Unregister-ScheduledTask -TaskName "SecondBrain-SSH-Tunnel" # remove
```

Then add to your local `.claude/scripts/.env`:
```
DATABASE_URL=postgresql://secondbrain:changeme@localhost:5432/secondbrain
```

Local Claude Code sessions, memory search, and the heartbeat will all use the VPS Postgres.

</details>

<details>
<summary>Configuration Reference</summary>

All variables go in `.claude/scripts/.env`. When using `setup_workspace.py`, set them in `master.env` using the prefixed names from `master.env.example`.

### Required

| Variable | Description |
|----------|-------------|
| `OWNER_NAME` | Your name — used in heartbeat prompts to personalize Claude's reasoning |

### Heartbeat

| Variable | Default | Description |
|----------|---------|-------------|
| `HEARTBEAT_INTERVAL_MINUTES` | `120` | Minutes between heartbeat runs |
| `HEARTBEAT_ACTIVE_HOURS_START` | `05:00` | Don't run before this time (24h format) |
| `HEARTBEAT_ACTIVE_HOURS_END` | `20:00` | Don't run after this time (24h format) |
| `HEARTBEAT_TIMEZONE` | `Europe/London` | Timezone for active hours (IANA format, e.g. `America/New_York`) |
| `REFLECTION_HOUR` | `8` | Hour to run daily reflection (0–23) |
| `DRAFT_EXPIRY_HOURS` | `24` | Hours before an unsent active draft is moved to expired |
| `EXPIRED_DRAFT_RETENTION_DAYS` | `7` | Days before expired drafts are permanently deleted |

### Google (shared OAuth token)

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_CALENDAR_ID` | | Calendar ID to read events from (usually your email address) |

Google OAuth also requires `google_credentials.json` in `.claude/scripts/integrations/`. Download from the Google Cloud Console (OAuth 2.0 Client ID, Desktop app type). Run `uv run python setup_auth.py` to complete the OAuth flow. Scopes: `gmail.readonly`, `gmail.compose`, `calendar.readonly`, `spreadsheets`, `documents.readonly`, `drive.readonly`.

### Asana

| Variable | Default | Description |
|----------|---------|-------------|
| `ASANA_ACCESS_TOKEN` | | Personal Access Token from the Asana developer console |
| `ASANA_WORKSPACE_ID` | | Workspace GID (from Asana URL or API) |
| `ASANA_PROJECT_ID` | | Default project GID (used when creating tasks without specifying a project) |
| `ASANA_USERS` | | Friendly name to GID mapping for assignees (format: `name:gid,name:gid`) |

### Slack

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_BOT_TOKEN` | | Bot User OAuth Token (`xoxb-...`) |
| `SLACK_APP_TOKEN` | | App-Level Token for Socket Mode (`xapp-...`) |
| `SLACK_OWNER_USER_ID` | | Your Slack user ID — used for @mention filtering and heartbeat thread reply detection |
| `SLACK_NOTIFICATION_CHANNEL` | | Channel where heartbeat alerts are posted (e.g. `#second-brain`) |
| `SLACK_MONITORED_CHANNELS` | | Comma-separated channel names to read during heartbeats |

### Chat Interface

| Variable | Default | Description |
|----------|---------|-------------|
| `CHAT_ALLOWED_USERS` | `SLACK_OWNER_USER_ID` | Comma-separated Slack user IDs allowed to chat with the bot |
| `CHAT_MAX_TURNS` | `25` | Maximum conversation turns per session |
| `CHAT_MAX_BUDGET_USD` | `2.0` | Maximum cost per conversation session in USD |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (empty = SQLite) | PostgreSQL connection string (e.g. `postgresql://user:pass@localhost:5432/secondbrain`) |

</details>

<details>
<summary>Database Backends</summary>

**SQLite (default — local):**
- File location: `.claude/data/memory.db`
- Vector search: sqlite-vec
- Keyword search: FTS5
- No setup required — created automatically on first index run
- Regenerable at any time: `uv run python memory_index.py --rebuild`

**PostgreSQL (VPS / shared):**
- Set `DATABASE_URL` in `.claude/scripts/.env`
- Requires pgvector extension (included in the `pgvector/pgvector:pg17` Docker image)
- Vector search: pgvector
- Keyword search: tsvector + GIN index
- Start with: `docker compose up -d postgres`

Both backends normalize scores to 0–1 so hybrid search weights (0.7 vector + 0.3 keyword) work identically across backends.

</details>

<details>
<summary>Docker Services</summary>

The `docker-compose.yml` defines two services intended for VPS deployment:

```bash
docker compose up -d              # Start Postgres + Obsidian
docker compose up -d postgres     # Postgres only
docker compose up -d obsidian     # Headless Obsidian only
docker compose down               # Stop all services
docker compose logs -f postgres   # Follow Postgres logs
```

**Postgres:** `pgvector/pgvector:pg17`, bound to `127.0.0.1:5432`, data persisted in the `pgdata` named volume.

**Obsidian:** `lscr.io/linuxserver/obsidian`, bound to `127.0.0.1:8080` (mapped from container port 3001), vault mounted at `./Fredis`. Access via SSH tunnel for Obsidian Sync setup. Timezone defaults to `America/Chicago` — override with `TZ=your/timezone` in your shell environment before running `docker compose up`.

</details>

<details>
<summary>Troubleshooting</summary>

### "No integrations configured" in heartbeat output

Your `.env` is missing integration credentials. Run `uv run python setup_auth.py --check` to see which integrations are active and which are missing config.

### Google OAuth token expired or invalid

Delete `.claude/scripts/integrations/google_token.json` and re-run `uv run python setup_auth.py`. This is also required when adding new Google integrations that require additional OAuth scopes (e.g., adding Sheets access after initial setup).

### Memory search returns no results

Run `uv run python memory_index.py --rebuild` to reindex from scratch. On first run the ~80MB FastEmbed ONNX model downloads to `.claude/data/models/`.

Run `uv run python memory_index.py --stats` to check file, chunk, and vector counts.

### Heartbeat not running on schedule

- **Windows:** `Get-ScheduledTask -TaskName "SecondBrain-Heartbeat"` in PowerShell
- **macOS:** `launchctl list | grep heartbeat`
- **Linux:** `crontab -l | grep heartbeat`

Check the daily log (`Fredis/Memory/daily/YYYY-MM-DD.md`) for `HEARTBEAT_OK` or error entries to confirm whether runs are happening.

### `uv` not found when running from cron or Task Scheduler

The `run_heartbeat.sh` and `run_reflect.sh` scripts add `~/.local/bin` to `PATH`. If `uv` is installed elsewhere, update the `export PATH` line in those scripts.

### Slack bot not responding to DMs or @mentions

1. Verify `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set in `.env`
2. Confirm Socket Mode is enabled in your Slack app settings (API dashboard)
3. Verify your Slack user ID matches `SLACK_OWNER_USER_ID` or is listed in `CHAT_ALLOWED_USERS`
4. Check service logs: `sudo journalctl -u secondbrain-chat -f` (VPS) or run `uv run python ../chat/main.py` directly to see output

### Heartbeat thread replies don't open a conversation

The Slack chat bot (`main.py`) must be running for thread replies to heartbeat alerts to open a full conversation. This is a separate persistent process from the heartbeat scheduler — it requires the Socket Mode WebSocket connection to stay alive.

</details>

---

See `CLAUDE.md` for detailed system documentation used by Claude Code during sessions.
