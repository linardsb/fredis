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

log() { printf '[%s] deploy: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

exec {LOCK_FD}>/var/lock/fredis-deploy.lock
flock -n "$LOCK_FD" || { log "another deploy is already running — aborting"; exit 1; }

cd "$REPO_ROOT"

OLD_HEAD="$(git rev-parse HEAD)"
log "pre-pull HEAD: ${OLD_HEAD:0:10}"

git fetch --quiet origin main
git pull --ff-only --quiet origin main

NEW_HEAD="$(git rev-parse HEAD)"
if [ "$OLD_HEAD" = "$NEW_HEAD" ]; then
    log "already up-to-date"
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

log "deploy complete at ${NEW_HEAD:0:10}"
