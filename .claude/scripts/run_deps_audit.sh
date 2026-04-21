#!/usr/bin/env bash
# Weekly dependency audit runner (macOS launchd / Linux systemd)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (scheduler runs with minimal PATH).
export PATH="$PATH:$HOME/.local/bin"

# Run the audit. Non-zero exit on HIGH/CRITICAL finding propagates to
# the scheduler so it logs/alerts.
uv run python deps_audit.py
EXIT=$?

if [ $EXIT -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deps audit OK" >> deps_audit_runs.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Deps audit HIGH/CRITICAL or error exit=$EXIT" >> deps_audit_runs.log
fi
exit $EXIT
