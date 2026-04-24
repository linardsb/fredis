"""Tests for the urgent-email filter in integrations/gmail.py."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from integrations import gmail
from integrations.gmail import Email, check_for_urgent_emails


def _make_email(sender_email: str, subject: str) -> Email:
    return Email(
        id=f"id-{sender_email}-{subject}",
        thread_id="t",
        subject=subject,
        sender=f"Someone <{sender_email}>",
        sender_email=sender_email,
        date=datetime(2026, 4, 24, 6, 0, 0),
        snippet="",
        is_unread=True,
    )


def _patch_list_emails(monkeypatch: pytest.MonkeyPatch, emails: list[Email]) -> None:
    def fake_list_emails(*args: Any, **kwargs: Any) -> list[Email]:
        return emails

    monkeypatch.setattr(gmail, "list_emails", fake_list_emails)


def test_noreply_sender_rejected_despite_urgent_keyword(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reproduces the Render pricing-change false positive.
    emails = [_make_email("no-reply@render.com", "[Important] Upcoming pricing changes")]
    _patch_list_emails(monkeypatch, emails)

    assert check_for_urgent_emails() == []


def test_human_sender_with_urgent_keyword_still_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    emails = [_make_email("matis@farm.lv", "Urgent: payment overdue")]
    _patch_list_emails(monkeypatch, emails)

    result = check_for_urgent_emails()
    assert len(result) == 1
    assert result[0].sender_email == "matis@farm.lv"


@pytest.mark.parametrize(
    "sender_email",
    [
        "no-reply@render.com",
        "noreply@stripe.com",
        "donotreply@indeed.com",
        "do-not-reply@aws.amazon.com",
        "notifications@github.com",
        "notification@slack.com",
        "mailer-daemon@googlemail.com",
        "mailerdaemon@gmail.com",
        "newsletter@substack.com",
        "jobalert@linkedin.com",
        "digest@medium.com",
        "marketing@hubspot.com",
        "NO-REPLY@render.com",
    ],
)
def test_automated_sender_prefixes_rejected(
    monkeypatch: pytest.MonkeyPatch, sender_email: str
) -> None:
    emails = [_make_email(sender_email, "Important: action required")]
    _patch_list_emails(monkeypatch, emails)

    assert check_for_urgent_emails() == []


def test_ambiguous_prefixes_not_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    # support@ / hello@ / team@ are deliberately not in the blocklist; they
    # often come from small companies with real humans behind them.
    emails = [
        _make_email("support@clientco.com", "Urgent: contract question"),
        _make_email("hello@startup.io", "Important: meeting tomorrow"),
        _make_email("team@agency.com", "Deadline reminder"),
    ]
    _patch_list_emails(monkeypatch, emails)

    result = check_for_urgent_emails()
    assert len(result) == 3


@pytest.mark.parametrize(
    "subject",
    [
        "[Important] Upcoming pricing changes",
        "(important letter about your trading)",
        "(Deadline approaching) Renew now",
        "[ACTION REQUIRED] Confirm your subscription",
    ],
)
def test_bracketed_urgent_keywords_rejected(
    monkeypatch: pytest.MonkeyPatch, subject: str
) -> None:
    # SaaS marketing convention — keyword inside brackets/parens. Reject
    # even when the sender isn't automated (e.g. support@toponefutures.com).
    emails = [_make_email("support@toponefutures.com", subject)]
    _patch_list_emails(monkeypatch, emails)

    assert check_for_urgent_emails() == []


def test_urgent_keyword_outside_brackets_still_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Bracketed prefixes like [RFP] are legitimate; the keyword outside the
    # brackets should still trigger the match.
    emails = [_make_email("ops@clientco.com", "[RFP] Important decision needed")]
    _patch_list_emails(monkeypatch, emails)

    result = check_for_urgent_emails()
    assert len(result) == 1
