#!/usr/bin/env bash
# Weekly synthesis runner for cron/launchd/systemd (macOS/Linux).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (cron / launchd strip it)
export PATH="$PATH:$HOME/.local/bin"

uv run python memory_synthesis.py \
  && echo "$(date '+%Y-%m-%d %H:%M:%S') - Synthesis completed" >> synthesis_runs.log \
  || echo "$(date '+%Y-%m-%d %H:%M:%S') - Synthesis FAILED" >> synthesis_runs.log
