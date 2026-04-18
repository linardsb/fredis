"""Tests for the PostToolUse redaction hook (.claude/hooks/redact-secrets.py)."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude" / "hooks" / "redact-secrets.py"
SCRIPTS_DIR = REPO_ROOT / ".claude" / "scripts"


def _run(stdin: dict[str, object], env_path: Path) -> subprocess.CompletedProcess[str]:
    """Run the hook with a custom ENV_FILE pointed at the test fixture."""
    wrapper = f"""
import sys, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("redact_secrets", r"{HOOK}")
m = importlib.util.module_from_spec(spec)
m.ENV_FILE = Path(r"{env_path}")
spec.loader.exec_module(m)
m.ENV_FILE = Path(r"{env_path}")
m.main()
"""
    return subprocess.run(
        ["uv", "run", "python", "-c", wrapper],
        input=json.dumps(stdin),
        text=True,
        capture_output=True,
        cwd=str(SCRIPTS_DIR),
        env={**os.environ},
        timeout=30,
    )


def test_no_env_file_is_passthrough(tmp_path: Path) -> None:
    res = _run({"tool_response": {"content": "anything"}}, tmp_path / "missing.env")
    assert res.returncode == 0
    assert res.stdout == ""


def test_no_secrets_present_is_passthrough(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("API_KEY=super-secret-token-abc123\n", encoding="utf-8")
    res = _run(
        {"tool_response": {"content": "no secret here, just plain text"}},
        env,
    )
    assert res.returncode == 0
    assert res.stdout == ""


def test_secret_in_string_gets_redacted(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("API_KEY=super-secret-token-abc123\n", encoding="utf-8")
    res = _run(
        {"tool_response": {"content": "leaked: super-secret-token-abc123 here"}},
        env,
    )
    assert res.returncode == 0
    envelope = json.loads(res.stdout)
    assert envelope["decision"] == "block"
    assert "super-secret-token-abc123" not in envelope["hookSpecificOutput"]["additionalContext"]
    assert "***REDACTED***" in envelope["hookSpecificOutput"]["additionalContext"]


def test_short_value_not_redacted(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("PORT=8080\n", encoding="utf-8")  # < MIN_VALUE_LEN
    res = _run({"tool_response": {"content": "running on 8080"}}, env)
    assert res.returncode == 0
    assert res.stdout == ""


def test_non_secret_key_not_redacted(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("HEARTBEAT_TIMEZONE=Europe/London\n", encoding="utf-8")
    res = _run(
        {"tool_response": {"content": "tz is Europe/London"}},
        env,
    )
    assert res.returncode == 0
    assert res.stdout == ""


def test_secret_in_nested_dict_gets_redacted(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("TOKEN=abcdefghij1234567890\n", encoding="utf-8")
    payload: dict[str, object] = {
        "tool_response": {
            "result": {
                "headers": {"Authorization": "Bearer abcdefghij1234567890"},
                "items": ["fine", "leaked: abcdefghij1234567890"],
            }
        }
    }
    res = _run(payload, env)
    assert res.returncode == 0
    envelope = json.loads(res.stdout)
    ctx = envelope["hookSpecificOutput"]["additionalContext"]
    assert "abcdefghij1234567890" not in ctx
    assert ctx.count("***REDACTED***") == 2


def test_multiple_secrets_use_longest_first(tmp_path: Path) -> None:
    """A short secret that is a prefix of a longer secret must not eclipse it."""
    env = tmp_path / ".env"
    env.write_text(
        "SHORT=common-prefix-v1\nLONG=common-prefix-v1-extended-token\n",
        encoding="utf-8",
    )
    res = _run(
        {"tool_response": {"content": "leaked: common-prefix-v1-extended-token end"}},
        env,
    )
    assert res.returncode == 0
    envelope = json.loads(res.stdout)
    ctx = envelope["hookSpecificOutput"]["additionalContext"]
    # The longer value should be replaced as a single unit, not partially
    assert "common-prefix-v1" not in ctx
    assert "extended-token" not in ctx
    assert ctx.count("***REDACTED***") == 1


def test_malformed_stdin_is_silent_passthrough(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("X=longvaluehere\n", encoding="utf-8")
    res = subprocess.run(
        ["uv", "run", "python", str(HOOK)],
        input="not json",
        text=True,
        capture_output=True,
        cwd=str(SCRIPTS_DIR),
        timeout=30,
    )
    assert res.returncode == 0
    assert res.stdout == ""
