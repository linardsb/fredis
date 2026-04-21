"""Phase 9 Task 6 — Auto-retrieval in the heartbeat gather path.

Unit-tests ``_extract_signals`` and ``_gather_relevant_memories``: dedup
across signals, per-signal failure isolation, empty-signal no-op, the
min-query-length filter, and the aggregate cap.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pytest


@dataclass
class _FakeEmail:
    id: str
    subject: str
    sender: str = "someone@example.com"
    sender_email: str = "someone@example.com"


@dataclass
class _FakeTask:
    gid: str
    name: str
    due_on: datetime | None = None
    completed: bool = False


@dataclass
class _FakeSlackMsg:
    channel: str
    ts: str
    text: str
    user_name: str = "alice"


def _make_hit(path: str, chunk_id: int, text: str = "fixture body text") -> Any:
    from memory_search import SearchResult

    return SearchResult(
        path=path,
        start_line=1,
        end_line=2,
        text=text,
        score=0.75,
        match_type="hybrid",
        section_title="",
        chunk_id=chunk_id,
    )


def _fake_raw_data() -> dict[str, Any]:
    """Raw data with three NEW items — one per source."""
    return {
        "urgent_emails": [_FakeEmail(id="e1", subject="VTV-first sequencing call agenda")],
        "recent_emails": [],
        "today_events": [],
        "upcoming_events": [],
        "overdue_tasks": [_FakeTask(gid="t1", name="Follow up on Šlesers email")],
        "due_soon_tasks": [],
        "slack_important": [
            _FakeSlackMsg(channel="C1", ts="1700.001", text="Kick off the Cab pilot this week")
        ],
        "monday_overdue": [],
        "monday_my_items": [],
        "github_commits": [],
        "github_review_requests": [],
        "errors": {},
    }


def _fake_diff_all_new() -> dict[str, Any]:
    return {
        "new_emails": {"e1"},
        "changed_emails": set(),
        "removed_emails": set(),
        "new_tasks": {"t1"},
        "changed_tasks": set(),
        "removed_tasks": set(),
        "new_slack": {"C1:1700.001"},
        "changed_slack": set(),
        "removed_slack": set(),
        "new_events": set(),
        "changed_events": set(),
        "removed_events": set(),
        "drafts_changed": False,
        "habits_changed": False,
        "has_changes": True,
    }


def test_extract_signals_pulls_subject_task_name_slack_text() -> None:
    import heartbeat

    signals = heartbeat._extract_signals(_fake_raw_data(), _fake_diff_all_new())
    # Order is not contractual; presence is.
    assert "VTV-first sequencing call agenda" in signals
    assert "Follow up on Šlesers email" in signals
    assert "Kick off the Cab pilot this week" in signals


def test_extract_signals_drops_empties_and_short_strings() -> None:
    import heartbeat

    raw = {
        "urgent_emails": [_FakeEmail(id="e1", subject="")],  # empty subject
        "recent_emails": [_FakeEmail(id="e2", subject="hi")],  # too short
        "today_events": [],
        "upcoming_events": [],
        "overdue_tasks": [_FakeTask(gid="t1", name="yo")],
        "due_soon_tasks": [],
        "slack_important": [],
        "monday_overdue": [],
        "monday_my_items": [],
        "github_commits": [],
        "github_review_requests": [],
        "errors": {},
    }
    diff: dict[str, Any] = {
        "new_emails": {"e1", "e2"},
        "new_tasks": {"t1"},
        "new_slack": set(),
    }
    assert heartbeat._extract_signals(raw, diff) == []


def test_extract_signals_first_run_treats_all_as_new() -> None:
    """With diff=None, all items in raw_data are eligible signals."""
    import heartbeat

    signals = heartbeat._extract_signals(_fake_raw_data(), diff=None)
    assert len(signals) == 3


def test_gather_relevant_memories_aggregates_three_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three signals → three searches → aggregated wrapped block with all hits."""
    import heartbeat

    def _hits_for(q: str, **kw: Any) -> list[Any]:
        # Return one unique hit per signal so we can check aggregation
        if "VTV" in q:
            return [_make_hit("daily/2026-04-19.md", chunk_id=1)]
        if "Šlesers" in q:
            return [_make_hit("research/lpv-landscape.md", chunk_id=2)]
        if "Cab" in q:
            return [_make_hit("MEMORY.md", chunk_id=3)]
        return []

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _hits_for)

    block, ids = heartbeat._gather_relevant_memories(_fake_raw_data(), _fake_diff_all_new())

    assert '<external_data source="memory_recall"' in block
    assert "daily/2026-04-19.md" in block
    assert "research/lpv-landscape.md" in block
    assert "MEMORY.md" in block
    assert sorted(ids) == [1, 2, 3]


