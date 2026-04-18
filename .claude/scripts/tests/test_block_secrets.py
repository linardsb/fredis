"""Tests for the PreToolUse block-secrets hook.

Exercises the tightened verb-style ``.env`` patterns end-to-end via
subprocess, proving:

* Real attack invocations still exit 2 (blocked).
* The false-positive class that affected commit messages and heredocs
  (``cat`` and ``.env`` both present, but ``.env`` is *not* an argument
  to ``cat``) now exits 0 (allowed).
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block-secrets.py"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"


def _run(tool_name: str, tool_input: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "python", str(HOOK)],
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        text=True,
        capture_output=True,
        cwd=str(SCRIPTS_DIR),
        env={**os.environ},
        timeout=30,
    )


# ----------------------------- BLOCKED: real attacks ---------------------------


@pytest.mark.parametrize("cmd", [
    "cat .env",
    "cat .env.local",
    "cat path/to/.env",
    "cat -E .env",
    "cat .env | head",
    "cat .env;",
    "head .env",
    "tail .env",
    "less .env",
    "more .env",
    "vim .env",
    "nano .env",
    "code .env",
    "source .env",
    "cp .env backup.env",
    "grep TOKEN .env",
    "rg TOKEN .env",
    "find . -name .env",
    "xxd .env",
    "od -c .env",
    "ln -s .env link",
])
def test_real_env_attacks_still_blocked(cmd: str) -> None:
    res = _run("Bash", {"command": cmd})
    assert res.returncode == 2, (
        f"expected block for {cmd!r}, got rc={res.returncode}\nstderr={res.stderr}"
    )


# ------------------------ ALLOWED: prior false positives -----------------------


def test_heredoc_body_mentioning_env_is_allowed() -> None:
    """The user's exact failure: a git commit heredoc mentioning .env."""
    cmd = (
        "git commit -m \"$(cat <<'EOF'\n"
        "feat: redact .env values from tool output\n"
        "EOF\n"
        ")\""
    )
    res = _run("Bash", {"command": cmd})
    assert res.returncode == 0, (
        f"heredoc mentioning .env should be allowed, stderr={res.stderr}"
    )


@pytest.mark.parametrize("cmd", [
    'echo "edit the .env file via the sanctioned editor"',
    'git commit -m "tighten .env protection patterns"',
    "uv run python set_env_var.py --key MY_KEY --value abc123",
    "grep -ri TODO src/",  # grep without .env as target
    "find . -name '*.py'",  # find without .env as target
])
def test_legit_commands_with_env_string_are_allowed(cmd: str) -> None:
    res = _run("Bash", {"command": cmd})
    assert res.returncode == 0, (
        f"expected allow for {cmd!r}, got rc={res.returncode}\nstderr={res.stderr}"
    )


# ---------------------- ALLOWED: editing the hook file itself -----------------


def test_editing_block_secrets_hook_is_allowed() -> None:
    """Tightening the hook itself shouldn't be blocked by its own content
    patterns just because the file naturally mentions ``cat`` and ``.env``.
    """
    snippet = (
        "    # Bash script: cat/echo env vars - tightened to require .env as arg.\n"
        '    (re.compile(r"\\bcat\\b\\s+\\S+/\\.env"), "Script cats .env file"),\n'
    )
    res = _run("Write", {
        "file_path": str(SCRIPTS_DIR.parent / "hooks" / "tmp_test_file.py"),
        "content": snippet,
    })
    assert res.returncode == 0, (
        f"editing hook source should be allowed, stderr={res.stderr}"
    )


# ------------------- BLOCKED: dangerous content in non-test scripts ------------


def test_writing_a_bash_script_that_actually_cats_env_is_blocked() -> None:
    bash_content = "#!/bin/bash\ncat .env > /tmp/leaked\n"
    res = _run("Write", {"file_path": "/tmp/leak.sh", "content": bash_content})
    assert res.returncode == 2, "literal `cat .env` in bash script should be blocked"
