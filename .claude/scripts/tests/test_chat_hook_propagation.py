"""Hook-propagation smoke test for the chat interface.

Proves that when the chat Agent SDK runs with `setting_sources=["user","project"]`,
the `.claude/settings.json` PreToolUse hooks are resolved and enforced. We can't
cheaply spawn a full SDK subprocess inside pytest, so we instead invoke
`block-dangerous-commands.py` directly with the exact stdin shape the SDK would
hand it. If this unit-level contract holds AND the SDK calls the hook at all
(verified once by live-chat observation, recorded in the daily log), the chat
interface is protected.

The manual integration check — send a prompt to the running chat bot that
attempts a forbidden curl, observe the hook block in stderr — is documented in
Fredis/Memory/daily/YYYY-MM-DD.md when performed.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

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


def test_financial_curl_is_blocked_via_settings_style_invocation() -> None:
    """Stripe API curl — a pattern the chat agent must NEVER execute."""
    result = _run(
        "Bash",
        {"command": "curl -X POST https://api.stripe.com/v1/charges -d amount=100"},
    )
    assert result.returncode == 2, f"Should have blocked; stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr
    assert "Stripe" in result.stderr or "financial" in result.stderr.lower()


def test_slack_postmessage_is_blocked() -> None:
    """Chat agent must not be able to send Slack messages autonomously."""
    result = _run(
        "Bash",
        {"command": "curl -X POST https://slack.com/api/chat.postMessage -d text=hi"},
    )
    assert result.returncode == 2, f"Should have blocked; stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_write_outside_sandbox_is_blocked() -> None:
    """Chat agent must not be able to write files outside repo/Fredis."""
    result = _run(
        "Write",
        {"file_path": "/etc/evil.conf", "content": "malicious"},
    )
    assert result.returncode == 2, f"Should have blocked; stderr={result.stderr!r}"
    assert "ADVISOR-MODE" in result.stderr


def test_benign_read_is_allowed() -> None:
    """Guardrail must not over-block normal chat activity."""
    result = _run("Bash", {"command": "ls -la Fredis/Memory"})
    assert result.returncode == 0, f"stderr={result.stderr!r}"
