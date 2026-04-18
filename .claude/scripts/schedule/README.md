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
