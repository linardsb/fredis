"""Subprocess-driven eval runner: exercise each PreToolUse hook with fixture inputs.

Uses the same subprocess harness as ``test_block_soul_edit.py``. Assert the
expected exit code (0 allow / 2 block) + stderr marker for each
(hook, tool_name, tool_input) combination.

This is separate from the per-hook tests in ``tests/test_block_*.py`` — those
test individual invariants; this file is the **adversarial regression ratchet**
for realistic attack payloads.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"


def _run(
    hook: Path, tool_name: str, tool_input: dict[str, Any]
) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(REPO_ROOT)}
    return subprocess.run(
        ["uv", "run", "python", str(hook)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        cwd=str(SCRIPTS_DIR),
        env=env,
        timeout=30,
    )


# =============================================================================
# Per-hook × per-attack-shape block matrix
# =============================================================================

# Each row: (hook, tool_name, tool_input, expected_exit, expected_stderr_marker)
_BLOCK_CASES: list[tuple[Path, str, dict[str, Any], int, str]] = [
    # block-soul-edit: MultiEdit against SOUL.md → blocked
    (
        HOOKS_DIR / "block-soul-edit.py",
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "SOUL.md"),
            "edits": [{"old_string": "x", "new_string": "y"}],
        },
        2,
        "BLOCK-SOUL-EDIT",
    ),
    # block-soul-edit: NotebookEdit against SOUL.md → blocked
    (
        HOOKS_DIR / "block-soul-edit.py",
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "Fredis" / "Memory" / "SOUL.md"),
            "cell_number": 0,
            "new_source": "mutated",
        },
        2,
        "BLOCK-SOUL-EDIT",
    ),
    # block-secrets: Read against .env → blocked
    (
        HOOKS_DIR / "block-secrets.py",
        "Read",
        {"file_path": str(REPO_ROOT / ".env")},
        2,
        "SECURITY",
    ),
    # block-secrets: Bash printenv → blocked
    (
        HOOKS_DIR / "block-secrets.py",
        "Bash",
        {"command": "printenv"},
        2,
        "SECURITY",
    ),
    # block-dangerous-commands: Bash rm -rf ~ → blocked
    (
        HOOKS_DIR / "block-dangerous-commands.py",
        "Bash",
        {"command": "rm -rf ~/sensitive"},
        2,
        "ADVISOR-MODE",
    ),
    # block-dangerous-commands: Bash Slack chat.postMessage → blocked
    (
        HOOKS_DIR / "block-dangerous-commands.py",
        "Bash",
        {"command": "curl -X POST https://slack.com/api/chat.postMessage"},
        2,
        "ADVISOR-MODE",
    ),
    # block-template-residue: Edit that re-adds 'Dynamous' outside allowlist → blocked
    (
        HOOKS_DIR / "block-template-residue.py",
        "Edit",
        {
            "file_path": str(REPO_ROOT / "README.md"),
            "new_string": "This repo was forked from the Dynamous template.",
        },
        2,
        "TEMPLATE-RESIDUE",
    ),
]


@pytest.mark.parametrize(
    "hook,tool_name,tool_input,expected_exit,expected_marker",
    _BLOCK_CASES,
    ids=[f"{c[0].stem}-{c[1]}" for c in _BLOCK_CASES],
)
def test_hook_blocks_attack_fixture(
    hook: Path,
    tool_name: str,
    tool_input: dict[str, Any],
    expected_exit: int,
    expected_marker: str,
) -> None:
    result = _run(hook, tool_name, tool_input)
    assert result.returncode == expected_exit, (
        f"{hook.stem}/{tool_name} expected exit={expected_exit} "
        f"actual={result.returncode} stderr={result.stderr!r}"
    )
    assert expected_marker in result.stderr


# =============================================================================
# Allow-path sanity: every hook allows a benign payload under its tool
# =============================================================================

_ALLOW_CASES: list[tuple[Path, str, dict[str, Any]]] = [
    (
        HOOKS_DIR / "block-soul-edit.py",
        "Edit",
        {
            "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "MEMORY.md"),
            "new_string": "benign note",
        },
    ),
    (
        HOOKS_DIR / "block-secrets.py",
        "Read",
        {"file_path": str(REPO_ROOT / "README.md")},
    ),
    (
        HOOKS_DIR / "block-dangerous-commands.py",
        "Bash",
        {"command": "ls -la"},
    ),
    (
        HOOKS_DIR / "block-template-residue.py",
        "Edit",
        {
            "file_path": str(REPO_ROOT / "README.md"),
            "new_string": "plain prose, no residue",
        },
    ),
]


@pytest.mark.parametrize(
    "hook,tool_name,tool_input",
    _ALLOW_CASES,
    ids=[f"{c[0].stem}-allow" for c in _ALLOW_CASES],
)
def test_hook_allows_benign_fixture(
    hook: Path, tool_name: str, tool_input: dict[str, Any]
) -> None:
    result = _run(hook, tool_name, tool_input)
    assert result.returncode == 0, (
        f"{hook.stem}/{tool_name} unexpectedly blocked: stderr={result.stderr!r}"
    )


# =============================================================================
# Fixture-file readability — block-secrets must NOT block reading eval fixtures
# =============================================================================


def test_tests_evals_fixtures_not_blocked() -> None:
    """block-secrets must exempt tests/evals/ fixtures — they contain token shapes by design."""
    fixture = Path(__file__).parent / "fixtures" / "secret_shapes.jsonl"
    result = _run(
        HOOKS_DIR / "block-secrets.py",
        "Read",
        {"file_path": str(fixture)},
    )
    assert result.returncode == 0, f"fixture read was blocked: stderr={result.stderr!r}"
