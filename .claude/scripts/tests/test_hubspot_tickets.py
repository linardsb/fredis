"""Tests for ticket helpers in integrations.hubspot_api.

All HTTP is mocked. No live HubSpot calls.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["HUBSPOT_API_TOKEN"] = "pat-test-fake"

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.hubspot_api as hubspot_api  # noqa: E402

importlib.reload(_config)
importlib.reload(hubspot_api)


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


FAKE_PIPELINE = {
    "id": "0",
    "label": "Fredis Review",
    "stages": [
        {"id": "5001", "label": "Drafted", "metadata": {"ticketState": "OPEN"}},
        {"id": "5002", "label": "In review", "metadata": {"ticketState": "OPEN"}},
        {"id": "5003", "label": "Needs send", "metadata": {"ticketState": "OPEN"}},
        {"id": "5004", "label": "Actioned", "metadata": {"ticketState": "CLOSED"}},
        {"id": "5005", "label": "Rejected", "metadata": {"ticketState": "CLOSED"}},
    ],
}


def _mock_response(
    json_body: dict[str, Any] | list[Any] | None = None,
    status_code: int = 200,
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body if json_body is not None else {}
    resp.content = b"{}" if json_body is not None else b""
    resp.text = str(json_body)
    return resp


def _capture_requests() -> tuple[list[dict[str, Any]], Any]:
    """Router that captures every HTTP call and returns canned responses.

    Set entries in the returned list's `_responses` (via closure variables)
    to script per-URL responses; default is an empty object.
    """
    calls: list[dict[str, Any]] = []

    def fake_request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        calls.append(
            {"method": method, "url": url, "json": json, "params": params}
        )
        # Pipeline lookups — always return the fake pipeline list.
        if url.endswith("/crm/v3/pipelines/tickets"):
            return _mock_response({"results": [FAKE_PIPELINE]})
        # Search endpoints — return empty by default.
        if url.endswith("/crm/v3/objects/tickets/search"):
            return _mock_response({"results": []})
        # Object create / patch — echo a minimal ticket back.
        return _mock_response({"id": "9999", "properties": (json or {}).get("properties", {})})

    return calls, fake_request


# ---------------------------------------------------------------------------
# Association constants
# ---------------------------------------------------------------------------


def test_ticket_association_type_ids() -> None:
    assert hubspot_api.ASSOCIATION_TICKET_TO_CONTACT == 16
    assert hubspot_api.ASSOCIATION_TICKET_TO_COMPANY == 26
    assert hubspot_api.ASSOCIATION_TICKET_TO_DEAL == 28
    assert hubspot_api.ASSOCIATION_NOTE_TO_TICKET == 228


# ---------------------------------------------------------------------------
# Stage resolution
# ---------------------------------------------------------------------------


def test_resolve_ticket_stage_id_case_insensitive() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        assert hubspot_api.resolve_ticket_stage_id("Drafted") == "5001"
        assert hubspot_api.resolve_ticket_stage_id("needs send") == "5003"
        assert hubspot_api.resolve_ticket_stage_id("REJECTED") == "5005"


def test_resolve_ticket_stage_id_unknown_label_raises() -> None:
    _, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        with pytest.raises(ValueError, match="ticket stage 'Ghost' not found"):
            hubspot_api.resolve_ticket_stage_id("Ghost")


def test_resolve_ticket_stage_id_unknown_pipeline_raises() -> None:
    _, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        with pytest.raises(ValueError, match="ticket pipeline 'Other' not found"):
            hubspot_api.resolve_ticket_stage_id("Drafted", pipeline_name="Other")


# ---------------------------------------------------------------------------
# create_ticket — payload shape
# ---------------------------------------------------------------------------


def test_create_ticket_minimal_payload() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket("Smoke test", content="body")

    create_call = [c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")][0]
    assert create_call["method"] == "POST"
    props = create_call["json"]["properties"]
    assert props["subject"] == "Smoke test"
    assert props["content"] == "body"
    assert props["hs_pipeline"] == "0"
    assert props["hs_pipeline_stage"] == "5001"  # Drafted
    # `source_type` is deliberately NOT set — HubSpot tickets module rejects
    # "API" as a value; leaving null is correct.
    assert "source_type" not in props
    # Optional fields not set
    assert "lane" not in props
    assert "hs_ticket_priority" not in props
    assert "associations" not in create_call["json"]


def test_create_ticket_urgency_today_maps_to_high_priority() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket(
            "Urgent", urgency="today", lane="client", skill_source="heartbeat"
        )

    props = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")
    ][0]["json"]["properties"]
    assert props["urgency"] == "today"
    assert props["hs_ticket_priority"] == "HIGH"
    assert props["lane"] == "client"
    assert props["skill_source"] == "heartbeat"


def test_create_ticket_urgency_this_week_maps_to_medium() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket("Soonish", urgency="this_week")
    props = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")
    ][0]["json"]["properties"]
    assert props["hs_ticket_priority"] == "MEDIUM"


def test_create_ticket_urgency_whenever_maps_to_low() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket("Someday", urgency="whenever")
    props = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")
    ][0]["json"]["properties"]
    assert props["hs_ticket_priority"] == "LOW"


def test_create_ticket_urgency_unknown_skips_priority() -> None:
    """Unknown urgency values are passed through but don't set priority."""
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket("Odd", urgency="eventually")
    props = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")
    ][0]["json"]["properties"]
    assert props["urgency"] == "eventually"
    assert "hs_ticket_priority" not in props


