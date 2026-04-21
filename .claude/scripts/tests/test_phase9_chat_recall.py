"""Phase 9 Task 5 — Auto-retrieval in the chat engine.

Checks the retrieval-block injection, fail-safe, empty-result / short-query
skip paths, and the touch-after-success discipline.
"""

from __future__ import annotations

import asyncio
import sys
import types
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


# ---------------------------------------------------------------------------
# SDK + store fixtures (mirrored from test_chat_engine.py)
# ---------------------------------------------------------------------------


def _install_fake_sdk(
    monkeypatch: pytest.MonkeyPatch, prompt_sink: list[str], raise_exc: Exception | None = None
) -> None:
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
        if raise_exc is not None:
            raise raise_exc
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


def _build_incoming(text: str) -> Any:
    from models import Channel, IncomingMessage, Platform, Thread, User

    return IncomingMessage(
        text=text,
        user=User(Platform.SLACK, "U1"),
        channel=Channel(Platform.SLACK, "C1", is_dm=True),
        platform=Platform.SLACK,
        thread=Thread(thread_id="1700.001"),
        platform_message_id="1700.001",
    )


def _make_hit(
    path: str,
    start_line: int = 1,
    end_line: int = 2,
    text: str = "relevant memory text",
    section_title: str = "Key Decisions",
    match_type: str = "hybrid",
    score: float = 0.8,
    chunk_id: int = 42,
) -> Any:
    from memory_search import SearchResult

    return SearchResult(
        path=path,
        start_line=start_line,
        end_line=end_line,
        text=text,
        score=score,
        match_type=match_type,
        section_title=section_title,
        chunk_id=chunk_id,
    )


class _FakeMemoryDB:
    def __init__(self) -> None:
        self.touched: list[list[int]] = []
        self.init_count = 0
        self.close_count = 0

    def init_schema(self) -> None:
        self.init_count += 1

    def touch_chunks(self, ids: list[int]) -> None:
        self.touched.append(list(ids))

    def close(self) -> None:
        self.close_count += 1


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_recall_block_injected_when_hits_found(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Three fixture hits → `<external_data source="memory_recall">` block
    appears in the prompt with all three file paths."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    hits = [
        _make_hit("daily/2026-04-19.md", chunk_id=1),
        _make_hit("drafts/sent/client-note.md", chunk_id=2),
        _make_hit("MEMORY.md", section_title="Key Decisions", chunk_id=3),
    ]
    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", lambda *a, **k: hits)

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("what did we decide about VTV sequencing")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    prompt = prompts[0]
    assert '<external_data source="memory_recall"' in prompt
    for hit in hits:
        assert hit.path in prompt
    # touch_chunks called with the three chunk IDs, on the successful path
    assert fake_db.touched == [[1, 2, 3]]


def test_recall_exception_is_swallowed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """search_hybrid raises → chat continues, no recall block, no touch."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    def _boom(*a: Any, **kw: Any) -> list[Any]:
        raise RuntimeError("embedding service unavailable")

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _boom)

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("what did we decide about the UK Ltd deadline")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    assert 'source="memory_recall"' not in prompts[0]
    assert fake_db.touched == []


def test_recall_empty_hits_injects_no_block(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No hits → no recall block, no touch."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", lambda *a, **k: [])

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("hello there how are you today")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    assert 'source="memory_recall"' not in prompts[0]
    assert fake_db.touched == []


def test_recall_short_query_skips_search_entirely(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Query <8 chars: retrieval skipped (no search_hybrid call, no DB call)."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    search_calls: list[str] = []

    def _spy_search(q: str, *a: Any, **kw: Any) -> list[Any]:
        search_calls.append(q)
        return []

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _spy_search)

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("hi")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert search_calls == []
    assert fake_db.touched == []
    assert 'source="memory_recall"' not in prompts[0]


def test_touch_chunks_not_called_on_sdk_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """SDK raises mid-turn → retrieval block still in prompt, but touch
    discipline means the chunks are NOT reinforced (aborted turn)."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts, raise_exc=RuntimeError("stream died"))

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    hits = [_make_hit("daily/2026-04-19.md", chunk_id=99)]
    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", lambda *a, **k: hits)

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("what did we decide about VTV sequencing")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    # SDK was called (prompt captured) but raised inside the generator
    assert len(prompts) == 1
    # Recall block WAS prepared on the successful branch…
    assert 'source="memory_recall"' in prompts[0]
    # …but touch was NOT called because the turn aborted.
    assert fake_db.touched == []


def test_recall_block_outside_inbound_trust_boundary(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Retrieval block must appear BEFORE the slack_inbound wrap — the wrap
    carries injection-defense framing and retrieval is assistant-side context."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    hits = [_make_hit("daily/2026-04-19.md", chunk_id=7)]
    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", lambda *a, **k: hits)

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("what did we decide about VTV sequencing")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    prompt = prompts[0]
    recall_idx = prompt.index('<external_data source="memory_recall"')
    inbound_idx = prompt.index('<external_data source="slack_inbound"')
    assert recall_idx < inbound_idx
    # Touch fired on success.
    assert fake_db.touched == [[7]]


def test_recall_truncates_over_budget(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A single oversized hit is truncated with the ``(truncated)`` marker."""
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    bulky = _make_hit("research/long-paper.md", text="x" * 5000, chunk_id=11)
    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", lambda *a, **k: [bulky])

    fake_db = _FakeMemoryDB()
    import db as db_module

    monkeypatch.setattr(db_module, "get_memory_db", lambda: fake_db)

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("tell me about the long research paper findings")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    prompt = prompts[0]
    assert "(truncated)" in prompt
    assert 'source="memory_recall"' in prompt


# Silence the datetime import-not-used warning (it is used indirectly via
# engine.py; keep the pattern mirror consistent with test_chat_engine.py).
_ = datetime