def test_gather_dedups_chunk_ids_across_signals(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same chunk_id returned for two signals → appears in the block once."""
    import heartbeat

    shared_hit = _make_hit("MEMORY.md", chunk_id=99)

    def _hits_for(q: str, **kw: Any) -> list[Any]:
        return [shared_hit]

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _hits_for)

    block, ids = heartbeat._gather_relevant_memories(_fake_raw_data(), _fake_diff_all_new())
    assert ids == [99]
    assert block.count("chunk_id=") == 0  # chunk_id not in header format
    assert block.count("MEMORY.md:") == 1


def test_gather_tolerates_partial_signal_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """One signal's search raises → other signals' hits still aggregate."""
    import heartbeat

    def _hits_for(q: str, **kw: Any) -> list[Any]:
        if "Šlesers" in q:
            raise RuntimeError("fastembed oom")
        if "VTV" in q:
            return [_make_hit("daily/2026-04-19.md", chunk_id=1)]
        if "Cab" in q:
            return [_make_hit("MEMORY.md", chunk_id=3)]
        return []

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _hits_for)

    block, ids = heartbeat._gather_relevant_memories(_fake_raw_data(), _fake_diff_all_new())
    assert sorted(ids) == [1, 3]
    assert "daily/2026-04-19.md" in block
    assert "MEMORY.md" in block


def test_gather_empty_when_no_signals(monkeypatch: pytest.MonkeyPatch) -> None:
    """No new items → no search calls → empty block."""
    import heartbeat

    called: list[str] = []

    def _spy(q: str, **kw: Any) -> list[Any]:
        called.append(q)
        return []

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _spy)

    empty_raw: dict[str, Any] = {
        "urgent_emails": [],
        "recent_emails": [],
        "today_events": [],
        "upcoming_events": [],
        "overdue_tasks": [],
        "due_soon_tasks": [],
        "slack_important": [],
        "monday_overdue": [],
        "monday_my_items": [],
        "github_commits": [],
        "github_review_requests": [],
        "errors": {},
    }
    empty_diff: dict[str, Any] = {
        "new_emails": set(),
        "new_tasks": set(),
        "new_slack": set(),
    }
    block, ids = heartbeat._gather_relevant_memories(empty_raw, empty_diff)
    assert block == ""
    assert ids == []
    assert called == []


def test_gather_caps_at_aggregate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    """With many hits per signal, aggregate is capped at ``_RECALL_AGGREGATE_CAP``."""
    import heartbeat

    counter = 0

    def _big_bag(q: str, **kw: Any) -> list[Any]:
        nonlocal counter
        out: list[Any] = []
        for _ in range(10):
            counter += 1
            out.append(_make_hit(f"file-{counter}.md", chunk_id=counter))
        return out

    import memory_search

    monkeypatch.setattr(memory_search, "search_hybrid", _big_bag)

    _, ids = heartbeat._gather_relevant_memories(_fake_raw_data(), _fake_diff_all_new())
    assert len(ids) == heartbeat._RECALL_AGGREGATE_CAP


def test_gather_handles_search_module_import_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ``memory_search`` can't even be imported, return empty — never raise."""
    import sys

    import heartbeat

    # Remove the cached module then cause a reload error by injecting a poison
    # entry so `from memory_search import search_hybrid` inside the helper
    # raises. Fail-safe: the helper returns ('', []).
    real_mod = sys.modules.pop("memory_search", None)
    try:

        class _Boom:
            def __getattr__(self, name: str) -> Any:
                raise ImportError("poisoned")

        monkeypatch.setitem(sys.modules, "memory_search", _Boom())

        block, ids = heartbeat._gather_relevant_memories(_fake_raw_data(), _fake_diff_all_new())
        assert block == ""
        assert ids == []
    finally:
        if real_mod is not None:
            sys.modules["memory_search"] = real_mod


@pytest.mark.parametrize(
    "verdict,should_run",
    [
        ("pass", True),
        ("suspicious", True),
        ("fail", False),
        ("error", False),
    ],
)
def test_run_heartbeat_verdict_gates_retrieval(
    monkeypatch: pytest.MonkeyPatch,
    verdict: str,
    should_run: bool,
) -> None:
    """Verdict gate: `_gather_relevant_memories` runs only on pass/suspicious.

    Failing on verdict=='fail' is already handled by an early ``return None``,
    so we only need to exercise the gate for pass/suspicious/error.
    """
    import heartbeat

    # Spy on the gather helper.
    gather_calls: list[tuple[Any, Any]] = []

    def _spy(raw: Any, diff: Any) -> tuple[str, list[int]]:
        gather_calls.append((raw, diff))
        return "", []

    monkeypatch.setattr(heartbeat, "_gather_relevant_memories", _spy)

    # Stub everything external so run_heartbeat can be entered without
    # network or SDK calls, and so the flow reaches (or bypasses) the gate.
    monkeypatch.setattr(heartbeat, "is_within_active_hours", lambda: True)
    monkeypatch.setattr(heartbeat, "load_state", lambda *a, **k: {})
    monkeypatch.setattr(heartbeat, "save_state", lambda *a, **k: None)
    monkeypatch.setattr(heartbeat, "append_to_daily_log", lambda *a, **k: None)
    monkeypatch.setattr(heartbeat, "log_hook_execution", lambda *a, **k: None)
    monkeypatch.setattr(heartbeat, "_fetch_raw_data", lambda: _fake_raw_data())
    monkeypatch.setattr(heartbeat, "gather_habits_context", lambda: "")
    monkeypatch.setattr(heartbeat, "gather_email_drafts_context", lambda: "")
    monkeypatch.setattr(heartbeat, "reconcile_active_drafts", lambda: "")
    monkeypatch.setattr(heartbeat, "expire_old_drafts", lambda: 0)
    monkeypatch.setattr(heartbeat, "cleanup_expired_drafts", lambda: 0)
    monkeypatch.setattr(heartbeat, "surface_gate_breaches", lambda: [])
    monkeypatch.setattr(heartbeat, "gather_active_drafts_context", lambda: "")
    monkeypatch.setattr(heartbeat, "format_context_with_diff", lambda *a, **k: ("", []))
    monkeypatch.setattr(heartbeat, "build_snapshot", lambda **k: {})
    monkeypatch.setattr(heartbeat, "diff_snapshot", lambda *a, **k: None)
    monkeypatch.setattr(heartbeat, "send_slack_notification", lambda *a, **k: None)

    async def _fake_guardrail(context: str, test_mode: bool = False) -> dict[str, Any]:
        return {"verdict": verdict, "flagged_items": [], "summary": None}

    monkeypatch.setattr(heartbeat, "run_guardrail_check", _fake_guardrail)

    # Stub the memory index sync so no FastEmbed loading happens.
    import sys
    import types

    fake_mi = types.ModuleType("memory_index")
    fake_mi.sync_index = lambda: {"files_indexed": 0, "files_skipped": 0}  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "memory_index", fake_mi)

    # Stub the SDK query so the loop terminates without producing output.
    import claude_agent_sdk

    async def _fake_query(**kwargs: Any) -> Any:
        if False:
            yield None  # noqa: UP026

    monkeypatch.setattr(claude_agent_sdk, "query", _fake_query)

    import asyncio

    asyncio.run(heartbeat.run_heartbeat(test_mode=True))

    if should_run:
        assert len(gather_calls) == 1, f"verdict={verdict} should trigger retrieval"
    else:
        assert gather_calls == [], f"verdict={verdict} must skip retrieval"
