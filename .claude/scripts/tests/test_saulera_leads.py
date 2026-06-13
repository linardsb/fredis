"""Tests for saulera_leads — contact-form parsing + Gmail fetch filtering.

Gmail calls are mocked; no network.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("HUBSPOT_API_TOKEN", "pat-test-fake")
os.environ.setdefault("HUBSPOT_HUB_ID", "1234567")

import saulera_leads  # noqa: E402


def _form_body(name: str, email: str, ask: str) -> str:
    """The exact body functions/api/contact.js emits (Resend text part)."""
    return (
        "New message from the saulera contact form\n"
        "\n"
        f"Name:  {name}\n"
        f"Email: {email}\n"
        "\n"
        f"{ask or '(no message)'}\n"
    )


def test_parse_standard_submission() -> None:
    body = _form_body("Jane Doe", "jane@acme.io", "We need an email workflow.")
    name, email, message = saulera_leads.parse_lead_fields("New enquiry — Jane Doe", body)
    assert name == "Jane Doe"
    assert email == "jane@acme.io"
    assert message == "We need an email workflow."


def test_parse_crlf_line_endings() -> None:
    body = _form_body("Bob", "bob@x.com", "Hello").replace("\n", "\r\n")
    name, email, message = saulera_leads.parse_lead_fields("New enquiry — Bob", body)
    assert name == "Bob"
    assert email == "bob@x.com"
    assert message == "Hello"


def test_parse_no_message_normalised() -> None:
    body = _form_body("Sam", "sam@y.com", "")
    _, _, message = saulera_leads.parse_lead_fields("New enquiry — Sam", body)
    assert message == "(no message)"


def test_parse_multiline_message() -> None:
    body = _form_body("Kim", "kim@z.com", "Line one.\nLine two.")
    _, _, message = saulera_leads.parse_lead_fields("New enquiry — Kim", body)
    assert message == "Line one.\nLine two."


def test_name_falls_back_to_subject() -> None:
    name, email, _ = saulera_leads.parse_lead_fields(
        "New enquiry — Subject Name", "Email: only@x.com\n"
    )
    assert name == "Subject Name"
    assert email == "only@x.com"


def test_missing_email_returns_empty() -> None:
    _, email, _ = saulera_leads.parse_lead_fields(
        "New enquiry — No Email", "Name:  No Email\n\nHi there\n"
    )
    assert email == ""


def test_fetch_filters_sender_and_drops_unparseable() -> None:
    listed = [
        SimpleNamespace(id="m1", sender_email="form@saulera.com"),
        SimpleNamespace(id="m2", sender_email="spoof@evil.com"),  # wrong sender → skip
        SimpleNamespace(id="m3", sender_email="form@saulera.com"),  # no email → drop
    ]
    fulls = {
        "m1": SimpleNamespace(
            id="m1",
            thread_id="t1",
            subject="New enquiry — Ann",
            body=_form_body("Ann", "ann@a.com", "Hi"),
            date=datetime(2026, 6, 13, 9, 0),
        ),
        "m3": SimpleNamespace(
            id="m3",
            thread_id="t3",
            subject="New enquiry — Broken",
            body="garbage with no email",
            date=datetime(2026, 6, 13, 10, 0),
        ),
    }

    def _get_details(_service: object, msg_id: str, include_body: bool = False) -> object:
        return fulls.get(msg_id)

    with (
        patch("integrations.gmail.list_emails", return_value=listed),
        patch("integrations.gmail.get_gmail_service", return_value=object()),
        patch("integrations.gmail.get_email_details", side_effect=_get_details),
    ):
        leads = saulera_leads.fetch_saulera_leads(hours_ago=6)

    assert len(leads) == 1
    assert leads[0].email == "ann@a.com"
    assert leads[0].message_id == "m1"
    assert leads[0].name == "Ann"
