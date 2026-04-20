"""Tests for .claude/chat/engine.py — attachment + image path + heartbeat injection.

We install a fake `claude_agent_sdk` in sys.modules before the engine imports it
lazily inside `handle_message`. The engine module sets CLAUDE_INVOKED_BY=chat on
import; that's fine for other tests since they explicitly monkeypatch.delenv it.
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
# _build_attachment_context (static)
# ---------------------------------------------------------------------------


def test_build_attachment_context_empty_returns_empty_string() -> None:
    from engine import ConversationEngine

    assert ConversationEngine._build_attachment_context([]) == ""


def test_build_attachment_context_includes_filename_mimetype_path() -> None:
    from engine import ConversationEngine
    from models import Attachment

    att = Attachment(
        filename="sketch.png", mimetype="image/png", url="/inbox/2026-04-20/sketch.png"
    )
    ctx = ConversationEngine._build_attachment_context([att])
    assert "sketch.png" in ctx
    assert "image/png" in ctx
    assert "/inbox/2026-04-20/sketch.png" in ctx
    assert "ATTACHED FILES" in ctx


# ---------------------------------------------------------------------------
# _extract_image_paths (regex + file existence)
# ---------------------------------------------------------------------------


def test_extract_image_paths_returns_only_existing_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from engine import ConversationEngine

    existing = {"/tmp/x.png"}

    def fake_is_file(self: Path) -> bool:
        return str(self) in existing

    monkeypatch.setattr(Path, "is_file", fake_is_file)

    text = "see /tmp/x.png and /tmp/missing.png plus /tmp/y.txt"
    paths = ConversationEngine._extract_image_paths(text)
    assert paths == ["/tmp/x.png"]


def test_extract_image_paths_ignores_non_image_extensions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from engine import ConversationEngine

    monkeypatch.setattr(Path, "is_file", lambda self: True)
    paths = ConversationEngine._extract_image_paths("read /tmp/notes.txt carefully")
    assert paths == []


# ---------------------------------------------------------------------------
# Heartbeat context injection (requires fake claude_agent_sdk)
# ---------------------------------------------------------------------------


def _install_fake_sdk(monkeypatch: pytest.MonkeyPatch, prompt_sink: list[str]) -> None:
    """Install a stub `claude_agent_sdk` module in sys.modules."""

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


class _FakeStore:
    def __init__(self, hb_thread: Any = None) -> None:
        self._hb = hb_thread
        self.created: list[Any] = []
        self.updated: list[Any] = []

    def get(self, platform: str, channel_id: str, thread_id: str) -> Any:
        return None

    def get_heartbeat_thread(self, channel_id: str, thread_ts: str) -> Any:
        return self._hb

    def create(self, session: Any) -> None:
        self.created.append(session)

    def update(self, session: Any) -> None:
        self.updated.append(session)


def _build_incoming(text: str = "what's up?") -> Any:
    from models import Channel, IncomingMessage, Platform, Thread, User

    return IncomingMessage(
        text=text,
        user=User(Platform.SLACK, "U1"),
        channel=Channel(Platform.SLACK, "C1", is_dm=True),
        platform=Platform.SLACK,
        thread=Thread(thread_id="1700.001"),
        platform_message_id="1700.001",
    )


def test_heartbeat_context_injected_into_prompt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from engine import ConversationEngine
    from session import HeartbeatThread

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    # Stub the shared.validate_bash_command used inside handle_message
    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    hb = HeartbeatThread(
        channel_id="C1",
        thread_ts="1700.001",
        alert_text="Overdue: invoice March 2026",
        created_at=datetime.now(),
    )
    store = _FakeStore(hb_thread=hb)
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("thread reply text")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    prompt = prompts[0]
    assert "heartbeat_alert" in prompt
    assert "<external_data source=\"heartbeat_alert\"" in prompt
    assert "Overdue: invoice March 2026" in prompt
    assert "thread reply text" in prompt


def test_no_heartbeat_thread_means_no_heartbeat_wrap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from engine import ConversationEngine

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    store = _FakeStore(hb_thread=None)
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("just a DM")

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    assert "heartbeat_alert" not in prompts[0]
    assert prompts[0].startswith("just a DM") or "just a DM" in prompts[0]


def test_attachment_context_appended_to_prompt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from engine import ConversationEngine
    from models import Attachment

    prompts: list[str] = []
    _install_fake_sdk(monkeypatch, prompts)

    import shared

    monkeypatch.setattr(
        shared, "validate_bash_command", lambda *a, **k: None, raising=False
    )

    store = _FakeStore()
    engine = ConversationEngine(store, tmp_path)
    msg = _build_incoming("here's a screenshot")
    msg.attachments = [
        Attachment(filename="ss.png", mimetype="image/png", url="/inbox/ss.png")
    ]

    async def _run() -> None:
        async for _ in engine.handle_message(msg):
            pass

    asyncio.run(_run())

    assert len(prompts) == 1
    assert "ss.png" in prompts[0]
    assert "/inbox/ss.png" in prompts[0]
