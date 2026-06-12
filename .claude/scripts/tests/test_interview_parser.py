"""Tests for `interview_parser.parse_interview`."""

from __future__ import annotations

from pathlib import Path

import pytest

from config import ONBOARDING_FILE
from interview_parser import parse_interview

FIXTURE = Path(__file__).parent / "fixtures" / "mini_interview.md"

# The real interview lives under .agent/plans/, which is gitignored by design —
# absent in CI checkouts and fresh worktrees. Skip rather than fail there.
requires_interview_file = pytest.mark.skipif(
    not ONBOARDING_FILE.exists(),
    reason=".agent/plans/ is gitignored — real interview file not present",
)


@pytest.fixture(scope="module")
def fixture_path() -> Path:
    return FIXTURE


def test_parse_counts(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    assert len(iv.sections) == 2
    assert len(iv.questions) == 6


def test_section_letters(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    assert [s.letter for s in iv.sections] == ["A", "Z"]


def test_tier_detection(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    tiers = {q.id: q.tier for q in iv.questions}
    assert tiers == {"A1": 1, "A2": 2, "A3": 3, "Z1": 1, "Z2": 2, "Z3": 3}


def test_empty_vs_filled_answer(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    assert iv.get("A1").answer == ""
    assert iv.get("A2").answer == "Already-filled answer for A2."
    assert iv.get("Z3").answer == ""


def test_multiparagraph_answer_preserved(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    answer = iv.get("A3").answer
    assert "multi-paragraph\nprior answer." in answer
    assert "\n\n" in answer  # blank line between paragraphs preserved
    assert answer.endswith('the Latvian word "paldies".')


def test_hint_extraction(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    a1_hint = iv.get("A1").hint
    assert a1_hint is not None
    assert "Linārds" in a1_hint  # UTF-8 round-trip
    assert iv.get("A3").hint is None  # no hint on A3
    assert iv.get("Z2").hint is None


def test_utf8_roundtrip(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    a1 = iv.get("A1")
    assert a1.hint is not None and "ā" in a1.hint
    a3_answer = iv.get("A3").answer
    assert "paldies" in a3_answer


def test_raw_lines_preserved_byte_for_byte(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    assert "".join(iv.raw_lines) == fixture_path.read_text(encoding="utf-8")


def test_answer_line_offsets_are_consistent(fixture_path: Path) -> None:
    iv = parse_interview(fixture_path)
    for q in iv.questions:
        # `answer_start_line` is 1-indexed and points at `**Answer:**`.
        idx = q.answer_start_line - 1
        assert iv.raw_lines[idx].strip() == "**Answer:**"
        assert q.answer_end_line >= q.answer_start_line + 1


@requires_interview_file
def test_real_interview_parses() -> None:
    """The actual onboarding interview file parses to expected counts."""
    from config import ONBOARDING_FILE

    iv = parse_interview(ONBOARDING_FILE)
    assert len(iv.sections) == 27
    assert len(iv.questions) == 103
    # Every question must have a tier in {1, 2, 3}.
    assert all(q.tier in {1, 2, 3} for q in iv.questions)
    # Section AA should exist (boundaries section).
    assert any(s.letter == "AA" for s in iv.sections)


@requires_interview_file
def test_part_attached_to_section_at_open_not_flush() -> None:
    """A section must be tagged with the Part it was opened under.

    Regression: an earlier bug flushed sections using the *current* part,
    so a Part heading between Section X and Section Y would retroactively
    relabel Section X with Part Y's heading. Section I (Daily Pillars)
    should sit under Part 6, not Part 7.
    """
    from config import ONBOARDING_FILE

    iv = parse_interview(ONBOARDING_FILE)
    parts_by_letter = {s.letter: s.part for s in iv.sections}
    assert parts_by_letter["A"].startswith("Part 1")
    assert parts_by_letter["B"].startswith("Part 1")
    assert parts_by_letter["I"].startswith("Part 6")
    assert parts_by_letter["J"].startswith("Part 7")
    assert parts_by_letter["AA"].startswith("Part 11")
