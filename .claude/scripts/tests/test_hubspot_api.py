"""Tests for integrations.hubspot_api.

All HTTP is mocked. The live HubSpot API is intentionally never reached.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import os  # noqa: E402

os.environ["HUBSPOT_API_TOKEN"] = "pat-test-fake"

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.hubspot_api as hubspot_api  # noqa: E402

importlib.reload(_config)
importlib.reload(hubspot_api)


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


def _capture() -> tuple[dict[str, Any], Any]:
    captured: dict[str, Any] = {}

    def fake_request(
        method: str,
        url: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        captured["params"] = params
        captured["headers"] = headers
        return _mock_response(captured.get("_response") or {})

    return captured, fake_request


# =============================================================================
# Auth header shape
# =============================================================================


def test_auth_header_has_bearer_prefix() -> None:
    """HubSpot expects `Authorization: Bearer <token>`."""
    captured, fake = _capture()
    captured["_response"] = {"results": []}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.list_objects("contacts", limit=5)

    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert captured["headers"]["Authorization"] == "Bearer pat-test-fake"


def test_401_surfaces_rotation_message() -> None:
    resp = _mock_response({"status": "error", "message": "unauthorized"}, status_code=401)
    with patch("integrations.hubspot_api.requests.request", return_value=resp):
        with pytest.raises(RuntimeError, match="rotate HUBSPOT_API_TOKEN"):
            hubspot_api.list_objects("contacts")


def test_4xx_surfaces_body_message() -> None:
    resp = _mock_response(
        {"message": "Property 'foo' does not exist", "category": "VALIDATION_ERROR"},
        status_code=400,
    )
    with patch("integrations.hubspot_api.requests.request", return_value=resp):
        with pytest.raises(RuntimeError, match="Property 'foo' does not exist"):
            hubspot_api.list_objects("contacts")


# =============================================================================
# Endpoint paths
# =============================================================================


def test_list_objects_hits_crm_v3_path() -> None:
    captured, fake = _capture()
    captured["_response"] = {"results": []}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.list_objects("contacts", limit=10)
    assert captured["method"] == "GET"
    assert captured["url"].endswith("/crm/v3/objects/contacts")
    assert captured["params"]["limit"] == 10


def test_search_objects_posts_to_search_endpoint() -> None:
    captured, fake = _capture()
    captured["_response"] = {"results": []}
    filter_groups = [
        {"filters": [{"propertyName": "dealstage", "operator": "EQ", "value": "appt"}]}
    ]
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.search_objects("deals", filter_groups, properties=["dealname"])
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/deals/search")
    assert captured["json"]["filterGroups"] == filter_groups
    assert captured["json"]["properties"] == ["dealname"]


def test_batch_create_shape() -> None:
    captured, fake = _capture()
    captured["_response"] = {"results": []}
    records = [
        {"properties": {"email": "a@b.com"}},
        {"properties": {"email": "c@d.com"}},
    ]
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.batch_create("contacts", records)
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/contacts/batch/create")
    assert captured["json"] == {"inputs": records}


def test_batch_upsert_fills_id_property() -> None:
    captured, fake = _capture()
    captured["_response"] = {"results": []}
    records = [
        {"id": "a@b.com", "properties": {"firstname": "Ana"}},
        {"id": "c@d.com", "properties": {"firstname": "Bob"}},
    ]
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.batch_upsert("contacts", records, id_property="email")
    assert captured["url"].endswith("/crm/v3/objects/contacts/batch/upsert")
    inputs = captured["json"]["inputs"]
    assert len(inputs) == 2
    assert all(i["idProperty"] == "email" for i in inputs)
    assert inputs[0]["id"] == "a@b.com"
    assert inputs[0]["properties"] == {"firstname": "Ana"}


def test_create_object_returns_parsed() -> None:
    captured, fake = _capture()
    captured["_response"] = {
        "id": "12345",
        "properties": {"email": "new@example.com", "firstname": "Ana"},
        "createdAt": "2026-04-22T12:00:00Z",
        "updatedAt": "2026-04-22T12:00:00Z",
    }
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        obj = hubspot_api.create_object("contacts", {"email": "new@example.com"})
    assert obj.id == "12345"
    assert obj.properties["email"] == "new@example.com"
    assert obj.created_at is not None
    assert obj.object_type == "contacts"


def test_update_object_uses_patch() -> None:
    captured, fake = _capture()
    captured["_response"] = {
        "id": "777",
        "properties": {"firstname": "Renamed"},
    }
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.update_object("contacts", "777", {"firstname": "Renamed"})
    assert captured["method"] == "PATCH"
    assert captured["url"].endswith("/crm/v3/objects/contacts/777")
    assert captured["json"]["properties"]["firstname"] == "Renamed"


def test_create_association_hits_v4_endpoint() -> None:
    captured, fake = _capture()
    captured["_response"] = {"status": "COMPLETE"}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_association(
            "contacts", "1", "companies", "99", type_id=1
        )
    assert captured["method"] == "PUT"
    assert captured["url"].endswith("/crm/v4/objects/contacts/1/associations/companies/99")
    body = captured["json"]
    assert body[0]["associationTypeId"] == 1
    assert body[0]["associationCategory"] == "HUBSPOT_DEFINED"


# =============================================================================
# Schema + pipelines
# =============================================================================


def test_create_property_posts_spec() -> None:
    captured, fake = _capture()
    captured["_response"] = {"name": "urgent_alert"}
    spec = {
        "name": "urgent_alert",
        "label": "Urgent alert",
        "type": "bool",
        "fieldType": "booleancheckbox",
        "groupName": "contactinformation",
    }
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_property("contacts", spec)
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/properties/contacts")
    assert captured["json"] == spec


def test_list_properties_filters_to_dicts() -> None:
    captured, fake = _capture()
    captured["_response"] = {
        "results": [
            {"name": "email", "type": "string"},
            "garbage_non_dict_entry",
            {"name": "urgent_alert", "type": "bool"},
        ]
    }
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        props = hubspot_api.list_properties("contacts")
    assert len(props) == 2
    assert {p["name"] for p in props} == {"email", "urgent_alert"}


def test_create_pipeline_includes_stages() -> None:
    captured, fake = _capture()
    captured["_response"] = {"id": "pipe_1"}
    stages = [
        {"label": "Inbound", "metadata": {"probability": 0.1, "isClosed": False},
         "displayOrder": 0},
        {"label": "Signed", "metadata": {"probability": 1.0, "isClosed": True},
         "displayOrder": 1},
    ]
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_pipeline("deals", "Consultancy", stages)
    assert captured["url"].endswith("/crm/v3/pipelines/deals")
    assert captured["json"]["label"] == "Consultancy"
    assert captured["json"]["stages"] == stages


# =============================================================================
# Engagements
# =============================================================================


def test_create_note_includes_body_and_timestamp() -> None:
    captured, fake = _capture()
    captured["_response"] = {"id": "note_1"}
    associations = [
        {
            "to": {"id": "42"},
            "types": [
                {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}
            ],
        }
    ]
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_note("Follow up tomorrow", associations=associations)
    assert captured["url"].endswith("/crm/v3/objects/notes")
    assert captured["json"]["properties"]["hs_note_body"] == "Follow up tomorrow"
    assert "hs_timestamp" in captured["json"]["properties"]
    assert captured["json"]["associations"] == associations


def test_create_task_sets_not_started_status() -> None:
    from datetime import date

    captured, fake = _capture()
    captured["_response"] = {"id": "task_1"}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.create_task("Call Ana", body="ping about invoice", due_date=date(2026, 5, 1))
    props = captured["json"]["properties"]
    assert props["hs_task_subject"] == "Call Ana"
    assert props["hs_task_status"] == "NOT_STARTED"
    assert "hs_task_due_date" in props


# =============================================================================
# Formatter
# =============================================================================


def test_format_objects_wraps_in_external_data_tag() -> None:
    obj = hubspot_api.HubSpotObject(
        id="1",
        object_type="contacts",
        properties={
            "firstname": "Ana",
            "lastname": "Laura",
            "email": "ana@example.com",
            "hs_lead_status": "NEW",
        },
    )
    out = hubspot_api.format_objects_for_context([obj])
    assert '<external_data source="hubspot"' in out
    assert "</external_data>" in out
    assert "Ana Laura" in out
    assert "ana@example.com" in out


def test_format_objects_empty_list_still_wraps() -> None:
    out = hubspot_api.format_objects_for_context([])
    assert '<external_data source="hubspot"' in out
    assert "No HubSpot records found" in out


def test_format_objects_groups_by_type() -> None:
    c = hubspot_api.HubSpotObject(id="1", object_type="contacts",
                                  properties={"firstname": "Ana"})
    d = hubspot_api.HubSpotObject(id="99", object_type="deals",
                                  properties={"dealname": "Acme SaaS", "amount": "5000"})
    out = hubspot_api.format_objects_for_context([c, d])
    # Section headers present
    assert "## Contacts" in out
    assert "## Deals" in out


# =============================================================================
# Object parsing
# =============================================================================


def test_parse_object_extracts_timestamps() -> None:
    raw = {
        "id": "42",
        "properties": {"firstname": "Ana"},
        "createdAt": "2026-04-20T09:15:00Z",
        "updatedAt": "2026-04-22T10:00:00Z",
    }
    obj = hubspot_api._parse_object(raw, "contacts")
    assert obj.id == "42"
    assert obj.created_at is not None and obj.created_at.year == 2026
    assert obj.updated_at is not None and obj.updated_at.day == 22


def test_name_falls_back_across_types() -> None:
    c = hubspot_api.HubSpotObject(id="1", object_type="contacts",
                                  properties={"email": "shared@inbox.com"})
    assert c.name == "shared@inbox.com"
    co = hubspot_api.HubSpotObject(id="1", object_type="companies",
                                   properties={"domain": "example.com"})
    assert co.name == "example.com"
    d = hubspot_api.HubSpotObject(id="1", object_type="deals", properties={})
    assert d.name == "deal:1"


# =============================================================================
# Archive
# =============================================================================


def test_archive_object_uses_delete() -> None:
    captured, fake = _capture()
    captured["_response"] = {}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.archive_object("contacts", "1234")
    assert captured["method"] == "DELETE"
    assert captured["url"].endswith("/crm/v3/objects/contacts/1234")


def test_batch_archive_posts_inputs() -> None:
    captured, fake = _capture()
    captured["_response"] = {}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.batch_archive("deals", ["1", "2", "3"])
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/deals/batch/archive")
    assert captured["json"] == {"inputs": [{"id": "1"}, {"id": "2"}, {"id": "3"}]}


# =============================================================================
# Associations — list / delete
# =============================================================================


def test_list_associations_hits_v4_endpoint() -> None:
    captured, fake = _capture()
    captured["_response"] = {
        "results": [
            {"toObjectId": "99", "associationTypes": [{"typeId": 1}]},
            "garbage_non_dict",
        ]
    }
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        results = hubspot_api.list_associations("contacts", "42", "companies")
    assert captured["method"] == "GET"
    assert captured["url"].endswith(
        "/crm/v4/objects/contacts/42/associations/companies"
    )
    assert len(results) == 1
    assert results[0]["toObjectId"] == "99"


def test_delete_association_hits_v4_delete() -> None:
    captured, fake = _capture()
    captured["_response"] = {}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.delete_association("contacts", "42", "companies", "99")
    assert captured["method"] == "DELETE"
    assert captured["url"].endswith(
        "/crm/v4/objects/contacts/42/associations/companies/99"
    )


# =============================================================================
# Engagement helpers — log_call / log_meeting / log_email
# =============================================================================


def test_log_call_posts_to_calls_endpoint() -> None:
    captured, fake = _capture()
    captured["_response"] = {"id": "call_1"}
    associations = hubspot_api.build_associations([("contacts", "42", 194)])
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.log_call(
            "Discovery call",
            duration_ms=1_800_000,
            disposition="CONNECTED",
            direction="OUTBOUND",
            body="discussed scope",
            associations=associations,
        )
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/calls")
    props = captured["json"]["properties"]
    assert props["hs_call_title"] == "Discovery call"
    assert props["hs_call_duration"] == 1_800_000
    assert props["hs_call_disposition"] == "CONNECTED"
    assert props["hs_call_direction"] == "OUTBOUND"
    assert props["hs_call_body"] == "discussed scope"
    assert "hs_timestamp" in props
    assert captured["json"]["associations"] == associations


def test_log_meeting_posts_start_and_end_ms() -> None:
    from datetime import UTC as _UTC
    from datetime import datetime as _dt

    start = _dt(2026, 5, 1, 10, 0, tzinfo=_UTC)
    end = _dt(2026, 5, 1, 11, 0, tzinfo=_UTC)
    captured, fake = _capture()
    captured["_response"] = {"id": "meeting_1"}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.log_meeting(
            "Kickoff", start, end, body="notes from call"
        )
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/meetings")
    props = captured["json"]["properties"]
    assert props["hs_meeting_title"] == "Kickoff"
    assert props["hs_meeting_body"] == "notes from call"
    assert props["hs_meeting_start_time"] == int(start.timestamp() * 1000)
    assert props["hs_meeting_end_time"] == int(end.timestamp() * 1000)


def test_log_email_posts_to_emails_endpoint() -> None:
    from datetime import UTC as _UTC
    from datetime import datetime as _dt

    sent_at = _dt(2026, 4, 22, 10, 30, tzinfo=_UTC)
    captured, fake = _capture()
    captured["_response"] = {"id": "email_1"}
    with patch("integrations.hubspot_api.requests.request", side_effect=fake):
        hubspot_api.log_email(
            "Proposal",
            "See attached",
            direction="EMAIL",
            sent_at=sent_at,
        )
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/crm/v3/objects/emails")
    props = captured["json"]["properties"]
    assert props["hs_email_subject"] == "Proposal"
    assert props["hs_email_text"] == "See attached"
    assert props["hs_email_direction"] == "EMAIL"
    assert props["hs_timestamp"] == int(sent_at.timestamp() * 1000)


def test_build_associations_shapes_v4_payload() -> None:
    out = hubspot_api.build_associations(
        [("contacts", "42", 194), ("deals", "77", 214)]
    )
    assert len(out) == 2
    assert out[0]["to"] == {"id": "42"}
    assert out[0]["types"][0]["associationTypeId"] == 194
    assert out[0]["types"][0]["associationCategory"] == "HUBSPOT_DEFINED"
    assert out[1]["to"] == {"id": "77"}
    assert out[1]["types"][0]["associationTypeId"] == 214


# =============================================================================
# 429 surfaces as runtime error with status code
# =============================================================================


def test_429_surfaces_as_runtime_error() -> None:
    resp = _mock_response({"message": "rate limit exceeded"}, status_code=429)
    with patch("integrations.hubspot_api.requests.request", return_value=resp):
        with pytest.raises(RuntimeError, match="429"):
            hubspot_api.list_objects("contacts")
