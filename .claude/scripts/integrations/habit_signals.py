"""
Habit-pillar signal detection per Fredis/Memory/HABITS.md.

Returns (tick, reason) pairs so the heartbeat can surface WHY a pillar
auto-checked. Replaces the github-commits-as-Ship proxy that previously
lived inline at heartbeat.py:1545 — per HABITS.md spec, internal commits
do NOT count as Ship.

Pillars covered:
- Ship — Gmail sent to client domain OR HubSpot engagement logged on a client
- Frontier — GitHub pushes to a build repo AND keyword match in today's log
- Ground-Body — calendar event matching movement keywords
- Frontier self-report nudge — single ask at ≥18:00 if Frontier is silent

Read and Ground-Near are self-report per spec; no auto-detection.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@dataclass
class PillarTick:
    """Outcome of a pillar-signal check."""

    tick: bool
    reason: str | None  # e.g. "email sent to acme.com" or None when silent


# Build repos to consider for the Frontier pillar. Push events to any other
# repo don't count (vault-sync noise, client infra with no Frontier intent).
BUILD_REPOS: frozenset[str] = frozenset(
    {
        "linardsb/fredis",
        "linardsb/merkle-email-hub",
    }
)

# Daily-log keywords that confirm a Frontier intent alongside build activity.
# Per HABITS.md: "agentic, experiment, build, prototype".
FRONTIER_KEYWORDS: frozenset[str] = frozenset(
    {"agentic", "experiment", "build", "prototype", "loop"}
)

# Calendar event-title keywords that auto-tick Ground-Body. The list is
# deliberately narrow — only unambiguous movement. Per HABITS.md we do NOT
# auto-check Ground-Near from metadata.
MOVEMENT_KEYWORDS: frozenset[str] = frozenset(
    {"training", "walk", "gym", "run", "swim", "ride", "workout", "yoga"}
)

# Frontier self-report nudge fires at or after this hour (local).
FRONTIER_NUDGE_HOUR: int = 18


# =============================================================================
# Ship — client email sent OR HubSpot engagement logged on a client
# =============================================================================


def ship_tick(raw_data: dict[str, Any], *, hours: int = 24) -> PillarTick:
    """Ship per HABITS.md: a concrete artifact forward for a client.

    Ticks when either signal fires in the last `hours`:
    - Gmail sent to a client domain (via integrations.gmail.sent_to_domain)
    - HubSpot note / call / meeting / email logged against a client company
      (via integrations.hubspot_api.recent_client_engagements)

    Explicitly does NOT count internal github commits — HABITS.md carves those
    out ("internal commits, config changes, routine maintenance" don't count).
    """
    from integrations.hubspot_api import (
        get_client_domains,
        recent_client_engagements,
    )

    client_domains = get_client_domains()
    if client_domains:
        try:
            from integrations.gmail import sent_to_domain

            sent = sent_to_domain(client_domains, hours=hours)
        except Exception as e:
            print(f"[habit_signals] Gmail sent-to-domain check failed: {e}")
            sent = []
        if sent:
            first = sent[0]
            subject = (first.subject or "").strip()
            snippet = subject[:40] + ("..." if len(subject) > 40 else "")
            reason = f"client email sent ({snippet})" if snippet else "client email sent"
            return PillarTick(True, reason)

    try:
        engagements = recent_client_engagements(hours=hours)
    except Exception as e:
        print(f"[habit_signals] HubSpot engagement check failed: {e}")
        engagements = []
    if engagements:
        eng = engagements[0]
        label = eng.engagement_type.rstrip("s")
        return PillarTick(True, f"{label} logged on a client account")

    return PillarTick(False, None)


# =============================================================================
# Frontier — build-repo commit + daily-log keyword
# =============================================================================


def frontier_tick(raw_data: dict[str, Any], daily_log_text: str) -> PillarTick:
    """Frontier per HABITS.md: file activity on a build repo + daily-log
    keyword match (agentic / experiment / build / prototype).

    Requires BOTH halves: push to a build repo AND at least one keyword in
    today's daily log. Build-only (no keyword) returns tick=False with a
    narrating reason so the heartbeat prompt can nudge Linards to journal.
    """
    commits = raw_data.get("github_commits") or []
    build_activity = any(getattr(c, "repo", "") in BUILD_REPOS for c in commits)
    if not build_activity:
        return PillarTick(False, None)

    log_lower = (daily_log_text or "").lower()
    matched_keyword = next((k for k in FRONTIER_KEYWORDS if k in log_lower), None)
    if matched_keyword:
        return PillarTick(True, f"build-repo push + '{matched_keyword}' in daily log")

    return PillarTick(False, "build-repo push but no frontier keyword in daily log yet")


def frontier_self_report_due(
    hour_local: int, raw_data: dict[str, Any], daily_log_text: str
) -> bool:
    """True at or after 18:00 local if Frontier has not ticked today.

    Heartbeat surfaces this as a single in-prompt nudge — per HABITS.md the
    late-day nudge cycle is OFF for every other pillar; Frontier's
    self-report is the documented exception.
    """
    if hour_local < FRONTIER_NUDGE_HOUR:
        return False
    return not frontier_tick(raw_data, daily_log_text).tick


# =============================================================================
# Ground (Body) — calendar movement keyword
# =============================================================================


def ground_body_tick(raw_data: dict[str, Any]) -> PillarTick:
    """Ground-Body per HABITS.md: calendar event matching a movement keyword.

    Looks at both today's events and upcoming events (so a 17:00 gym session
    counts even when the heartbeat fires at 10:00). Only the first match is
    surfaced; the signal is binary.
    """
    events = list(raw_data.get("today_events") or []) + list(
        raw_data.get("upcoming_events") or []
    )
    for ev in events:
        title = (getattr(ev, "summary", "") or "").lower()
        matched = next((k for k in MOVEMENT_KEYWORDS if k in title), None)
        if matched:
            return PillarTick(True, f"calendar: {getattr(ev, 'summary', '') or matched}")

    return PillarTick(False, None)


# Read and Ground-Near: NEVER auto-detect per HABITS.md. Linards self-reports.
# Kept as no-op stubs so callers can iterate all four pillars uniformly if
# needed — Returns tick=False always.


def read_tick(raw_data: dict[str, Any]) -> PillarTick:
    """Read pillar — self-report only per HABITS.md. Always returns False."""
    return PillarTick(False, None)


def ground_near_tick(raw_data: dict[str, Any]) -> PillarTick:
    """Ground-Near pillar — self-report only per HABITS.md. Always returns False."""
    return PillarTick(False, None)
