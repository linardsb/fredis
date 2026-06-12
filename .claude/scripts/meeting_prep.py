"""
Meeting prep notifier — Slack a prep pack shortly before each meeting.

SOUL.md names "meeting prep 15 min before" as a stated want that the
2-hourly heartbeat cadence cannot serve. This script runs every 10 minutes
via systemd timer (fredis-meeting-prep.timer) and is fully deterministic —
no Claude call, one Calendar API read per tick.

For each timed event starting within the next PREP_WINDOW_MIN minutes that
has not been prepped yet, it assembles:
  - event title / time / location / attendees
  - top memory-search hits for each external attendee (keyword mode, local)
  - the most recent Gmail thread subject with the first external attendee
and sends it via the Slack notification channel. Prepped event ids are
tracked in .claude/data/state/meeting-prep-state.json so each event fires
exactly once.

Usage:
    uv run python meeting_prep.py          # normal tick (timer entry point)
    uv run python meeting_prep.py --test   # print the pack, no Slack, no state
"""

from __future__ import annotations

import os
import sys
from datetime import datetime

from config import (
    GOOGLE_CALENDAR_ID,
    LOCAL_TZ,
    STATE_DIR,
    ensure_directories,
    is_within_active_hours,
    now_local,
)
from integrations.calendar_api import CalendarEvent
from notifications import send_console_notification, send_slack_notification
from shared import load_state, save_state

MEETING_PREP_STATE_FILE = STATE_DIR / "meeting-prep-state.json"

# Fire for events starting within this many minutes: 15 min of desired lead
# plus one 10-min timer interval of slack, so a tick can never skip past an
# event between polls.
PREP_WINDOW_MIN = int(os.getenv("MEETING_PREP_WINDOW_MIN", "25"))

# Drop prepped-event records after this many days (state hygiene).
_STATE_RETENTION_DAYS = 2


def select_events_to_prep(
    events: list[CalendarEvent],
    now: datetime,
    already_prepped: set[str],
    window_min: int = PREP_WINDOW_MIN,
) -> list[CalendarEvent]:
    """Timed events starting in (now, now + window_min] not yet prepped."""
    selected: list[CalendarEvent] = []
    for ev in events:
        if ev.is_all_day or ev.id in already_prepped:
            continue
        start = ev.start if ev.start.tzinfo else ev.start.replace(tzinfo=LOCAL_TZ)
        minutes_away = (start - now).total_seconds() / 60
        if 0 < minutes_away <= window_min:
            selected.append(ev)
    return selected


def external_attendees(ev: CalendarEvent, owner_email: str) -> list[str]:
    """Attendee addresses excluding the owner's own."""
    return [a for a in ev.attendees if a and a.lower() != owner_email.lower()]


def format_prep_pack(
    ev: CalendarEvent,
    now: datetime,
    memory_hits: list[tuple[str, str]],
    last_thread: str | None,
    attendees: list[str],
) -> str:
    """Render the prep pack text sent to Slack."""
    start = ev.start.astimezone(LOCAL_TZ) if ev.start.tzinfo else ev.start
    end = ev.end.astimezone(LOCAL_TZ) if ev.end.tzinfo else ev.end
    minutes_away = max(0, int((start - now).total_seconds() // 60))

    lines = [
        ev.summary,
        f"{start.strftime('%H:%M')}–{end.strftime('%H:%M')} — starts in {minutes_away} min",
    ]
    if ev.location:
        lines.append(f"Where: {ev.location}")
    if attendees:
        lines.append(f"With: {', '.join(attendees)}")
    if memory_hits:
        lines.append("")
        lines.append("From memory:")
        for path, snippet in memory_hits[:3]:
            lines.append(f"- {path}: {snippet}")
    if last_thread:
        lines.append("")
        lines.append(f"Last email thread: {last_thread}")
    return "\n".join(lines)


def _memory_context(attendees: list[str]) -> list[tuple[str, str]]:
    """Keyword memory-search hits for attendee names/addresses (best-effort)."""
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    try:
        from memory_search import search_keyword
    except Exception as e:
        print(f"[{now_local()}] memory search unavailable: {e}")
        return hits
    for addr in attendees[:3]:
        name = addr.split("@")[0].replace(".", " ")
        for term in {addr, name}:
            try:
                results = search_keyword(term, limit=2)
            except Exception as e:
                print(f"[{now_local()}] memory search failed for {term!r}: {e}")
                continue
            for r in results:
                key = f"{r.path}:{r.start_line}"
                if key in seen:
                    continue
                seen.add(key)
                snippet = " ".join(r.text.split())[:160]
                hits.append((r.path, snippet))
    return hits[:4]


def _last_email_thread(attendee: str) -> str | None:
    """Subject + date of the most recent email exchanged with the attendee."""
    try:
        from integrations.gmail import list_emails

        emails = list_emails(max_results=1, query=f"from:{attendee} OR to:{attendee}")
        if emails:
            em = emails[0]
            return f'"{em.subject}" ({em.date.strftime("%Y-%m-%d")})'
    except Exception as e:
        print(f"[{now_local()}] gmail lookup failed for {attendee}: {e}")
    return None


def _prune_state(prepped: dict[str, str], now: datetime) -> dict[str, str]:
    """Drop prepped-event records older than _STATE_RETENTION_DAYS."""
    keep: dict[str, str] = {}
    for event_id, stamp in prepped.items():
        try:
            ts = datetime.fromisoformat(stamp)
        except (ValueError, TypeError):
            continue
        if (now - ts).days < _STATE_RETENTION_DAYS:
            keep[event_id] = stamp
    return keep


def run_meeting_prep(test_mode: bool = False) -> list[str]:
    """One timer tick. Returns the summaries of events prepped this tick."""
    if not test_mode and not is_within_active_hours():
        print(f"[{now_local()}] Outside active hours, skipping meeting prep")
        return []

    from integrations.calendar_api import get_upcoming_events

    now = now_local()
    try:
        events = get_upcoming_events(hours_ahead=1, max_results=10)
    except Exception as e:
        print(f"[{now_local()}] Calendar fetch failed: {e}")
        return []

    state = load_state(MEETING_PREP_STATE_FILE)
    prepped = _prune_state(dict(state.get("prepped", {})), now)

    to_prep = select_events_to_prep(events, now, set(prepped))
    if not to_prep:
        print(f"[{now_local()}] No meetings in the next {PREP_WINDOW_MIN} min")
        if not test_mode:
            state["prepped"] = prepped
            save_state(state, MEETING_PREP_STATE_FILE)
        return []

    owner_email = GOOGLE_CALENDAR_ID if "@" in GOOGLE_CALENDAR_ID else ""
    sent: list[str] = []
    for ev in to_prep:
        attendees = external_attendees(ev, owner_email)
        memory_hits = _memory_context(attendees)
        last_thread = _last_email_thread(attendees[0]) if attendees else None
        pack = format_prep_pack(ev, now, memory_hits, last_thread, attendees)
        if test_mode:
            send_console_notification("Meeting prep (TEST)", pack)
        else:
            send_slack_notification("Meeting prep", pack)
            prepped[ev.id] = now.isoformat()
        sent.append(ev.summary)
        print(f"[{now_local()}] Prep sent: {ev.summary}")

    if not test_mode:
        state["prepped"] = prepped
        save_state(state, MEETING_PREP_STATE_FILE)
    return sent


def main() -> None:
    ensure_directories()
    test_mode = "--test" in sys.argv
    if test_mode:
        print("Running in TEST MODE (console output, no Slack, no state writes)")
    run_meeting_prep(test_mode=test_mode)


if __name__ == "__main__":
    main()
