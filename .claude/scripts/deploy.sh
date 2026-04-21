#!/usr/bin/env bash
# VPS deploy: git pull main, then selectively reload systemd / sync deps / restart chat.
# Invoked remotely from the local machine's post-push hook:
#   ssh root@<vps> /root/claude-code-second-brain/.claude/scripts/deploy.sh
#
# Triggers (each independent, evaluated against the diff of the pulled range):
#   - .claude/scripts/pyproject.toml | uv.lock            -> uv sync
#   - .claude/scripts/schedule/*.service | *.timer        -> re-render into /etc/systemd/system, daemon-reload
#   - .claude/chat/*.py | .claude/scripts/chat*           -> systemctl restart secondbrain-chat.service
#
# Exit non-zero on any step failure; a concurrent invocation aborts via flock.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS_DIR="$REPO_ROOT/.claude/scripts"
SCHEDULE_DIR="$SCRIPTS_DIR/schedule"
STATE_DIR="/var/lib/fredis-deploy"
LAST_HEAD_FILE="$STATE_DIR/last-deployed-head"

log() { printf '[%s] deploy: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

exec {LOCK_FD}>/var/lock/fredis-deploy.lock
flock -n "$LOCK_FD" || { log "another deploy is already running — aborting"; exit 1; }

cd "$REPO_ROOT"

mkdir -p "$STATE_DIR"

# Anchor OLD_HEAD on the LAST-DEPLOYED commit, not the pre-pull HEAD.
# Why: vault-sync.timer pulls origin/main every 2 min. If it lands a
# code commit before this deploy fires, pre-pull HEAD == post-pull HEAD
# and the selective-restart diff sees nothing — stale service keeps
# running. Persisting the last-deployed commit separates "what's on disk"
# from "what's been reacted to", so the diff reflects the actual deploy.
if [ -f "$LAST_HEAD_FILE" ]; then
    OLD_HEAD="$(cat "$LAST_HEAD_FILE")"
    log "last-deployed HEAD: ${OLD_HEAD:0:10} (from $LAST_HEAD_FILE)"
else
    OLD_HEAD="$(git rev-parse HEAD)"
    log "no state file — treating current HEAD ${OLD_HEAD:0:10} as last-deployed"
fi

git fetch --quiet origin main
git pull --ff-only --quiet origin main

NEW_HEAD="$(git rev-parse HEAD)"
if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
    log "already up-to-date"
    # Refresh the state file defensively; NEW_HEAD == OLD_HEAD here so
    # nothing actually changes, but this self-heals a corrupt file.
    printf '%s\n' "$NEW_HEAD" > "$LAST_HEAD_FILE"
    exit 0
fi
log "advanced ${OLD_HEAD:0:10} -> ${NEW_HEAD:0:10}"

CHANGED="$(git diff --name-only "$OLD_HEAD" "$NEW_HEAD")"
log "changed files:"
printf '%s\n' "$CHANGED" | sed 's/^/  /'

matches() { printf '%s\n' "$CHANGED" | grep -qE "$1"; }

if matches '^\.claude/scripts/(pyproject\.toml|uv\.lock)$'; then
    log "dep manifest changed -> uv sync"
    (cd "$SCRIPTS_DIR" && uv sync --quiet)
fi

if matches '^\.claude/scripts/schedule/.*\.(service|timer)$'; then
    log "systemd unit(s) changed -> re-render + daemon-reload"
    # Re-render every installed unit so __REPO_ROOT__ stays substituted.
    # Units without the placeholder (e.g. secondbrain-chat.service) pass through unchanged.
    for src in "$SCHEDULE_DIR"/*.service "$SCHEDULE_DIR"/*.timer; do
        [ -f "$src" ] || continue
        name="$(basename "$src")"
        dst="/etc/systemd/system/$name"
        [ -f "$dst" ] || continue  # skip units not installed on this host
        sed "s|__REPO_ROOT__|$REPO_ROOT|g" "$src" > "$dst"
    done
    systemctl daemon-reload
fi

if matches '^(\.claude/chat/.*\.py|\.claude/scripts/chat.*)$'; then
    log "chat code changed -> restart secondbrain-chat.service"
    systemctl restart secondbrain-chat.service
fi

printf '%s\n' "$NEW_HEAD" > "$LAST_HEAD_FILE"
log "deploy complete at ${NEW_HEAD:0:10} (state: $LAST_HEAD_FILE)"
