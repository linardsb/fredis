"""Engine → channel router → summary writer integration tests.

Covers:
    - A successful turn writes a summary file to the router-resolved folder.
    - DMs land in the DM-default folder (daily/).
    - Unknown channels fall through to the fallback folder.
    - Router disabled (None) is a no-op — no file is written.
    - A summary-writer exception does NOT surface to the caller.
"""

from __future__ import annotations

import asyncio
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


# ---------------------------------------------------------------------------
# Fake SDK + fake store — copied minimally from test_chat_engine.py
# ---------------------------------------------------------------------------


def _install_fake_sdk_with_sink(
    monkeypatch: pytest.MonkeyPatch, prompt_sink: list[str]
) -> None:
    """Like `_install_fake_sdk` but captures every prompt the fake SDK receives.

    Used by the D5-acknowledgment regression test to assert the save-to
    directive reaches Claude verbatim.
    """

    @dataclass
    class TextBlock:
        text: str

    @dataclass
    class AssistantMessage:
        content: list[Any] = field(default_factory=list)

    @dataclass
    class ResultMessage:
        session_id: str = "sdk-session-xyz"
        total_cost_usd: float | None = 0.01

    class ClaudeAgentOptions:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    class HookMatcher:
        def __init__(self, matcher: str, hooks: list[Any]) -> None:
            self.matcher = matcher
            self.hooks = hooks

    async def query(prompt: str, options: Any) -> Any:
        prompt_sink.append(prompt)
        yield AssistantMessage(content=[TextBlock(text="ok")])
        yield ResultMessage()

    fake = types.ModuleType("claude_agent_sdk")
    fake.AssistantMessage = AssistantMessage  # type: ignore[attr-defined]
    fake.ClaudeAgentOptions = ClaudeAgentOptions  # type: ignore[attr-defined]
    fake.HookMatcher = HookMatcher  # type: ignore[attr-defined]
    fake.ResultMessage = ResultMessage  # type: ignore[attr-defined]
    fake.TextBlock = TextBlock  # type: ignore[attr-defined]
    fake.query = query  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake)


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    @dataclass
    class TextBlock:
        text: str

    @dataclass
    class AssistantMessage:
        content: list[Any] = field(default_factory=list)

    @dataclass
    class ResultMessage:
        session_id: str = "sdk-session-xyz"
        total_cost_usd: float | None = 0.0123

    class ClaudeAgentOptions:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    class HookMatcher:
        def __init__(self, matcher: str, hooks: list[Any]) -> None:
            self.matcher = matcher
            self.hooks = hooks

    async def query(prompt: str, options: Any) -> Any:
        yield AssistantMessage(content=[TextBlock(text="Here is your answer.")])
        yield ResultMessage()

    fake = types.ModuleType("claude_agent_sdk")
    fake.AssistantMessage = AssistantMessage  # type: ignore[attr-defined]
    fake.ClaudeAgentOptions = ClaudeAgentOptions  # type: ignore[attr-defined]
    fake.HookMatcher = HookMatcher  # type: ignore[attr-defined]
    fake.ResultMessage = ResultMessage  # type: ignore[attr-defined]
    fake.TextBlock = TextBlock  # type: ignore[attr-defined]
    fake.query = query  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake)


class _FakeStore:
    def __init__(self) -> None:
        self.created: list[Any] = []
        self.updated: list[Any] = []

    def get(self, platform: str, channel_id: str, thread_id: str) -> Any:
        return None

    def get_heartbeat_thread(self, channel_id: str, thread_ts: str) -> Any:
        return None

    def create(self, session: Any) -> None:
        self.created.append(session)

    def update(self, session: Any) -> None:
        self.updated.append(session)


def _write_routing_config(tmp_path: Path) -> Path:
    cfg = tmp_path / "channel-routing.yaml"
    cfg.write_text(
        """\
version: 1
channels:
  ideation: Fredis/Memory/ideation/
  marketing: Fredis/Memory/marketing/
by_id: {}
defaults:
  dm: Fredis/Memory/daily/
  fallback: Fredis/Memory/daily/
""",
        encoding="utf-8",
    )
    return cfg


def _build_incoming(
    text: str,
    channel_id: str,
    channel_name: str | None,
    is_dm: bool,
    thread_ts: str = "1700.001",
) -> Any:
    from models import Channel, IncomingMessage, Platform, Thread, User

    return IncomingMessage(
        text=text,
        user=User(Platform.SLACK, "U1"),
        channel=Channel(Platform.SLACK, channel_id, name=channel_name, is_dm=is_dm),
        platform=Platform.SLACK,
        thread=Thread(thread_id=thread_ts),
        platform_message_id=thread_ts,
    )


