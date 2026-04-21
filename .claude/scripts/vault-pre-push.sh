#!/usr/bin/env bash
# Fredis vault pre-push hook — refuse to push if the GitHub repo is not private.
#
# Installation: copy this file to Fredis/.git/hooks/pre-push and chmod +x.
# (Do NOT symlink — git ignores symlinked hooks.)
#
# Prerequisites on every machine running vault-sync:
#   - `gh` CLI installed and authenticated (`gh auth status` must succeed
#     non-interactively).
#
# Failure modes:
#   - Repo is public                → exit 1 (block push; retries next cycle)
#   - `gh` CLI missing or errored   → exit 1 (fail closed on any transient
#                                     network / auth error)
#   - Remote URL not on GitHub      → exit 0 (can't enforce; git-sync
#                                     defaults to the vault remote so the
#                                     enforcement hook only applies there)
#
# git-sync (the caller) treats exit != 0 as a failed push and retries on the
# next 2-minute cycle.

set -u

# Read the first line of git's pre-push stdin protocol to derive remote
# details (git passes refs on stdin; we only need remote_name + remote_url
# from argv).
remote_name="${1:-}"
remote_url="${2:-}"

if [ -z "${remote_url}" ]; then
    # Fallback: read current origin URL.
    remote_url=$(git config --get remote."${remote_name:-origin}".url || echo "")
fi

# Normalise remote URL into <owner>/<repo>. Accepts:
#   - git@github.com:owner/repo.git
#   - https://github.com/owner/repo(.git)?
#   - ssh://git@github.com/owner/repo.git
owner_repo=""
case "$remote_url" in
    git@github.com:*)
        owner_repo="${remote_url#git@github.com:}"
        ;;
    https://github.com/*)
        owner_repo="${remote_url#https://github.com/}"
        ;;
    ssh://git@github.com/*)
        owner_repo="${remote_url#ssh://git@github.com/}"
        ;;
    *)
        # Not a GitHub remote — this enforcement only applies to GitHub.
        # Other hosts use their own privacy UX; skip without blocking.
        echo "[vault-pre-push] remote '$remote_url' is not github.com — skipping privacy check"
        exit 0
        ;;
esac
owner_repo="${owner_repo%.git}"

# Require gh CLI.
if ! command -v gh >/dev/null 2>&1; then
    echo "[vault-pre-push] ERROR: gh CLI not found — cannot verify repo privacy" >&2
    echo "[vault-pre-push] Install: https://cli.github.com/" >&2
    exit 1
fi

# Check authentication (non-interactive).
if ! gh auth status >/dev/null 2>&1; then
    echo "[vault-pre-push] ERROR: gh CLI not authenticated — run 'gh auth login'" >&2
    exit 1
fi

# Query the repo's privacy flag.
private_value=$(gh api "repos/${owner_repo}" --jq '.private' 2>/dev/null || echo "error")

case "$private_value" in
    true)
        # Private repo — allow.
        exit 0
        ;;
    false)
        # Public repo — BLOCK.
        cat >&2 <<MSG

============================================================
[vault-pre-push] ABORT — repo is PUBLIC

    Repository: ${owner_repo}
    Remote:     ${remote_url}

The Fredis vault contains drafts, daily logs, memory files, and
other personal content. Pushing to a public GitHub repo would
publish all of that.

To fix:
  gh repo edit ${owner_repo} --visibility private

Then re-run the push (git-sync retries automatically on the
next 2-minute cycle).
============================================================
MSG
        exit 1
        ;;
    *)
        # gh call failed (network, permissions, bad owner/repo) — fail closed.
        echo "[vault-pre-push] ERROR: gh api failed for '${owner_repo}' (got '${private_value}')" >&2
        echo "[vault-pre-push] Failing closed. Check network / gh auth status." >&2
        exit 1
        ;;
esac
