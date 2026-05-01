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


# ---------------------------------------------------------------------------
# Thread auto-engage — follow-ups without @mention once Fredis has replied.
# ---------------------------------------------------------------------------


def test_is_existing_chat_session_delegates_to_store() -> None:
    """Channel+thread key with a session in the store → True; without → False."""
    from adapters.slack import SlackAdapter

    class _Store:
        def __init__(self) -> None:
            self.calls: list[tuple[str, str, str]] = []

        def get(self, platform: str, channel: str, ts: str) -> Any:
            self.calls.append((platform, channel, ts))
            return object() if (platform, channel, ts) == ("slack", "C1", "200.002") else None

        def get_heartbeat_thread(self, channel: str, ts: str) -> Any:
            return None  # unused here

    store = _Store()
    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=store,
    )
    assert a._is_existing_chat_session("C1", "200.002") is True
    assert a._is_existing_chat_session("C1", "nope") is False
    assert store.calls == [("slack", "C1", "200.002"), ("slack", "C1", "nope")]


def test_is_existing_chat_session_without_store_returns_false(adapter: Any) -> None:
    """Fail-closed when session_store is None — can't engage if we can't check."""
    assert adapter._is_existing_chat_session("C1", "200.002") is False


def test_is_existing_chat_session_store_error_fails_closed() -> None:
    """Store raising must not crash the handler — default to not-engaged."""
    from adapters.slack import SlackAdapter

    class _BrokenStore:
        def get(self, *_: Any, **__: Any) -> Any:
            raise RuntimeError("db offline")

    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=_BrokenStore(),
    )
    assert a._is_existing_chat_session("C1", "200.002") is False


def _run_on_message(adapter_obj: Any, event: dict[str, Any]) -> None:
    """Sync helper: drive the async _on_message handler via asyncio.run()."""
    import asyncio

    asyncio.run(adapter_obj._on_message(event, say=None, client=None))


def test_on_message_auto_engages_in_existing_chat_thread() -> None:
    """Channel message in a thread with an existing chat session is queued.

    This is the new behaviour — previously only heartbeat threads triggered
    channel-message handling; now any thread where Fredis already has a
    session counts too.
    """
    from adapters.slack import SlackAdapter

    class _Store:
        def get(self, platform: str, channel: str, ts: str) -> Any:
            # Sentinel session for this (slack, C1, 300.003) thread.
            return object() if (platform, channel, ts) == ("slack", "C1", "300.003") else None

        def get_heartbeat_thread(self, channel: str, ts: str) -> Any:
            return None  # NOT a heartbeat thread — this is the key test

    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=_Store(),
    )

    event = {
        "user": "U1",
        "channel": "C1",
        "channel_type": "channel",
        "thread_ts": "300.003",
        "ts": "300.004",
        "text": "follow-up with no mention",
    }

    _run_on_message(a, event)
    assert a._queue.qsize() == 1


def test_on_message_ignores_untracked_channel_thread() -> None:
    """Channel message in a thread Fredis isn't engaged in is dropped."""
    from adapters.slack import SlackAdapter

    class _Store:
        def get(self, *_: Any, **__: Any) -> Any:
            return None

        def get_heartbeat_thread(self, *_: Any, **__: Any) -> Any:
            return None

    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=_Store(),
    )

    event = {
        "user": "U1",
        "channel": "C1",
        "channel_type": "channel",
        "thread_ts": "400.004",
        "ts": "400.005",
        "text": "random channel chatter",
    }

    _run_on_message(a, event)
    assert a._queue.qsize() == 0


def test_on_message_ignores_top_level_channel_message() -> None:
    """Top-level channel message (no thread_ts) always requires @Fredis."""
    from adapters.slack import SlackAdapter

    class _Store:
        def get(self, *_: Any, **__: Any) -> Any:
            return object()  # even with an existing session — top-level should ignore

        def get_heartbeat_thread(self, *_: Any, **__: Any) -> Any:
            return None

    a = SlackAdapter(
        bot_token="xoxb-t",
        app_token="xapp-t",
        allowed_users=["U1"],
        session_store=_Store(),
    )

    event = {
        "user": "U1",
        "channel": "C1",
        "channel_type": "channel",
        # no thread_ts
        "ts": "500.005",
        "text": "hello channel",
    }

    _run_on_message(a, event)
    assert a._queue.qsize() == 0


