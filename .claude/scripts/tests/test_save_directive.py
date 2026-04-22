"""Tests for .claude/chat/save_directive.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


# ---------------------------------------------------------------------------
# Match — save-to directive
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected_target",
    [
        ("save this to email-hub", "email-hub"),
        ("save this to build-email-hub", "build-email-hub"),
        ("Save this to email-hub", "email-hub"),  # case-insensitive verb
        ("SAVE THIS TO email-hub", "email-hub"),
        ("save it to research-ai", "research-ai"),
        ("save this in marketing", "marketing"),
        ("save this under legal", "legal"),
        ("save this to research/ai/sora", "research/ai/sora"),  # nested path
        ("save this to builds/email-hub/api", "builds/email-hub/api"),
    ],
)
def test_save_directive_match_extracts_target(text: str, expected_target: str) -> None:
    from save_directive import parse

    result = parse(text)

    assert result.target == expected_target
    assert result.is_clear is False
    assert result.matched is True


def test_save_directive_uppercase_target_normalised_to_lowercase() -> None:
    """Targets are lowercased to match YAML channel keys."""
    from save_directive import parse

    result = parse("save this to Email-Hub")

    assert result.target == "email-hub"


def test_save_directive_trailing_slash_stripped() -> None:
    from save_directive import parse

    result = parse("save this to research/ai/sora/")

    assert result.target == "research/ai/sora"


def test_save_directive_strips_from_cleaned_text() -> None:
    from save_directive import parse

    result = parse(
        "here are pricing thoughts for the app, save this to email-hub please"
    )

    assert result.target == "email-hub"
    # The parsed span is removed; surrounding text stays natural.
    assert "save this to" not in result.cleaned_text
    assert "pricing thoughts for the app" in result.cleaned_text


def test_save_directive_last_match_wins() -> None:
    """Multiple save directives in one message → take the LAST one."""
    from save_directive import parse

    result = parse("save this to ideation, actually save this to email-hub")

    assert result.target == "email-hub"


def test_save_directive_stops_at_trailing_punctuation() -> None:
    from save_directive import parse

    assert parse("save this to email-hub.").target == "email-hub"
    assert parse("save this to email-hub, then continue").target == "email-hub"
    assert parse("save this to email-hub!").target == "email-hub"


def test_save_directive_stops_at_whitespace() -> None:
    from save_directive import parse

    result = parse("save this to email-hub please")

    assert result.target == "email-hub"


# ---------------------------------------------------------------------------
# No match — must NOT fire on natural chat
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "save your thoughts for later",  # no `this|it`
        "let's save this for later",  # no `to|in|under`
        "could you file this somewhere?",  # wrong verb
        "put this in writing",  # wrong pattern
        "tag as email-hub",  # not supported (loose match rejected)
        "",  # empty
        "just a regular message",
        "save this. to email-hub",  # sentence boundary breaks the phrase
    ],
)
def test_save_directive_no_match_returns_none(text: str) -> None:
    from save_directive import parse

    result = parse(text)

    assert result.target is None
    assert result.is_clear is False
    assert result.matched is False
    # Input unchanged (for empty string or non-matches).
    assert result.cleaned_text == text


def test_save_directive_missing_target_is_no_match() -> None:
    """`save this to` with no target token → no match."""
    from save_directive import parse

    # No target after the preposition.
    result = parse("save this to")

    assert result.target is None
    assert result.matched is False


def test_save_directive_rejects_unsafe_target_chars() -> None:
    """Targets cannot contain `..`, quotes, or whitespace."""
    from save_directive import parse

    # `..` contains a literal dot which is NOT in the allowed char class.
    # The match should not capture it.
    result = parse("save this to ../etc")
    # The regex is anchored; since `.` isn't allowed, match fails or stops early.
    assert result.target != "../etc"


# ---------------------------------------------------------------------------
# Clear directive
# ---------------------------------------------------------------------------


def test_clear_save_target_match() -> None:
    from save_directive import parse

    result = parse("clear save target")

    assert result.is_clear is True
    assert result.target is None
    assert result.matched is True


def test_clear_save_target_case_insensitive() -> None:
    from save_directive import parse

    result = parse("Clear Save Target")

    assert result.is_clear is True


def test_clear_save_target_in_sentence() -> None:
    from save_directive import parse

    result = parse("ok, clear save target now, I'm done with that thread")

    assert result.is_clear is True
    assert "clear save target" not in result.cleaned_text.lower()
    assert "done with that thread" in result.cleaned_text


def test_clear_wins_over_save_when_both_present() -> None:
    """If both `save` and `clear` appear, clear is the winning intent."""
    from save_directive import parse

    result = parse("clear save target, and save this to email-hub")

    assert result.is_clear is True
    assert result.target is None


# ---------------------------------------------------------------------------
# Cleaned-text whitespace collapse
# ---------------------------------------------------------------------------


def test_cleaned_text_collapses_whitespace_left_by_excision() -> None:
    from save_directive import parse

    result = parse("some text    save this to ideation    more text")

    assert result.cleaned_text == "some text more text"


def test_cleaned_text_preserves_paragraph_breaks() -> None:
    from save_directive import parse

    text = (
        "first paragraph about pricing\n\nsave this to email-hub\n\n"
        "second paragraph on positioning"
    )
    result = parse(text)

    assert result.target == "email-hub"
    assert "first paragraph" in result.cleaned_text
    assert "second paragraph" in result.cleaned_text
    assert "save this to" not in result.cleaned_text


def test_empty_text_short_circuits() -> None:
    from save_directive import parse

    result = parse("")

    assert result.target is None
    assert result.is_clear is False
    assert result.cleaned_text == ""
