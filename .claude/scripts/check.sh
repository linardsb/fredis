#!/usr/bin/env bash
# Local quality gate — the pre-commit trio from CLAUDE.md §Pre-Commit Workflow.
# Run directly before committing code, and invoked by ci-local-fallback.sh
# (pre-push hook) when GitHub Actions is unavailable. Mirrors .github/workflows/ci.yml.
set -euo pipefail
cd "$(dirname "$0")"

echo "[check] ruff" >&2
uv run --extra dev ruff check .
echo "[check] mypy" >&2
uv run --extra dev mypy . --ignore-missing-imports
echo "[check] pytest" >&2
uv run --extra dev pytest tests/ -q
echo "[check] local gate passed" >&2
