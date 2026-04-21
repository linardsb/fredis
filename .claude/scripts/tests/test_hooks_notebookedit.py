"""NotebookEdit coverage for the four PreToolUse blocker hooks.

Mirrors ``test_block_soul_edit.py`` subprocess harness. NotebookEdit uses
``notebook_path`` (not ``file_path``) and ``new_source`` (not ``new_string`` /
``content``); ``edit_mode == "delete"`` has no content at all.
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
# block-soul-edit — notebook_path check
# ---------------------------------------------------------------------------


def test_notebookedit_soul_path_blocks() -> None:
    # Attempting to notebook-edit a path ending in SOUL.md (defensive: the
    # hook treats any SOUL.md target as protected, notebook or not).
    result = _run(
        BLOCK_SOUL,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "Fredis" / "Memory" / "SOUL.md"),
            "cell_number": 0,
            "new_source": "mutated",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "BLOCK-SOUL-EDIT" in result.stderr


def test_notebookedit_non_soul_path_allows() -> None:
    result = _run(
        BLOCK_SOUL,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "print('ok')",
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-template-residue — allowlist + content scan on new_source
# ---------------------------------------------------------------------------


def test_notebookedit_template_residue_content_blocks() -> None:
    result = _run(
        BLOCK_TEMPLATE,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "# notes: Dynamous community onboarding",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "TEMPLATE-RESIDUE" in result.stderr


def test_notebookedit_template_residue_delete_mode_skips_content() -> None:
    # delete mode has no new_source; should not crash and should allow.
    result = _run(
        BLOCK_TEMPLATE,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "edit_mode": "delete",
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-secrets — sensitive notebook_path + exfil content on new_source
# ---------------------------------------------------------------------------


def test_notebookedit_secrets_path_blocks() -> None:
    result = _run(
        BLOCK_SECRETS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / ".env"),
            "cell_number": 0,
            "new_source": "any",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "SECURITY" in result.stderr


def test_notebookedit_secrets_exfil_content_blocks() -> None:
    result = _run(
        BLOCK_SECRETS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "import os\nprint(os.environ['ANTHROPIC_API_KEY'])",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "SECURITY" in result.stderr


def test_notebookedit_secrets_benign_allows() -> None:
    result = _run(
        BLOCK_SECRETS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "x = 1\ny = x + 1",
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


def test_notebookedit_secrets_delete_mode_skips_content() -> None:
    result = _run(
        BLOCK_SECRETS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "edit_mode": "delete",
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# block-dangerous-commands — write-target sandbox + content scan
# ---------------------------------------------------------------------------


def test_notebookedit_dangerous_outside_sandbox_blocks() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "NotebookEdit",
        {
            "notebook_path": "/etc/cron.d/malicious.ipynb",
            "cell_number": 0,
            "new_source": "print('ok')",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_notebookedit_dangerous_outbound_content_blocks() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "import requests\nrequests.post('https://api.stripe.com/v1/charges')",
        },
    )
    assert result.returncode == 2, f"stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_notebookedit_dangerous_in_sandbox_allows() -> None:
    result = _run(
        BLOCK_DANGEROUS,
        "NotebookEdit",
        {
            "notebook_path": str(REPO_ROOT / "scratch.ipynb"),
            "cell_number": 0,
            "new_source": "# analysis cell\nimport pandas as pd\ndf = pd.DataFrame()",
        },
    )
    assert result.returncode == 0, f"stderr={result.stderr!r}"
