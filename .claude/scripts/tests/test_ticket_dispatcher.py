"""Tests for ticket_dispatcher — dedupe, flag-gating, Slack post failure.

All external calls (HubSpot + Slack) mocked. No network.
"""

from __future__ import annotations

import importlib
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["HUBSPOT_API_TOKEN"] = "pat-test-fake"
os.environ["HUBSPOT_HUB_ID"] = "1234567"

import config as _config  # noqa: E402

importlib.reload(_config)

import integrations.hubspot_api as hubspot_api  # noqa: E402

importlib.reload(hubspot_api)


def _stub_ticket(id_: str = "t1",
                 properties: dict[str, Any] | None = None) -> hubspot_api.HubSpotObject:
    return hubspot_api.HubSpotObject(
        id=id_, object_type="tickets", properties=properties or {}
    )


def _reload_dispatcher_with_flag(enabled: bool) -> Any:
    """Reload config + ticket_dispatcher so the module-level flag reflects env."""
    os.environ["HUBSPOT_TICKETS_ENABLED"] = "true" if enabled else "false"
    importlib.reload(_config)
    import ticket_dispatcher  # noqa: WPS433
    importlib.reload(ticket_dispatcher)
    return ticket_dispatcher


# ---------------------------------------------------------------------------
# stable_dedupe_key
# ---------------------------------------------------------------------------


def test_dedupe_key_is_deterministic() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    k1 = td.stable_dedupe_key("heartbeat", "Overdue: Acme £500", "p/q.md")
    k2 = td.stable_dedupe_key("heartbeat", "Overdue: Acme £500", "p/q.md")
    assert k1 == k2
    assert len(k1) == 16


def test_dedupe_key_differs_by_subject() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    k_a = td.stable_dedupe_key("heartbeat", "A", "p/q.md")
    k_b = td.stable_dedupe_key("heartbeat", "B", "p/q.md")
    assert k_a != k_b


# ---------------------------------------------------------------------------
# hubspot_ticket_url
# ---------------------------------------------------------------------------


def test_ticket_url_uses_hub_id_when_configured() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    assert td.hubspot_ticket_url("999") == (
        "https://app.hubspot.com/contacts/1234567/ticket/999"
    )


# ---------------------------------------------------------------------------
# Flag-off path
# ---------------------------------------------------------------------------


def test_dispatch_skips_when_flag_off() -> None:
    td = _reload_dispatcher_with_flag(enabled=False)
    with patch("integrations.hubspot_api.create_ticket") as create_ticket:
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert result == {"skipped": "flag_off"}
    create_ticket.assert_not_called()


# ---------------------------------------------------------------------------
# Dedupe: open + recent closed
# ---------------------------------------------------------------------------


def test_dispatch_skips_when_open_ticket_exists() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    existing = _stub_ticket(id_="77", properties={"dedupe_key": "k"})
    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              return_value=[existing]) as search,
        patch("integrations.hubspot_api.create_ticket") as create_ticket,
    ):
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert result == {"skipped": "dedupe_open", "ticket_id": "77"}
    # Only the open_only=True search runs; the open path short-circuits.
    search.assert_called_once()
    create_ticket.assert_not_called()


def test_dispatch_skips_when_recent_closed_ticket_exists() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    # 2 days ago — within default reopen window of 7 days.
    recent = datetime.now(UTC) - timedelta(days=2)
    closed = _stub_ticket(
        id_="88",
        properties={"hs_lastmodifieddate": recent.isoformat().replace("+00:00", "Z")},
    )

    def fake_search(key: str, open_only: bool = True, pipeline_name: str = "") -> Any:
        return [] if open_only else [closed]

    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              side_effect=fake_search),
        patch("integrations.hubspot_api.create_ticket") as create_ticket,
    ):
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert result == {"skipped": "dedupe_recent", "ticket_id": "88"}
    create_ticket.assert_not_called()


def test_dispatch_creates_when_closed_ticket_is_older_than_reopen_window() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    # 30 days ago — past the default 7-day reopen window.
    old = datetime.now(UTC) - timedelta(days=30)
    closed = _stub_ticket(
        id_="88",
        properties={"hs_lastmodifieddate": old.isoformat().replace("+00:00", "Z")},
    )

    def fake_search(key: str, open_only: bool = True, pipeline_name: str = "") -> Any:
        return [] if open_only else [closed]

    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              side_effect=fake_search),
        patch("integrations.hubspot_api.create_ticket") as create_ticket,
        patch("integrations.slack_api.send_notification"),
    ):
        create_ticket.return_value = _stub_ticket(id_="new")
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert result == {"created": True, "ticket_id": "new"}


# ---------------------------------------------------------------------------
# Happy path: ticket created + Slack post
# ---------------------------------------------------------------------------