# ---------------------------------------------------------------------------
# _neutralise_mentions (Phase 4) — @channel / @here / @everyone / <@USER> /
# <!subteam> triggers are defanged; URL links pass through untouched.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,trigger",
    [
        ("<!channel> hey team", "<!channel>"),
        ("<!here> quick question", "<!here>"),
        ("<!everyone> announcement", "<!everyone>"),
        ("attn <@U123456> please review", "<@U123456>"),
        ("<!subteam^S12345|devs> sanity check", "<!subteam^S12345|devs>"),
    ],
)
def test_neutralise_mentions_defangs_all_broadcast_shapes(raw: str, trigger: str) -> None:
    from adapters.slack import _neutralise_mentions

    out = _neutralise_mentions(raw)
    # The raw trigger (exact match) no longer appears
    assert trigger not in out
    # Human-readable text is preserved after the zero-width joiner
    label = trigger[1:]  # drop leading "<"
    assert label in out  # "!channel>" still reads fine
    # Output still contains a "<" (just with ZWJ inside now)
    assert "<" in out


def test_neutralise_mentions_preserves_url_links() -> None:
    from adapters.slack import _neutralise_mentions

    url_form = "see <https://example.com|the docs> for details"
    out = _neutralise_mentions(url_form)
    assert out == url_form


def test_neutralise_mentions_preserves_plain_text() -> None:
    from adapters.slack import _neutralise_mentions

    plain = "no mentions here, just text"
    assert _neutralise_mentions(plain) == plain


def test_neutralise_mentions_handles_multiple_triggers() -> None:
    from adapters.slack import _neutralise_mentions

    raw = "<!channel> and <@UABCDEF> and <!subteam^SABCDEF|team>"
    out = _neutralise_mentions(raw)
    assert "<!channel>" not in out
    assert "<@UABCDEF>" not in out
    assert "<!subteam^SABCDEF|team>" not in out


# ---------------------------------------------------------------------------
# RateLimiter (Phase 9.2) — sliding-window burst + hourly limits
# ---------------------------------------------------------------------------


def test_rate_limiter_allows_under_burst_limit() -> None:
    from adapters.slack import RateLimiter

    rl = RateLimiter(burst_limit=5, burst_window_seconds=60)
    for _ in range(5):
        ok, _ = rl.check("U1")
        assert ok is True


def test_rate_limiter_blocks_burst_over_limit() -> None:
    from adapters.slack import RateLimiter

    rl = RateLimiter(burst_limit=5, burst_window_seconds=60)
    for _ in range(5):
        rl.check("U1")
    ok, reason = rl.check("U1")
    assert ok is False
    assert "burst" in reason


def test_rate_limiter_blocks_hourly_over_limit() -> None:
    from adapters.slack import RateLimiter

    # Large burst window so only the hourly cap trips. Note: the limiter
    # stamps time via `_now()` so monkeypatching it lets us advance freely.
    rl = RateLimiter(
        burst_limit=100,
        burst_window_seconds=60.0,
        hourly_limit=30,
        hourly_window_seconds=3600.0,
    )
    fake_time = [0.0]

    def _tick() -> float:
        return fake_time[0]

    rl._now = _tick

    # Feed 30 events spaced 90s apart — well under 3600s but exceeds burst
    # window so each event sits alone in its burst slot, tripping only the
    # hourly counter on #31.
    for i in range(30):
        fake_time[0] = i * 90.0
        ok, _ = rl.check("U1")
        assert ok is True, f"event {i} unexpectedly blocked"

    fake_time[0] = 30 * 90.0
    ok, reason = rl.check("U1")
    assert ok is False
    assert "hourly" in reason


def test_rate_limiter_per_user_isolation() -> None:
    from adapters.slack import RateLimiter

    rl = RateLimiter(burst_limit=2, burst_window_seconds=60)
    for _ in range(2):
        assert rl.check("U1") == (True, "")
    assert rl.check("U1")[0] is False
    # Different user still allowed.
    assert rl.check("U2") == (True, "")


def test_rate_limiter_window_ages_out() -> None:
    from adapters.slack import RateLimiter

    rl = RateLimiter(burst_limit=2, burst_window_seconds=60)
    fake_time = [0.0]
    rl._now = lambda: fake_time[0]

    fake_time[0] = 0.0
    rl.check("U1")
    fake_time[0] = 30.0
    rl.check("U1")
    fake_time[0] = 45.0
    assert rl.check("U1")[0] is False  # burst exceeded

    # Advance past the burst window — first two events age out.
    fake_time[0] = 100.0
    assert rl.check("U1") == (True, "")


# ---------------------------------------------------------------------------
# _resolve_channel_name — Phase 11 channel routing
# ---------------------------------------------------------------------------


class _FakeClient:
    """Minimal stand-in for ``AsyncApp.client`` used by ``_resolve_channel_name``."""

    def __init__(self, name: str | None = "marketing", raises: bool = False) -> None:
        self._name = name
        self._raises = raises
        self.call_count = 0

    async def conversations_info(self, *, channel: str) -> dict[str, Any]:
        self.call_count += 1
        if self._raises:
            raise RuntimeError("channels:read scope missing")
        ch: dict[str, Any] = {"id": channel}
        if self._name is not None:
            ch["name"] = self._name
        return {"ok": True, "channel": ch}


