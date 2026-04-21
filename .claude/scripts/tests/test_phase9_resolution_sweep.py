"""Phase 9 Task 1 — Resolution sweep in the reflection prompt.

Captures the prompt passed into the SDK and asserts the new resolution-sweep
instructions are present. The live integration test runs the real SDK and is
opt-in via ``PHASE9_LIVE=1``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

import pytest


class _FakeResult:
    """Minimal stand-in for the SDK ResultMessage."""

    subtype = "success"
    total_cost_usd = 0.0


def _make_capture_query(captured: list[str]) -> Any:
    """Return an async generator that records prompt= kwargs and yields one result."""

    async def _fake_query(**kwargs: Any) -> Any:
        captured.append(kwargs.get("prompt", ""))
        yield _FakeResult()

    return _fake_query


def _seed_memory_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the writable memory files at tmp_path so the test does not
    touch the real vault."""
    import memory_reflect

    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text(
        "# MEMORY\n\n## Key Decisions\n\n## Open Watch Items\n\n"
        "- **VTV-first sequencing (2026-04-19).** Confirm with Atis.\n",
        encoding="utf-8",
    )
    user_file = tmp_path / "USER.md"
    user_file.write_text("# USER\n", encoding="utf-8")
    soul_file = tmp_path / "SOUL.md"
    soul_file.write_text("# SOUL\n", encoding="utf-8")

    monkeypatch.setattr(memory_reflect, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_reflect, "USER_FILE", user_file)
    monkeypatch.setattr(memory_reflect, "SOUL_FILE", soul_file)
    monkeypatch.setattr(memory_reflect, "MEMORY_LINE_LIMIT", 10_000)


def _stub_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise state writes + daily-log appends so the test is hermetic."""
    import memory_reflect

    monkeypatch.setattr(memory_reflect, "append_to_daily_log", lambda *a, **kw: None)
    monkeypatch.setattr(memory_reflect, "save_state", lambda *a, **kw: None)
    monkeypatch.setattr(memory_reflect, "load_state", lambda *a, **kw: {})


def test_prompt_contains_resolution_sweep_block(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fixture daily log with a resolved watch item → prompt includes the
    resolution-sweep instructions."""
    import memory_reflect

    _seed_memory_files(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)

    resolving_log = (
        "### Entry (10:00)\n\n"
        "Call with Atis — decided: VTV ships first, Cab rides on VTV's "
        "distribution. Confirmed sequencing.\n\n"
    )
    monkeypatch.setattr(
        memory_reflect,
        "get_recent_logs",
        lambda days=1: [("2026-04-20", resolving_log)],
    )

    captured: list[str] = []
    import claude_agent_sdk

    monkeypatch.setattr(claude_agent_sdk, "query", _make_capture_query(captured))

    asyncio.run(memory_reflect._run_reflection_inner(test_mode=False, days=1))

    assert len(captured) >= 1
    prompt = captured[-1]
    assert "### 1a. Resolution sweep" in prompt
    assert "Open Watch Items" in prompt
    assert "(resolved YYYY-MM-DD)" in prompt
    assert "Killed" in prompt
    # Evidence threshold guidance must ship with the block
    assert "Evidence threshold" in prompt
    assert 'NOT\nresolution' in prompt or 'NOT resolution' in prompt


def test_prompt_includes_evidence_threshold_for_weak_mention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even when the daily log only mentions the topic conversationally, the
    evidence-threshold guidance is still in the prompt (the instructions are
    universal, the agent decides case-by-case)."""
    import memory_reflect

    _seed_memory_files(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)

    weak_log = (
        "### Entry (10:00)\n\n"
        "Chatted about VTV sequencing briefly. Nothing firm yet.\n\n"
    )
    monkeypatch.setattr(
        memory_reflect,
        "get_recent_logs",
        lambda days=1: [("2026-04-20", weak_log)],
    )

    captured: list[str] = []
    import claude_agent_sdk

    monkeypatch.setattr(claude_agent_sdk, "query", _make_capture_query(captured))

    asyncio.run(memory_reflect._run_reflection_inner(test_mode=False, days=1))

    prompt = captured[-1]
    assert "Evidence threshold" in prompt
    assert "Decided X" in prompt or "going with option Y" in prompt
    assert "leave it" in prompt.lower()


@pytest.mark.skipif(
    os.getenv("PHASE9_LIVE") != "1",
    reason="live SDK run — opt-in via PHASE9_LIVE=1",
)
def test_live_resolution_sweep_moves_watch_item(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:  # pragma: no cover — live, opt-in
    """Opt-in integration test: run the real SDK against a fixture MEMORY.md
    and assert the watch item is moved to Key Decisions with a `(resolved
    YYYY-MM-DD)` stamp."""
    import memory_reflect

    _seed_memory_files(tmp_path, monkeypatch)
    _stub_side_effects(monkeypatch)

    resolving_log = (
        "### Entry (10:00)\n\n"
        "Call with Atis — decided: VTV ships first, Cab rides on VTV's "
        "distribution. Confirmed sequencing.\n\n"
    )
    monkeypatch.setattr(
        memory_reflect,
        "get_recent_logs",
        lambda days=1: [("2026-04-20", resolving_log)],
    )

    asyncio.run(memory_reflect._run_reflection_inner(test_mode=False, days=1))

    final = memory_reflect.MEMORY_FILE.read_text(encoding="utf-8")  # type: ignore[attr-defined]
    assert "(resolved" in final
    # Watch item should no longer be in Open Watch Items
    watch_section = final.split("## Open Watch Items", 1)[-1]
    assert "VTV-first sequencing" not in watch_section
