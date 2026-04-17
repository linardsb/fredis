#!/usr/bin/env bash
# Reflection runner for cron/launchd (macOS/Linux)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (cron uses minimal PATH)
export PATH="$PATH:$HOME/.local/bin"

# Run reflection using UV and log result
uv run python memory_reflect.py \
  && echo "$(date '+%Y-%m-%d %H:%M:%S') - Reflection completed" >> reflection_runs.log \
  || echo "$(date '+%Y-%m-%d %H:%M:%S') - Reflection FAILED" >> reflection_runs.log