def test_create_ticket_with_all_custom_properties() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket(
            "Full",
            content="body",
            lane="content",
            skill_source="content-social",
            urgency="whenever",
            draft_path="Fredis/Memory/drafts/active/content-social/post.md",
            dedupe_key="abc123",
            heartbeat_run_id="hb-20260423-0600",
            slack_thread_url="https://slack.com/archives/C1/p123",
        )
    props = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")
    ][0]["json"]["properties"]
    assert props["lane"] == "content"
    assert props["skill_source"] == "content-social"
    assert props["draft_path"] == "Fredis/Memory/drafts/active/content-social/post.md"
    assert props["dedupe_key"] == "abc123"
    assert props["heartbeat_run_id"] == "hb-20260423-0600"
    assert props["slack_thread_url"] == "https://slack.com/archives/C1/p123"


def test_create_ticket_builds_contact_company_deal_associations() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_ticket(
            "Assoc",
            contact_ids=["101"],
            company_ids=["202"],
            deal_ids=["303"],
        )

    create_call = [c for c in calls if c["url"].endswith("/crm/v3/objects/tickets")][0]
    associations = create_call["json"]["associations"]
    by_type = {a["types"][0]["associationTypeId"]: a["to"]["id"] for a in associations}
    assert by_type[16] == "101"  # ticket→contact
    assert by_type[26] == "202"  # ticket→company
    assert by_type[28] == "303"  # ticket→deal
    assert all(
        a["types"][0]["associationCategory"] == "HUBSPOT_DEFINED" for a in associations
    )


def test_create_ticket_unknown_stage_label_raises() -> None:
    _, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        with pytest.raises(ValueError, match="ticket stage 'Phantom' not found"):
            hubspot_api.create_ticket("Bad", stage_label="Phantom")


# ---------------------------------------------------------------------------
# move_ticket
# ---------------------------------------------------------------------------


def test_move_ticket_patches_stage_id() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.move_ticket("1234", "Needs send")

    patch_calls = [c for c in calls if c["method"] == "PATCH"]
    assert len(patch_calls) == 1
    assert patch_calls[0]["url"].endswith("/crm/v3/objects/tickets/1234")
    assert patch_calls[0]["json"]["properties"] == {"hs_pipeline_stage": "5003"}


# ---------------------------------------------------------------------------
# close_ticket
# ---------------------------------------------------------------------------


def test_close_ticket_as_actioned_moves_to_closed_stage() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.close_ticket("1234", as_="actioned")

    patch_calls = [c for c in calls if c["method"] == "PATCH"]
    assert patch_calls[0]["json"]["properties"]["hs_pipeline_stage"] == "5004"
    # No note engagement created when no note supplied
    assert not any(c["url"].endswith("/crm/v3/objects/notes") for c in calls)


