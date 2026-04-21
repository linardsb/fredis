"""Phase 9 Task 2 — Importance + status tagging.

Asserts the reflection prompt teaches the tag format, the archive prompt
enforces the impact-first tiebreak, and that a simple parser round-trips
tagged bullets.
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any

import pytest


class _FakeResult:
    subtype = "success"
    total_cost_usd = 0.0


def _make_capture_query(captured: list[str]) -> Any:
    async def _fake_query(**kwargs: Any) -> Any:
        captured.append(kwargs.get("prompt", ""))
        yield _FakeResult()

    return _fake_query


def _stub_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    import memory_reflect

    monkeypatch.setattr(memory_reflect, "append_to_daily_log", lambda *a, **kw: None)
    monkeypatch.setattr(memory_reflect, "save_state", lambda *a, **kw: None)
    monkeypatch.setattr(memory_reflect, "load_state", lambda *a, **kw: {})


_TAG_RE = re.compile(
    r"`\[\s*impact:\s*(?P<impact>high|med|low)"
    r"\s*,\s*status:\s*(?P<status>pending|decided|resolved|killed)\s*\]`"
)


def parse_entry_tag(line: str) -> dict[str, str] | None:
    """Extract impact + status from a tagged entry line. Returns None if the
    tag is missing."""
    match = _TAG_RE.search(line)
    if not match:
        return None
    return {"impact": match.group("impact"), "status": match.group("status")}


def test_tag_parser_roundtrip() -> None:
    """Given a bullet formatted with the Phase 9 tag, the parser extracts
    impact + status."""
    line = (
        "- **UK Ltd registration deadline (2026-04-21).** Register before first "
        "invoice issues. `[impact: high, status: decided]`"
    )
    tag = parse_entry_tag(line)
    assert tag == {"impact": "high", "status": "decided"}


def test_tag_parser_handles_all_levels() -> None:
    """All impact × status combinations parse."""
    cases = [
        ("[impact: high, status: pending]", ("high", "pending")),
        ("[impact: med, status: decided]", ("med", "decided")),
        ("[impact: low, status: resolved]", ("low", "resolved")),
        ("[impact: high, status: killed]", ("high", "killed")),
    ]
    for raw, (imp, stat) in cases:
        tag = parse_entry_tag(f"Body text. `{raw}`")
        assert tag == {"impact": imp, "status": stat}


def test_tag_parser_missing_returns_none() -> None:
    """Legacy untagged line returns None — backward compat signal."""
    legacy = "- **Old decision (2026-04-01).** Some body text without tags."
    assert parse_entry_tag(legacy) is None


def test_reflection_prompt_contains_tag_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reflection prompt teaches the Phase 9 tag format."""
    import memory_reflect

    memory_file = tmp_path / "MEMORY.md"
    memory_file.write_text("# MEMORY\n", encoding="utf-8")
    user_file = tmp_path / "USER.md"
    user_file.write_text("# USER\n", encoding="utf-8")
    soul_file = tmp_path / "SOUL.md"
    soul_file.write_text("# SOUL\n", encoding="utf-8")

    monkeypatch.setattr(memory_reflect, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_reflect, "USER_FILE", user_file)
    monkeypatch.setattr(memory_reflect, "SOUL_FILE", soul_file)
    monkeypatch.setattr(memory_reflect, "MEMORY_LINE_LIMIT", 10_000)
    _stub_side_effects(monkeypatch)
    monkeypatch.setattr(
        memory_reflect,
        "get_recent_logs",
        lambda days=1: [("2026-04-20", "### Entry (09:00)\n\nNo incidents today.\n\n")],
    )

    captured: list[str] = []
    import claude_agent_sdk

    monkeypatch.setattr(claude_agent_sdk, "query", _make_capture_query(captured))

    asyncio.run(memory_reflect._run_reflection_inner(test_mode=False, days=1))

    prompt = captured[-1]
    assert "impact: high|med|low" in prompt
    assert "status: pending|decided|resolved|killed" in prompt
    assert "Backward compat" in prompt
    # The exact example bullet shape must appear so Claude copies it verbatim
    assert "**Short title (YYYY-MM-DD).**" in prompt


def test_archive_prompt_contains_impact_first_tiebreak(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Archive prompt enforces impact-first selection on date ties."""
    import memory_reflect

    fake_memory = tmp_path / "MEMORY.md"
    # Content above the limit forces the archive pass into the SDK branch
    fake_memory.write_text("\n".join(f"line {i}" for i in range(300)) + "\n", encoding="utf-8")

    monkeypatch.setattr(memory_reflect, "MEMORY_FILE", fake_memory)
    monkeypatch.setattr(memory_reflect, "MEMORY_LINE_LIMIT", 200)
    monkeypatch.setattr(memory_reflect, "append_to_daily_log", lambda *a, **kw: None)

    captured: list[str] = []
    import claude_agent_sdk

    monkeypatch.setattr(claude_agent_sdk, "query", _make_capture_query(captured))

    asyncio.run(memory_reflect._archive_memory_overflow(test_mode=False))

    assert len(captured) >= 1
    prompt = captured[-1]
    assert "Impact-first tiebreak" in prompt
    assert "[impact: low]" in prompt
    assert "[status: pending]" in prompt
    # Legacy entries treated as med for the comparison
    assert "impact: med" in prompt
