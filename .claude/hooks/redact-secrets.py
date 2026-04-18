"""PostToolUse hook: redact .env values from tool results.

For every tool result, scan the payload for literal occurrences of any
``.env`` value (length >= 8, not in the explicit non-secret allowlist).
If any are found, emit a ``decision: "block"`` envelope with a redacted
copy of the result inside ``additionalContext`` so the LLM sees the
redacted version instead of the original.

Hot path (no secrets detected): parse JSON, build regex, scan, exit 0.
Cost is dominated by Python interpreter cold-start (~80ms).

Hooks docs: https://code.claude.com/docs/en/hooks.md
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
ENV_FILE = SCRIPTS_DIR / ".env"

# Values shorter than this are too likely to collide with normal text.
MIN_VALUE_LEN = 8

# Keys that are configuration, not secrets — never redact even if long.
NON_SECRET_KEYS = {
    "HEARTBEAT_TIMEZONE",
    "HEARTBEAT_INTERVAL_MINUTES",
    "HEARTBEAT_ACTIVE_HOURS_START",
    "HEARTBEAT_ACTIVE_HOURS_END",
    "REFLECTION_HOUR",
    "DRAFT_EXPIRY_HOURS",
    "EXPIRED_DRAFT_RETENTION_DAYS",
    "CHAT_MAX_TURNS",
    "CHAT_MAX_BUDGET_USD",
    "OWNER_NAME",
    "GOOGLE_CALENDAR_ID",
    "SLACK_NOTIFICATION_CHANNEL",
    "SLACK_MONITORED_CHANNELS",
    "SLACK_OWNER_USER_ID",
    "ASANA_WORKSPACE_ID",
    "ASANA_PROJECT_ID",
    "ASANA_USERS",
    "DATABASE_URL",
}

REPLACEMENT = "***REDACTED***"


def _load_secret_values() -> list[str]:
    """Return distinct ``.env`` values worth redacting, longest-first."""
    if not ENV_FILE.exists():
        return []
    try:
        from dotenv import dotenv_values  # type: ignore[import-untyped]
    except ImportError:
        return []
    raw = dotenv_values(str(ENV_FILE))
    seen: set[str] = set()
    out: list[str] = []
    for key, val in raw.items():
        if not val or len(val) < MIN_VALUE_LEN:
            continue
        if key in NON_SECRET_KEYS:
            continue
        if val in seen:
            continue
        seen.add(val)
        out.append(val)
    out.sort(key=len, reverse=True)
    return out


def _build_redactor(values: list[str]) -> re.Pattern[str] | None:
    if not values:
        return None
    return re.compile("|".join(re.escape(v) for v in values))


def _redact(payload: Any, redactor: re.Pattern[str]) -> tuple[Any, int]:
    """Recursively walk payload, redact secret literals in strings."""
    if isinstance(payload, str):
        new, n = redactor.subn(REPLACEMENT, payload)
        return new, n
    if isinstance(payload, list):
        out_list: list[Any] = []
        total = 0
        for item in payload:
            new_item, n = _redact(item, redactor)
            out_list.append(new_item)
            total += n
        return out_list, total
    if isinstance(payload, dict):
        out_dict: dict[Any, Any] = {}
        total = 0
        for k, v in payload.items():
            new_v, n = _redact(v, redactor)
            out_dict[k] = new_v
            total += n
        return out_dict, total
    return payload, 0


def _emit_block(redacted: Any, count: int) -> None:
    """Tell Claude Code to suppress the original tool result and inject the
    redacted version as additional context.
    """
    redacted_json = json.dumps(redacted, ensure_ascii=False, default=str)
    envelope = {
        "decision": "block",
        "reason": (
            f"redact-secrets: {count} secret value(s) from .env appeared in the "
            "tool result. The original output has been suppressed; the version "
            "below has been scrubbed."
        ),
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                f"[redacted tool_response, {count} replacement(s)]\n{redacted_json}"
            ),
        },
    }
    print(json.dumps(envelope))


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # Never break a tool call because of a parse error

    values = _load_secret_values()
    redactor = _build_redactor(values)
    if redactor is None:
        sys.exit(0)

    tool_response = hook_input.get("tool_response", {})
    new_response, count = _redact(tool_response, redactor)
    if count == 0:
        sys.exit(0)

    _emit_block(new_response, count)
    sys.exit(0)


if __name__ == "__main__":
    main()
