"""Regression tests for get_unread_count().

The original implementation queried ``is:unread in:inbox`` with
``maxResults=1`` and returned Gmail's ``resultSizeEstimate``. That estimate is
wildly inflated at small page sizes — it returned 201 for a true count of 8 —
so the heartbeat reported nonsense unread totals. The fix reads the INBOX
label's exact ``messagesUnread`` field instead.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from integrations import gmail


def test_get_unread_count_uses_inbox_label_messages_unread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = MagicMock()
    labels_get = service.users.return_value.labels.return_value.get
    labels_get.return_value.execute.return_value = {
        "messagesUnread": 8,
        "messagesTotal": 39,
    }
    monkeypatch.setattr(gmail, "get_gmail_service", lambda: service)

    assert gmail.get_unread_count() == 8
    labels_get.assert_called_once_with(userId="me", id="INBOX")
    # The buggy resultSizeEstimate search path must not be used.
    service.users.return_value.messages.return_value.list.assert_not_called()


def test_get_unread_count_defaults_to_zero_when_field_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = MagicMock()
    service.users.return_value.labels.return_value.get.return_value.execute.return_value = {}
    monkeypatch.setattr(gmail, "get_gmail_service", lambda: service)

    assert gmail.get_unread_count() == 0
