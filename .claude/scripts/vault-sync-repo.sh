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
LOCK_DIR="/tmp/fredis-vault-sync.lock.d"

cd "$REPO_ROOT"

log() { printf '[%s] vault-sync: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$LOG"; }

# Atomic mkdir-based lock (cross-platform; macOS has no flock).
# Stale-lock reclaim: if the owning PID is gone, retake.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    if [ -f "$LOCK_DIR/pid" ]; then
        owner="$(cat "$LOCK_DIR/pid" 2>/dev/null || echo '')"
        if [ -n "$owner" ] && ! kill -0 "$owner" 2>/dev/null; then
            log "reclaiming stale lock from pid $owner"
            rm -rf "$LOCK_DIR"
            mkdir "$LOCK_DIR" 2>/dev/null || { log "lock reclaim race — skip"; exit 0; }
        else
            log "another vault-sync running (pid $owner) — skip"
            exit 0
        fi
    else
        log "another vault-sync running — skip"
        exit 0
    fi
fi
echo "$$" > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

# 0. Bail fast if no Fredis/ directory (shouldn't happen post-Phase-10.5).
if [ ! -d "$REPO_ROOT/Fredis" ]; then
    log "Fredis/ not present in repo — nothing to sync"
    exit 0
fi

# 0.5. SSHD ban recovery (REMOVE AFTER RECOVERY — added 2026-04-26 v2).
# sshd is fine; fail2ban banned the Mac's IP (89.241.201.32) after the
# launchd ssh-tunnel kept failing auth. Unban the Mac and dump auth config
# to a diag file so we can fix the underlying key/auth mismatch.
if command -v systemctl >/dev/null 2>&1; then
    DIAG="$REPO_ROOT/Fredis/Memory/_ssh_diag.txt"
    MAC_IP="89.241.201.32"
    {
        echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) sshd ban recovery ==="
        echo "--- fail2ban status (overall) ---"
        fail2ban-client status 2>&1 || echo "(fail2ban-client unavailable)"
        echo "--- fail2ban status sshd jail ---"
        fail2ban-client status sshd 2>&1 || echo "(no sshd jail)"
        echo "--- unban $MAC_IP (all jails) ---"
        fail2ban-client unban "$MAC_IP" 2>&1 || echo "(unban failed)"
        echo "--- iptables filter (lines mentioning $MAC_IP or DROP/REJECT) ---"
        iptables -L -n 2>&1 | grep -E "$MAC_IP|DROP|REJECT|Chain " || echo "(no matching lines)"
        echo "--- /etc/ssh/sshd_config restrictions ---"
        grep -E "^[[:space:]]*(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|AllowUsers|AllowGroups|DenyUsers|MaxAuthTries|AuthorizedKeysFile)" /etc/ssh/sshd_config 2>&1 || echo "(unreadable)"
        echo "--- /root/.ssh/authorized_keys (key types + comments only, no key bodies) ---"
        if [ -f /root/.ssh/authorized_keys ]; then
            awk '{ comment=""; for(i=3;i<=NF;i++) comment=comment" "$i; printf "%-20s%s\n", $1, comment }' /root/.ssh/authorized_keys 2>&1
            echo "(total lines: $(wc -l < /root/.ssh/authorized_keys))"
        else
            echo "(/root/.ssh/authorized_keys does not exist)"
        fi
        echo "--- recent sshd journal lines for $MAC_IP ---"
        journalctl -u ssh -n 200 --no-pager 2>&1 | grep -E "$MAC_IP|Accepted|fail2ban" | tail -20 || echo "(no relevant lines)"
    } > "$DIAG" 2>&1 || true
    log "sshd ban recovery probe → $DIAG"
fi

# 1. Stage only Fredis/ changes (new/mod/del).
git add -A -- Fredis/ 2>&1 | tee -a "$LOG" >/dev/null || true

# 2. Commit if anything staged — ONLY the Fredis/ subtree (leaves WIP code alone).
if ! git diff --cached --quiet -- Fredis/; then
    HOST_SHORT="$(hostname -s 2>/dev/null || hostname)"
    STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if git -c user.name="fredis-vault-sync" \
           -c user.email="vault-sync@fredis.local" \
           commit --only -m "vault: sync from $HOST_SHORT @ $STAMP" \
           -- Fredis/ >>"$LOG" 2>&1; then
        log "committed vault changes"
    else
        log "commit failed — leaving staged for next run"
    fi
fi

# 3. Pull (merge, concat-both handles daily logs). Identity passed explicitly
#    so merge commits can be authored even when the host has no global git
#    user.name / user.email set.
if ! git -c user.name="fredis-vault-sync" \
        -c user.email="vault-sync@fredis.local" \
        pull --no-rebase --no-edit --quiet origin main >>"$LOG" 2>&1; then
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
