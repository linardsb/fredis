"""Loop-failure alerting — aborted/crashed memory loops page Slack."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import notifications  # noqa: E402


def test_alert_sends_titled_slack_message(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(
        notifications,
        "send_slack_notification",
        lambda title, message, channel=None: sent.append((title, message)),
    )
    notifications.send_loop_failure_alert(
        "reflection", "Aborted on injection pattern(s): dan_jailbreak"
    )
    assert sent
    title, message = sent[0]
    assert "reflection" in title
    assert "Aborted" in message


def test_alert_never_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(*a: object, **kw: object) -> None:
        raise RuntimeError("slack down")

    monkeypatch.setattr(notifications, "send_slack_notification", _boom)
    # Must not raise — alerting can never compound the original failure.
    notifications.send_loop_failure_alert("synthesis", "reason")
