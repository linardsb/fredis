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

# Mark this process as an Agent SDK caller so PreCompact/SessionEnd hooks
# invoked by any sub-session exit skip themselves (prevents flush recursion).
# Must be set at module top so the SDK subprocess inherits it at fork time.
# setdefault preserves the first caller's label if two of these modules get
# imported in one process (keeps hook-execution.log observability accurate).
os.environ.setdefault("CLAUDE_INVOKED_BY", "memory_reflect")

from config import (
    DAILY_DIR,
    MEMORY_ARCHIVE_DIR,
    MEMORY_FILE,
    MEMORY_LINE_LIMIT,
    OWNER_NAME,
    PROJECT_ROOT,
    REFLECTION_STATE_FILE,
    SOUL_FILE,
    USER_FILE,
    ensure_directories,
    get_today_log_path,
    now_local,
)
from notifications import send_loop_failure_alert
from sanitize import TRUST_BOUNDARY_INSTRUCTION, check_injection_patterns, wrap_external_data
from shared import append_to_daily_log, file_lock, load_state, save_state, validate_bash_command

# SOUL.md write-protection is enforced by the standalone PreToolUse hook
# `.claude/hooks/block-soul-edit.py` (registered in `.claude/settings.json`),
# which the SDK inherits via `setting_sources=["user","project"]` below.

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


def count_file_lines(path) -> int:  # type: ignore[no-untyped-def]
    """Return the line count of a file, or 0 if it does not exist."""
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


# =============================================================================
# ARCHIVE OVERFLOW
# =============================================================================


async def _archive_memory_overflow(test_mode: bool = False) -> str | None:
    """Archive oldest MEMORY.md entries when the file exceeds MEMORY_LINE_LIMIT.

    Runs as a focused second SDK pass after the promotion pass. Wholesale
    cut/paste from MEMORY.md into ``Fredis/Memory/archive/YYYY-MM.md``.
    A single footer line in MEMORY.md enumerates the archive files so the
    main session still sees that older context exists.

    Returns the response summary, or None if no archive action was needed
    or the pass was skipped (test_mode / under limit).
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        HookMatcher,
        ResultMessage,
        TextBlock,
        query,
    )

    current_lines = count_file_lines(MEMORY_FILE)
    if current_lines <= MEMORY_LINE_LIMIT:
        return None

    if test_mode:
        print(
            f"[{now_local()}] DRY RUN - MEMORY.md at {current_lines} lines "
            f"(limit {MEMORY_LINE_LIMIT}), would archive oldest entries"
        )
        return None

    MEMORY_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archive_filename = f"{now_local().strftime('%Y-%m')}.md"
    archive_file = MEMORY_ARCHIVE_DIR / archive_filename

    archive_prompt = f"""MEMORY.md archive pass. The file is currently \
{current_lines} lines; the limit is {MEMORY_LINE_LIMIT} lines.

Move the **oldest** entries from `{MEMORY_FILE}` to `{archive_file}`.

## Rules

- **Wholesale move only.** Cut entries from MEMORY.md, paste into the archive. \
Do NOT rewrite, compress, summarise, or replace them with pointer lines.
- Pick "oldest" by the date-stamp in each entry (e.g. `(2026-04-18)`). If an \
entry has no date, treat entries at the TOP of these sections as oldest, in \
this order: *Key Decisions*, *Lessons Learned*, *Important Facts*.
- **Impact-first tiebreak.** When two entries tie on date, prefer archiving the \
one tagged `[impact: low]`. A legacy entry without tags counts as `impact: med` \
for this comparison. Never archive entries tagged `[status: pending]` — those \
are active watch items.
- Stop when MEMORY.md is between {MEMORY_LINE_LIMIT - 50} and {MEMORY_LINE_LIMIT} lines. \
Do not over-archive.
- **Do NOT touch** the following sections: *Active Projects*, *Upcoming Events*, \
*Preferences Confirmed*, *Research Lanes*, *Open Watch Items*, or the top \
header / intro blurb.
- Preserve any existing content in the archive file: append new entries under \
a dated header `## Archived from MEMORY.md ({now_local().strftime('%Y-%m-%d')})`.
- If the archive file does not yet exist, create it with a top-level header \
`# MEMORY Archive — {now_local().strftime('%Y-%m')}` followed by the dated \
archived section.

## Footer

After the move, ensure MEMORY.md ends with exactly one footer line naming \
every archive file present in `{MEMORY_ARCHIVE_DIR}`, in ascending order. \
Format:

    _Older entries archived: [YYYY-MM](archive/YYYY-MM.md), ... — searchable via memory_search._

Replace the line whenever you add a new archive file. Leave one blank line \
above the footer. The original closing blurb \
(`_This file is curated from daily logs..._`) should stay above the footer.

## Tools

