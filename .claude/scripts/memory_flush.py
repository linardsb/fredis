"""
Memory Flush — Background Agent SDK Script

Spawned by the PreCompact hook (pre-compact-flush.py). Reads conversation
context from a temp file and uses Claude to intelligently decide what
decisions, lessons, and facts to save to the daily log.

Inspired by OpenClaw's approach: the LLM decides what matters, not keyword
heuristics.

Usage:
    uv run python memory_flush.py --context-file <path>         # Run flush
    uv run python memory_flush.py --context-file <path> --test  # Dry run
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

# Mark this process as an Agent SDK caller so PreCompact/SessionEnd hooks
# invoked by any sub-session exit skip themselves (prevents flush recursion).
# Must be set at module top so the SDK subprocess inherits it at fork time.
# setdefault preserves the first caller's label if two of these modules get
# imported in one process (keeps hook-execution.log observability accurate).
os.environ.setdefault("CLAUDE_INVOKED_BY", "memory_flush")

from config import (
    LOCAL_TZ,
    PROJECT_ROOT,
    STATE_DIR,
    ensure_directories,
    now_local,
)
from shared import append_to_daily_log, file_lock, load_state, save_state

FLUSH_STATE_FILE = STATE_DIR / "flush-state.json"

# Routing: how each flush source is labelled and which top-level section
# of the daily log it lands under.
SOURCE_ROUTING: dict[str, tuple[str, str]] = {
    "pre-compact": ("Pre-Compaction Flush", "Memory Maintenance"),
    "session-end": ("Session End Flush", "Sessions"),
}


# Secret-shape patterns. The transcript excerpt is captured by Claude Code during
# compaction/session-end and may legitimately contain tool_result blocks that echo
# .env values. Scrub before handing to the flush reasoner so token-shaped strings
# never reach the SDK call (defense-in-depth layered on redact-secrets hook).
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"xoxb-[0-9A-Za-z-]{10,}"),                # Slack bot token
    re.compile(r"xapp-[0-9A-Za-z-]{10,}"),                # Slack app-level token
    re.compile(r"xoxp-[0-9A-Za-z-]{10,}"),                # Slack user token
    re.compile(r"ghp_[0-9A-Za-z]{20,}"),                  # GitHub classic PAT
    re.compile(r"gho_[0-9A-Za-z]{20,}"),                  # GitHub OAuth token
    re.compile(r"ghs_[0-9A-Za-z]{20,}"),                  # GitHub server-to-server
    re.compile(r"github_pat_[0-9A-Za-z_]{20,}"),          # GitHub fine-grained PAT
    re.compile(r"sk-ant-[0-9A-Za-z_-]{20,}"),             # Anthropic API key
    re.compile(r"\b2/\d+/\d+:[0-9a-f]{20,}"),             # Asana PAT
    # JWT shape (covers Monday.com tokens as well).
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
)


def _scrub_secrets(text: str) -> str:
    """Replace token-shaped substrings with <REDACTED_SECRET> before LLM exposure."""
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("<REDACTED_SECRET>", text)
    return text


def _safe_unlink(path: Path) -> None:
    """Delete the context file, swallowing missing-file errors."""
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except OSError as e:
        print(f"[{now_local()}] Warning: Could not delete context file {path}: {e}")


def _extract_session_id(context_file: Path) -> str:
    """Extract session_id from context filename like flush-context-{session_id}-{timestamp}.md."""
    stem = context_file.stem  # e.g., "flush-context-abc123-20260206-153654"
    parts = stem.split("-")
    # Skip prefix words (flush, context or session, flush) and trailing timestamp parts
    # Filename patterns: flush-context-{uuid}-{YYYYMMDD}-{HHMMSS}
    #                     session-flush-{uuid}-{YYYYMMDD}-{HHMMSS}
    # UUID has 5 groups separated by hyphens, timestamp has 2 groups
    # Last 2 parts are YYYYMMDD and HHMMSS, first 2 are prefix
    if len(parts) >= 5:
        return "-".join(parts[2:-2])
    return "unknown"


# =============================================================================
# MAIN FLUSH FUNCTION
# =============================================================================


async def run_flush(
    context_file: Path,
    test_mode: bool = False,
    source: str = "pre-compact",
) -> str | None:
    """Run the memory flush with concurrency guard.

    Wraps the inner flush with a file lock to prevent simultaneous runs.
    """
    try:
        with file_lock(FLUSH_STATE_FILE, timeout=5.0):
            return await _run_flush_inner(context_file, test_mode, source)
    except TimeoutError:
        print(f"[{now_local()}] Another flush is already running, skipping")
        return None


async def _run_flush_inner(
    context_file: Path,
    test_mode: bool = False,
    source: str = "pre-compact",
) -> str | None:
    """Run the memory flush using Agent SDK.

    Args:
        context_file: Path to the context file written by the hook.
        test_mode: If True, run in dry-run mode (no file edits).

    Returns:
        Response summary, or None if FLUSH_OK.
    """
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    section_name, parent_section = SOURCE_ROUTING.get(
        source, SOURCE_ROUTING["pre-compact"]
    )

    if not context_file.exists():
        print(f"[memory-flush] Context file not found: {context_file}")
        return None

    # Dedup: skip if same session was flushed < 60s ago
    state = load_state(FLUSH_STATE_FILE)
    session_id = _extract_session_id(context_file)
    last_session = state.get("last_flushed_session_id", "")
    last_flush_str = state.get("last_flush", "")
    if session_id != "unknown" and session_id == last_session and last_flush_str:
        try:
            last_flush_time = datetime.fromisoformat(last_flush_str)
            if last_flush_time.tzinfo is None:
                last_flush_time = last_flush_time.replace(tzinfo=LOCAL_TZ)
            if (now_local() - last_flush_time).total_seconds() < 60:
                print(f"[{now_local()}] Skipping duplicate flush for session {session_id}")
                _safe_unlink(context_file)
                return None
        except ValueError:
            pass  # Malformed timestamp, proceed with flush

    context_content = context_file.read_text(encoding="utf-8").strip()
    if not context_content:
        print("[memory-flush] Context file is empty, nothing to flush")
        _safe_unlink(context_file)
        return None

    # Scrub token-shaped strings before they cross the SDK boundary.
    context_content = _scrub_secrets(context_content)

    # Truncate if needed
    if len(context_content) > 15_000:
        context_content = context_content[-15_000:]

    dry_run_note = (
        "\n\nDRY RUN: Do NOT edit any files. Just describe what you would save.\n"
        if test_mode
        else ""
    )

    priority_bullet = (
        "- **Priority signals (weight these highest):** client names, deliverable "
        "deadlines, decisions about UK vs Latvia regulatory/tax context, "
        "consultancy retainer changes, content/livestream commitments."
    )

    flush_prompt = f"""Pre-compaction memory flush. The session is near auto-compaction.
{dry_run_note}
Review the conversation context below and respond with a concise summary of important items.
You have NO tools available — respond with plain text only. Do not attempt to call
Write, Edit, or any other tool; the daily-log file will be written by the caller.

