"""
PreToolUse hook: block Edit/Write to Fredis/Memory/SOUL.md.

SOUL.md encodes agent personality + advisor-mode boundaries. Edits must be
explicitly approved by Linards, not made by the heartbeat, reflection, chat,
or memory-flush Agent SDK sessions — and not silently by a Claude Code
session reacting to prompt injection from external data.

Covers all four execution surfaces because the three write-capable SDK
callers (heartbeat.py, memory_reflect.py, chat/engine.py) all set
`setting_sources=["user","project"]`, which loads this hook from
`.claude/settings.json`. memory_flush.py has `allowed_tools=[]` so Edit/Write
don't exist as tools there.

Exit codes:
  0 = allow
  2 = block (stderr shown to Claude as feedback)
"""

from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

SOUL_PATH_SUFFIX = "Fredis/Memory/SOUL.md"


def _normalize_path(file_path: str) -> str | None:
    """Resolve symlinks + relativize against CLAUDE_PROJECT_DIR.

    Returns the project-relative path (forward slashes) or None if the path
    is empty or falls outside the project.
    """
    if not file_path:
        return None
    abs_path = os.path.realpath(file_path)
    try:
        rel = os.path.relpath(abs_path, REPO_ROOT)
    except ValueError:
        return None
    return rel.replace(os.sep, "/")


def _is_soul_file(file_path: str) -> bool:
    rel = _normalize_path(file_path)
    if rel is None:
        return False
    return rel == SOUL_PATH_SUFFIX or rel.endswith("/" + SOUL_PATH_SUFFIX)


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Failed to parse hook input JSON", file=sys.stderr)
        sys.exit(1)

    tool_name = hook_input.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        sys.exit(0)

    tool_input = hook_input.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")

    if _is_soul_file(file_path):
        print(
            "BLOCK-SOUL-EDIT: Refusing to modify Fredis/Memory/SOUL.md. "
            "SOUL.md encodes agent personality + advisor-mode boundaries and "
            "requires explicit user approval. If you believe a change is "
            "warranted, append a suggestion to today's daily log "
            "(Fredis/Memory/daily/YYYY-MM-DD.md) instead — Linards reviews "
            "and applies SOUL edits manually.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
