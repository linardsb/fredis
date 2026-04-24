"""Tests for heartbeat._surface_slack_failures — aggregation of dispatcher
Slack failures into stderr + the daily log.

No live dispatch; no live daily log.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("HUBSPOT_API_TOKEN", "pat-test-fake")

import heartbeat  # noqa: E402


def test_surface_slack_failures_no_op_when_list_empty(capsys: Any) -> None:
    with patch("shared.append_to_daily_log") as append:
        heartbeat._surface_slack_failures([])
    append.assert_not_called()
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_surface_slack_failures_logs_and_prints(capsys: Any) -> None:
    failures = [
        "ticket 123: connection refused",
        "ticket 456: channel not_found",
    ]
    with patch("shared.append_to_daily_log") as append:
        heartbeat._surface_slack_failures(failures)
    append.assert_called_once()
    kwargs = append.call_args.kwargs
    assert kwargs["section_name"] == "Dispatcher Warnings"
    assert kwargs["parent_section"] == "Heartbeats"
    assert kwargs["source"] == "ticket_dispatcher"
    body = append.call_args.args[0]
    assert "Slack post failed" in body
    assert "ticket 123: connection refused" in body
    assert "ticket 456: channel not_found" in body

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "ticket 123" in captured.err
    assert "ticket 456" in captured.err
