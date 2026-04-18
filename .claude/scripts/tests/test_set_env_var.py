"""Tests for the sanctioned env editor (.claude/scripts/set_env_var.py)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
EDITOR = SCRIPTS_DIR / "set_env_var.py"


def _run(env_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Invoke the sanctioned editor against a temporary env file."""
    # Patch ENV_FILE via a tiny wrapper script that monkey-patches the module
    wrapper = f"""
import sys, importlib.util, importlib.machinery
from pathlib import Path
spec = importlib.util.spec_from_file_location("set_env_var", r"{EDITOR}")
m = importlib.util.module_from_spec(spec)
m.ENV_FILE = Path(r"{env_path}")
sys.modules["set_env_var"] = m
spec.loader.exec_module(m)
sys.argv = ["set_env_var.py"] + {list(args)!r}
m.ENV_FILE = Path(r"{env_path}")
m.main()
"""
    return subprocess.run(
        [sys.executable, "-c", wrapper],
        text=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(SCRIPTS_DIR)},
        timeout=10,
    )


def test_creates_file_when_missing(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    res = _run(env, "--key", "MY_KEY", "--value", "hello")
    assert res.returncode == 0, res.stderr
    assert env.read_text() == "MY_KEY=hello\n"


def test_updates_existing_key_in_place(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=old\nOTHER=keep\n", encoding="utf-8")
    res = _run(env, "--key", "FOO", "--value", "new")
    assert res.returncode == 0, res.stderr
    content = env.read_text()
    assert "FOO=new\n" in content
    assert "OTHER=keep\n" in content
    assert "FOO=old" not in content


def test_appends_when_key_absent(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("FOO=1\n", encoding="utf-8")
    res = _run(env, "--key", "BAR", "--value", "2")
    assert res.returncode == 0, res.stderr
    assert env.read_text() == "FOO=1\nBAR=2\n"


def test_remove_drops_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text("A=1\nB=2\n# comment\n", encoding="utf-8")
    res = _run(env, "--remove", "A")
    assert res.returncode == 0, res.stderr
    assert env.read_text() == "B=2\n# comment\n"


def test_rejects_lowercase_key(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    res = _run(env, "--key", "lower_case", "--value", "x")
    assert res.returncode == 2
    assert "Invalid key" in res.stderr


def test_rejects_key_starting_with_digit(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    res = _run(env, "--key", "1FOO", "--value", "x")
    assert res.returncode == 2
    assert "Invalid key" in res.stderr


def test_does_not_print_existing_values(tmp_path: Path) -> None:
    """Critical: editor must never echo any value to stdout/stderr."""
    env = tmp_path / ".env"
    env.write_text("API_KEY=super-secret-12345\n", encoding="utf-8")
    res = _run(env, "--key", "API_KEY", "--value", "rotated-value-67890")
    assert res.returncode == 0, res.stderr
    combined = res.stdout + res.stderr
    assert "super-secret-12345" not in combined
    assert "rotated-value-67890" not in combined


def test_key_without_value_errors(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    res = _run(env, "--key", "FOO")
    assert res.returncode == 2


@pytest.mark.parametrize("bad_key", ["", "FOO BAR", "FOO=BAR", "foo-bar"])
def test_more_invalid_keys(tmp_path: Path, bad_key: str) -> None:
    env = tmp_path / ".env"
    res = _run(env, "--key", bad_key, "--value", "x")
    assert res.returncode != 0
