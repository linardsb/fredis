# macOS launchd Agents

Three launchd plists live here:

| Plist | Purpose | Schedule |
|-------|---------|----------|
| `com.linards.ssh-tunnel.plist` | SSH tunnel for VPS Postgres | keep-alive |
| `com.linards.fredis-heartbeat.plist` | Proactive second-brain check | every 7200s (120 min); script self-gates 05:00–20:00 Europe/London |
| `com.linards.fredis-reflect.plist` | Daily memory consolidation | daily at 08:00 local |

Each section below is independent — install only what you need.

## macOS Full Disk Access (required for Fredis agents)

Any launchd agent that reads/executes files under `~/Desktop/`, `~/Documents/`, or `~/Downloads/` hits macOS TCC and is blocked with `Operation not permitted`. If this repo lives under one of those folders, grant **Full Disk Access** to `/bin/bash` **before** loading the Fredis plists:

1. System Settings → Privacy & Security → Full Disk Access → **+**
2. Authenticate, then `⌘⇧G`, type `/bin`, Enter, select `bash`, Open.
3. Toggle `bash` on.

Symptom if skipped: `launchctl list | grep fredis` shows exit code **126** and `.claude/data/logs/heartbeat.err.log` contains `Operation not permitted`.

---

# macOS SSH Tunnel (launchd)

Keeps an SSH tunnel alive for VPS Postgres at `localhost:5432`.

**Skip if:** `DATABASE_URL` is unset or points at SQLite (`.claude/data/memory.db`).
This plist is only needed in VPS Postgres mode.

## Prerequisites

- SSH key on disk (e.g. `~/.ssh/id_ed25519`).
- Key loaded in `ssh-agent` (`ssh-add ~/.ssh/id_ed25519`) — launchd cannot prompt for a passphrase.
- VPS reachable from this machine.
- Logs directory exists: `mkdir -p .claude/data/logs`.

## Install

```bash
cp com.linards.ssh-tunnel.plist ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist

# Substitute placeholders (replace with your values).
# REPO_ROOT must be an absolute path to this repo's working copy.
REPO_ROOT="$(git -C "$(pwd)" rev-parse --show-toplevel)"
sed -i '' \
  -e "s|__HOME__|$HOME|g" \
  -e "s|__REPO_ROOT__|$REPO_ROOT|g" \
  -e "s|__KEY_PATH__|$HOME/.ssh/id_ed25519|g" \
  -e "s|__VPS_USER__|<your-vps-user>|g" \
  -e "s|__VPS_HOST__|<your-vps-host>|g" \
  ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist

mkdir -p "$REPO_ROOT/.claude/data/logs"

launchctl load ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist
```

## Check

```bash
launchctl list | grep com.linards.ssh-tunnel
nc -z localhost 5432 && echo TUNNEL_OK
tail .claude/data/logs/ssh-tunnel.err.log
```

## Unload / Reload

```bash
launchctl unload ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist
launchctl load   ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist
```

## Notes

- `KeepAlive=true` respawns the tunnel on any exit (including laptop wake).
- `ThrottleInterval=30` prevents a tight respawn loop on auth failure.
- If the tunnel keeps dying, check `.claude/data/logs/ssh-tunnel.err.log` —
  most common cause is the SSH key not being loaded in `ssh-agent`.

---

# Fredis Heartbeat + Reflection (launchd)

Drives the proactive second-brain loop locally. The heartbeat polls integrations every 120 minutes during active hours; the reflection agent reviews yesterday's daily log every morning at 08:00 and promotes items into `MEMORY.md` / `USER.md`.

## Prerequisites

- `uv` installed at `~/.local/bin/uv` (check with `which uv`).
- `.env` configured in `.claude/scripts/` (Gmail/Calendar/Asana/Slack/Monday/GitHub tokens).
- Both smoke tests pass first:
  ```bash
  cd .claude/scripts
  uv run python memory_reflect.py --test     # dry run, ~90s
  uv run python heartbeat.py --test          # live APIs, no notifications, ~2min
  ```
- Full Disk Access for `/bin/bash` (see top of file).

## Install

```bash
REPO_ROOT="$(git -C "$(pwd)" rev-parse --show-toplevel)"
mkdir -p "$REPO_ROOT/.claude/data/logs"

for name in fredis-heartbeat fredis-reflect; do
  src="$REPO_ROOT/.claude/scripts/schedule/com.linards.${name}.plist"
  dst="$HOME/Library/LaunchAgents/com.linards.${name}.plist"
  cp "$src" "$dst"
  sed -i '' -e "s|__HOME__|$HOME|g" -e "s|__REPO_ROOT__|$REPO_ROOT|g" "$dst"
  launchctl unload "$dst" 2>/dev/null
  launchctl load   "$dst"
done

launchctl list | grep com.linards.fredis
```

## Force a run now (for verification, not scheduling)

```bash
launchctl kickstart -k "gui/$(id -u)/com.linards.fredis-heartbeat"
launchctl kickstart -k "gui/$(id -u)/com.linards.fredis-reflect"
```

Verify:
```bash
# Exit code should be 0; a running PID appears in the first column while live
launchctl list | grep com.linards.fredis

# State files update on successful completion
cat .claude/data/state/heartbeat-state.json | python3 -c "import json,sys; print(json.load(sys.stdin)['last_run'])"
cat .claude/data/state/reflection-state.json
```

## Unload / Reload

```bash
for name in fredis-heartbeat fredis-reflect; do
  dst="$HOME/Library/LaunchAgents/com.linards.${name}.plist"
  launchctl unload "$dst"
  launchctl load   "$dst"
done
```

## Logs

- `.claude/data/logs/heartbeat.{out,err}.log` — raw launchd stdout/stderr.
- `.claude/data/logs/reflect.{out,err}.log` — same, for reflection.
- `.claude/scripts/heartbeat_runs.log` / `reflection_runs.log` — one line per run (success/failure).
- `Fredis/Memory/daily/YYYY-MM-DD.md` — heartbeat alerts and `REFLECTION_OK` markers.

## Notes

- Heartbeat is **time-gated inside the script** (`config.is_within_active_hours()`, default 05:00–20:00 Europe/London). Outside that window the plist still fires but the script no-ops — don't double-gate in the plist.
- Reflection intentionally has `RunAtLoad=false` so installing the plist doesn't trigger a surprise run. It will fire at the next 08:00.
- If `launchctl list` shows exit code **126**, TCC is blocking `/bin/bash` — re-check Full Disk Access.
- If exit code **127**, `uv` is missing from the plist's `PATH` — the plist hardcodes `$HOME/.local/bin`; adjust if your install location differs.
