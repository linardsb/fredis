#!/usr/bin/env bash
# Daily summary runner (15:00 Europe/London) — cron/systemd (Linux VPS)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (cron/systemd uses minimal PATH)
export PATH="$PATH:/root/.local/bin"

# Run heartbeat in summary mode; log success/failure
uv run python heartbeat.py --summary \
  && echo "$(date '+%Y-%m-%d %H:%M:%S') - Summary completed" >> heartbeat_runs.log \
  || echo "$(date '+%Y-%m-%d %H:%M:%S') - Summary FAILED" >> heartbeat_runs.log
