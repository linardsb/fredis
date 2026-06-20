#!/usr/bin/env bash
# VPS deploy: git pull main, then selectively reload systemd / sync deps / restart chat.
# Invoked remotely from the local machine's post-push hook:
#   ssh root@<vps> /root/claude-code-second-brain/.claude/scripts/deploy.sh
#
# Triggers (each independent, evaluated against the diff of the pulled range):
#   - .claude/scripts/pyproject.toml | uv.lock            -> uv sync
#   - .claude/scripts/schedule/*.service | *.timer        -> re-render into /etc/systemd/system, daemon-reload
#   - .claude/chat/*.py | .claude/scripts/chat* | .claude/config/channel-routing.yaml -> systemctl restart secondbrain-chat.service
#
# Exit non-zero on any step failure; a concurrent invocation aborts via flock.

set -euo pipefail

# Non-interactive SSH sessions (e.g. GitHub Actions via appleboy/ssh-action)
# don't inherit login-shell PATH, so uv installed under $HOME/.local/bin is
# invisible. Prepend it here so every invocation path (systemd timer, manual
# ssh, CI) resolves uv consistently. HOME is unset when invoked from the
# systemd vault-sync service (no login shell), and `set -u` would abort on a
# bare $HOME, so fall back to /root (the VPS deploy user).
export PATH="${HOME:-/root}/.local/bin:$PATH"

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

# Self-heal a dirty working tree. `git pull --ff-only` aborts if any tracked
# file is modified (manual VPS edit, errant scp, half-applied patch). Stash
# with a timestamp-tagged message and DO NOT pop — the operator can inspect
# `git stash list` and recover anything intentional. Untracked files (??)
# don't block fast-forward, so they're ignored.
if ! git diff --quiet || ! git diff --cached --quiet; then
    stash_msg="deploy-autostash-$(date -u +%Y%m%dT%H%M%SZ)"
    log "WARNING: dirty working tree on VPS — stashing as '$stash_msg'"
    git stash push --include-untracked=false --quiet -m "$stash_msg"
    log "stash created; inspect with: git stash list | grep $stash_msg"
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

if matches '^(\.claude/chat/.*\.py|\.claude/scripts/chat.*|\.claude/config/channel-routing\.yaml)$'; then
    log "chat code/config changed -> restart secondbrain-chat.service"
    systemctl restart secondbrain-chat.service
fi

# Phase 1B — restart the MCP server when its code or unit file changes. Skip
# silently if the unit isn't enabled on this host so Macs (or a VPS that
# hasn't done the one-time install yet) don't trip on a missing unit.
if matches '^\.claude/scripts/(fredis_mcp_server\.py|fredis_mcp_tools\.py|fredis_mcp_auth\.py|schedule/secondbrain-mcp-server\.service)$'; then
    if systemctl is-enabled --quiet secondbrain-mcp-server.service 2>/dev/null; then
        log "mcp server code/unit changed -> restart secondbrain-mcp-server.service"
        systemctl restart secondbrain-mcp-server.service
    else
        log "mcp server code/unit changed -> skip (secondbrain-mcp-server.service not enabled on this host)"
    fi
fi

printf '%s\n' "$NEW_HEAD" > "$LAST_HEAD_FILE"
log "deploy complete at ${NEW_HEAD:0:10} (state: $LAST_HEAD_FILE)"
