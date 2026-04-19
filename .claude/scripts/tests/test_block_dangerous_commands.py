"""Tests for the PreToolUse block-dangerous-commands hook.

Philosophy: each pattern family gets at least one blocked fixture and the
benign-case check reassures us the hook isn't over-blocking ordinary work.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block-dangerous-commands.py"
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
# Outbound mutation (Slack / Gmail / Asana / Monday / Linear / Discord)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "curl -X POST https://slack.com/api/chat.postMessage -d 'channel=xyz&text=hi'",
    "python -c 'client.chat_postMessage(channel=\"x\", text=\"y\")'",
    "curl https://gmail.googleapis.com/gmail/v1/users/me/drafts/send",
    "curl -X POST https://api.monday.com/v2 -d '{\"query\":\"mutation { create_item }\"}'",
    "curl https://discord.com/api/webhooks/123/abc -X POST",
])
def test_blocks_outbound_mutation(cmd: str) -> None:
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 2, f"Should have blocked: {cmd!r}\nstderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


# ---------------------------------------------------------------------------
# Social-media posting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    'curl -X POST https://api.twitter.com/2/tweets -d \'{"text":"hi"}\'',
    'curl -X POST https://api.linkedin.com/v2/ugcPosts -d \'{}\'',
    "curl https://graph.facebook.com/v18.0/me/feed -X POST",
])
def test_blocks_social_post(cmd: str) -> None:
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 2, f"Should have blocked: {cmd!r}"


# ---------------------------------------------------------------------------
# Financial APIs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "curl https://api.stripe.com/v1/charges -u sk_test_xyz:",
    "curl https://api-m.paypal.com/v2/checkout/orders -H 'Authorization: Bearer x'",
])
def test_blocks_financial_api(cmd: str) -> None:
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 2


# ---------------------------------------------------------------------------
# Destructive commands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "rm -rf /",
    "rm -rf ~",
    "rm -rf $HOME",
    "rm -rf *",
    "git reset --hard HEAD~5",
    "git clean -fd",
    "git push --force origin main",
    "git push -f origin main",
    "git branch -D feature-branch",
    "git checkout -- .",
    "DROP TABLE users;",
    "DROP DATABASE secondbrain;",
    "DELETE FROM users;",
    "TRUNCATE TABLE logs;",
])
def test_blocks_destructive(cmd: str) -> None:
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 2, f"Should have blocked: {cmd!r}"


# ---------------------------------------------------------------------------
# Benign — must pass through
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "ls -la",
    "git status",
    "git log --oneline -10",
    "echo hello",
    "cd .claude/scripts && uv run pytest",
    "grep -r 'pattern' .claude",
    "rm -rf /tmp/scratch",           # temp dir — allowed
    "rm -rf /var/folders/xx/scratch", # temp dir — allowed
    "python -c 'print(1+1)'",
    "curl https://api.github.com/users/linardsb/events",  # read-only GET
])
def test_allows_benign(cmd: str) -> None:
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 0, f"Should have allowed: {cmd!r}\nstderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# `git checkout -- <path>` — only blocks the standalone `.` (discards all),
# not paths that happen to start with `.` (e.g. .agent/, .gitignore).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "git checkout -- .agent/plans/second-brain-prd.md",
    "git checkout -- .gitignore",
    "git checkout -- ./src/file.py",
    "git checkout -- .claude/hooks/block-dangerous-commands.py",
    "git checkout -- .env.example",
])
def test_allows_git_checkout_dotpath(cmd: str) -> None:
    """git checkout -- .<path> restores a specific file and must not be confused
    with `git checkout -- .` (discards all unstaged changes)."""
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 0, f"Should have allowed: {cmd!r}\nstderr={result.stderr!r}"


@pytest.mark.parametrize("cmd", [
    "git checkout -- .",
    "git checkout -- . ",  # trailing whitespace
    "git checkout -- . ; echo done",
    "git checkout -- . && echo reset",
])
def test_still_blocks_git_checkout_dot_standalone(cmd: str) -> None:
    """The tightened regex must still catch the real destructive form."""
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 2, f"Should have blocked: {cmd!r}\nstderr={result.stderr!r}"


# ---------------------------------------------------------------------------
# Write path sandboxing
# ---------------------------------------------------------------------------


def test_blocks_write_outside_repo(tmp_path_factory: pytest.TempPathFactory) -> None:
    # Pick a path deliberately outside the repo and outside /tmp.
    bad_path = "/Users/Berzins/Desktop/NOT_IN_REPO.txt"
    result = _run("Write", {"file_path": bad_path, "content": "x"})
    assert result.returncode == 2
    assert "write outside repo" in result.stderr.lower()


def test_allows_write_inside_repo() -> None:
    good_path = str(REPO_ROOT / ".claude" / "scripts" / "tmp_scratch.txt")
    result = _run("Write", {"file_path": good_path, "content": "hello"})
    assert result.returncode == 0


def test_allows_write_inside_fredis() -> None:
    good_path = str(REPO_ROOT / "Fredis" / "Memory" / "daily" / "scratch.md")
    result = _run("Write", {"file_path": good_path, "content": "note"})
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Content scan — blocks scripts that would send on re-execution
# ---------------------------------------------------------------------------


def test_blocks_write_of_outbound_script() -> None:
    good_path = str(REPO_ROOT / ".claude" / "scripts" / "evil.py")
    bad_content = "import slack_sdk\nclient.chat_postMessage(channel='x', text='y')"
    result = _run("Write", {"file_path": good_path, "content": bad_content})
    assert result.returncode == 2


def test_allows_write_of_outbound_script_in_tests_dir() -> None:
    """Test fixtures legitimately contain attack strings; exempted by path check."""
    good_path = str(REPO_ROOT / ".claude" / "scripts" / "tests" / "test_fixture.py")
    bad_content = "# fixture for hook tests\ncmd = 'DROP TABLE users;'"
    result = _run("Write", {"file_path": good_path, "content": bad_content})
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# Git-commit + hook-source exemptions (self-referential false-positive fixes)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", [
    "git commit -m 'docs: describe DROP TABLE handling'",
    'git commit -m "blocks chat.postMessage and drafts.send"',
    "git log --grep='rm -rf'",
    "git log --oneline -20",
    "git show HEAD",
    "git blame README.md",
    "git diff HEAD~1",
    "git status",
])
def test_allows_benign_git_subcommands(cmd: str) -> None:
    """git commit message bodies + git log output can legitimately quote deny-pattern
    strings. These subcommands never execute their string contents as shell."""
    result = _run("Bash", {"command": cmd})
    assert result.returncode == 0, f"Should have allowed: {cmd!r}\nstderr={result.stderr!r}"


def test_git_push_force_still_blocked_despite_git_prefix() -> None:
    """The git-benign exemption must not weaken destructive git operations."""
    result = _run("Bash", {"command": "git push --force origin main"})
    assert result.returncode == 2


def test_allows_edit_of_hook_source() -> None:
    """Hook source files contain deny-pattern regexes as their catalog; must be editable."""
    hook_path = str(REPO_ROOT / ".claude" / "hooks" / "block-dangerous-commands.py")
    content = 're.compile(r"chat\\.postMessage")  # outbound mutation pattern'
    result = _run("Edit", {"file_path": hook_path, "new_string": content})
    assert result.returncode == 0, f"stderr={result.stderr!r}"
