"""Tests for the block-template-residue PreToolUse hook."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block-template-residue.py"
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
# Positive: content in non-allowlisted paths should be blocked
# ---------------------------------------------------------------------------


def test_blocks_dynamous_in_claude_md() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "CLAUDE.md"),
        "new_string": "The Dynamous community runs this...",
    })
    assert result.returncode == 2
    assert "TEMPLATE-RESIDUE" in result.stderr
    assert "Dynamous" in result.stderr


def test_blocks_circle_integration_in_readme() -> None:
    result = _run("Write", {
        "file_path": str(REPO_ROOT / "README.md"),
        "content": "The Circle integration polls posts every 5 min.",
    })
    assert result.returncode == 2
    assert "TEMPLATE-RESIDUE" in result.stderr
    assert "Circle" in result.stderr


def test_blocks_tone_of_voice_reference() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / ".claude" / "skills" / "pptx-generator" / "SKILL.md"),
        "new_string": "Read the brand's tone-of-voice.md file for style.",
    })
    assert result.returncode == 2
    assert "tone-of-voice.md" in result.stderr


# ---------------------------------------------------------------------------
# Negative: allowlisted paths should permit the same content
# ---------------------------------------------------------------------------


def test_allows_dynamous_in_plans_dir() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / ".agent" / "plans" / "reconciliation.md"),
        "new_string": "The original Dynamous template had X...",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_dynamous_in_audits_dir() -> None:
    result = _run("Write", {
        "file_path": str(REPO_ROOT / ".agent" / "audits" / "2026-04-18_phases-0-4-audit.md"),
        "content": "Dynamous residue remained in 4 locations.",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_dynamous_in_user_md() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "USER.md"),
        "new_string": "Cole Medin — runs the Dynamous community.",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_allows_circle_in_daily_log() -> None:
    result = _run("Write", {
        "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "daily" / "2026-04-17.md"),
        "content": "Removed the Circle integration today.",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# False-positive guard: idiom "circle back" stays allowed
# ---------------------------------------------------------------------------


def test_allows_circle_back_idiom() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "some_content.md"),
        "new_string": "Let's circle back to this after the meeting.",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# Benign content: ordinary edits with no match should pass
# ---------------------------------------------------------------------------


def test_allows_unrelated_content() -> None:
    result = _run("Edit", {
        "file_path": str(REPO_ROOT / "CLAUDE.md"),
        "new_string": "Heartbeat runs every 120 minutes.",
    })
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# Non-Edit/Write tools should pass through
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tool_name", ["Bash", "Read", "Grep", "Glob"])
def test_other_tools_pass_through(tool_name: str) -> None:
    result = _run(tool_name, {"command": "echo Dynamous"})
    assert result.returncode == 0, f"tool={tool_name} stderr={result.stderr!r}"
