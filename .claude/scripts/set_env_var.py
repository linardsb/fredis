"""Sanctioned editor for ``.claude/scripts/.env``.

The PreToolUse ``block-secrets`` hook allowlists this script as the *only*
sanctioned way for automation to mutate the env file. Ad-hoc Bash/Write
edits — including ``python -c``, ``sed``, redirected ``echo``, and freshly
written Python — remain blocked.

This script never reads or prints any existing value. On success it exits
silently.

Usage:
    set_env_var.py --key NAME --value VAL
    set_env_var.py --remove NAME
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

KEY_PATTERN = re.compile(r"^[A-Z_][A-Z0-9_]*$")
ENV_FILE = Path(__file__).parent / ".env"

# Reuse the project's cross-platform file lock helper.
sys.path.insert(0, str(Path(__file__).parent))
from shared import file_lock  # noqa: E402


def _validate_key(key: str) -> None:
    if not KEY_PATTERN.match(key):
        print(
            f"Invalid key {key!r}: must match {KEY_PATTERN.pattern}",
            file=sys.stderr,
        )
        sys.exit(2)


def _set(key: str, val: str) -> None:
    new_line = f"{key}={val}\n"
    if not ENV_FILE.exists():
        ENV_FILE.write_text(new_line, encoding="utf-8")
        return

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    replaced = False
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        head = stripped.split("=", 1)[0].strip()
        if head == key:
            lines[i] = new_line
            replaced = True
            break

    if not replaced:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(new_line)

    ENV_FILE.write_text("".join(lines), encoding="utf-8")


def _remove(key: str) -> None:
    if not ENV_FILE.exists():
        return
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#"):
            out.append(line)
            continue
        head = stripped.split("=", 1)[0].strip()
        if head == key:
            continue
        out.append(line)
    ENV_FILE.write_text("".join(out), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sanctioned env editor (write-only, never reads or prints values)"
    )
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--remove", metavar="KEY", help="Delete the line for KEY")
    g.add_argument("--key", metavar="KEY", help="Set KEY=VAL")
    parser.add_argument("--value", metavar="VAL", help="Required with --key")
    args = parser.parse_args()

    if args.remove:
        _validate_key(args.remove)
        with file_lock(ENV_FILE, timeout=5.0):
            _remove(args.remove)
        return

    if args.value is None:
        print("--key requires --value", file=sys.stderr)
        sys.exit(2)
    _validate_key(args.key)
    with file_lock(ENV_FILE, timeout=5.0):
        _set(args.key, args.value)


if __name__ == "__main__":
    main()
