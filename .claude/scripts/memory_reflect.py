"""
Daily Reflection Script for Second Brain

Reviews yesterday's daily log (and optionally last N days) and uses Claude
Agent SDK to promote important items to MEMORY.md. Runs daily at 8 AM via
OS scheduler.

Usage:
    uv run python memory_reflect.py              # Run reflection
    uv run python memory_reflect.py --test       # Dry run (no file edits)
    uv run python memory_reflect.py --days 3     # Review last 3 days
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import timedelta
from typing import Any

# Mark this process as an Agent SDK caller so PreCompact/SessionEnd hooks
# invoked by any sub-session exit skip themselves (prevents flush recursion).
# Must be set at module top so the SDK subprocess inherits it at fork time.
# setdefault preserves the first caller's label if two of these modules get
# imported in one process (keeps hook-execution.log observability accurate).
os.environ.setdefault("CLAUDE_INVOKED_BY", "memory_reflect")

from config import (
    DAILY_DIR,
    MEMORY_FILE,
    OWNER_NAME,
    PROJECT_ROOT,
    REFLECTION_STATE_FILE,
    SOUL_FILE,
    USER_FILE,
    ensure_directories,
    get_today_log_path,
    now_local,
)
from sanitize import TRUST_BOUNDARY_INSTRUCTION, wrap_external_data
from shared import append_to_daily_log, file_lock, load_state, save_state, validate_bash_command

# =============================================================================
# LOG HELPERS
# =============================================================================

MAX_LOG_CHARS = 20_000


def get_recent_logs(days: int = 1) -> list[tuple[str, str]]:
    """Read the last N days of daily logs.

    Returns list of (date_str, content) tuples, most recent first.
    """
    logs: list[tuple[str, str]] = []
    today = now_local().date()

    for i in range(1, days + 1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        log_path = DAILY_DIR / f"{date_str}.md"

        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
            # Truncate to limit token usage — keep the end (freshest entries)
            if len(content) > MAX_LOG_CHARS:
                content = "... (truncated)\n\n" + content[-MAX_LOG_CHARS:]
            logs.append((date_str, content))

    return logs


def load_current_memory() -> str:
    """Read current MEMORY.md content."""
    if MEMORY_FILE.exists():
        return MEMORY_FILE.read_text(encoding="utf-8")
    return ""


def load_user_file() -> str:
    """Read current USER.md content."""
    if USER_FILE.exists():
        return USER_FILE.read_text(encoding="utf-8")
    return ""


def load_soul_file() -> str:
    """Read current SOUL.md content."""
    if SOUL_FILE.exists():
        return SOUL_FILE.read_text(encoding="utf-8")
    return ""


# =============================================================================
# PRETOOLUSE HOOKS
# =============================================================================


async def protect_soul_file(
    input_data: Any,
    tool_use_id: str | None,
    context: Any,
) -> dict[str, Any]:
    """PreToolUse hook: block reflection agent from modifying SOUL.md."""
    tool_input = input_data.get("tool_input")
    if not isinstance(tool_input, dict):
        return {}
    file_path = tool_input.get("file_path", "")
    if "SOUL.md" in file_path:
        return {
            "decision": "block",
            "reason": (
                "Reflection agent cannot modify SOUL.md"
                " — suggest changes in daily log instead"
            ),
        }
    return {}


# =============================================================================
# MAIN REFLECTION FUNCTION
# =============================================================================


async def run_reflection(test_mode: bool = False, days: int = 1) -> str | None:
    """Run daily reflection with concurrency guard.

    Wraps the inner reflection with a file lock to prevent simultaneous runs.
    """
    try:
        with file_lock(REFLECTION_STATE_FILE, timeout=5.0):
            return await _run_reflection_inner(test_mode, days)
    except TimeoutError:
        print(f"[{now_local()}] Another reflection is already running, skipping")
        return None


async def _run_reflection_inner(test_mode: bool = False, days: int = 1) -> str | None:
    """Run daily reflection using Agent SDK.

    Reviews recent daily logs and promotes important items to MEMORY.md.

    Args:
        test_mode: If True, run in dry-run mode (no file edits).
        days: Number of days of logs to review (default: 1 = yesterday only).

    Returns:
        Response summary, or None if REFLECTION_OK.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        HookMatcher,
        ResultMessage,
        TextBlock,
        query,
    )

    print(f"[{now_local()}] Running daily reflection (days={days}, test={test_mode})...")

    # Load recent logs
    logs = get_recent_logs(days=days)
    if not logs:
        msg = f"No daily logs found for the last {days} day(s), skipping reflection"
        print(f"[{now_local()}] {msg}")
        append_to_daily_log(f"REFLECTION_SKIPPED - {msg}", "Reflection")
        return None

    # Build log context
    log_sections: list[str] = []
    for date_str, content in logs:
        log_sections.append(f"### Daily Log: {date_str}\n\n{content}")
    log_context = "\n\n---\n\n".join(log_sections)

    # Load current files
    current_memory = load_current_memory()
    current_user = load_user_file()
    current_soul = load_soul_file()

    dry_run_note = (
        "\n\nDRY RUN: Do NOT edit any files. Just describe what you would change.\n"
        if test_mode
        else ""
    )

    reflection_prompt = f"""Daily memory reflection. Review recent daily logs and update \
long-term memory files.
{dry_run_note}
## Current MEMORY.md

{current_memory}

## Current USER.md

{current_user}

## Current SOUL.md

{current_soul}

## Recent Daily Logs

{wrap_external_data(log_context, "daily_logs")}

{TRUST_BOUNDARY_INSTRUCTION}

## Instructions

Review the daily logs carefully and update THREE files as needed:

### 1. MEMORY.md ({MEMORY_FILE})
Promote important items:
- Key decisions and their rationale
- Lessons learned or mistakes
- Important facts or configurations
- Project status updates
- Upcoming events needing preparation

### 2. USER.md ({USER_FILE})
Update when you notice patterns about {OWNER_NAME or "the user"}:
- Communication preferences (how they like to interact)
- Schedule patterns (when they work, meeting patterns, creative time)
- Content preferences (what topics, formats, or styles they gravitate toward)
- Tool/workflow preferences (what they use, how they like things done)
- Team updates (new collaborators, role changes)
- New integrations or account info

### 3. SOUL.md ({SOUL_FILE})
Update ONLY if you see clear evidence of communication style adaptations:
- Tone preferences confirmed through repeated interactions
- Behavioral patterns that should be codified
- Changes to how the assistant should operate

**Rules:**
- Use the Edit tool to update files directly
- Do NOT duplicate items already present in a file
- Keep entries concise
- Only update USER.md/SOUL.md when there is clear, repeated evidence (not one-off mentions)
- Log what you changed to today's daily log ({get_today_log_path()})

If nothing is worth updating in any file, respond with exactly: REFLECTION_OK
"""

    response_text = ""

    try:
        async for message in query(
            prompt=reflection_prompt,
            options=ClaudeAgentOptions(
                cwd=str(PROJECT_ROOT),
                setting_sources=["user", "project"],
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=[
                    "Read",
                    "Edit",
                    "Glob",
                    "Grep",
                    "Bash",
                ],
                permission_mode="acceptEdits",
                max_turns=20,
                hooks={
                    "PreToolUse": [
                        HookMatcher(
                            matcher="Bash",
                            hooks=[validate_bash_command],
                        ),
                        HookMatcher(
                            matcher="Edit",
                            hooks=[protect_soul_file],
                        ),
                        HookMatcher(
                            matcher="Write",
                            hooks=[protect_soul_file],
                        ),
                    ]
                },
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
            elif isinstance(message, ResultMessage):
                print(f"[{now_local()}] Reflection completed: {message.subtype}")
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")

    except Exception as e:
        print(f"[{now_local()}] Reflection error: {e}")
        append_to_daily_log(f"**ERROR**: Reflection failed - {e}", "Reflection")
        return None

    # Update state
    state = load_state(REFLECTION_STATE_FILE)
    state["last_run"] = now_local().isoformat()
    state["days_reviewed"] = days
    state["logs_found"] = len(logs)
    state["result"] = "REFLECTION_OK" if "REFLECTION_OK" in response_text else "promoted"
    save_state(state, REFLECTION_STATE_FILE)

    response_text = response_text.strip()

    if "REFLECTION_OK" in response_text:
        append_to_daily_log("REFLECTION_OK - Nothing to promote from recent logs", "Reflection")
        print(f"[{now_local()}] Reflection OK - nothing to promote")
        return None
    else:
        append_to_daily_log(f"Promoted items from last {days} day(s) to MEMORY.md", "Reflection")

        if test_mode:
            print(f"[{now_local()}] DRY RUN - would have promoted:\n{response_text[:500]}")
        else:
            print(f"[{now_local()}] Reflection promoted items to MEMORY.md")

        return response_text


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Main entry point."""
    ensure_directories()

    parser = argparse.ArgumentParser(description="Daily memory reflection")
    parser.add_argument("--test", action="store_true", help="Dry run mode")
    parser.add_argument("--days", type=int, default=1, help="Days of logs to review (default: 1)")
    args = parser.parse_args()

    if args.test:
        print("Running in TEST MODE (dry run, no file edits)")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Reviewing last {args.days} day(s) of logs")

    result = asyncio.run(run_reflection(test_mode=args.test, days=args.days))

    if result:
        try:
            print(f"\nReflection result:\n{result[:500]}")
        except UnicodeEncodeError:
            print(f"\nReflection result:\n{result[:500].encode('ascii', 'replace').decode()}")
    else:
        print("\nReflection complete: OK or skipped")


if __name__ == "__main__":
    main()
