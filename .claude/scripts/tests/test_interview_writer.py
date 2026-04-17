"""Tests for `interview_writer.write_answer`."""

from __future__ import annotations

import shutil
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from interview_parser import parse_interview
from interview_writer import write_answer
from shared import file_lock

FIXTURE = Path(__file__).parent / "fixtures" / "mini_interview.md"


@pytest.fixture
def working_copy(tmp_path: Path) -> Path:
    """Copy the fixture into tmp so tests can mutate it freely."""
    dest = tmp_path / "interview.md"
    shutil.copy2(FIXTURE, dest)
    return dest


def test_write_single_line_answer(working_copy: Path) -> None:
    iv = parse_interview(working_copy)
    new_iv = write_answer(iv, "A1", "Linards Berzins, called 'L' by friends.")
    assert new_iv.get("A1").answer == "Linards Berzins, called 'L' by friends."
    # Other answers untouched.
    assert new_iv.get("A2").answer == "Already-filled answer for A2."
    assert new_iv.get("Z1").answer == ""


def test_write_empty_answer(working_copy: Path) -> None:
    iv = parse_interview(working_copy)
    new_iv = write_answer(iv, "A2", "")
    assert new_iv.get("A2").answer == ""
    # The file must still parse — no structural breakage.
    assert len(new_iv.questions) == 6


def test_write_multiparagraph(working_copy: Path) -> None:
    iv = parse_interview(working_copy)
    body = "Paragraph one with detail.\n\nParagraph two follows.\n\nParagraph three."
    new_iv = write_answer(iv, "Z3", body)
    assert new_iv.get("Z3").answer == body


def test_overwrite_existing_answer(working_copy: Path) -> None:
    iv = parse_interview(working_copy)
    assert "multi-paragraph" in iv.get("A3").answer
    new_iv = write_answer(iv, "A3", "Replaced.")
    assert new_iv.get("A3").answer == "Replaced."
    # Old text gone from the file.
    assert "multi-paragraph" not in working_copy.read_text(encoding="utf-8")


def test_other_questions_byte_stable(working_copy: Path) -> None:
    """Writing one answer must not perturb the surrounding question structure."""
    iv = parse_interview(working_copy)
    new_iv = write_answer(iv, "A1", "Test name.")
    # All non-target questions retain identical answers, prompts, hints, tiers.
    for qid in ("A2", "A3", "Z1", "Z2", "Z3"):
        original = iv.get(qid)
        updated = new_iv.get(qid)
        assert original.answer == updated.answer
        assert original.prompt == updated.prompt
        assert original.hint == updated.hint
        assert original.tier == updated.tier


def test_utf8_roundtrip(working_copy: Path) -> None:
    iv = parse_interview(working_copy)
    body = "Latviski: paldies, čau, šodien — visi diakritiskie zīmīgi."
    new_iv = write_answer(iv, "Z1", body)
    assert new_iv.get("Z1").answer == body
    text = working_copy.read_text(encoding="utf-8")
    assert "šodien" in text


def test_atomic_write_survives_interruption(working_copy: Path) -> None:
    """If the write fails mid-flight, the original file is intact."""
    iv = parse_interview(working_copy)
    original_text = working_copy.read_text(encoding="utf-8")

    def boom(self: Any, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("simulated disk failure")

    with patch.object(Path, "write_text", boom):
        with pytest.raises(RuntimeError):
            write_answer(iv, "A1", "This should never land.")

    # Original file unchanged because we write to .tmp first.
    assert working_copy.read_text(encoding="utf-8") == original_text


def test_lock_contention_blocks_then_succeeds(working_copy: Path) -> None:
    """Concurrent lock holder forces `write_answer` to wait, then succeed."""
    iv = parse_interview(working_copy)
    started = threading.Event()
    release = threading.Event()

    def hold_lock() -> None:
        with file_lock(working_copy, timeout=5.0):
            started.set()
            release.wait(timeout=5.0)

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert started.wait(timeout=2.0)

    # Release the lock shortly after triggering the writer so it can succeed
    # within its own 5 s timeout.
    def releaser() -> None:
        time.sleep(0.3)
        release.set()

    threading.Thread(target=releaser, daemon=True).start()

    new_iv = write_answer(iv, "Z2", "Boundary respected.")
    holder.join(timeout=5.0)
    assert new_iv.get("Z2").answer == "Boundary respected."
