"""
Atomic writer for the Phase 1 onboarding interview file.

Replaces the answer body of a single question while preserving every other
byte of the source file. Writes via temp file + `os.replace` for atomicity,
guarded by `file_lock` from `shared.py` so concurrent Obsidian saves or
`git-sync` pulls cannot corrupt the round-trip.
"""

from __future__ import annotations

import os
import re

from interview_parser import Interview, parse_interview
from shared import file_lock


def _normalise_answer(new_answer: str) -> str:
    """Strip trailing whitespace per line and collapse 3+ blank lines to 2.

    Keeps a single trailing newline. Empty input becomes an empty string.
    """
    if not new_answer.strip():
        return ""
    lines = [line.rstrip() for line in new_answer.splitlines()]
    # Collapse runs of >2 blank lines to exactly 2.
    collapsed: list[str] = []
    blank_run = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                collapsed.append(line)
        else:
            blank_run = 0
            collapsed.append(line)
    # Trim leading and trailing blank lines.
    while collapsed and collapsed[0] == "":
        collapsed.pop(0)
    while collapsed and collapsed[-1] == "":
        collapsed.pop()
    return "\n".join(collapsed)


def write_answer(interview: Interview, question_id: str, new_answer: str) -> Interview:
    """Persist `new_answer` for `question_id` and return a fresh `Interview`.

    The file is rewritten atomically (temp file + `os.replace`) under a
    cross-platform file lock. Returns a re-parsed `Interview` so callers see
    updated `answer_start_line` / `answer_end_line` offsets.
    """
    question = interview.get(question_id)
    path = interview.source_path
    raw_lines = list(interview.raw_lines)

    # `answer_start_line` is 1-indexed and points at `**Answer:**`.
    # `answer_end_line` is 1-indexed exclusive end of the answer block.
    marker_idx = question.answer_start_line - 1  # index of `**Answer:**` line
    body_start = marker_idx + 1
    body_end = question.answer_end_line - 1  # exclusive in 0-indexed terms

    # Detect whether the original file had a trailing newline so we preserve it.
    file_ends_with_newline = bool(raw_lines) and raw_lines[-1].endswith("\n")

    normalised = _normalise_answer(new_answer)
    if normalised == "":
        # Empty answer: a single blank line keeps the parser happy on re-read.
        replacement = ["\n"]
    else:
        # Build replacement lines with trailing newlines to match file style.
        replacement = [f"{line}\n" for line in normalised.split("\n")]
        # Append a blank separator line so the next structural element doesn't
        # collide with the answer body (mirrors original file style).
        replacement.append("\n")

    new_raw = raw_lines[:body_start] + replacement + raw_lines[body_end:]

    # Restore original trailing-newline state if our slicing changed it.
    if new_raw:
        if file_ends_with_newline and not new_raw[-1].endswith("\n"):
            new_raw[-1] = new_raw[-1] + "\n"
        elif not file_ends_with_newline and new_raw[-1].endswith("\n"):
            new_raw[-1] = new_raw[-1].rstrip("\n")

    new_text = "".join(new_raw)
    # Collapse runs of >2 consecutive blank lines anywhere created by edits.
    new_text = re.sub(r"\n{4,}", "\n\n\n", new_text)

    with file_lock(path, timeout=5.0):
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(new_text, encoding="utf-8")
        os.replace(tmp, path)

    return parse_interview(path)
