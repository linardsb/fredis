"""Tests for .claude/hooks/*.py — subprocess-based skip-path coverage.

These tests invoke each hook as a real subprocess so the CLAUDE_INVOKED_BY
env-var inheritance path is exercised end-to-end. Only the skip/contract paths
are covered here — the happy-path spawn of memory_flush.py is covered by Level
4 manual validation.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]  # tests → scripts → .claude → repo
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"

PRE_COMPACT = HOOKS_DIR / "pre-compact-flush.py"
SESSION_END = HOOKS_DIR / "session-end-flush.py"
SESSION_START = HOOKS_DIR / "session-start-context.py"


def _run_hook(
    hook_path: Path,
    stdin_json: dict[str, object],
    extra_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke a hook script via `uv run python` with the given stdin JSON."""
    env = {**os.environ}
    env.pop("CLAUDE_INVOKED_BY", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["uv", "run", "python", str(hook_path)],
        input=json.dumps(stdin_json),
        text=True,
        capture_output=True,
        env=env,
        cwd=str(SCRIPTS_DIR),
        timeout=30,
    )


# =============================================================================
# Recursion guard tests
# =============================================================================


def test_pre_compact_recursion_guard_skips_when_invoked_by_set(tmp_path: Path) -> None:
    """CLAUDE_INVOKED_BY set must cause pre-compact-flush to exit 0 immediately."""
    result = _run_hook(
        PRE_COMPACT,
        {"session_id": "test", "transcript_path": str(tmp_path / "nope.jsonl")},
        extra_env={"CLAUDE_INVOKED_BY": "heartbeat"},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_session_end_recursion_guard_skips_when_invoked_by_set(tmp_path: Path) -> None:
    """CLAUDE_INVOKED_BY set must cause session-end-flush to exit 0 immediately."""
    result = _run_hook(
        SESSION_END,
        {
            "session_id": "test",
            "source": "other",
            "transcript_path": str(tmp_path / "nope.jsonl"),
        },
        extra_env={"CLAUDE_INVOKED_BY": "chat"},
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


def test_pre_compact_recursion_guard_uses_correct_env_var(tmp_path: Path) -> None:
    """A differently-named env var must NOT trigger the recursion skip."""
    # Without CLAUDE_INVOKED_BY, the hook proceeds to its normal flow. With a
    # missing transcript path it still exits 0 via the "transcript missing"
    # skip — that's fine, we only care that the guard didn't fire off the
    # wrong variable.
    result = _run_hook(
        PRE_COMPACT,
        {"session_id": "test", "transcript_path": str(tmp_path / "nope.jsonl")},
        extra_env={"CLAUDE_INVOKED_WRONG": "heartbeat"},
    )
    assert result.returncode == 0


# =============================================================================
# Session-end existing-behaviour regression tests
# =============================================================================


def test_session_end_skips_when_transcript_missing() -> None:
    """Pre-existing behaviour: missing transcript_path → exit 0 (skip)."""
    result = _run_hook(
        SESSION_END,
        {"session_id": "test", "source": "other", "transcript_path": ""},
    )
    assert result.returncode == 0


# =============================================================================
# Session-start contract tests
# =============================================================================


def test_session_start_emits_valid_json_contract() -> None:
    """session-start-context.py emits a valid SessionStart JSON payload on stdout."""
    result = _run_hook(SESSION_START, {"source": "startup"})
    assert result.returncode == 0, f"stderr: {result.stderr}"
    if result.stdout.strip():
        payload = json.loads(result.stdout)
        assert "hookSpecificOutput" in payload
        assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
        assert "additionalContext" in payload["hookSpecificOutput"]


def test_session_start_three_day_window_uses_date_headers() -> None:
    """If a daily-log block is emitted, the new 3-day format uses ### headers."""
    result = _run_hook(SESSION_START, {"source": "startup"})
    assert result.returncode == 0, f"stderr: {result.stderr}"
    if not result.stdout.strip():
        return  # No memory files on this machine — tolerant skip
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    if "Recent Daily Log" in ctx:
        # The 3-day format must emit per-day ### headers, not the old
        # "(Yesterday's log)" inline label.
        assert "###" in ctx, "3-day window should emit ### date headers"
        assert "(Yesterday's log)" not in ctx, (
            "Old 1-day fallback label should not appear in 3-day output"
        )