def _inject_fake_client(adapter: Any, client: _FakeClient) -> None:
    """Replace ``adapter.app.client`` with ``client`` for name-lookup tests."""
    class _FakeApp:
        pass

    app = _FakeApp()
    app.client = client  # type: ignore[attr-defined]
    adapter.app = app


def test_resolve_channel_name_dm_skips_api_call(adapter: Any) -> None:
    import asyncio

    client = _FakeClient(name="should-not-be-looked-up")
    _inject_fake_client(adapter, client)

    result = asyncio.run(adapter._resolve_channel_name("D001", is_dm=True))

    assert result is None
    assert client.call_count == 0


def test_resolve_channel_name_hits_api_and_caches(adapter: Any) -> None:
    import asyncio

    client = _FakeClient(name="marketing")
    _inject_fake_client(adapter, client)

    # First call: API hit.
    r1 = asyncio.run(adapter._resolve_channel_name("C123", is_dm=False))
    # Second call: served from cache.
    r2 = asyncio.run(adapter._resolve_channel_name("C123", is_dm=False))

    assert r1 == "marketing"
    assert r2 == "marketing"
    assert client.call_count == 1


def test_resolve_channel_name_api_error_caches_miss(adapter: Any) -> None:
    """An API failure should cache ``None`` and not retry on every message."""
    import asyncio

    client = _FakeClient(raises=True)
    _inject_fake_client(adapter, client)

    r1 = asyncio.run(adapter._resolve_channel_name("C456", is_dm=False))
    r2 = asyncio.run(adapter._resolve_channel_name("C456", is_dm=False))

    assert r1 is None
    assert r2 is None
    # Exactly one API call — second hit the cached miss.
    assert client.call_count == 1


def test_resolve_channel_name_empty_id_returns_none(adapter: Any) -> None:
    import asyncio

    client = _FakeClient()
    _inject_fake_client(adapter, client)

    result = asyncio.run(adapter._resolve_channel_name("", is_dm=False))

    assert result is None
    assert client.call_count == 0


# ---------------------------------------------------------------------------
# Socket Mode reconnect — permanent fix for silent WebSocket drops
# ---------------------------------------------------------------------------


class _FakeHandler:
    """Stand-in for AsyncSocketModeHandler to test reconnect cycling."""

    def __init__(self, app: Any, app_token: str) -> None:
        self.app = app
        self.app_token = app_token
        self.connected = False
        self.closed = False

    async def connect_async(self) -> None:
        self.connected = True

    async def close_async(self) -> None:
        self.closed = True


def test_note_turn_start_end_increments_and_decrements(adapter: Any) -> None:
    """Turn counter pairs symmetrically and never goes negative."""
    assert adapter._in_flight_turns == 0
    adapter.note_turn_start()
    adapter.note_turn_start()
    assert adapter._in_flight_turns == 2
    adapter.note_turn_end()
    assert adapter._in_flight_turns == 1
    adapter.note_turn_end()
    adapter.note_turn_end()  # extra end — should clamp at 0, not go negative
    assert adapter._in_flight_turns == 0


def test_reconnect_skips_when_turn_in_flight(
    adapter: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A reconnect cycle never lands mid-turn — it returns False and retries later."""
    import asyncio

    # Wire a fake handler so we can detect whether reconnect actually fired.
    monkeypatch.setattr(
        "slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler",
        _FakeHandler,
    )
    fake_existing = _FakeHandler(adapter.app, "xapp-test")
    adapter._handler = fake_existing
    adapter.note_turn_start()  # simulate router mid-turn

    result = asyncio.run(adapter.reconnect())

    assert result is False
    assert adapter._handler is fake_existing  # untouched
    assert fake_existing.closed is False


def test_reconnect_cycles_handler_when_idle(
    adapter: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Idle reconnect: new handler connects FIRST, then old one closes (no event-loss window)."""
    import asyncio

    monkeypatch.setattr(
        "slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler",
        _FakeHandler,
    )
    old = _FakeHandler(adapter.app, "xapp-test")
    adapter._handler = old

    result = asyncio.run(adapter.reconnect())

    assert result is True
    assert adapter._handler is not old
    assert isinstance(adapter._handler, _FakeHandler)
    assert adapter._handler.connected is True
    assert old.closed is True


def test_reconnect_tolerates_old_handler_close_failure(
    adapter: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If close_async on the dead handler raises, the new handler still wins."""
    import asyncio

    monkeypatch.setattr(
        "slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler",
        _FakeHandler,
    )

    class _BrokenOld(_FakeHandler):
        async def close_async(self) -> None:
            raise RuntimeError("WebSocket already torn down")

    broken = _BrokenOld(adapter.app, "xapp-test")
    adapter._handler = broken

    result = asyncio.run(adapter.reconnect())

    assert result is True
    assert adapter._handler is not broken
    assert adapter._handler.connected is True
