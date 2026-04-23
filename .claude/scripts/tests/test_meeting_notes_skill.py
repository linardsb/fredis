"""Convention tests for the `meeting-notes` skill.

Pure-markdown skill — these tests verify that SKILL.md declares the right
capture-mode contract and that the folder scaffold is in place.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_FILE = REPO_ROOT / ".claude" / "skills" / "meeting-notes" / "SKILL.md"
MEETINGS_README = REPO_ROOT / "Fredis" / "Memory" / "meetings" / "README.md"
CONVENTION_FILE = REPO_ROOT / ".claude" / "skills" / "_shared" / "draft-path-convention.md"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


def test_skill_file_exists() -> None:
    assert SKILL_FILE.is_file()


def test_frontmatter_declares_name(skill_text: str) -> None:
    assert skill_text.startswith("---\n")
    fm = skill_text[3 : skill_text.index("---", 3)]
    assert "name: meeting-notes" in fm


def test_path_pattern_matches_capture_mode_shape(skill_text: str) -> None:
    # Path must be `Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md` — the date
    # separator is underscore, not the hyphen used by drafts/.
    assert re.search(
        r"Fredis/Memory/meetings/YYYY-MM-DD_<slug>\.md",
        skill_text,
    ), "Capture-mode path shape must be documented exactly"


def test_template_has_required_sections(skill_text: str) -> None:
    # Fixed-order sections are the contract that retrieval relies on.
    for heading in (
        "## Attendees",
        "## Agenda",
        "## Discussion",
        "## Decisions",
        "## Action items",
        "## Open questions",
    ):
        assert heading in skill_text, f"Template missing required section `{heading}`"


def test_frontmatter_template_lists_meeting_metadata(skill_text: str) -> None:
    for key in ("type: meeting", "date:", "attendees:", "lane:"):
        assert key in skill_text, f"Template missing frontmatter key `{key}`"


def test_carve_out_is_documented(skill_text: str) -> None:
    # The whole point of the capture-mode carve-out is visibility — Linards
    # needs to see why this skill breaks the drafts-path rule.
    lowered = skill_text.lower()
    assert "carve-out" in lowered or "exception" in lowered
    assert "capture" in lowered


def test_shared_convention_lists_meeting_notes_carve_out() -> None:
    # If the shared convention doesn't list this skill as an exception, a
    # future reader would see the direct write and think it's a bug.
    text = CONVENTION_FILE.read_text(encoding="utf-8")
    assert "meeting-notes" in text
    assert "meetings/" in text


def test_meetings_readme_scaffold_exists() -> None:
    assert MEETINGS_README.is_file(), (
        "Fredis/Memory/meetings/README.md must be scaffolded so the folder "
        "isn't empty on fresh clones and retrieval via --path-prefix meetings/ "
        "has something to index."
    )
    text = MEETINGS_README.read_text(encoding="utf-8")
    assert "meeting-notes" in text


def test_boundary_no_calendar_or_transcription(skill_text: str) -> None:
    lowered = skill_text.lower()
    # Out-of-scope items are the non-goals. If these drift, scope creep starts.
    assert "no calendar integration" in lowered
    assert "no auto-transcription" in lowered
