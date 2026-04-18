"""
Session End Memory Flush Hook

Called by Claude Code when a session ends. Extracts readable conversation
context from the JSONL transcript and spawns a background Agent SDK process
(memory_flush.py) that intelligently decides what to save to the daily log.

This hook does NO API calls — pure local file I/O for speed (<10s).
Mirrors pre-compact-flush.py architecture.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time as _time
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for config imports
_scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_scripts_dir))

from config import SCRIPTS_DIR, STATE_DIR, ensure_directories  # noqa: E402
from shared import invocation_source, log_hook_execution  # noqa: E402

# === Constants ===
MAX_TURNS = 30
MAX_CONTEXT_CHARS = 15_000
MIN_TURNS_TO_FLUSH = 5  # Skip trivial sessions


def extract_text_from_content(content: object) -> str:
    """Extract readable text from a message content field.

    Content can be a string or a list of content blocks.
    """
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)

    return ""


def extract_conversation_context(transcript_path: Path) -> tuple[str, int]:
    """Read JSONL transcript and extract last ~N conversation turns as markdown.

    Returns:
        Tuple of (context_string, turn_count)
    """
    turns: list[dict[str, str]] = []

    with open(transcript_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry: dict[str, object] = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Transcript entries nest the message under a "message" key
            msg = entry.get("message")
            if isinstance(msg, dict):
                role = msg.get("role")
                content = msg.get("content", "")
            else:
                role = entry.get("role")
                content = entry.get("content", "")

            if role not in ("user", "assistant"):
                continue

            text = extract_text_from_content(content)
            text = text.strip()
            if not text:
                continue

            label = "User" if role == "user" else "Assistant"
            turns.append({"role": label, "text": text})

    # Take last N turns
    recent = turns[-MAX_TURNS:]

    # Build readable markdown
    parts: list[str] = []
    for turn in recent:
        parts.append(f"**{turn['role']}:** {turn['text']}\n")

    context = "\n".join(parts)

    # Truncate to max chars
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[-MAX_CONTEXT_CHARS:]
        # Find first complete turn boundary after truncation
        boundary = context.find("\n**")
        if boundary > 0:
            context = context[boundary + 1 :]

    return context, len(recent)


def main() -> None:
    """Main hook entry point. Reads stdin, extracts context, spawns background flush."""
    _start = _time.time()

    # Recursion guard: skip when invoked inside an Agent SDK sub-session
    # (heartbeat, memory_flush, memory_reflect, chat all set CLAUDE_INVOKED_BY).
    invoked = invocation_source()
    if invoked:
        log_hook_execution(
            "session-end-flush", "exit", "SKIP",
            _time.time() - _start, f"invoked_by={invoked}",
        )
        sys.exit(0)

    ensure_directories()

    # Read hook input from stdin
    # Claude Code on Windows may pass paths with unescaped backslashes (e.g. C:\Users\...)
    # which are invalid JSON. Try normal parse first; on failure, escape lone backslashes.
    try:
        raw_input = sys.stdin.read()
        try:
            hook_input: dict[str, object] = json.loads(raw_input)
        except json.JSONDecodeError:
            fixed_input = re.sub(r'(?<!\\)\\(?!["\\])', r'\\\\', raw_input)
            hook_input = json.loads(fixed_input)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[session-end-flush] Failed to parse stdin: {e}", file=sys.stderr)
        log_hook_execution("session-end-flush", "unknown", "ERROR", _time.time() - _start, f"stdin parse: {e}")
        sys.exit(0)

    session_id = hook_input.get("session_id", "unknown")
    source = str(hook_input.get("source", "unknown"))
    transcript_path_str = hook_input.get("transcript_path", "")

    # Handle empty/missing transcript_path
    if not transcript_path_str or not isinstance(transcript_path_str, str):
        log_hook_execution("session-end-flush", source, "SKIP", _time.time() - _start, "no transcript")
        sys.exit(0)

    transcript_path = Path(transcript_path_str)
    if not transcript_path.exists():
        log_hook_execution("session-end-flush", source, "SKIP", _time.time() - _start, "transcript missing")
        sys.exit(0)

    # Extract conversation context
    try:
        context, turn_count = extract_conversation_context(transcript_path)
    except Exception as e:
        print(f"[session-end-flush] Context extraction failed: {e}", file=sys.stderr)
        log_hook_execution("session-end-flush", source, "ERROR", _time.time() - _start, f"extraction: {e}")
        sys.exit(0)

    if not context.strip():
        log_hook_execution("session-end-flush", source, "SKIP", _time.time() - _start, "empty context")
        sys.exit(0)

    # Skip trivial sessions (< MIN_TURNS_TO_FLUSH conversation turns)
    if turn_count < MIN_TURNS_TO_FLUSH:
        log_hook_execution("session-end-flush", source, "SKIP", _time.time() - _start, f"<{MIN_TURNS_TO_FLUSH} turns")
        sys.exit(0)

    # Write context file for background process
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    context_filename = f"session-flush-{session_id}-{timestamp}.md"
    context_path = STATE_DIR / context_filename
    context_path.write_text(context, encoding="utf-8")

    # Spawn background flush process
    cmd = [
        "uv",
        "run",
        "--directory",
        str(SCRIPTS_DIR),
        "python",
        "memory_flush.py",
        "--context-file",
        str(context_path),
        "--source",
        "session-end",
    ]

    # On Windows, avoid flash console window
    creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    try:
        subprocess.Popen(  # noqa: S603
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
        )
        log_hook_execution("session-end-flush", source, "OK", _time.time() - _start, "spawned flush")
    except Exception as e:
        print(f"[session-end-flush] Failed to spawn flush: {e}", file=sys.stderr)
        log_hook_execution("session-end-flush", source, "ERROR", _time.time() - _start, f"spawn: {e}")


if __name__ == "__main__":
    main()
