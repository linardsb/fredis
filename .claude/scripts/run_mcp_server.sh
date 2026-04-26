#!/usr/bin/env bash
# Fredis MCP server launcher (OB1 Phase 1.1).
#
# External MCP clients (Claude Desktop, Cursor, etc.) point their `command`
# at this script. The Python entry point loads .claude/scripts/.env via
# python-dotenv (config.py at import time), so we don't source it from the
# shell — that breaks on values with spaces (e.g. pipeline names).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure uv is in PATH (callers like launchd / Claude Desktop use minimal PATH).
export PATH="$HOME/.local/bin:$PATH:/root/.local/bin"

exec uv run python fredis_mcp_server.py