def _run_turn(engine: Any, msg: Any) -> None:
    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())


def _stub_bash_validator(monkeypatch: pytest.MonkeyPatch) -> None:
    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


def test_channel_match_writes_summary_to_topic_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _FakeStore(), tmp_path, channel_router=router
    )
    msg = _build_incoming(
        "pricing thoughts", channel_id="C999", channel_name="marketing", is_dm=False
    )

    _run_turn(engine, msg)

    marketing = tmp_path / "Fredis/Memory/marketing"
    assert marketing.is_dir()
    files = list(marketing.glob("*.md"))
    assert len(files) == 1
    text = files[0].read_text(encoding="utf-8")
    assert "pricing thoughts" in text
    assert "Here is your answer." in text


def test_dm_writes_summary_to_daily_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _FakeStore(), tmp_path, channel_router=router
    )
    msg = _build_incoming(
        "DM question", channel_id="D001", channel_name=None, is_dm=True
    )

    _run_turn(engine, msg)

    daily = tmp_path / "Fredis/Memory/daily"
    assert daily.is_dir()
    files = list(daily.glob("*.md"))
    assert len(files) == 1


def test_unknown_channel_falls_through_to_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _FakeStore(), tmp_path, channel_router=router
    )
    # Channel name not in config → fallback (daily/).
    msg = _build_incoming(
        "random chat", channel_id="CZZZ", channel_name="random-channel", is_dm=False
    )

    _run_turn(engine, msg)

    daily = tmp_path / "Fredis/Memory/daily"
    files = list(daily.glob("*.md"))
    assert len(files) == 1


def test_router_none_writes_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When no router is passed, summary writing is a no-op."""
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    engine = ConversationEngine(_FakeStore(), tmp_path, channel_router=None)
    msg = _build_incoming(
        "nothing should be written",
        channel_id="C999",
        channel_name="marketing",
        is_dm=False,
    )

    _run_turn(engine, msg)

    # Nothing under Fredis/Memory/ should have been created.
    assert not (tmp_path / "Fredis/Memory").exists() or not any(
        (tmp_path / "Fredis/Memory").rglob("*.md")
    )


def test_empty_channel_prefix_runs_single_global_search(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression guard on the Phase 9 path: when no channel prefix is passed,
    only the global search runs (one call, `path_prefix=""`, `limit=5`)."""
    from engine import ConversationEngine

    calls: list[dict[str, Any]] = []

    def fake_search_hybrid(
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
        path_prefix: str = "",
    ) -> list[Any]:
        calls.append({"query": query, "limit": limit, "path_prefix": path_prefix})
        return []

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", fake_search_hybrid)

    ConversationEngine._build_retrieved_memories(
        "enough characters to clear the min-length gate", channel_prefix=""
    )

    assert len(calls) == 1
    assert calls[0]["path_prefix"] == ""
    assert calls[0]["limit"] == ConversationEngine._RECALL_GLOBAL_LIMIT


def test_channel_scoped_retrieval_runs_two_searches_and_dedupes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """When a channel matches, _build_retrieved_memories must run a
    channel-scoped search first and a global search second, with dedup."""
    from engine import ConversationEngine

    scoped_calls: list[dict[str, Any]] = []

    @dataclass
    class FakeHit:
        path: str
        start_line: int
        end_line: int
        text: str
        score: float
        match_type: str
        section_title: str | None
        chunk_id: int | None

    def fake_search_hybrid(
        query: str,
        limit: int = 5,
        min_score: float = 0.5,
        path_prefix: str = "",
    ) -> list[FakeHit]:
        scoped_calls.append({"query": query, "limit": limit, "path_prefix": path_prefix})
        if path_prefix == "marketing/":
            return [
                FakeHit(
                    path="marketing/pricing.md",
                    start_line=1,
                    end_line=5,
                    text="local channel pricing context",
                    score=0.9,
                    match_type="hybrid",
                    section_title=None,
                    chunk_id=101,
                ),
                # This one duplicates a global hit below — must be deduped.
                FakeHit(
                    path="shared/overlap.md",
                    start_line=1,
                    end_line=3,
                    text="overlap text",
                    score=0.8,
                    match_type="hybrid",
                    section_title=None,
                    chunk_id=202,
                ),
            ]
        # Global search
        return [
            FakeHit(
                path="shared/overlap.md",
                start_line=1,
                end_line=3,
                text="overlap text",
                score=0.7,
                match_type="hybrid",
                section_title=None,
                chunk_id=202,
            ),
            FakeHit(
                path="SOUL.md",
                start_line=10,
                end_line=20,
                text="soul snippet",
                score=0.65,
                match_type="hybrid",
                section_title="Core Identity",
                chunk_id=303,
            ),
        ]

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", fake_search_hybrid)

    block, chunk_ids = ConversationEngine._build_retrieved_memories(
        "tell me about marketing pricing", channel_prefix="marketing/"
    )

    # Two calls: one scoped, one global.
    assert len(scoped_calls) == 2
    assert scoped_calls[0]["path_prefix"] == "marketing/"
    assert scoped_calls[1]["path_prefix"] == ""

    # Scoped hit first in output.
    assert "marketing/pricing.md" in block
    assert "SOUL.md" in block
    idx_channel = block.index("marketing/pricing.md")
    idx_global = block.index("SOUL.md")
    assert idx_channel < idx_global, "channel-scoped hit must rank before global"

    # Dedup: overlap.md appears only ONCE (not twice).
    assert block.count("shared/overlap.md") == 1

    # Chunk IDs collected from both searches.
    assert 101 in chunk_ids
    assert 202 in chunk_ids
    assert 303 in chunk_ids


