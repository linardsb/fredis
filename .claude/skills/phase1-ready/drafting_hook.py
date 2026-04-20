"""
PreToolUse hook for the phase1-ready skill.

Restricts Edit / Write / Bash tool use to the Phase 1 personalisation allowlist.
Returns ``{"decision": "block", "reason": ...}`` for any out-of-scope path or
command, ``{}`` otherwise.

Note: this hook is only auto-active when the skill spawns a sub-agent SDK
session that wires it up via `HookMatcher`. In the default in-conversation
flow, the main session must follow the allowlist manually — this file is the
canonical reference for the rules.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Any

# === Allowlist =============================================================

_ALLOWED_MEMORY_FILES = frozenset(
    {
        "Fredis/Memory/SOUL.md",
        "Fredis/Memory/USER.md",
        "Fredis/Memory/MEMORY.md",
        "Fredis/Memory/HABITS.md",
        "Fredis/Memory/HEARTBEAT.md",
    }
)

_ALLOWED_FOLDER_READMES = frozenset(
    {
        "Fredis/Memory/research/README.md",
        "Fredis/Memory/competitors/README.md",
        "Fredis/Memory/retainers/README.md",
        "Fredis/Memory/case-studies/README.md",
        "Fredis/Memory/investors/README.md",
        "Fredis/Memory/collaborators/README.md",
    }
)

# Research sub-folders — each with its own README
_ALLOWED_RESEARCH_LANES = frozenset(
    {
        "Fredis/Memory/research/markets/README.md",
        "Fredis/Memory/research/policy/README.md",
        "Fredis/Memory/research/ai/README.md",
        "Fredis/Memory/research/robotics/README.md",
        "Fredis/Memory/research/materials/README.md",
        "Fredis/Memory/research/agriculture/README.md",
    }
)

_ALLOWED_PRD = "agent/plans/second-brain-prd.md"  # matched as suffix
_DAILY_LOG_RE = re.compile(r"Fredis/Memory/daily/\d{4}-\d{2}-\d{2}\.md$")
_INVESTOR_FILE_RE = re.compile(r"^Fredis/Memory/investors/[A-Za-z0-9_\-]+\.md$")
_COLLABORATOR_FILE_RE = re.compile(r"^Fredis/Memory/collaborators/[A-Za-z0-9_\-]+\.md$")

_ALLOWED_BASH_PATTERNS = (
    re.compile(
        r"^\s*mkdir\s+-p\s+Fredis/Memory/(research|competitors|retainers|case-studies|investors|collaborators)\b"
    ),
    re.compile(
        r"^\s*mkdir\s+-p\s+Fredis/Memory/research/"
        r"(markets|policy|ai|robotics|materials|agriculture)\b"
    ),
    re.compile(r"^\s*rm\s+Fredis/Memory/BOOTSTRAP\.md\s*$"),
)


def _normalise(path: str) -> str:
    """Project-relative POSIX path with leading `./` stripped."""
    p = PurePosixPath(path.replace("\\", "/"))
    parts = list(p.parts)
    if parts and parts[0] == ".":
        parts = parts[1:]
    return "/".join(parts)


def _path_allowed(file_path: str) -> bool:
    norm = _normalise(file_path)
    if norm in _ALLOWED_MEMORY_FILES:
        return True
    if norm in _ALLOWED_FOLDER_READMES:
        return True
    if norm in _ALLOWED_RESEARCH_LANES:
        return True
    if _INVESTOR_FILE_RE.match(norm):
        return True
    if _COLLABORATOR_FILE_RE.match(norm):
        return True
    if _DAILY_LOG_RE.search(norm):
        return True
    if norm.endswith(".agent/plans/second-brain-prd.md") or norm.endswith(_ALLOWED_PRD):
        return True
    return False


def _bash_allowed(command: str) -> bool:
    return any(pattern.match(command) for pattern in _ALLOWED_BASH_PATTERNS)


async def restrict_writes_to_phase1_targets(
    input_data: Any,
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """Block Edit/Write/Bash calls outside the Phase 1 allowlist."""
    tool_name = ""
    if isinstance(input_data, dict):
        tool_name = input_data.get("tool_name", "") or ""
        tool_input = input_data.get("tool_input")
    else:
        tool_input = None

    if not isinstance(tool_input, dict):
        return {}

    if tool_name in {"Edit", "Write"}:
        path = tool_input.get("file_path", "")
        if not isinstance(path, str) or not _path_allowed(path):
            return {
                "decision": "block",
                "reason": (
                    f"phase1-ready: writes restricted to the Phase 1 allowlist; "
                    f"target {path!r} is out of scope."
                ),
            }
        return {}

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if not isinstance(command, str) or not _bash_allowed(command):
            return {
                "decision": "block",
                "reason": (
                    f"phase1-ready: bash restricted to mkdir of the four topic folders "
                    f"and a single `rm Fredis/Memory/BOOTSTRAP.md`; command {command!r} blocked."
                ),
            }
        return {}

    return {}
