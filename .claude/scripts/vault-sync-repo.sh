#!/usr/bin/env bash
# Single-repo vault sync for Fredis/ subtree.
#
# - Only stages/commits Fredis/ changes; WIP code outside Fredis/ stays untouched.
# - Pulls origin/main with merge (concat-both driver auto-resolves daily-log appends).
# - Pushes only if we have commits ahead of upstream.
# - Log verdicts to vault_sync_runs.log. Use flock so concurrent invocations no-op.
#
# Install points:
#   - Mac: com.linards.fredis-vault-sync.plist (launchd, 120s StartInterval)
#   - VPS: fredis-vault-sync.service + fredis-vault-sync.timer (OnUnitActiveSec=2min)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG="$SCRIPT_DIR/vault_sync_runs.log"
LOCK="/tmp/fredis-vault-sync.lock"

cd "$REPO_ROOT"

log() { printf '[%s] vault-sync: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }

exec 9>"$LOCK"
flock -n 9 || { log "another vault-sync running — skip"; exit 0; }

# 0. Bail fast if no Fredis/ directory (shouldn't happen post-Phase-10.5).
if [ ! -d "$REPO_ROOT/Fredis" ]; then
    log "Fredis/ not present in repo — nothing to sync"
    exit 0
fi

# 1. Stage only Fredis/ changes (new/mod/del).
git add -A -- Fredis/ 2>&1 | tee -a "$LOG" >/dev/null || true

# 2. Commit if anything staged — ONLY the Fredis/ subtree (leaves WIP code alone).
if ! git diff --cached --quiet -- Fredis/; then
    HOST_SHORT="$(hostname -s 2>/dev/null || hostname)"
    STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if git -c user.name="fredis-vault-sync" \
           -c user.email="vault-sync@fredis.local" \
           commit --only -- Fredis/ \
           -m "vault: sync from $HOST_SHORT @ $STAMP" >>"$LOG" 2>&1; then
        log "committed vault changes"
    else
        log "commit failed — leaving staged for next run"
    fi
fi

# 3. Pull (merge, concat-both handles daily logs). No rebase to keep history linear-ish.
if ! git pull --no-rebase --no-edit --quiet origin main >>"$LOG" 2>&1; then
    log "pull failed — manual resolution likely needed in Fredis/Memory/daily/"
    exit 1
fi

# 4. Push only if ahead.
UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null || echo '')"
if [ -z "$UPSTREAM" ]; then
    log "no upstream configured — skipping push"
    exit 0
fi

AHEAD="$(git rev-list --count '@{upstream}..HEAD' 2>/dev/null || echo 0)"
if [ "$AHEAD" -gt 0 ]; then
    if git push --quiet origin main >>"$LOG" 2>&1; then
        log "pushed $AHEAD commit(s)"
    else
        log "push failed — will retry next cycle"
        exit 1
    fi
else
    log "up-to-date"
fi