def test_dispatch_happy_path_creates_ticket_and_posts_slack() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              return_value=[]) as search,
        patch("integrations.hubspot_api.create_ticket") as create_ticket,
        patch("integrations.slack_api.send_notification") as send,
    ):
        create_ticket.return_value = _stub_ticket(id_="new")
        result = td.dispatch_ticket(
            subject="Overdue: Acme",
            content="body",
            lane="client",
            skill_source="heartbeat",
            urgency="today",
            draft_path="Fredis/Memory/drafts/active/heartbeat/overdue-invoice-1.md",
            heartbeat_run_id="hb-20260423-0800",
            deal_ids=["42"],
        )

    assert result == {"created": True, "ticket_id": "new"}
    # Two dedupe searches run (open_only=True, then all).
    assert search.call_count == 2

    # create_ticket got a stable dedupe_key.
    ct_kwargs = create_ticket.call_args.kwargs
    assert ct_kwargs["lane"] == "client"
    assert ct_kwargs["skill_source"] == "heartbeat"
    assert ct_kwargs["urgency"] == "today"
    assert ct_kwargs["deal_ids"] == ["42"]
    assert isinstance(ct_kwargs["dedupe_key"], str) and len(ct_kwargs["dedupe_key"]) == 16

    # Slack post uses the configured channel + expected message format.
    slack_args = send.call_args.args
    assert slack_args[0] == "hubspot"
    msg = slack_args[1]
    assert "[DRAFT] Overdue: Acme" in msg
    assert "Lane: client · Urgency: today · Skill: heartbeat" in msg
    assert "Draft: Fredis/Memory/drafts/active/heartbeat/overdue-invoice-1.md" in msg
    assert "Ticket: https://app.hubspot.com/contacts/1234567/ticket/new" in msg


def test_dispatch_reports_slack_error_without_failing(capsys: Any) -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              return_value=[]),
        patch("integrations.hubspot_api.create_ticket") as create_ticket,
        patch("integrations.slack_api.send_notification",
              side_effect=RuntimeError("slack down")),
    ):
        create_ticket.return_value = _stub_ticket(id_="new")
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert result["created"] is True
    assert result["ticket_id"] == "new"
    assert "slack_error" in result
    # Dispatcher must surface the failure on stderr so systemd journal and
    # local stdout show it (heartbeat callers additionally aggregate into
    # the daily log via _surface_slack_failures).
    captured = capsys.readouterr()
    assert "slack post failed for ticket new" in captured.err
    assert "slack down" in captured.err


def test_dispatch_reports_error_on_create_failure() -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    with (
        patch("integrations.hubspot_api.search_tickets_by_dedupe_key",
              return_value=[]),
        patch("integrations.hubspot_api.create_ticket",
              side_effect=RuntimeError("400 oops")) as create_ticket,
    ):
        result = td.dispatch_ticket(
            subject="x", content="", lane="admin",
            skill_source="heartbeat", urgency="today",
            draft_path="p.md",
        )
    assert "error" in result
    assert "create_ticket" in result["error"]
    create_ticket.assert_called_once()


# ---------------------------------------------------------------------------
# write_heartbeat_draft
# ---------------------------------------------------------------------------


def test_write_heartbeat_draft_creates_stable_path(tmp_path: Path, monkeypatch: Any) -> None:
    # Point DRAFTS_ACTIVE_DIR + PROJECT_ROOT at a tmp tree so we don't write
    # into the real vault during tests.
    td = _reload_dispatcher_with_flag(enabled=True)
    monkeypatch.setattr(td, "DRAFTS_ACTIVE_DIR", tmp_path)
    monkeypatch.setattr(td, "PROJECT_ROOT", tmp_path.parent)

    rel = td.write_heartbeat_draft(
        "overdue-invoice", "deal-42", "title", "body"
    )
    written = tmp_path / "heartbeat" / "overdue-invoice-deal-42.md"
    assert written.exists()
    content = written.read_text(encoding="utf-8")
    assert "alert_type: overdue-invoice" in content
    assert "entity_id: deal-42" in content
    assert rel.endswith("heartbeat/overdue-invoice-deal-42.md")


def test_write_heartbeat_draft_is_idempotent(tmp_path: Path, monkeypatch: Any) -> None:
    td = _reload_dispatcher_with_flag(enabled=True)
    monkeypatch.setattr(td, "DRAFTS_ACTIVE_DIR", tmp_path)
    monkeypatch.setattr(td, "PROJECT_ROOT", tmp_path.parent)

    p1 = td.write_heartbeat_draft("overdue-invoice", "42", "t1", "b1")
    p2 = td.write_heartbeat_draft("overdue-invoice", "42", "t2", "b2")
    assert p1 == p2  # same stable filename
    assert "t2" in (tmp_path / "heartbeat" / "overdue-invoice-42.md").read_text(
        encoding="utf-8"
    )


# Clean up: restore flag to default false for other tests that might run later.
def teardown_module(module: Any) -> None:
    os.environ["HUBSPOT_TICKETS_ENABLED"] = "false"
    importlib.reload(_config)
    import ticket_dispatcher
    importlib.reload(ticket_dispatcher)


# Silence unused import warnings.
_ = MagicMock