class _StatefulFakeStore(_FakeStore):
    """Tracks the latest session so thread-sticky override tests can verify
    that subsequent `get()` calls surface the override previously set."""

    def __init__(self) -> None:
        super().__init__()
        self._sessions: dict[str, Any] = {}

    def get(self, platform: str, channel_id: str, thread_id: str) -> Any:
        key = f"{platform}:{channel_id}:{thread_id}"
        return self._sessions.get(key)

    def create(self, session: Any) -> None:
        self._sessions[session.session_id] = session
        self.created.append(session)

    def update(self, session: Any) -> None:
        self._sessions[session.session_id] = session
        self.updated.append(session)


def test_save_directive_fresh_thread_lands_in_override_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _StatefulFakeStore(), tmp_path, channel_router=router
    )
    # Chatting in #ideation, but directive redirects to marketing.
    msg = _build_incoming(
        "brainstorm pricing, save this to marketing",
        channel_id="C999",
        channel_name="ideation",
        is_dm=False,
    )

    _run_turn(engine, msg)

    marketing = tmp_path / "Fredis/Memory/marketing"
    ideation = tmp_path / "Fredis/Memory/ideation"

    # File lands in marketing, NOT ideation.
    assert marketing.is_dir()
    assert len(list(marketing.glob("*.md"))) == 1
    assert not ideation.exists() or not any(ideation.glob("*.md"))


