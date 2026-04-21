"""Tests for .claude/chat/summary_writer.py."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import yaml  # type: ignore[import-untyped]

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


def _read_frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n")
    _, fm, _body = text.split("---", 2)
    data = yaml.safe_load(fm)
    assert isinstance(data, dict)
    return data


def test_first_turn_creates_file_with_frontmatter(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "marketing"
    ts = datetime(2026, 4, 21, 16, 55, 0)

    result = append_summary(
        folder=folder,
        channel="marketing",
        channel_id="C01234ABC",
        thread_ts="1729532400.123456",
        user_text="What's our pricing for the consulting retainer?",
        bot_text="Your baseline retainer is £5k/month for two-day-a-week work.",
        timestamp=ts,
        cost_usd=0.0123,
    )

    assert result.created is True
    assert result.turn_number == 1
    assert result.path.exists()
    assert result.path.name.startswith("2026-04-21_1729532400.123456_")
    assert result.path.name.endswith(".md")

    fm = _read_frontmatter(result.path)
    assert fm["channel"] == "marketing"
    assert fm["channel_id"] == "C01234ABC"
    assert fm["thread_ts"] == "1729532400.123456"
    assert fm["turns"] == 1
    assert fm["created_at"] == "2026-04-21T16:55:00"
    assert fm["updated_at"] == "2026-04-21T16:55:00"

    body = result.path.read_text(encoding="utf-8")
    assert "# What's our pricing for the consulting retainer?" in body
    assert "## Turn 1 · 16:55" in body
    assert "**You:** What's our pricing for the consulting retainer?" in body
    assert "**Fredis:** Your baseline retainer" in body


def test_second_turn_appends_and_bumps_frontmatter(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "marketing"
    t1 = datetime(2026, 4, 21, 16, 55, 0)
    t2 = datetime(2026, 4, 21, 17, 2, 0)

    append_summary(
        folder=folder,
        channel="marketing",
        channel_id="C01234ABC",
        thread_ts="1729532400.123456",
        user_text="first question",
        bot_text="first answer",
        timestamp=t1,
        cost_usd=0.01,
    )
    result = append_summary(
        folder=folder,
        channel="marketing",
        channel_id="C01234ABC",
        thread_ts="1729532400.123456",
        user_text="follow-up question",
        bot_text="follow-up answer",
        timestamp=t2,
        cost_usd=0.02,
    )

    assert result.created is False
    assert result.turn_number == 2

    # Only one file in the folder.
    files = list(folder.glob("*.md"))
    assert len(files) == 1
    assert files[0] == result.path

    fm = _read_frontmatter(result.path)
    assert fm["turns"] == 2
    assert fm["created_at"] == "2026-04-21T16:55:00"
    assert fm["updated_at"] == "2026-04-21T17:02:00"
    # Cost accumulates.
    assert fm["total_cost_usd"] == 0.03

    text = result.path.read_text(encoding="utf-8")
    # Both turns present, correct order.
    idx1 = text.index("## Turn 1 · 16:55")
    idx2 = text.index("## Turn 2 · 17:02")
    assert idx1 < idx2
    assert "first question" in text
    assert "follow-up question" in text
    assert "first answer" in text
    assert "follow-up answer" in text
    # First-turn heading preserved — NOT overwritten by the second turn's text.
    assert "# first question" in text
    assert "# follow-up question" not in text


def test_lazy_folder_creation(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "does" / "not" / "yet" / "exist"
    assert not folder.exists()

    append_summary(
        folder=folder,
        channel="ideation",
        channel_id="C1",
        thread_ts="1700.001",
        user_text="scratch an idea",
        bot_text="ok",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    assert folder.is_dir()
    assert len(list(folder.glob("*.md"))) == 1


def test_long_heading_is_truncated(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "ideation"
    long_text = (
        "This is a really long first message that should be clipped in the "
        "summary heading because otherwise the markdown heading would be "
        "absurdly wide and unreadable in Obsidian and GitHub previews."
    )

    result = append_summary(
        folder=folder,
        channel="ideation",
        channel_id="C1",
        thread_ts="1700.001",
        user_text=long_text,
        bot_text="got it",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    text = result.path.read_text(encoding="utf-8")
    # Find the `# ` heading line.
    heading_line = next(line for line in text.splitlines() if line.startswith("# "))
    # Heading body (minus `# ` prefix) must be ≤80 chars, ending with ellipsis.
    heading_body = heading_line[2:]
    assert len(heading_body) <= 80
    assert heading_body.endswith("…")


def test_slug_sanitised_for_filesystem(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "legal"
    # Input with punctuation, path separators, and non-ASCII.
    user_text = "Can we use /etc/passwd as a variable name? — no, really! 😅"

    result = append_summary(
        folder=folder,
        channel="legal",
        channel_id="C1",
        thread_ts="1700.001",
        user_text=user_text,
        bot_text="no",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    # The slug portion sits between the thread_ts and `.md`.
    name = result.path.name
    assert name.startswith("2026-04-21_1700.001_")
    slug = name[len("2026-04-21_1700.001_") : -len(".md")]
    # Only lowercase alphanumerics and hyphens.
    assert slug
    for ch in slug:
        assert ch.isalnum() or ch == "-", f"slug has bad char {ch!r}"
    # No path separators.
    assert "/" not in slug
    assert "\\" not in slug


def test_empty_user_text_slug_fallback(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "x"

    result = append_summary(
        folder=folder,
        channel="x",
        channel_id="C1",
        thread_ts="1700.001",
        user_text="!!!",
        bot_text="ok",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    # Non-alnum input collapses to the fallback slug.
    assert result.path.name.endswith("_thread.md")


def test_slack_permalink_in_frontmatter_when_provided(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "product"
    result = append_summary(
        folder=folder,
        channel="product",
        channel_id="C1",
        thread_ts="1700.001",
        user_text="roadmap question",
        bot_text="answer",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
        slack_permalink="https://workspace.slack.com/archives/C1/p1700001",
    )

    fm = _read_frontmatter(result.path)
    assert fm["slack_permalink"] == "https://workspace.slack.com/archives/C1/p1700001"


def test_no_slack_permalink_means_absent_key(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "product"
    result = append_summary(
        folder=folder,
        channel="product",
        channel_id="C1",
        thread_ts="1700.001",
        user_text="q",
        bot_text="a",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    fm = _read_frontmatter(result.path)
    assert "slack_permalink" not in fm


def test_dm_channel_name_empty_is_tolerated(tmp_path: Path) -> None:
    """DMs pass `channel=None`; the writer must not crash on None."""
    from summary_writer import append_summary

    folder = tmp_path / "daily"
    result = append_summary(
        folder=folder,
        channel=None,
        channel_id="D001",
        thread_ts="1700.001",
        user_text="private question",
        bot_text="private answer",
        timestamp=datetime(2026, 4, 21, 10, 0, 0),
    )

    fm = _read_frontmatter(result.path)
    assert fm["channel"] == ""
    assert fm["channel_id"] == "D001"


def test_third_turn_accumulates_cost_and_timestamp(tmp_path: Path) -> None:
    from summary_writer import append_summary

    folder = tmp_path / "finance"
    for i, t in enumerate(
        [
            datetime(2026, 4, 21, 9, 0, 0),
            datetime(2026, 4, 21, 9, 5, 0),
            datetime(2026, 4, 21, 9, 10, 0),
        ],
        start=1,
    ):
        append_summary(
            folder=folder,
            channel="finance",
            channel_id="C1",
            thread_ts="1700.001",
            user_text=f"q{i}",
            bot_text=f"a{i}",
            timestamp=t,
            cost_usd=0.01,
        )

    files = list(folder.glob("*.md"))
    assert len(files) == 1
    fm = _read_frontmatter(files[0])
    assert fm["turns"] == 3
    assert fm["updated_at"] == "2026-04-21T09:10:00"
    assert fm["total_cost_usd"] == 0.03
    body = files[0].read_text(encoding="utf-8")
    assert "Turn 1" in body and "Turn 2" in body and "Turn 3" in body