Use `Read`, `Edit`, `Write`, and `Glob`. Do not use `Bash` for file edits.

If MEMORY.md is already at or below {MEMORY_LINE_LIMIT} lines when you start, \
respond with exactly: `ARCHIVE_SKIP`.

When you complete the archive, respond with one line: `Archived N entries \
({current_lines} → M lines) to archive/{archive_filename}`.
"""

    print(
        f"[{now_local()}] Running MEMORY.md archive pass "
        f"({current_lines} lines > {MEMORY_LINE_LIMIT} limit)..."
    )

    response_text = ""
    sdk_succeeded = False

    try:
        async for message in query(
            prompt=archive_prompt,
            options=ClaudeAgentOptions(
                # Daily-log curation — Sonnet is sufficient; pinned so it no
                # longer inherits the VPS CLI default model.
                model="sonnet",
                cwd=str(PROJECT_ROOT),
                setting_sources=["user", "project"],
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=[
                    "Read",
                    "Edit",
                    "Write",
                    "Glob",
                ],
                permission_mode="acceptEdits",
                max_turns=15,
                hooks={
                    "PreToolUse": [
                        HookMatcher(
                            matcher="Bash",
                            hooks=[validate_bash_command],
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
                print(f"[{now_local()}] Archive pass completed: {message.subtype}")
                if message.subtype == "success":
                    sdk_succeeded = True
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")

    except Exception as e:
        # Same benign-teardown guard as the reflection pass: a post-success SDK
        # exit-1 means the archive edits already landed. Only fail on a pre-success
        # error.
        if not sdk_succeeded:
            print(f"[{now_local()}] Archive pass error: {e}")
            append_to_daily_log(
                f"**ERROR**: MEMORY.md archive pass failed - {e}",
                "Reflection",
                "Memory Maintenance",
            )
            return None
        print(f"[{now_local()}] Ignoring benign SDK teardown after archive success: {e}")

    final_lines = count_file_lines(MEMORY_FILE)
    if final_lines > MEMORY_LINE_LIMIT:
        append_to_daily_log(
            f"**WARNING**: MEMORY.md still at {final_lines} lines after archive "
            f"pass (limit {MEMORY_LINE_LIMIT}). Manual review needed.",
            "Reflection",
            "Memory Maintenance",
        )
    elif final_lines < current_lines:
        append_to_daily_log(
            f"Archived oldest MEMORY.md entries: {current_lines} → {final_lines} "
            f"lines (archive: `archive/{archive_filename}`)",
            "Reflection",
            "Memory Maintenance",
        )

    return response_text.strip() or None


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
        append_to_daily_log(f"REFLECTION_SKIPPED - {msg}", "Reflection", "Memory Maintenance")
        return None

    # Build log context
    log_sections: list[str] = []
    for date_str, content in logs:
        log_sections.append(f"### Daily Log: {date_str}\n\n{content}")
    log_context = "\n\n---\n\n".join(log_sections)

    # Memory-read defense: route daily-log content through the injection
    # pipeline BEFORE it reaches the reflection prompt. If a known pattern
    # leaked past the heartbeat guardrail into yesterday's log, we abort
    # rather than feed it to the SDK. Suspicious-only (partial flags) still
    # proceeds via the trust-boundary wrap below — the abort is reserved
    # for confirmed pattern matches.
    injection_flags = check_injection_patterns(log_context)
    if injection_flags:
        # Pattern names only — never echo the matched text. The abort entry
        # below lands in today's daily log, which tomorrow's pass scans, so
        # quoting the match made aborts self-sustaining (June 2026
        # dan_jailbreak loop: the only "Dan" left in the logs was the
        # previous day's abort message).
        flag_summary = ", ".join(name for name, _ in injection_flags)
        print(
            f"[{now_local()}] Reflection aborted: "
            f"injection patterns in daily log ({flag_summary})"
        )
        state = load_state(REFLECTION_STATE_FILE)
        state["last_run"] = now_local().isoformat()
        state["days_reviewed"] = days
        state["logs_found"] = len(logs)
        state["result"] = "aborted_on_memory_injection"
        save_state(state, REFLECTION_STATE_FILE)
        append_to_daily_log(
            f"**ABORTED**: Reflection skipped — injection pattern detected in daily log "
            f"({flag_summary}). Review yesterday's log before the next reflection pass.",
            "Reflection",
            "Memory Maintenance",
            source="reflection-aborted",
        )
        if not test_mode:
            send_loop_failure_alert(
                "reflection",
                f"Aborted on injection pattern(s): {flag_summary}. "
                "MEMORY.md was not updated this pass.",
            )
        return None

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
- **Scope decisions** — items explicitly dropped, deferred, marked out of scope, \
  declared won't-build, or killed. Scan for language like: "dropped", "deferred", \
  "out of scope", "not shipping", "won't build", "skip", "postpone", "defer to". \
  These MUST be promoted even when they look trivial — they are the class of \
  decision most likely to be re-proposed by a future auditor who can't see the \
  original daily log. Tag `[status: killed]` for dropped items, `[status: decided]` \
  for deferred-to-future items.
- Lessons learned or mistakes
- Important facts or configurations
- Project status updates
- Upcoming events needing preparation

Format each promoted item as:
- **Short title (YYYY-MM-DD).** Body. \
`[impact: high|med|low, status: pending|decided|resolved|killed]`

Impact levels:
- `high` — financial decision >£100, client-facing commitment, regulatory/legal,
  kill-trigger event, security incident.
- `med` — process choice, tool adoption, scheduling change, medium-confidence lesson.
- `low` — one-off observation, minor preference, routine housekeeping.

Status levels:
- `pending` — an Open Watch Item awaiting resolution.
- `decided` — decision made, now in effect.
- `resolved` — previously pending, now closed by evidence.
- `killed` — kill-trigger fired; the thing was dropped / invalidated.

Backward compat: legacy entries without tags still live in the file. Do NOT
retroactively tag them unless you are already editing the entry for another
reason.

### 1a. Resolution sweep (Open Watch Items → Key Decisions / Killed)
For each entry in MEMORY.md's **Open Watch Items** section, check today's log for
explicit resolution evidence. Only act when the log shows concrete language, not
conversational mention:
- If resolved (decision reached, question answered) → move to **Key Decisions**
  with a `(resolved YYYY-MM-DD)` stamp in the title.
- If kill-trigger fired (deadline passed, condition breached) → move to a new
  **Killed** subsection with `(killed YYYY-MM-DD, reason: ...)`.
- Otherwise → leave unchanged.

Evidence threshold: explicit confirmation statement. "We discussed X" is NOT
resolution; "Decided X — going with option Y" IS. When in doubt, leave it.

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
    sdk_succeeded = False

    try:
        async for message in query(
            prompt=reflection_prompt,
            options=ClaudeAgentOptions(
                # Daily-log curation — Sonnet is sufficient; pinned so it no
                # longer inherits the VPS CLI default model.
                model="sonnet",
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
                if message.subtype == "success":
                    sdk_succeeded = True
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")

    except Exception as e:
        # The Agent SDK raises a teardown error ("Fatal error in message reader:
        # Command failed with exit code 1") when the `claude` CLI subprocess exits
        # non-zero AFTER it has already streamed a successful ResultMessage. By then
        # the reflection's edits + reasoning are done, so a post-success exception is
        # benign — note it and fall through to the state save. Only a pre-success
        # error is a real reflection failure. (Daily regression from 2026-06-18.)
        if not sdk_succeeded:
            print(f"[{now_local()}] Reflection error: {e}")
            append_to_daily_log(
                f"**ERROR**: Reflection failed - {e}", "Reflection", "Memory Maintenance"
            )
            return None
        print(f"[{now_local()}] Ignoring benign SDK teardown after success: {e}")

    # Update state
    state = load_state(REFLECTION_STATE_FILE)
    state["last_run"] = now_local().isoformat()
    state["days_reviewed"] = days
    state["logs_found"] = len(logs)
    state["result"] = "REFLECTION_OK" if "REFLECTION_OK" in response_text else "promoted"
    save_state(state, REFLECTION_STATE_FILE)

    # Second pass: if MEMORY.md has grown past the line limit, archive the
    # oldest entries so the in-context file stays compact. Runs regardless of
    # whether this reflection promoted anything — past runs may already have
    # pushed the file over.
    await _archive_memory_overflow(test_mode=test_mode)

    response_text = response_text.strip()

    if "REFLECTION_OK" in response_text:
        append_to_daily_log(
            "REFLECTION_OK - Nothing to promote from recent logs",
            "Reflection",
            "Memory Maintenance",
        )
        print(f"[{now_local()}] Reflection OK - nothing to promote")
        return None
    else:
        append_to_daily_log(
            f"Promoted items from last {days} day(s) to MEMORY.md",
            "Reflection",
            "Memory Maintenance",
        )

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

    try:
        result = asyncio.run(run_reflection(test_mode=args.test, days=args.days))
    except Exception as exc:
        # The scheduler only sees an exit code — page the owner before dying.
        if not args.test:
            send_loop_failure_alert("reflection", f"Crashed: {exc}")
        raise

    if result:
        try:
            print(f"\nReflection result:\n{result[:500]}")
        except UnicodeEncodeError:
            print(f"\nReflection result:\n{result[:500].encode('ascii', 'replace').decode()}")
    else:
        print("\nReflection complete: OK or skipped")


if __name__ == "__main__":
    main()
