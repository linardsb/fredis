"""MultiEdit coverage for the four PreToolUse blocker hooks.

Mirrors ``test_block_soul_edit.py`` subprocess harness. Each hook is invoked
with a MultiEdit payload and we assert the correct block/allow behaviour.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"

BLOCK_SOUL = HOOKS_DIR / "block-soul-edit.py"
BLOCK_TEMPLATE = HOOKS_DIR / "block-template-residue.py"
BLOCK_SECRETS = HOOKS_DIR / "block-secrets.py"
BLOCK_DANGEROUS = HOOKS_DIR / "block-dangerous-commands.py"


def _run(
    hook: Path, tool_name: str, tool_input: dict[str, object]
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


# ---------------------------------------------------------------------------
# block-soul-edit — path-only check
# ---------------------------------------------------------------------------


def test_multiedit_soul_path_blocks() -> None:
    result = _run(
        BLOCK_SOUL,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "SOUL.md"),
            "edits": [{"old_string": "a", "new_string": "b"}],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "BLOCK-SOUL-EDIT" in result.stderr


def test_multiedit_non_soul_path_allows() -> None:
    result = _run(
        BLOCK_SOUL,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "MEMORY.md"),
            "edits": [{"old_string": "a", "new_string": "b"}],
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-template-residue — path allowlist + per-edit content scan
# ---------------------------------------------------------------------------


def test_multiedit_template_residue_content_blocks() -> None:
    # Not on allowlist path; one edit injects a banned residue token.
    result = _run(
        BLOCK_TEMPLATE,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "README.md"),
            "edits": [
                {"old_string": "x", "new_string": "harmless"},
                {"old_string": "y", "new_string": "Dynamous community"},
            ],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "TEMPLATE-RESIDUE" in result.stderr


def test_multiedit_template_residue_allowlist_passes() -> None:
    # Allowlist path exempts content check.
    result = _run(
        BLOCK_TEMPLATE,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "Fredis" / "Memory" / "daily" / "2026-04-21.md"),
            "edits": [{"old_string": "x", "new_string": "history: Dynamous"}],
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_multiedit_template_residue_empty_edits_allows() -> None:
    result = _run(
        BLOCK_TEMPLATE,
        "MultiEdit",
        {"file_path": str(REPO_ROOT / "README.md"), "edits": []},
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-secrets — sensitive file path + exfiltration content per edit
# ---------------------------------------------------------------------------


def test_multiedit_secrets_path_blocks() -> None:
    result = _run(
        BLOCK_SECRETS,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / ".env"),
            "edits": [{"old_string": "a", "new_string": "b"}],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "SECURITY" in result.stderr


def test_multiedit_secrets_exfil_content_blocks() -> None:
    # Non-sensitive target path, but one edit writes a script that exposes env.
    result = _run(
        BLOCK_SECRETS,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "scratch.py"),
            "edits": [
                {"old_string": "a", "new_string": "print('hello')"},
                {"old_string": "b", "new_string": "print(os.environ['SLACK_BOT_TOKEN'])"},
            ],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "SECURITY" in result.stderr


def test_multiedit_secrets_benign_allows() -> None:
    result = _run(
        BLOCK_SECRETS,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "scratch.md"),
            "edits": [{"old_string": "a", "new_string": "plain prose"}],
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-dangerous-commands — write-target sandbox + per-edit content
# ---------------------------------------------------------------------------


def test_multiedit_dangerous_outside_sandbox_blocks() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "MultiEdit",
        {
            "file_path": "/etc/hosts",
            "edits": [{"old_string": "a", "new_string": "b"}],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_multiedit_dangerous_outbound_content_blocks() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "scratch.py"),
            "edits": [
                {"old_string": "a", "new_string": "harmless"},
                {"old_string": "b", "new_string": "requests.post('https://api.stripe.com/v1/charges')"},
            ],
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_multiedit_dangerous_in_sandbox_allows() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "MultiEdit",
        {
            "file_path": str(REPO_ROOT / "scratch.md"),
            "edits": [{"old_string": "a", "new_string": "plain prose"}],
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
