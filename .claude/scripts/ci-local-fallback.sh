#!/usr/bin/env bash
# Pre-push local-CI fallback (ported from merkle-email-hub).
#
# Runs the full local gate (check.sh) ONLY when (a) the pushed range touches
# code paths and (b) GitHub-hosted Actions appear unavailable (billing/quota
# exhausted). Everyday pushes — including the 2-minute vault syncs, which are
# Fredis/-only — stay fast. Bypass entirely with `git push --no-verify`.
#
# Detection: when Actions is unfunded, GitHub still *creates* a workflow run,
# but it fails to start and no steps execute (vs a genuine failure, which runs
# steps and then fails them). We sample the most recent *completed* run; zero
# executed steps across its jobs ⇒ CI is not running ⇒ validate locally.
#
# Fail-safe bias: any uncertainty about GitHub state (gh missing, not
# authenticated, API error, no runs yet) runs the local gate. Missing local
# tooling (uv) allows the push with a warning instead — a wedged 2-minute
# vault-sync is worse than one unvalidated push.
#
# Install (one-time per dev machine):
#   cp .claude/scripts/ci-local-fallback.sh .git/hooks/pre-push && chmod +x .git/hooks/pre-push
#
# Override with env vars:
#   LOCAL_CI=1   force the local gate to run regardless of GitHub state
#   LOCAL_CI=0   skip the local gate regardless of GitHub state

set -uo pipefail

ZERO=0000000000000000000000000000000000000000
CODE_PATHS=".claude/scripts .claude/chat .github/workflows"

root="$(git rev-parse --show-toplevel)" || exit 0

# launchd/systemd contexts have a minimal PATH — make uv/gh findable.
PATH="$PATH:$HOME/.local/bin:/usr/local/bin:/opt/homebrew/bin"

run_local() {
	if ! command -v uv >/dev/null 2>&1; then
		echo "[ci-fallback] GitHub Actions unavailable and uv not found — allowing push UNVALIDATED." >&2
		exit 0
	fi
	echo "[ci-fallback] GitHub Actions unavailable — running local gate (check.sh)…" >&2
	exec bash "$root/.claude/scripts/check.sh"
}
skip_local() {
	echo "[ci-fallback] GitHub Actions healthy — skipping local gate; CI will validate." >&2
	exit 0
}

# 1. Does the pushed range touch code? Pre-push stdin protocol:
#    "<local_ref> <local_sha> <remote_ref> <remote_sha>" per ref being pushed.
code_changed=0
while read -r _local_ref local_sha _remote_ref remote_sha; do
	[ -z "${local_sha:-}" ] && continue
	[ "$local_sha" = "$ZERO" ] && continue # ref deletion — nothing to validate
	if [ "${remote_sha:-$ZERO}" = "$ZERO" ]; then
		code_changed=1 # brand-new ref — can't diff a range, be safe
		break
	fi
	# shellcheck disable=SC2086
	if git diff --name-only "$remote_sha".."$local_sha" -- $CODE_PATHS 2>/dev/null | grep -q .; then
		code_changed=1
		break
	fi
done
[ "$code_changed" -eq 0 ] && exit 0

# Explicit overrides win.
case "${LOCAL_CI:-}" in
	1) run_local ;;
	0)
		echo "[ci-fallback] LOCAL_CI=0 — skipping local gate." >&2
		exit 0
		;;
esac

# 2. Is GitHub Actions actually executing?
command -v gh >/dev/null 2>&1 || run_local
gh auth status >/dev/null 2>&1 || run_local

repo=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null) || run_local
[ -n "${repo:-}" ] || run_local

# Most recent run (any branch — billing/quota is account/repo-wide).
read -r run_id status < <(
	gh run list --repo "$repo" --limit 1 \
		--json databaseId,status -q '.[0] | "\(.databaseId) \(.status)"' 2>/dev/null
) || run_local
[ -n "${run_id:-}" ] || run_local # no runs yet → be safe

# An in-progress run means Actions is actively executing → CI is up.
[ "${status:-}" != "completed" ] && skip_local

# Completed run: count executed steps. Zero ⇒ nothing ran ⇒ billing/startup block.
steps=$(gh api "repos/$repo/actions/runs/$run_id/jobs" \
	-q '[.jobs[].steps[]] | length' 2>/dev/null)
[ "${steps:-0}" -eq 0 ] && run_local

skip_local