def test_save_directive_override_persists_on_session(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    msg = _build_incoming(
        "idea, save this to marketing",
        channel_id="C999",
        channel_name="ideation",
        is_dm=False,
    )

    _run_turn(engine, msg)

    # Session row now has override set.
    assert len(store.created) == 1
    session = store.created[0]
    expected = str((tmp_path / "Fredis/Memory/marketing").resolve())
    assert session.summary_folder_override == expected


def test_save_directive_second_turn_without_directive_stays_sticky(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Thread-sticky: once set, the override carries into future turns."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    # Turn 1: directive sets override → marketing.
    _run_turn(
        engine,
        _build_incoming(
            "idea, save this to marketing",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )

    # Turn 2: no directive, but override should persist.
    _run_turn(
        engine,
        _build_incoming(
            "follow-up thought",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )

    marketing = tmp_path / "Fredis/Memory/marketing"
    files = list(marketing.glob("*.md"))
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert "Turn 1" in body
    assert "Turn 2" in body
    assert "follow-up thought" in body


def test_save_directive_mid_thread_moves_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Turn 1 writes to channel default; turn 2 override moves the file."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    ideation = tmp_path / "Fredis/Memory/ideation"
    marketing = tmp_path / "Fredis/Memory/marketing"

    # Turn 1: no directive → lands in ideation.
    _run_turn(
        engine,
        _build_incoming(
            "first brainstorm",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )
    assert len(list(ideation.glob("*.md"))) == 1
    assert not marketing.exists() or not any(marketing.glob("*.md"))

    # Turn 2: directive redirects → file moves to marketing.
    _run_turn(
        engine,
        _build_incoming(
            "actually, save this to marketing",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )

    assert len(list(marketing.glob("*.md"))) == 1
    assert not any(ideation.glob("*.md"))


def test_save_directive_clear_reverts_to_channel_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`clear save target` removes the override and moves the file back."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    ideation = tmp_path / "Fredis/Memory/ideation"
    marketing = tmp_path / "Fredis/Memory/marketing"

    # Set override.
    _run_turn(
        engine,
        _build_incoming(
            "save this to marketing",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )
    assert len(list(marketing.glob("*.md"))) == 1

    # Clear.
    _run_turn(
        engine,
        _build_incoming(
            "clear save target",
            channel_id="C999",
            channel_name="ideation",
            is_dm=False,
        ),
    )

    # File moved back to ideation; marketing is empty.
    assert len(list(ideation.glob("*.md"))) == 1
    assert not any(marketing.glob("*.md"))

    # Session override cleared.
    session = store._sessions["slack:C999:1700.001"]
    assert session.summary_folder_override is None


def test_save_directive_free_form_path_creates_subfolder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Target not in YAML → treated as relative vault path, lazy-created."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _StatefulFakeStore(), tmp_path, channel_router=router
    )

    msg = _build_incoming(
        "OpenAI Sora research, save this to research/ai/sora",
        channel_id="C999",
        channel_name="research-ai",
        is_dm=False,
    )

    _run_turn(engine, msg)

    sora = tmp_path / "Fredis/Memory/research/ai/sora"
    assert sora.is_dir()
    assert len(list(sora.glob("*.md"))) == 1


def test_save_directive_text_reaches_the_sdk_for_acknowledgment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """D5 contract: Claude must SEE the directive so it can naturally
    acknowledge the save destination to the user. The engine parses for
    routing but does not strip the directive from the user text."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk_with_sink(monkeypatch, prompts)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _StatefulFakeStore(), tmp_path, channel_router=router
    )
    msg = _build_incoming(
        "pricing ideas, save this to marketing",
        channel_id="C999",
        channel_name="ideation",
        is_dm=False,
    )

    _run_turn(engine, msg)

    assert len(prompts) == 1
    prompt = prompts[0]
    # Directive must be present in what Claude sees — otherwise no ack.
    assert "save this to marketing" in prompt


def test_clear_directive_without_prior_override_is_noop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`clear save target` in a fresh thread just lands in the channel
    default — no relocate, no crash, override stays None."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    msg = _build_incoming(
        "clear save target, just chatting",
        channel_id="C999",
        channel_name="ideation",
        is_dm=False,
    )

    _run_turn(engine, msg)

    # File in ideation; no override persisted.
    ideation = tmp_path / "Fredis/Memory/ideation"
    assert len(list(ideation.glob("*.md"))) == 1
    session = store._sessions.get("slack:C999:1700.001")
    assert session is not None
    assert session.summary_folder_override is None


def test_save_directive_in_dm_is_a_noop_override_not_set(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """DMs route to daily/ — a save directive in a DM actually should
    still work because the router can resolve the target; only the channel
    default is DM-daily. Verify the override wins over the DM default."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _StatefulFakeStore(), tmp_path, channel_router=router
    )
    msg = _build_incoming(
        "private brainstorm, save this to marketing",
        channel_id="D001",
        channel_name=None,
        is_dm=True,
    )

    _run_turn(engine, msg)

    marketing = tmp_path / "Fredis/Memory/marketing"
    daily = tmp_path / "Fredis/Memory/daily"
    assert len(list(marketing.glob("*.md"))) == 1
    # Nothing in daily/ — the override took precedence over the DM default.
    assert not daily.exists() or not any(daily.glob("*.md"))


def test_save_directive_invalid_target_falls_back_to_channel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An invalid target (traversal attempt) must NOT set an override; the
    summary lands in the channel default."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    store = _StatefulFakeStore()
    engine = ConversationEngine(store, tmp_path, channel_router=router)

    msg = _build_incoming(
        "sneaky save this to ../etc attempt",
        channel_id="C999",
        channel_name="ideation",
        is_dm=False,
    )

    _run_turn(engine, msg)

    # No override persisted.
    session = store._sessions.get("slack:C999:1700.001")
    assert session is not None
    assert session.summary_folder_override is None

    # File in ideation (channel default).
    ideation = tmp_path / "Fredis/Memory/ideation"
    assert len(list(ideation.glob("*.md"))) == 1


def test_summary_write_exception_is_nonfatal(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A failing summary writer must NOT break the turn — reply still flows."""
    from channel_router import ChannelRouter
    from engine import ConversationEngine

    _install_fake_sdk(monkeypatch)
    _stub_bash_validator(monkeypatch)

    router = ChannelRouter(_write_routing_config(tmp_path), tmp_path)
    engine = ConversationEngine(
        _FakeStore(), tmp_path, channel_router=router
    )

    # Monkeypatch the writer to blow up.
    import engine as engine_mod

    def boom(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(engine_mod, "append_summary", boom)

    msg = _build_incoming(
        "hello", channel_id="C999", channel_name="marketing", is_dm=False
    )

    # Should NOT raise.
    _run_turn(engine, msg)
