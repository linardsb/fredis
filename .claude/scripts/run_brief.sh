#!/usr/bin/env bash
# Morning brief runner (07:00 Europe/London) — cron/systemd (Linux VPS)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (cron/systemd uses minimal PATH)
export PATH="$PATH:/root/.local/bin"

# Run heartbeat in brief mode; log success/failure
uv run python heartbeat.py --brief \
  && echo "$(date '+%Y-%m-%d %H:%M:%S') - Brief completed" >> heartbeat_runs.log \
  || echo "$(date '+%Y-%m-%d %H:%M:%S') - Brief FAILED" >> heartbeat_runs.log
