"""
PreToolUse hook: block future template residue from re-entering the repo.

Fredis was originally forked/derived from a template that carried references
to "Dynamous" (a community Linards is not part of as an owner), a "Circle"
integration (removed in Phase 4), and a "tone-of-voice.md" file (folded into
brand-system.md). This hook stops those strings from being re-introduced by
Edit/Write tool calls, except on an allowlist of historical/context paths.

Patterns blocked on fresh content:
  * \bDynamous\b — the template source community name
  * \bCircle\s+(integration|post|content|drafting|api) — Circle-product refs
  * \btone-of-voice\.md\b — the removed voice-guideline template file

Allowlist (paths where these strings may legitimately appear):
  * .agent/plans/       — plans and reconciliation docs
  * .agent/audits/      — historical audits
  * Fredis/Memory/daily/ — daily logs naming past events
  * Fredis/Memory/USER.md — Cole Medin / Dynamous community affiliation
  * .claude/hooks/      — hook sources ARE the pattern catalog
  * .claude/scripts/tests/ — test fixtures enumerate attack / residue strings

Exit codes:
  0 = allow
  2 = block (stderr shown to Claude as feedback)
"""

from __future__ import annotations

import json
import os
import re
import sys

REPO_ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

BLOCK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bDynamous\b"), "references 'Dynamous' (template residue)"),
    (
        re.compile(r"\bCircle\s+(integration|post|content|drafting|api)\b", re.IGNORECASE),
        "references the Circle product (removed Phase 4)",
    ),
    (re.compile(r"\btone-of-voice\.md\b"), "references the removed tone-of-voice.md file"),
]

ALLOWLIST_PREFIXES = (
    ".agent/plans/",
    ".agent/audits/",
    "Fredis/Memory/daily/",
    ".claude/hooks/",
    ".claude/scripts/tests/",
)

ALLOWLIST_EXACT = ("Fredis/Memory/USER.md",)


def _path_is_allowlisted(file_path: str) -> bool:
    if not file_path:
        return False
    abs_path = os.path.realpath(file_path)
    try:
        rel = os.path.relpath(abs_path, REPO_ROOT)
    except ValueError:
        return False
    rel = rel.replace(os.sep, "/")
    if rel in ALLOWLIST_EXACT:
        return True
    return any(rel.startswith(prefix) for prefix in ALLOWLIST_PREFIXES)


def check_content(content: str) -> str | None:
    """Return the first matched reason or None."""
    if not content:
        return None
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(content):
            return reason
    return None


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
    content = tool_input.get("new_string", "") or tool_input.get("content", "")

    if _path_is_allowlisted(file_path):
        sys.exit(0)

    reason = check_content(content)
    if reason:
        print(
            f"TEMPLATE-RESIDUE: Blocked: content {reason}. "
            "This repo was scrubbed of template residue on 2026-04-19; "
            "re-introducing it defeats the point. If the reference is "
            "legitimate (historical audit, daily log, context fact), put it "
            "under .agent/plans/, .agent/audits/, Fredis/Memory/daily/, or "
            "Fredis/Memory/USER.md instead.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
