"""Tests for integrations.habit_signals — HABITS.md-spec pillar auto-detection."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("HUBSPOT_API_TOKEN", "pat-fake-for-tests")

from integrations import habit_signals  # noqa: E402
from integrations.habit_signals import (  # noqa: E402
    PillarTick,
    frontier_self_report_due,
    frontier_tick,
    ground_body_tick,
    read_tick,
    ship_tick,
)

# -----------------------------------------------------------------------------
# Fakes matching the shape heartbeat passes in raw_data
# -----------------------------------------------------------------------------


@dataclass
class _FakeEmail:
    id: str
    subject: str
    sender: str = "me@fredis.dev"
    sender_email: str = "me@fredis.dev"


@dataclass
class _FakeGitHubEvent:
    id: str
    type: str
    repo: str
    summary: str = "1 commit"


@dataclass
class _FakeCalEvent:
    id: str
    summary: str


def _base_raw_data() -> dict[str, Any]:
    return {
        "urgent_emails": [],
        "recent_emails": [],
        "today_events": [],
        "upcoming_events": [],
        "slack_important": [],
        "hubspot_overdue_invoices": [],
        "hubspot_silent_contacts": [],
        "hubspot_stale_deals": [],
        "github_breached_gates": [],
        "github_commits": [],
        "github_review_requests": [],
        "errors": {},
    }


# =============================================================================
# Ship pillar
# =============================================================================


def test_ship_ticks_when_client_email_sent(monkeypatch: pytest.MonkeyPatch) -> None:
    import integrations.gmail as gmail
    from integrations import hubspot_api

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: {"acme.com"})
    monkeypatch.setattr(hubspot_api, "recent_client_engagements", lambda *a, **k: [])
    monkeypatch.setattr(
        gmail,
        "sent_to_domain",
        lambda domains, hours=24: [_FakeEmail(id="e1", subject="Q3 scope update")],
    )

    result = ship_tick(_base_raw_data())
    assert result.tick is True
    assert result.reason is not None
    assert "client email sent" in result.reason.lower()


def test_ship_ticks_when_hubspot_engagement_logged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import integrations.gmail as gmail
    from integrations import hubspot_api

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: {"acme.com"})
    monkeypatch.setattr(gmail, "sent_to_domain", lambda domains, hours=24: [])
    monkeypatch.setattr(
        hubspot_api,
        "recent_client_engagements",
        lambda *a, **k: [
            hubspot_api.ClientEngagement(
                engagement_type="calls",
                engagement_id="eng-99",
                company_id="co-7",
                created_at_ms=1700000000000,
            )
        ],
    )

    result = ship_tick(_base_raw_data())
    assert result.tick is True
    assert result.reason is not None
    assert "call" in result.reason.lower()


def test_ship_silent_when_no_client_domains_and_no_engagements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import integrations.gmail as gmail
    from integrations import hubspot_api

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: set())
    monkeypatch.setattr(hubspot_api, "recent_client_engagements", lambda *a, **k: [])
    monkeypatch.setattr(gmail, "sent_to_domain", lambda domains, hours=24: [])

    result = ship_tick(_base_raw_data())
    assert result.tick is False
    assert result.reason is None


def test_ship_skips_gmail_when_no_client_domains_known(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With no client domains, don't call Gmail's sent_to_domain at all."""
    import integrations.gmail as gmail
    from integrations import hubspot_api

    called: list[str] = []

    def _should_not_be_called(domains: set[str], hours: int = 24) -> list[Any]:
        called.append("gmail")
        return []

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: set())
    monkeypatch.setattr(hubspot_api, "recent_client_engagements", lambda *a, **k: [])
    monkeypatch.setattr(gmail, "sent_to_domain", _should_not_be_called)

    ship_tick(_base_raw_data())
    assert called == []


