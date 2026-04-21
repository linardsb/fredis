#!/usr/bin/env bash
# Slack chat interface runner for launchd (long-running process).
# SENTINEL: if this script ran, /tmp/fredis-chat-wrapper-ran exists.
date > /tmp/fredis-chat-wrapper-ran 2>/dev/null

exec 2>&1
set -x

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 70

export PATH="/Users/Berzins/.nvm/versions/node/v24.11.0/bin:/Users/Berzins/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
export PYTHONUNBUFFERED=1

echo "=== wrapper start $(date '+%Y-%m-%d %H:%M:%S') ==="
echo "PATH=$PATH"
echo "HOME=$HOME"
echo "PWD=$(pwd)"
which uv
which claude
ls -la ~/.claude/.credentials.json 2>&1 | head -1

exec uv run python ../chat/main.py
