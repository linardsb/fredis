#!/usr/bin/env bash
# Hourly auth watchdog runner (Linux systemd). Probes the Claude and Google
# credentials and Slack-alerts on an auth failure. The Python script always
# exits 0, so a failing run here means the runner itself broke (visible in the
# systemd journal).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (systemd strips it to /usr/bin:/bin).
export PATH="$PATH:$HOME/.local/bin"

uv run python auth_watchdog.py
