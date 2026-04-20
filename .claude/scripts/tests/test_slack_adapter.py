"""Tests for .claude/chat/adapters/slack.py — allowlist, mrkdwn, splitting."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


@pytest.fixture
def adapter() -> Any:
    """Build a SlackAdapter without connecting to Slack."""
    from adapters.slack import SlackAdapter

    return SlackAdapter(
        bot_token="xoxb-test",
        app_token="xapp-test",
        allowed_users=["U123"],
        session_store=None,
    )


# ---------------------------------------------------------------------------
# Allowlist — fail-closed
# ---------------------------------------------------------------------------


def test_allowlist_allows_listed_user(adapter: Any) -> None:
    assert adapter._is_allowed("U123") is True


def test_allowlist_rejects_unlisted_user(adapter: Any) -> None:
    assert adapter._is_allowed("Uother") is False


def test_allowlist_rejects_empty_user(adapter: Any) -> None:
    assert adapter._is_allowed("") is False


def test_allowlist_empty_list_fails_closed() -> None:
    from adapters.slack import SlackAdapter

    a = SlackAdapter(bot_token="xoxb-t", app_token="xapp-t", allowed_users=[])
    assert a._is_allowed("U123") is False
    assert a._is_allowed("") is False


def test_allowlist_strips_whitespace() -> None:
    from adapters.slack import SlackAdapter

    a = SlackAdapter(bot_token="xoxb-t", app_token="xapp-t", allowed_users=["  U1  ", " "])
    assert a._is_allowed("U1") is True
    assert a._is_allowed(" ") is False


# ---------------------------------------------------------------------------
# mrkdwn conversion
# ---------------------------------------------------------------------------


def test_mrkdwn_converts_bold(adapter: Any) -> None:
    assert adapter._markdown_to_mrkdwn("**bold**") == "*bold*"


def test_mrkdwn_converts_link(adapter: Any) -> None:
    assert adapter._markdown_to_mrkdwn("[click](https://x)") == "<https://x|click>"


def test_mrkdwn_converts_heading(adapter: Any) -> None:
    assert adapter._markdown_to_mrkdwn("## H1") == "*H1*"


def test_mrkdwn_preserves_fenced_code(adapter: Any) -> None:
    src = "before\n```python\n**do not convert**\n[keep](url)\n```\nafter"
    out = adapter._markdown_to_mrkdwn(src)
    assert "```python\n**do not convert**\n[keep](url)\n```" in out
    assert out.startswith("before")
    assert out.endswith("after")


def test_mrkdwn_preserves_inline_code(adapter: Any) -> None:
    out = adapter._markdown_to_mrkdwn("use `**not converted**` now")
    assert "`**not converted**`" in out


# ---------------------------------------------------------------------------
# Message splitting
# ---------------------------------------------------------------------------


def test_split_short_message_passes_through(adapter: Any) -> None:
    chunks = adapter._split_message("short message")
    assert chunks == ["short message"]


def test_split_long_message_returns_multiple_chunks(adapter: Any) -> None:
    # 8000 chars — two paragraphs separated by double newline
    text = ("a" * 3000) + "\n\n" + ("b" * 3000) + "\n\n" + ("c" * 2000)
    chunks = adapter._split_message(text, max_length=3900)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk) <= 3900


def test_split_never_breaks_inside_fenced_block(adapter: Any) -> None:
    # 4000 chars of filler, then an open fence with 200 chars inside
    text = ("a" * 3500) + "\n\n```python\n" + ("x" * 200) + "\n```\ndone"
    chunks = adapter._split_message(text, max_length=3900)
    # No chunk should contain the open ``` without the closing ```
    for chunk in chunks:
        opens = chunk.count("```")
        assert opens % 2 == 0, f"Unbalanced fences in chunk: {chunk[-200:]!r}"


# ---------------------------------------------------------------------------
# Heartbeat-thread detection
# ---------------------------------------------------------------------------


def test_is_heartbeat_thread_delegates_to_store() -> None:
    from adapters.slack import SlackAdapter

    class _Store:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str]] = []

        def get_heartbeat_thread(self, channel: str, ts: str) -> Any:
            self.calls.append((channel, ts))
            return object() if (channel, ts) == ("C1", "100.001") else None

    store = _Store()
    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=store,
    )
    assert a._is_heartbeat_thread("C1", "100.001") is True
    assert a._is_heartbeat_thread("C1", "other") is False
    assert store.calls == [("C1", "100.001"), ("C1", "other")]


def test_is_heartbeat_thread_without_store_returns_false(adapter: Any) -> None:
    # adapter fixture has session_store=None
    assert adapter._is_heartbeat_thread("C1", "100.001") is False