def test_ship_survives_gmail_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gmail API blowing up must not crash the heartbeat — fall through to HubSpot."""
    import integrations.gmail as gmail
    from integrations import hubspot_api

    def _blow_up(domains: set[str], hours: int = 24) -> list[Any]:
        raise RuntimeError("gmail api oom")

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: {"acme.com"})
    monkeypatch.setattr(gmail, "sent_to_domain", _blow_up)
    monkeypatch.setattr(
        hubspot_api,
        "recent_client_engagements",
        lambda *a, **k: [
            hubspot_api.ClientEngagement(
                engagement_type="notes",
                engagement_id="eng-1",
                company_id="co-1",
                created_at_ms=1700000000000,
            )
        ],
    )

    result = ship_tick(_base_raw_data())
    assert result.tick is True
    assert result.reason is not None
    assert "note" in result.reason.lower()


def test_ship_survives_hubspot_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import integrations.gmail as gmail
    from integrations import hubspot_api

    def _blow_up(*a: Any, **k: Any) -> list[Any]:
        raise RuntimeError("hubspot api rate limit")

    monkeypatch.setattr(hubspot_api, "get_client_domains", lambda *a, **k: {"acme.com"})
    monkeypatch.setattr(gmail, "sent_to_domain", lambda *a, **k: [])
    monkeypatch.setattr(hubspot_api, "recent_client_engagements", _blow_up)

    result = ship_tick(_base_raw_data())
    assert result.tick is False
    assert result.reason is None


# =============================================================================
# Frontier pillar
# =============================================================================


def test_frontier_ticks_on_build_repo_plus_keyword() -> None:
    raw = _base_raw_data()
    raw["github_commits"] = [_FakeGitHubEvent(id="1", type="PushEvent", repo="linardsb/fredis")]
    log_text = "Shipped the new agentic loop for draft reconcile."

    result = frontier_tick(raw, log_text)
    assert result.tick is True
    assert result.reason is not None
    assert "build-repo push" in result.reason


def test_frontier_silent_when_build_but_no_keyword() -> None:
    raw = _base_raw_data()
    raw["github_commits"] = [_FakeGitHubEvent(id="1", type="PushEvent", repo="linardsb/fredis")]
    log_text = "Did some client work."  # No frontier keyword

    result = frontier_tick(raw, log_text)
    assert result.tick is False
    assert result.reason is not None
    assert "no frontier keyword" in result.reason


def test_frontier_silent_when_no_build_activity() -> None:
    raw = _base_raw_data()
    raw["github_commits"] = [
        _FakeGitHubEvent(id="1", type="PushEvent", repo="linardsb/some-other-repo")
    ]
    log_text = "Built a new prototype."

    result = frontier_tick(raw, log_text)
    assert result.tick is False
    assert result.reason is None


# =============================================================================
# Ground (Body) pillar
# =============================================================================


def test_ground_body_ticks_on_movement_event() -> None:
    raw = _base_raw_data()
    raw["today_events"] = [_FakeCalEvent(id="1", summary="Morning run 5k")]

    result = ground_body_tick(raw)
    assert result.tick is True
    assert result.reason is not None
    assert "5k" in result.reason or "Morning run" in result.reason


def test_ground_body_ticks_from_upcoming_events() -> None:
    """Evening gym on today's calendar counts even when heartbeat fires at 10:00."""
    raw = _base_raw_data()
    raw["upcoming_events"] = [_FakeCalEvent(id="1", summary="Gym session at 17:00")]

    result = ground_body_tick(raw)
    assert result.tick is True


def test_ground_body_silent_without_movement_keyword() -> None:
    raw = _base_raw_data()
    raw["today_events"] = [_FakeCalEvent(id="1", summary="Client call with Atis")]

    result = ground_body_tick(raw)
    assert result.tick is False
    assert result.reason is None


# =============================================================================
# Frontier self-report nudge
# =============================================================================


def test_frontier_nudge_not_due_before_18h() -> None:
    raw = _base_raw_data()
    assert frontier_self_report_due(10, raw, "") is False
    assert frontier_self_report_due(17, raw, "") is False


def test_frontier_nudge_due_at_18h_when_silent() -> None:
    raw = _base_raw_data()  # No build activity
    assert frontier_self_report_due(18, raw, "") is True
    assert frontier_self_report_due(20, raw, "") is True


def test_frontier_nudge_skipped_when_already_ticked() -> None:
    raw = _base_raw_data()
    raw["github_commits"] = [_FakeGitHubEvent(id="1", type="PushEvent", repo="linardsb/fredis")]
    log_text = "Built a new prototype."

    # Frontier ticks, so no nudge due even at 18:00
    assert frontier_self_report_due(19, raw, log_text) is False


# =============================================================================
# No-op pillars (Read + Ground-Near always self-report)
# =============================================================================


def test_read_tick_is_never_auto_detected() -> None:
    result = read_tick(_base_raw_data())
    assert result.tick is False
    assert result.reason is None


def test_build_repos_constant_matches_design() -> None:
    """Guard against accidental edits to the build-repo filter."""
    assert "linardsb/fredis" in habit_signals.BUILD_REPOS
    # vault-sync-noise repos should NOT be in the set
    assert "linardsb/second-brain-vault" not in habit_signals.BUILD_REPOS


def test_pillar_tick_dataclass_shape() -> None:
    t = PillarTick(tick=True, reason="smoke test")
    assert t.tick is True
    assert t.reason == "smoke test"
    # Defaults work
    silent = PillarTick(tick=False, reason=None)
    assert silent.reason is None
