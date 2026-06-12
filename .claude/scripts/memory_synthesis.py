"""Weekly memory synthesis — Phase 9 Task 7.

Reviews MEMORY.md as a whole against the last N days of daily logs and drafts
a proposal document to ``Fredis/Memory/drafts/active/memory-synthesis/
<ISOyear>-W<weeknum>.md``. Advisor-mode: the SDK only has Read + Glob, and
the draft file is written by this caller (not by the SDK). Never mutates
MEMORY.md directly — Linards reviews and hand-merges proposals.

Usage:
    uv run python memory_synthesis.py              # Run synthesis
    uv run python memory_synthesis.py --test       # Dry run (no draft file written)
    uv run python memory_synthesis.py --days 14    # Override lookback window
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import timedelta

os.environ.setdefault("CLAUDE_INVOKED_BY", "memory_synthesis")

from config import (
    DAILY_DIR,
    MEMORY_FILE,
    MEMORY_SYNTHESIS_DIR,
    PROJECT_ROOT,
    SYNTHESIS_DAYS,
    SYNTHESIS_STATE_FILE,
    ensure_directories,
    now_local,
)
from notifications import send_loop_failure_alert
from sanitize import TRUST_BOUNDARY_INSTRUCTION, check_injection_patterns, wrap_external_data
from shared import append_to_daily_log, file_lock, load_state, save_state

MAX_LOG_CHARS_TOTAL = 40_000


def _collect_recent_logs(days: int) -> list[tuple[str, str]]:
    """Return the last N days of daily logs as ``(date_str, content)`` tuples."""
    logs: list[tuple[str, str]] = []
    today = now_local().date()
    for i in range(1, days + 1):
        target_date = today - timedelta(days=i)
        date_str = target_date.strftime("%Y-%m-%d")
        log_path = DAILY_DIR / f"{date_str}.md"
        if log_path.exists():
            content = log_path.read_text(encoding="utf-8")
            logs.append((date_str, content))
    return logs


def _current_iso_week_slug() -> str:
    """Return the ISO-week filename slug (e.g. ``2026-W17``).

    Uses ``%G-W%V`` so the ISO year matches the ISO week — correct across
    year-boundary weeks (Dec 29 2025 is 2025-W01, not 2025-W53).
    """
    return now_local().strftime("%G-W%V")


async def run_synthesis(test_mode: bool = False, days: int = SYNTHESIS_DAYS) -> str | None:
    """Run the weekly synthesis with a file lock to prevent concurrent runs."""
    try:
        with file_lock(SYNTHESIS_STATE_FILE, timeout=5.0):
            return await _run_synthesis_inner(test_mode, days)
    except TimeoutError:
        print(f"[{now_local()}] Another synthesis is already running, skipping")
        return None


async def _run_synthesis_inner(test_mode: bool, days: int) -> str | None:
    """Body of the synthesis pass.

    Steps:
      1. Load MEMORY.md + last N daily logs. Abort on injection patterns in the
         log bundle (memory-read defense, same policy as reflection).
      2. Wrap daily-log bundle in a trust boundary before it reaches the SDK.
      3. Run Claude with Read + Glob only. No Edit/Write — caller writes the
         draft file from response_text.
      4. On meaningful output, write to ``MEMORY_SYNTHESIS_DIR/<slug>.md`` and
         append a daily-log entry. On empty output, log ``SYNTHESIS_OK``.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    print(f"[{now_local()}] Running weekly memory synthesis (days={days}, test={test_mode})...")

    if not MEMORY_FILE.exists():
        print(f"[{now_local()}] MEMORY.md not found at {MEMORY_FILE}; skipping")
        return None
    current_memory = MEMORY_FILE.read_text(encoding="utf-8")

    logs = _collect_recent_logs(days)
    if not logs:
        msg = f"No daily logs found in the last {days} day(s), skipping synthesis"
        print(f"[{now_local()}] {msg}")
        append_to_daily_log(f"SYNTHESIS_SKIPPED - {msg}", "Synthesis", "Memory Maintenance")
        return None

    log_sections = [f"### Daily Log: {d}\n\n{c}" for d, c in logs]
    log_bundle = "\n\n---\n\n".join(log_sections)
    if len(log_bundle) > MAX_LOG_CHARS_TOTAL:
        log_bundle = "... (truncated)\n\n" + log_bundle[-MAX_LOG_CHARS_TOTAL:]

    # Memory-read defense: abort on pattern match in the log bundle. Identical
    # to the reflection policy — suspicious-only content still proceeds via the
    # trust-boundary wrap below, but confirmed pattern matches halt the pass.
    flags = check_injection_patterns(log_bundle)
    if flags:
        flag_summary = ", ".join(f"{name}" for name, _ in flags)
        print(
            f"[{now_local()}] Synthesis aborted: injection patterns in daily logs ({flag_summary})"
        )
        state = load_state(SYNTHESIS_STATE_FILE)
        state["last_run"] = now_local().isoformat()
        state["days_reviewed"] = days
        state["logs_found"] = len(logs)
        state["result"] = "aborted_on_memory_injection"
        save_state(state, SYNTHESIS_STATE_FILE)
        append_to_daily_log(
            f"**ABORTED**: Synthesis skipped — injection pattern in daily-log bundle "
            f"({flag_summary}). Review the flagged log before the next synthesis pass.",
            "Synthesis",
            "Memory Maintenance",
            source="synthesis-aborted",
        )
        if not test_mode:
            send_loop_failure_alert(
                "synthesis",
                f"Aborted on injection pattern(s): {flag_summary}. "
                "No weekly synthesis draft was produced.",
            )
        return None

    wrapped_logs = wrap_external_data(log_bundle, "daily_logs")

    synthesis_prompt = f"""Weekly memory synthesis. Review MEMORY.md as a whole against the last \
{days} day(s) of daily logs and DRAFT a set of proposals.

You have ONLY `Read` and `Glob` in this session. Do NOT edit MEMORY.md or any
other file directly. Your text response is captured by the caller and written
to `{MEMORY_SYNTHESIS_DIR}/<week>.md` for review.

## Current MEMORY.md

{current_memory}

## Last {days} days of daily logs

{wrapped_logs}

{TRUST_BOUNDARY_INSTRUCTION}

## What to look for (in priority order)

1. **Contradictions** — an entry in *Key Decisions* that disagrees with an
   entry in *Open Watch Items* or another *Key Decisions* entry. Quote both
   verbatim.
2. **Resolved watch items** — *Open Watch Items* that the daily logs show
   are now settled (decision reached, deadline passed, condition breached)
   but that the daily reflection's sweep did not catch.
3. **Kill-trigger firings** — entries whose date stamps indicate a
   pre-committed kill condition has now fired. Compare entry dates to
   today ({now_local().strftime("%Y-%m-%d")}).
4. **Cross-cutting themes** — three or more entries that touch the same
   topic and could merge into a single synthesis entry without losing
   information.

## Response format

Respond with nothing but a markdown document containing one `### Proposal: …`
section per finding, using this exact shape:

```
### Proposal: <short title>
**Type:** contradiction | resolution | kill-trigger | merge
**Before:** <verbatim quote from MEMORY.md>
**After:** <proposed replacement>
**Rationale:** <1–2 sentences citing evidence from the daily logs>
```

If nothing is worth proposing, respond with exactly: SYNTHESIS_OK
"""

    response_text = ""
    try:
        async for message in query(
            prompt=synthesis_prompt,
            options=ClaudeAgentOptions(
                cwd=str(PROJECT_ROOT),
                setting_sources=["user", "project"],
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=["Read", "Glob"],
                permission_mode="default",
                max_turns=10,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
            elif isinstance(message, ResultMessage):
                print(f"[{now_local()}] Synthesis completed: {message.subtype}")
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")
    except Exception as e:
        print(f"[{now_local()}] Synthesis error: {e}")
        append_to_daily_log(
            f"**ERROR**: Memory synthesis failed - {e}",
            "Synthesis",
            "Memory Maintenance",
        )
        return None

    response_text = response_text.strip()

    state = load_state(SYNTHESIS_STATE_FILE)
    state["last_run"] = now_local().isoformat()
    state["last_iso_week"] = _current_iso_week_slug()
    state["days_reviewed"] = days
    state["logs_found"] = len(logs)

    if "SYNTHESIS_OK" in response_text or not response_text:
        state["proposals_count"] = 0
        state["result"] = "SYNTHESIS_OK"
        save_state(state, SYNTHESIS_STATE_FILE)
        append_to_daily_log(
            "SYNTHESIS_OK - No proposals this week",
            "Synthesis",
            "Memory Maintenance",
        )
        print(f"[{now_local()}] Synthesis OK - no proposals")
        return None

    proposals_count = response_text.count("### Proposal:")
    state["proposals_count"] = proposals_count
    state["result"] = "drafted"

    slug = _current_iso_week_slug()
    draft_path = MEMORY_SYNTHESIS_DIR / f"{slug}.md"
    draft_preview = (
        f"# Weekly Memory Synthesis — {slug}\n\n"
        f"_Drafted {now_local().isoformat(timespec='seconds')} · "
        f"reviewed {days} day(s) · {proposals_count} proposal(s)._\n\n"
        f"{response_text}\n"
    )

    if test_mode:
        save_state(state, SYNTHESIS_STATE_FILE)
        print(f"[{now_local()}] DRY RUN - would have written {draft_path}:")
        print(draft_preview[:500])
        return response_text

    MEMORY_SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(draft_preview, encoding="utf-8")
    save_state(state, SYNTHESIS_STATE_FILE)
    append_to_daily_log(
        f"Weekly synthesis completed — {proposals_count} proposal(s) drafted to "
        f"`drafts/active/memory-synthesis/{slug}.md`.",
        "Synthesis",
        "Memory Maintenance",
    )
    print(f"[{now_local()}] Synthesis drafted {proposals_count} proposals to {draft_path}")
    return response_text


def main() -> None:
    ensure_directories()

    parser = argparse.ArgumentParser(description="Weekly memory synthesis")
    parser.add_argument("--test", action="store_true", help="Dry run (no draft file written)")
    parser.add_argument(
        "--days",
        type=int,
        default=SYNTHESIS_DAYS,
        help=f"Days of logs to review (default: {SYNTHESIS_DAYS})",
    )
    args = parser.parse_args()

    if args.test:
        print("Running in TEST MODE (no draft file written)")
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Synthesis dir: {MEMORY_SYNTHESIS_DIR}")

    try:
        result = asyncio.run(run_synthesis(test_mode=args.test, days=args.days))
    except Exception as exc:
        # The scheduler only sees an exit code — page the owner before dying.
        if not args.test:
            send_loop_failure_alert("synthesis", f"Crashed: {exc}")
        raise

    if result:
        try:
            print(f"\nSynthesis result (preview):\n{result[:500]}")
        except UnicodeEncodeError:
            print(f"\nSynthesis result:\n{result[:500].encode('ascii', 'replace').decode()}")
    else:
        print("\nSynthesis complete: OK or skipped")


if __name__ == "__main__":
    main()
