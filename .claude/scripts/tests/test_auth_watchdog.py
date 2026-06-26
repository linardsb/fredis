"""Tests for the auth watchdog alert / dedup logic (the pure decision path).

The probes themselves hit the network, so they are out of scope here; what
matters is that ``_evaluate`` alerts on the transition into failure, suppresses
repeat alerts while still down, fires a recovery notice, and never flaps on a
transient blip — because that logic is what has to work unattended a year from
now when the token expires.
"""

from __future__ import annotations

from typing import Any

import pytest

import auth_watchdog
from config import now_local


def _capture(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    """Replace the Slack sender with a recorder; return the record list."""
    sent: list[tuple[str, str]] = []

    def _fake_send(title: str, message: str, channel: str | None = None) -> None:
        sent.append((title, message))

    monkeypatch.setattr(auth_watchdog, "send_slack_notification", _fake_send)
    return sent


def test_alerts_on_transition_to_down(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _capture(monkeypatch)
    new = auth_watchdog._evaluate("Claude", auth_watchdog._DOWN, "401", "fix", {})
    assert new["status"] == auth_watchdog._DOWN
    assert len(sent) == 1
    assert "DOWN" in sent[0][0]


def test_dedupes_while_recently_down(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _capture(monkeypatch)
    prev: dict[str, Any] = {
        "status": auth_watchdog._DOWN,
        "last_alert": now_local().isoformat(),
    }
    new = auth_watchdog._evaluate("Claude", auth_watchdog._DOWN, "401", "fix", prev)
    assert new["status"] == auth_watchdog._DOWN
    assert sent == []


def test_recovery_notice(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _capture(monkeypatch)
    prev: dict[str, Any] = {
        "status": auth_watchdog._DOWN,
        "last_alert": now_local().isoformat(),
    }
    new = auth_watchdog._evaluate("Google", auth_watchdog._OK, "", "fix", prev)
    assert new["status"] == auth_watchdog._OK
    assert len(sent) == 1
    assert "recovered" in sent[0][0].lower()


def test_transient_does_not_flap(monkeypatch: pytest.MonkeyPatch) -> None:
    sent = _capture(monkeypatch)
    prev: dict[str, Any] = {"status": auth_watchdog._OK, "last_alert": None}
    new = auth_watchdog._evaluate("Claude", auth_watchdog._TRANSIENT, "timeout", "fix", prev)
    assert new["status"] == auth_watchdog._OK
    assert sent == []