def test_close_ticket_as_rejected_with_note_creates_engagement() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.close_ticket("1234", as_="rejected", note="already handled")

    patch_calls = [c for c in calls if c["method"] == "PATCH"]
    assert patch_calls[0]["json"]["properties"]["hs_pipeline_stage"] == "5005"

    note_calls = [c for c in calls if c["url"].endswith("/crm/v3/objects/notes")]
    assert len(note_calls) == 1
    note_body = note_calls[0]["json"]
    assert note_body["properties"]["hs_note_body"] == "already handled"
    # Note must associate to the ticket via typeId 228.
    assoc = note_body["associations"][0]
    assert assoc["to"]["id"] == "1234"
    assert assoc["types"][0]["associationTypeId"] == 228


def test_close_ticket_invalid_disposition_raises() -> None:
    _, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        with pytest.raises(ValueError, match="must be 'actioned' or 'rejected'"):
            hubspot_api.close_ticket("1234", as_="snoozed")


# ---------------------------------------------------------------------------
# list_open_tickets
# ---------------------------------------------------------------------------


def test_list_open_tickets_filters_by_open_stages() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.list_open_tickets()

    search_call = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets/search")
    ][0]
    filters = search_call["json"]["filterGroups"][0]["filters"]
    stage_filter = [f for f in filters if f["propertyName"] == "hs_pipeline_stage"][0]
    assert stage_filter["operator"] == "IN"
    assert set(stage_filter["values"]) == {"5001", "5002", "5003"}
    # No lane/urgency filter unless passed
    assert not any(f["propertyName"] in ("lane", "urgency") for f in filters)


def test_list_open_tickets_with_lane_and_urgency() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.list_open_tickets(lane="content", urgency="today")

    search_call = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets/search")
    ][0]
    filters = search_call["json"]["filterGroups"][0]["filters"]
    lane_filter = [f for f in filters if f["propertyName"] == "lane"][0]
    urgency_filter = [f for f in filters if f["propertyName"] == "urgency"][0]
    assert lane_filter == {"propertyName": "lane", "operator": "EQ", "value": "content"}
    assert urgency_filter == {"propertyName": "urgency", "operator": "EQ", "value": "today"}


# ---------------------------------------------------------------------------
# search_tickets_by_dedupe_key
# ---------------------------------------------------------------------------


def test_search_tickets_by_dedupe_key_open_only() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.search_tickets_by_dedupe_key("hash-abc", open_only=True)

    search_call = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets/search")
    ][0]
    filters = search_call["json"]["filterGroups"][0]["filters"]
    key_filter = [f for f in filters if f["propertyName"] == "dedupe_key"][0]
    assert key_filter == {
        "propertyName": "dedupe_key",
        "operator": "EQ",
        "value": "hash-abc",
    }
    # Open-stage filter also present
    stage_filter = [f for f in filters if f["propertyName"] == "hs_pipeline_stage"][0]
    assert set(stage_filter["values"]) == {"5001", "5002", "5003"}


def test_search_tickets_by_dedupe_key_all_stages() -> None:
    calls, fake = _capture_requests()
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.search_tickets_by_dedupe_key("hash-abc", open_only=False)

    search_call = [
        c for c in calls if c["url"].endswith("/crm/v3/objects/tickets/search")
    ][0]
    filters = search_call["json"]["filterGroups"][0]["filters"]
    # Only the dedupe_key filter — no stage filter when open_only=False
    assert len(filters) == 1
    assert filters[0]["propertyName"] == "dedupe_key"


# ---------------------------------------------------------------------------
# get_ticket — thin wrapper over get_object
# ---------------------------------------------------------------------------


def test_get_ticket_returns_none_on_404() -> None:
    resp = _mock_response({"message": "not found"}, status_code=404)
    with patch("integrations.hubspot_api.requests.request", return_value=resp):
        assert hubspot_api.get_ticket("missing") is None


def test_get_ticket_returns_object_on_200() -> None:
    resp = _mock_response(
        {
            "id": "555",
            "properties": {"subject": "Hi", "lane": "admin"},
        }
    )
    with patch("integrations.hubspot_api.requests.request", return_value=resp):
        ticket = hubspot_api.get_ticket("555", properties=["subject", "lane"])
    assert ticket is not None
    assert ticket.id == "555"
    assert ticket.properties["lane"] == "admin"
