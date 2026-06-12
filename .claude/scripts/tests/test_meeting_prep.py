"""Meeting-prep notifier — window selection, dedupe, formatting, state."""

from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-fake-for-tests")
os.environ.setdefault("SLACK_OWNER_USER_ID", "U0OWNER123")

from config import now_local  # noqa: E402,I001  — must follow env overrides
from integrations.calendar_api import CalendarEvent  # noqa: E402

import meeting_prep  # noqa: E402


def _event(
    event_id: str,
    minutes_from_now: float,
    *,
    all_day: bool = False,
    attendees: list[str] | None = None,
) -> CalendarEvent:
    start = now_local() + timedelta(minutes=minutes_from_now)
    return CalendarEvent(
        id=event_id,
        summary=f"Meeting {event_id}",
        start=start,
        end=start + timedelta(minutes=30),
        location="Zoom",
        attendees=attendees if attendees is not None else ["ana@example.com"],
        is_all_day=all_day,
    )


def test_select_window() -> None:
    now = now_local()
    events = [
        _event("in-window", 10),
        _event("too-far", 40),
        _event("already-started", -5),
        _event("all-day", 10, all_day=True),
        _event("already-prepped", 10),
    ]
    selected = meeting_prep.select_events_to_prep(
        events, now, already_prepped={"already-prepped"}, window_min=25
    )
    assert [e.id for e in selected] == ["in-window"]


def test_external_attendees_excludes_owner() -> None:
    ev = _event("x", 10, attendees=["Ana@example.com", "owner@example.com"])
    assert meeting_prep.external_attendees(ev, "OWNER@example.com") == ["Ana@example.com"]


def test_format_prep_pack_contains_essentials() -> None:
    ev = _event("x", 12)
    pack = meeting_prep.format_prep_pack(
        ev,
        now_local(),
        memory_hits=[("retainers/ana.md", "Ana retainer context")],
        last_thread='"Re: build review" (2026-06-10)',
        attendees=["ana@example.com"],
    )
    assert "Meeting x" in pack
    assert "ana@example.com" in pack
    assert "retainers/ana.md" in pack
    assert "Re: build review" in pack
    assert "starts in" in pack


def test_prune_state_drops_old_and_garbage_entries() -> None:
    now = now_local()
    prepped = {
        "fresh": now.isoformat(),
        "old": (now - timedelta(days=5)).isoformat(),
        "garbage": "not-a-date",
    }
    kept = meeting_prep._prune_state(prepped, now)
    assert set(kept) == {"fresh"}


def test_run_dedupes_across_ticks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import integrations.calendar_api as calendar_api

    ev = _event("evt-1", 10)
    monkeypatch.setattr(
        calendar_api, "get_upcoming_events", lambda hours_ahead=1, max_results=10: [ev]
    )
    monkeypatch.setattr(
        meeting_prep, "MEETING_PREP_STATE_FILE", tmp_path / "meeting-prep-state.json"
    )
    monkeypatch.setattr(meeting_prep, "is_within_active_hours", lambda: True)
    monkeypatch.setattr(meeting_prep, "_memory_context", lambda attendees: [])
    monkeypatch.setattr(meeting_prep, "_last_email_thread", lambda attendee: None)

    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        meeting_prep,
        "send_slack_notification",
        lambda title, message, channel=None: sent.append((title, message)),
    )

    first = meeting_prep.run_meeting_prep()
    second = meeting_prep.run_meeting_prep()
    assert first == ["Meeting evt-1"]
    assert second == []
    assert len(sent) == 1


def test_run_skips_outside_active_hours(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(meeting_prep, "is_within_active_hours", lambda: False)
    assert meeting_prep.run_meeting_prep() == []
