#!/usr/bin/env bash
# Meeting-prep tick (every 10 min, 05:00–20:00 Europe/London) — systemd (Linux VPS)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (cron/systemd uses minimal PATH)
export PATH="$PATH:/root/.local/bin"

# Deterministic — no Claude call. Only logs failures to keep the log quiet.
uv run python meeting_prep.py \
  || echo "$(date '+%Y-%m-%d %H:%M:%S') - Meeting prep FAILED" >> meeting_prep_runs.log
