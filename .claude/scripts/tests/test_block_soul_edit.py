"""Tests for the block-soul-edit PreToolUse hook."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block-soul-edit.py"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"


def _run(tool_name: str, tool_input: dict[str, object]) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(REPO_ROOT)}
    return subprocess.run(
        ["uv", "run", "python", str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        cwd=str(SCRIPTS_DIR),
        env=env,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# Positive: SOUL.md edits must be blocked regardless of how the path is spelled
# ---------------------------------------------------------------------------


def test_blocks_soul_edit_relative_path() -> None:
    result = _run("Edit", {
        "file_path": "Fredis/Memory/SOUL.md",
        "new_string": "mutated content",
    })
    assert result.returncode == 2
    assert "BLOCK-SOUL-EDIT" in result.stderr


def test_blocks_soul_write_absolute_path() -> None:
    result = _run("Write", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "SOUL.md"),
        "content": "overwrite attempt",
    })
    assert result.returncode == 2
    assert "BLOCK-SOUL-EDIT" in result.stderr


def test_blocks_soul_edit_with_dot_slash_prefix() -> None:
    result = _run("Edit", {
        "file_path": "./Fredis/Memory/SOUL.md",
        "new_string": "x",
    })
    assert result.returncode == 2
    assert "BLOCK-SOUL-EDIT" in result.stderr


# ---------------------------------------------------------------------------
# Negative: other memory files remain editable
# ---------------------------------------------------------------------------


def test_allows_memory_md_edit() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "MEMORY.md"),
        "new_string": "new entry",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_user_md_edit() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "USER.md"),
        "new_string": "user detail",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_daily_log_write() -> None:
    result = _run("Write", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "daily" / "2026-04-20.md"),
        "content": "log line",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# False-positive guard: filenames containing "soul" but not SOUL.md are allowed
# ---------------------------------------------------------------------------


def test_allows_soul_lookalike_filename() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "notes-about-soul.md"),
        "new_string": "musings",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_soul_md_in_unrelated_nested_path() -> None:
    # A path that happens to end in SOUL.md but lives outside Fredis/Memory
    # still blocks (defensive: the hook treats any SOUL.md as protected).
    # This test documents the opposite — a different filename is fine.
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "drafts" / "soul-notes.md"),
        "new_string": "draft",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# Non-Edit/Write tools should pass through
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tool_name", ["Bash", "Read", "Grep", "Glob"])
def test_other_tools_pass_through(tool_name: str) -> None:
    result = _run(tool_name, {"file_path": "Fredis/Memory/SOUL.md"})
    assert result.returncode == 0, f"tool={tool_name} stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# Defensive: missing file_path should not crash
# ---------------------------------------------------------------------------


def test_edit_without_file_path_passes() -> None:
    result = _run("Edit", {"new_string": "x"})
    assert result.returncode == 0, f"stderr={result.stderr!r}"
