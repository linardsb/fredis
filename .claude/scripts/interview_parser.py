"""
Parser for the Phase 1 onboarding interview markdown file.

Reads `.agent/plans/phase1-onboarding-interview.md` (or any file using the same
question format) into a typed `Interview` model. Pure logic — no I/O beyond a
single read of the source path. Safe to import without Textual.

Question format:

    **{ID}. {★|★★|★★★} {prompt text…}** _(optional hint)_

    **Answer:**

    {answer body — may be empty, single line, or multi-paragraph}

Where `ID` is a 1–2 letter section code followed by an integer (e.g. `A1`, `AA3`).
Sections start with `## Section X — Title`. Parts start with `# Part N — Title`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# Question opener — matches the bold line that introduces a question.
# Captures: id_letters, id_number, stars, remainder of opener line.
_QUESTION_OPENER = re.compile(r"^\*\*([A-Z]{1,2})(\d+)\. (★{1,3}) (.*)$")

# Section heading: `## Section X — Title`
_SECTION_HEADING = re.compile(r"^## Section ([A-Z]{1,2}) — (.+)$")

# Part heading: `# Part N — Title`
_PART_HEADING = re.compile(r"^# Part (\d+) — (.+)$")

# Answer marker — must be the entire (trimmed) line.
_ANSWER_MARKER = re.compile(r"^\*\*Answer:\*\*\s*$")

# Trailing hint extractor — `_(...)_` at end of the prompt blob, optionally
# followed by closing bold markers we may have already stripped.
_TRAILING_HINT = re.compile(r"\s*_\((.+?)\)_\s*$", re.DOTALL)


@dataclass(frozen=True, slots=True)
class Question:
    """A single interview question and its current answer state."""

    id: str
    section: str
    number: int
    tier: int  # 1 = ★, 2 = ★★, 3 = ★★★
    prompt: str
    hint: str | None
    answer: str
    answer_start_line: int  # 1-indexed line in source where `**Answer:**` sits
    answer_end_line: int  # 1-indexed exclusive end of the answer block


@dataclass(frozen=True, slots=True)
class Section:
    """A section heading and its questions."""

    letter: str
    title: str
    part: str
    questions: tuple[Question, ...]


@dataclass(frozen=True, slots=True)
class Interview:
    """Parsed interview file with verbatim source preserved for round-tripping."""

    source_path: Path
    sections: tuple[Section, ...]
    raw_lines: tuple[str, ...] = field(repr=False)

    @property
    def questions(self) -> tuple[Question, ...]:
        """Flat view of all questions in document order."""
        return tuple(q for s in self.sections for q in s.questions)

    def get(self, qid: str) -> Question:
        """Look up a question by ID. Raises KeyError if missing."""
        for q in self.questions:
            if q.id == qid:
                return q
        raise KeyError(qid)


def parse_interview(path: Path) -> Interview:
    """Parse the interview markdown file into a typed `Interview`.

    Keeps `raw_lines` (with line endings) so the writer can round-trip the file
    byte-for-byte outside the answer slots.
    """
    text = path.read_text(encoding="utf-8")
    raw_lines = tuple(text.splitlines(keepends=True))
    # Working copy without trailing newlines for matching.
    lines = [line.rstrip("\n").rstrip("\r") for line in raw_lines]

    sections: list[Section] = []
    current_part: str = ""
    current_section_letter: str | None = None
    current_section_title: str = ""
    current_section_part: str = ""
    current_questions: list[Question] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]

        part_match = _PART_HEADING.match(line)
        if part_match:
            current_part = f"Part {part_match.group(1)} — {part_match.group(2)}"
            i += 1
            continue

        section_match = _SECTION_HEADING.match(line)
        if section_match:
            # Flush the previous section using the part it was opened under,
            # not the current_part (which may have advanced since then).
            if current_section_letter is not None:
                sections.append(
                    Section(
                        letter=current_section_letter,
                        title=current_section_title,
                        part=current_section_part,
                        questions=tuple(current_questions),
                    )
                )
            current_section_letter = section_match.group(1)
            current_section_title = section_match.group(2).strip()
            current_section_part = current_part
            current_questions = []
            i += 1
            continue

        opener_match = _QUESTION_OPENER.match(line)
        if opener_match and current_section_letter is not None:
            qid_letters = opener_match.group(1)
            qid_number = int(opener_match.group(2))
            stars = opener_match.group(3)
            tier = len(stars)
            opener_remainder = opener_match.group(4)

            # Accumulate prompt+hint blob: opener remainder plus any continuation
            # lines until we hit the blank line that precedes `**Answer:**`.
            blob_parts: list[str] = [opener_remainder]
            j = i + 1
            while j < n:
                nxt = lines[j]
                if _ANSWER_MARKER.match(nxt):
                    break
                if nxt.strip() == "":
                    # Blank line — usually the gap between prompt and answer.
                    # Peek ahead: if the next non-blank line is the answer marker,
                    # this blank terminates the prompt blob.
                    k = j + 1
                    while k < n and lines[k].strip() == "":
                        k += 1
                    if k < n and _ANSWER_MARKER.match(lines[k]):
                        break
                    # Otherwise this blank is part of the prompt body — keep going.
                    blob_parts.append("")
                    j += 1
                    continue
                blob_parts.append(nxt)
                j += 1

            blob = "\n".join(blob_parts).strip()
            # Strip trailing closing-bold markers.
            blob = re.sub(r"\*\*\s*$", "", blob).rstrip()
            hint_match = _TRAILING_HINT.search(blob)
            if hint_match:
                hint: str | None = hint_match.group(1).strip()
                prompt = blob[: hint_match.start()].rstrip()
            else:
                hint = None
                prompt = blob
            # Strip trailing closing-bold from the prompt remainder.
            prompt = re.sub(r"\*\*\s*$", "", prompt).rstrip()

            # Find the answer marker line.
            answer_marker_idx = j
            while answer_marker_idx < n and not _ANSWER_MARKER.match(lines[answer_marker_idx]):
                answer_marker_idx += 1
            if answer_marker_idx >= n:
                # Malformed question — skip and continue past the opener.
                i = j
                continue

            # Answer body runs from the line after the marker until the next
            # structural element (next question opener, section, part, `---`,
            # or EOF). Trim leading and trailing blank lines from the body.
            body_start = answer_marker_idx + 1
            body_end = body_start
            while body_end < n:
                nxt = lines[body_end]
                if (
                    _QUESTION_OPENER.match(nxt)
                    or _SECTION_HEADING.match(nxt)
                    or _PART_HEADING.match(nxt)
                    or nxt.strip() == "---"
                ):
                    break
                body_end += 1

            # Trim trailing blanks from the body for the parsed `answer` string,
            # but keep `answer_end_line` pointing one past the last *content* line.
            content_end = body_end
            while content_end > body_start and lines[content_end - 1].strip() == "":
                content_end -= 1
            content_start = body_start
            while content_start < content_end and lines[content_start].strip() == "":
                content_start += 1

            if content_start >= content_end:
                answer_text = ""
            else:
                answer_text = "\n".join(lines[content_start:content_end])

            current_questions.append(
                Question(
                    id=f"{qid_letters}{qid_number}",
                    section=qid_letters,
                    number=qid_number,
                    tier=tier,
                    prompt=prompt,
                    hint=hint,
                    answer=answer_text,
                    answer_start_line=answer_marker_idx + 1,  # 1-indexed
                    answer_end_line=body_end + 1,  # 1-indexed exclusive
                )
            )
            i = body_end
            continue

        i += 1

    # Flush the final section (using the part it was opened under).
    if current_section_letter is not None:
        sections.append(
            Section(
                letter=current_section_letter,
                title=current_section_title,
                part=current_section_part,
                questions=tuple(current_questions),
            )
        )

    return Interview(
        source_path=path,
        sections=tuple(sections),
        raw_lines=raw_lines,
    )