Format your response as bullet points covering:
{priority_bullet}

- Decisions made and their rationale
- Lessons learned or mistakes to avoid
- Important facts, configurations, or patterns discovered
- Action items or follow-ups mentioned
- Key context that would be lost after compaction

Skip anything that is:
- Routine tool calls or file reads
- Content that's already in memory files
- Trivial back-and-forth or clarification exchanges

If nothing is worth saving, respond with exactly: FLUSH_OK

## Conversation Context

{context_content}
"""

    print(f"[{now_local()}] Running memory flush (test={test_mode})...")

    response_text = ""

    try:
        # INVARIANT: do NOT add setting_sources here. Omitting it means this
        # sub-session does not load .claude/settings.json, so its own end does
        # NOT re-trigger SessionEnd/PreCompact hooks. CLAUDE_INVOKED_BY is
        # defense-in-depth; this omission is the primary recursion firewall.
        async for message in query(
            prompt=flush_prompt,
            options=ClaudeAgentOptions(
                cwd=str(PROJECT_ROOT),
                allowed_tools=[],
                max_turns=4,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_text += block.text
            elif isinstance(message, ResultMessage):
                print(f"[{now_local()}] Flush completed: {message.subtype}")
                if message.total_cost_usd:
                    print(f"[{now_local()}] Cost: ${message.total_cost_usd:.4f}")

    except Exception as e:
        print(f"[{now_local()}] Flush error: {e}")
        append_to_daily_log(
            f"**ERROR**: Memory flush failed - {e}", section_name, parent_section
        )
        _safe_unlink(context_file)
        return None

    response_text = response_text.strip()

    # Update state
    state["last_flush"] = now_local().isoformat()
    state["context_file"] = str(context_file)
    state["last_flushed_session_id"] = session_id
    state["result"] = "FLUSH_OK" if "FLUSH_OK" in response_text else "flushed"
    save_state(state, FLUSH_STATE_FILE)

    # Clean up context file
    _safe_unlink(context_file)
    print(f"[{now_local()}] Cleaned up context file: {context_file}")

    if "FLUSH_OK" in response_text:
        print(f"[{now_local()}] Flush OK - nothing worth saving")
        append_to_daily_log(
            "FLUSH_OK - Nothing worth saving from this session",
            section_name,
            parent_section,
        )
        return None

    if test_mode:
        print(f"[{now_local()}] DRY RUN - would have saved:\n{response_text[:500]}")
    else:
        # Write the analysis to the daily log directly
        append_to_daily_log(response_text, section_name, parent_section)
        print(f"[{now_local()}] Flush saved items to daily log")
    return response_text


# =============================================================================
# ENTRY POINT
# =============================================================================


def main() -> None:
    """Main entry point."""
    ensure_directories()

    parser = argparse.ArgumentParser(description="Memory flush background agent")
    parser.add_argument("--context-file", required=True, help="Path to context file")
    parser.add_argument("--test", action="store_true", help="Dry run mode")
    parser.add_argument(
        "--source",
        choices=sorted(SOURCE_ROUTING),
        default="pre-compact",
        help="Which hook spawned this flush (controls daily-log routing)",
    )
    args = parser.parse_args()

    context_file = Path(args.context_file)

    if args.test:
        print("Running in TEST MODE (dry run, no file edits)")

    result = asyncio.run(
        run_flush(context_file=context_file, test_mode=args.test, source=args.source)
    )

    if result:
        try:
            print(f"\nFlush result:\n{result[:500]}")
        except UnicodeEncodeError:
            print(f"\nFlush result:\n{result[:500].encode('ascii', 'replace').decode()}")
    else:
        print("\nFlush complete: OK or skipped")


if __name__ == "__main__":
    main()
