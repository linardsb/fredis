"""Tests for query.cmd_hubspot write subcommands.

The hubspot_api module is patched at the import boundary used inside
cmd_hubspot — assertions check that each subcommand calls the right API
with the right arguments. Resolver helpers are tested separately.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["HUBSPOT_API_TOKEN"] = "pat-test-fake"

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.hubspot_api as hubspot_api  # noqa: E402

importlib.reload(_config)
importlib.reload(hubspot_api)

import query  # noqa: E402

# =============================================================================
# Helpers
# =============================================================================


def _ns(**kwargs: Any) -> argparse.Namespace:
    """Build a Namespace with all hubspot args set to None plus overrides."""
    defaults = dict(
        action=None,
        target_id=None,
        max=25,
        stage=None,
        query=None,
        email=None, firstname=None, lastname=None, phone=None,
        urgent=None, conflict=None, conflict_reason=None,
        preferred_channel=None, lifecyclestage=None,
        name=None, domain=None, engagement=None,
        retainer_gbp=None, contract_end=None,
        amount=None, pipeline="Consultancy", currency=None,
        contact_email=None, company_domain=None,
        service_line=None, source=None, close_date=None,
        probability=None, to_stage=None, close_as=None,
        about=None, text=None, title=None, due=None,
        notes=None, status=None,
        with_target=None, summary=None, duration_min=None,
        disposition=None, direction=None,
        start=None, end=None, subject=None, sent_at=None, body=None,
        assoc_from=None, assoc_to=None, type_id=None,
        # Ticket-specific flags
        lane=None, urgency=None, skill_source=None, draft_path=None,
        dedupe_key=None, heartbeat_run=None, slack_thread=None,
        content=None, contact_id=None, company_id=None, deal_id=None,
        note=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _stub_obj(id_: str = "1", object_type: str = "contacts",
              properties: dict[str, Any] | None = None) -> hubspot_api.HubSpotObject:
    return hubspot_api.HubSpotObject(
        id=id_, object_type=object_type, properties=properties or {}
    )


@pytest.fixture
def hs_mocks() -> Any:
    """Patch every hubspot_api function used by cmd_hubspot writes."""
    with (
        patch("integrations.hubspot_api.create_object") as create_object,
        patch("integrations.hubspot_api.update_object") as update_object,
        patch("integrations.hubspot_api.archive_object") as archive_object,
        patch("integrations.hubspot_api.create_association") as create_association,
        patch("integrations.hubspot_api.delete_association") as delete_association,
        patch("integrations.hubspot_api.create_note") as create_note,
        patch("integrations.hubspot_api.create_task") as create_task,
        patch("integrations.hubspot_api.log_call") as log_call,
        patch("integrations.hubspot_api.log_meeting") as log_meeting,
        patch("integrations.hubspot_api.log_email") as log_email,
        patch("integrations.hubspot_api.search_objects") as search_objects,
        patch("integrations.hubspot_api.list_pipelines") as list_pipelines,
    ):
        # Default search → 1 match (resolver passes through)
        search_objects.return_value = [_stub_obj(id_="999")]
        create_object.return_value = _stub_obj(id_="123")
        update_object.return_value = _stub_obj(id_="123")
        create_note.return_value = {"id": "note_1"}
        create_task.return_value = {"id": "task_1"}
        log_call.return_value = {"id": "call_1"}
        log_meeting.return_value = {"id": "meet_1"}
        log_email.return_value = {"id": "email_1"}
        # Default pipeline shape
        list_pipelines.return_value = [{
            "id": "pipe_1", "label": "Consultancy",
            "stages": [
                {"id": "1", "label": "Inbound",
                 "metadata": {"probability": "0.1", "isClosed": "false"}},
                {"id": "2", "label": "Discovery",
                 "metadata": {"probability": "0.2", "isClosed": "false"}},
                {"id": "3", "label": "Post-delivery",
                 "metadata": {"probability": "1.0", "isClosed": "true"}},
                {"id": "4", "label": "Closed Lost",
                 "metadata": {"probability": "0.0", "isClosed": "true"}},
            ],
        }]
        yield {
            "create_object": create_object,
            "update_object": update_object,
            "archive_object": archive_object,
            "create_association": create_association,
            "delete_association": delete_association,
            "create_note": create_note,
            "create_task": create_task,
            "log_call": log_call,
            "log_meeting": log_meeting,
            "log_email": log_email,
            "search_objects": search_objects,
            "list_pipelines": list_pipelines,
        }


# =============================================================================
# Resolver helpers
# =============================================================================


def test_resolve_key_passes_numeric_through(hs_mocks: Any) -> None:
    assert query._hubspot_resolve_key("contacts", "12345") == "12345"
    hs_mocks["search_objects"].assert_not_called()


def test_resolve_key_searches_by_email(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [_stub_obj(id_="42")]
    out = query._hubspot_resolve_key("contacts", "tim@walking.vc")
    assert out == "42"
    args, _ = hs_mocks["search_objects"].call_args
    assert args[0] == "contacts"
    fg = args[1]
    assert fg[0]["filters"][0]["propertyName"] == "email"
    assert fg[0]["filters"][0]["value"] == "tim@walking.vc"


def test_resolve_key_searches_companies_by_domain(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [_stub_obj(id_="77",
                                                         object_type="companies")]
    out = query._hubspot_resolve_key("companies", "walking.vc")
    assert out == "77"
    fg = hs_mocks["search_objects"].call_args.args[1]
    assert fg[0]["filters"][0]["propertyName"] == "domain"


def test_resolve_key_no_match_raises(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = []
    with pytest.raises(ValueError, match="No contact"):
        query._hubspot_resolve_key("contacts", "nobody@example.com")


def test_resolve_key_ambiguous_raises_with_ids(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [
        _stub_obj(id_="1"), _stub_obj(id_="2")
    ]
    with pytest.raises(ValueError, match="IDs: 1, 2"):
        query._hubspot_resolve_key("contacts", "shared@inbox.com")


def test_resolve_stage_id_case_insensitive(hs_mocks: Any) -> None:
    assert query._hubspot_resolve_stage_id("discovery") == "2"
    assert query._hubspot_resolve_stage_id("INBOUND") == "1"


def test_resolve_stage_id_unknown_raises(hs_mocks: Any) -> None:
    with pytest.raises(ValueError, match="Stage 'BogusStage' not in"):
        query._hubspot_resolve_stage_id("BogusStage")


def test_resolve_closed_stage_won(hs_mocks: Any) -> None:
    # Highest probability among closed → Post-delivery (id=3)
    assert query._hubspot_resolve_closed_stage_id("won") == "3"


def test_resolve_closed_stage_lost(hs_mocks: Any) -> None:
    # Probability=0 closed → Closed Lost (id=4)
    assert query._hubspot_resolve_closed_stage_id("lost") == "4"


def test_resolve_closed_stage_invalid_status(hs_mocks: Any) -> None:
    with pytest.raises(ValueError, match="must be 'won' or 'lost'"):
        query._hubspot_resolve_closed_stage_id("draw")


def test_parse_about_normalises_singular() -> None:
    assert query._hubspot_parse_about("contact:tim@x.com") == ("contacts", "tim@x.com")
    assert query._hubspot_parse_about("deal:42") == ("deals", "42")
    assert query._hubspot_parse_about("Company:walking.vc") == ("companies", "walking.vc")


def test_parse_about_missing_colon_raises() -> None:
    with pytest.raises(ValueError, match="<type>:<key>"):
        query._hubspot_parse_about("contact-tim@x.com")


def test_bool_arg_normalises() -> None:
    assert query._bool_arg("true") == "true"
    assert query._bool_arg("YES") == "true"
    assert query._bool_arg("false") == "false"
    assert query._bool_arg("0") == "false"
    assert query._bool_arg(None) is None
    with pytest.raises(ValueError):
        query._bool_arg("maybe")


# =============================================================================
# Contacts
# =============================================================================


def test_create_contact_minimal(hs_mocks: Any) -> None:
    args = _ns(action="create-contact", email="new@example.com")
    query.cmd_hubspot(args)
    hs_mocks["create_object"].assert_called_once_with(
        "contacts", {"email": "new@example.com"}
    )


def test_create_contact_with_urgent_and_company(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [
        _stub_obj(id_="55", object_type="companies")
    ]
    args = _ns(
        action="create-contact",
        email="tim@walking.vc",
        firstname="Tim", lastname="Jackson",
        urgent="true", preferred_channel="email",
        company_domain="walking.vc",
    )
    query.cmd_hubspot(args)
    create_args = hs_mocks["create_object"].call_args.args
    assert create_args[0] == "contacts"
    props = create_args[1]
    assert props["urgent_alert"] == "true"
    assert props["firstname"] == "Tim"
    assert props["preferred_channel"] == "email"
    # Association created on the new contact (id 123 from fixture default)
    hs_mocks["create_association"].assert_called_once()
    assoc_args = hs_mocks["create_association"].call_args
    assert assoc_args.args[0] == "contacts"
    assert assoc_args.args[2] == "companies"
    assert assoc_args.args[3] == "55"
    assert assoc_args.kwargs["type_id"] == 1


def test_update_contact_resolves_email(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [_stub_obj(id_="42")]
    args = _ns(action="update-contact", target_id="tim@walking.vc",
               urgent="false")
    query.cmd_hubspot(args)
    hs_mocks["update_object"].assert_called_once()
    call = hs_mocks["update_object"].call_args
    assert call.args[1] == "42"
    assert call.args[2] == {"urgent_alert": "false"}


def test_update_contact_no_fields_raises(hs_mocks: Any) -> None:
    args = _ns(action="update-contact", target_id="42")
    with pytest.raises(ValueError, match="no fields to update"):
        query.cmd_hubspot(args)


def test_archive_contact_resolves_then_archives(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [_stub_obj(id_="42")]
    args = _ns(action="archive-contact", target_id="tim@walking.vc")
    query.cmd_hubspot(args)
    hs_mocks["archive_object"].assert_called_once_with("contacts", "42")


# =============================================================================
# Companies
# =============================================================================


def test_create_company_requires_name_and_domain(hs_mocks: Any) -> None:
    args = _ns(action="create-company", name="Walking", domain=None)
    with pytest.raises(ValueError, match="--name and --domain"):
        query.cmd_hubspot(args)


def test_create_company_passes_props(hs_mocks: Any) -> None:
    args = _ns(
        action="create-company",
        name="Walking", domain="walking.vc",
        engagement="retainer", retainer_gbp=2500.0,
        contract_end="2026-12-31",
    )
    query.cmd_hubspot(args)
    props = hs_mocks["create_object"].call_args.args[1]
    assert props["name"] == "Walking"
    assert props["engagement_type"] == "retainer"
    assert props["retainer_gbp_mo"] == 2500.0
    assert props["contract_end_date"] == "2026-12-31"


def test_update_company_resolves_domain(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [
        _stub_obj(id_="77", object_type="companies")
    ]
    args = _ns(action="update-company", target_id="walking.vc",
               engagement="dormant")
    query.cmd_hubspot(args)
    call = hs_mocks["update_object"].call_args
    assert call.args[0] == "companies"
    assert call.args[1] == "77"
    assert call.args[2] == {"engagement_type": "dormant"}


def test_archive_company(hs_mocks: Any) -> None:
    args = _ns(action="archive-company", target_id="77")  # numeric → no search
    query.cmd_hubspot(args)
    hs_mocks["archive_object"].assert_called_once_with("companies", "77")


# =============================================================================
# Deals
# =============================================================================


def test_create_deal_with_stage_label(hs_mocks: Any) -> None:
    args = _ns(
        action="create-deal",
        name="Smoke Deal", amount=100.0, stage="Inbound", currency="GBP",
    )
    query.cmd_hubspot(args)
    props = hs_mocks["create_object"].call_args.args[1]
    assert props["dealname"] == "Smoke Deal"
    assert props["dealstage"] == "1"  # Inbound stage id
    assert props["pipeline"] == "pipe_1"
    assert props["amount"] == "100.0"
    assert props["deal_currency_code"] == "GBP"


def test_create_deal_associates_contact_and_company(hs_mocks: Any) -> None:
    # Two distinct search results in order: contact lookup, then company lookup
    hs_mocks["search_objects"].side_effect = [
        [_stub_obj(id_="42", object_type="contacts")],
        [_stub_obj(id_="55", object_type="companies")],
    ]
    args = _ns(
        action="create-deal",
        name="Smoke Deal", amount=100.0, stage="Inbound",
        contact_email="tim@walking.vc", company_domain="walking.vc",
    )
    query.cmd_hubspot(args)
    # Two associations created, on the new deal id (123 from fixture)
    assert hs_mocks["create_association"].call_count == 2
    types_called = {
        c.kwargs["type_id"]
        for c in hs_mocks["create_association"].call_args_list
    }
    assert types_called == {3, 5}  # deal→contact=3, deal→company=5


def test_move_deal_resolves_stage_label(hs_mocks: Any) -> None:
    args = _ns(action="move-deal", target_id="123", to_stage="Discovery")
    query.cmd_hubspot(args)
    call = hs_mocks["update_object"].call_args
    assert call.args == ("deals", "123", {"dealstage": "2"})


def test_close_deal_won_uses_post_delivery_stage(hs_mocks: Any) -> None:
    args = _ns(action="close-deal", target_id="123", close_as="won")
    query.cmd_hubspot(args)
    call = hs_mocks["update_object"].call_args
    assert call.args == ("deals", "123", {"dealstage": "3"})


def test_close_deal_lost_uses_lost_stage(hs_mocks: Any) -> None:
    args = _ns(action="close-deal", target_id="123", close_as="lost")
    query.cmd_hubspot(args)
    call = hs_mocks["update_object"].call_args
    assert call.args == ("deals", "123", {"dealstage": "4"})


def test_archive_deal_does_not_resolve(hs_mocks: Any) -> None:
    args = _ns(action="archive-deal", target_id="123")
    query.cmd_hubspot(args)
    hs_mocks["archive_object"].assert_called_once_with("deals", "123")
    hs_mocks["search_objects"].assert_not_called()


# =============================================================================
# Engagements
# =============================================================================


def test_add_note_associates_to_contact(hs_mocks: Any) -> None:
    hs_mocks["search_objects"].return_value = [_stub_obj(id_="42")]
    args = _ns(action="add-note", about="contact:tim@walking.vc",
               text="smoke test note")
    query.cmd_hubspot(args)
    call = hs_mocks["create_note"].call_args
    assert call.args[0] == "smoke test note"
    assoc = call.kwargs["associations"]
    assert assoc[0]["to"] == {"id": "42"}
    assert assoc[0]["types"][0]["associationTypeId"] == 202


def test_create_task_associates_to_deal(hs_mocks: Any) -> None:
    args = _ns(action="create-task", about="deal:123",
               title="Send proposal", due="2026-05-01",
               notes="follow up")
    query.cmd_hubspot(args)
    call = hs_mocks["create_task"].call_args
    assert call.args[0] == "Send proposal"
    assert call.kwargs["body"] == "follow up"
    assoc = call.kwargs["associations"]
    assert assoc[0]["to"] == {"id": "123"}
    assert assoc[0]["types"][0]["associationTypeId"] == 216


def test_log_call_converts_minutes_and_direction(hs_mocks: Any) -> None:
    args = _ns(action="log-call", with_target="contact:42",
               summary="Discovery call", duration_min=30,
               direction="in", disposition="CONNECTED")
    query.cmd_hubspot(args)
    call = hs_mocks["log_call"].call_args
    assert call.args[0] == "Discovery call"
    assert call.kwargs["duration_ms"] == 30 * 60 * 1000
    assert call.kwargs["direction"] == "INBOUND"
    assert call.kwargs["disposition"] == "CONNECTED"


def test_log_meeting_parses_iso(hs_mocks: Any) -> None:
    args = _ns(
        action="log-meeting", with_target="contact:42",
        title="Kickoff",
        start="2026-05-01T10:00:00+00:00",
        end="2026-05-01T11:00:00+00:00",
    )
    query.cmd_hubspot(args)
    call = hs_mocks["log_meeting"].call_args
    assert call.args[0] == "Kickoff"
    # start and end positionally
    assert call.args[1].year == 2026
    assert call.args[2].hour == 11


def test_log_email_normalises_direction(hs_mocks: Any) -> None:
    args = _ns(
        action="log-email", with_target="contact:42",
        subject="Proposal", direction="in",
        sent_at="2026-04-22T10:00:00+00:00", body="see attached",
    )
    query.cmd_hubspot(args)
    call = hs_mocks["log_email"].call_args
    assert call.args[0] == "Proposal"
    assert call.kwargs["direction"] == "INCOMING_EMAIL"


# =============================================================================
# Associations
# =============================================================================


def test_associate_uses_default_type_id(hs_mocks: Any) -> None:
    # Two resolves for from/to
    hs_mocks["search_objects"].side_effect = [
        [_stub_obj(id_="42")],  # contact
        [_stub_obj(id_="77", object_type="companies")],  # company
    ]
    args = _ns(action="associate",
               assoc_from="contact:tim@walking.vc",
               assoc_to="company:walking.vc")
    query.cmd_hubspot(args)
    call = hs_mocks["create_association"].call_args
    assert call.args == ("contacts", "42", "companies", "77")
    assert call.kwargs["type_id"] == 1  # contacts→companies default


def test_associate_accepts_type_id_override(hs_mocks: Any) -> None:
    args = _ns(action="associate",
               assoc_from="contact:42",
               assoc_to="company:77",
               type_id=280)
    query.cmd_hubspot(args)
    assert hs_mocks["create_association"].call_args.kwargs["type_id"] == 280


def test_unassociate_calls_delete_association(hs_mocks: Any) -> None:
    args = _ns(action="unassociate",
               assoc_from="contact:42",
               assoc_to="company:77")
    query.cmd_hubspot(args)
    hs_mocks["delete_association"].assert_called_once_with(
        "contacts", "42", "companies", "77"
    )


# =============================================================================
# Tickets — Fredis Review queue
# =============================================================================


def _stub_ticket(id_: str = "t1",
                 properties: dict[str, Any] | None = None) -> hubspot_api.HubSpotObject:
    return hubspot_api.HubSpotObject(
        id=id_, object_type="tickets", properties=properties or {}
    )


def test_create_ticket_invokes_api_with_custom_props() -> None:
    with patch("integrations.hubspot_api.create_ticket") as create_ticket:
        create_ticket.return_value = _stub_ticket(id_="77")
        args = _ns(
            action="create-ticket",
            subject="Smoke",
            content="body",
            lane="admin",
            skill_source="integrations",
            urgency="whenever",
            draft_path="Fredis/Memory/drafts/active/admin/smoke.md",
            contact_id="111",
            deal_id="222",
        )
        query.cmd_hubspot(args)
    kwargs = create_ticket.call_args.kwargs
    assert kwargs["subject"] == "Smoke"
    assert kwargs["content"] == "body"
    assert kwargs["lane"] == "admin"
    assert kwargs["skill_source"] == "integrations"
    assert kwargs["urgency"] == "whenever"
    assert kwargs["draft_path"] == "Fredis/Memory/drafts/active/admin/smoke.md"
    assert kwargs["contact_ids"] == ["111"]
    assert kwargs["company_ids"] is None
    assert kwargs["deal_ids"] == ["222"]


def test_create_ticket_requires_subject() -> None:
    with patch("integrations.hubspot_api.create_ticket") as create_ticket:
        args = _ns(action="create-ticket")
        with pytest.raises(ValueError, match="--subject required"):
            query.cmd_hubspot(args)
        create_ticket.assert_not_called()


def test_get_ticket_prints_found(capsys: Any) -> None:
    with patch("integrations.hubspot_api.get_ticket") as get_ticket:
        get_ticket.return_value = _stub_ticket(
            id_="77",
            properties={"subject": "Hi", "lane": "admin", "urgency": "today"},
        )
        args = _ns(action="get-ticket", target_id="77")
        query.cmd_hubspot(args)
    out = capsys.readouterr().out
    assert "Ticket 77" in out
    assert "subject: Hi" in out
    assert "lane: admin" in out


def test_get_ticket_missing_prints_not_found(capsys: Any) -> None:
    with patch("integrations.hubspot_api.get_ticket") as get_ticket:
        get_ticket.return_value = None
        args = _ns(action="get-ticket", target_id="404")
        query.cmd_hubspot(args)
    assert "not found" in capsys.readouterr().out


def test_move_ticket_invokes_api() -> None:
    with patch("integrations.hubspot_api.move_ticket") as move_ticket:
        move_ticket.return_value = _stub_ticket(id_="77")
        args = _ns(action="move-ticket", target_id="77", to_stage="Needs send")
        query.cmd_hubspot(args)
    move_ticket.assert_called_once_with("77", "Needs send")


def test_move_ticket_requires_id_and_stage() -> None:
    args = _ns(action="move-ticket", to_stage="Needs send")  # no target_id
    with pytest.raises(ValueError, match="Ticket id .* required"):
        query.cmd_hubspot(args)


def test_close_ticket_actioned() -> None:
    with patch("integrations.hubspot_api.close_ticket") as close_ticket:
        close_ticket.return_value = _stub_ticket(id_="77")
        args = _ns(action="close-ticket", target_id="77", close_as="actioned")
        query.cmd_hubspot(args)
    close_ticket.assert_called_once_with("77", as_="actioned", note=None)


def test_close_ticket_rejected_with_note() -> None:
    with patch("integrations.hubspot_api.close_ticket") as close_ticket:
        close_ticket.return_value = _stub_ticket(id_="77")
        args = _ns(
            action="close-ticket",
            target_id="77",
            close_as="rejected",
            note="already handled",
        )
        query.cmd_hubspot(args)
    close_ticket.assert_called_once_with(
        "77", as_="rejected", note="already handled"
    )


def test_close_ticket_rejects_deal_disposition() -> None:
    """--as won/lost is valid for deals but not tickets."""
    args = _ns(action="close-ticket", target_id="77", close_as="won")
    with pytest.raises(ValueError, match="must be 'actioned' or 'rejected'"):
        query.cmd_hubspot(args)


def test_list_tickets_prints_flat(capsys: Any) -> None:
    with patch("integrations.hubspot_api.list_open_tickets") as list_open:
        list_open.return_value = [
            _stub_ticket(
                id_="77",
                properties={
                    "subject": "Invoice review",
                    "lane": "client",
                    "urgency": "today",
                },
            ),
        ]
        args = _ns(action="list-tickets")
        query.cmd_hubspot(args)
    list_open.assert_called_once_with(lane=None, urgency=None, limit=25)
    out = capsys.readouterr().out
    assert "Open tickets (1)" in out
    assert "77 | client | today | Invoice review" in out


def test_list_tickets_filters_by_lane_and_urgency() -> None:
    with patch("integrations.hubspot_api.list_open_tickets") as list_open:
        list_open.return_value = []
        args = _ns(
            action="list-tickets", lane="content", urgency="today", max=50
        )
        query.cmd_hubspot(args)
    list_open.assert_called_once_with(lane="content", urgency="today", limit=50)


def test_queue_groups_by_urgency(capsys: Any) -> None:
    with patch("integrations.hubspot_api.list_open_tickets") as list_open:
        list_open.return_value = [
            _stub_ticket(id_="a", properties={
                "subject": "Pay VAT",
                "lane": "admin",
                "urgency": "today",
                "skill_source": "heartbeat",
            }),
            _stub_ticket(id_="b", properties={
                "subject": "LinkedIn draft",
                "lane": "content",
                "urgency": "whenever",
                "skill_source": "content-social",
            }),
            _stub_ticket(id_="c", properties={
                "subject": "Silent: Jane",
                "lane": "client",
                "urgency": "this_week",
                "skill_source": "heartbeat",
            }),
        ]
        args = _ns(action="queue")
        query.cmd_hubspot(args)
    out = capsys.readouterr().out
    # Sections must appear in today → this_week → whenever order
    today_pos = out.index("## today")
    week_pos = out.index("## this_week")
    whenever_pos = out.index("## whenever")
    assert today_pos < week_pos < whenever_pos
    assert "[admin] Pay VAT" in out
    assert "[client] Silent: Jane" in out
    assert "[content] LinkedIn draft" in out


def test_queue_empty_prints_no_tickets(capsys: Any) -> None:
    with patch("integrations.hubspot_api.list_open_tickets") as list_open:
        list_open.return_value = []
        args = _ns(action="queue")
        query.cmd_hubspot(args)
    assert "No open tickets" in capsys.readouterr().out
