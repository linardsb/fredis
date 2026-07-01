"""Tests for the Archon HTTP client (integrations.archon_api).

All HTTP is mocked — the live engine is never reached. Pins the wire contract
verified against the engine's OpenAPI routes: idle-conversation creation (no
`message`), the {conversationId, message} run body, and approve/reject bodies.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import requests

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import integrations.archon_api as api  # noqa: E402
from integrations.archon_api import ArchonError, ArchonUnreachableError  # noqa: E402


def _resp(status: int = 200, body: Any = None, text: str = "") -> MagicMock:
    r = MagicMock()
    r.status_code = status
    if body is not None:
        r.content = b'{"x":1}'
        r.json.return_value = body
    else:
        r.content = text.encode() if text else b""
        r.json.side_effect = ValueError("no json")
        r.text = text
    return r


def test_list_workflows_gets_endpoint() -> None:
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body=[{"name": "archon-fix-github-issue"}])
        out = api.list_workflows()
    method, url = m.call_args.args
    assert method == "GET"
    assert url.endswith("/api/workflows")
    assert out == [{"name": "archon-fix-github-issue"}]


def test_create_conversation_is_idle() -> None:
    """Must omit `message` so the conversation stays idle for a workflow fire."""
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body={"conversationId": "orch-1", "id": "web-9"})
        api.create_conversation("cb-1")
    method, url = m.call_args.args
    assert method == "POST"
    assert url.endswith("/api/conversations")
    assert m.call_args.kwargs["json"] == {"codebaseId": "cb-1"}
    assert "message" not in m.call_args.kwargs["json"]


def test_run_workflow_body() -> None:
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body={"accepted": True, "status": "started"})
        out = api.run_workflow("archon-assist", "orch-1", "the approved PRD body")
    method, url = m.call_args.args
    assert method == "POST"
    assert url.endswith("/api/workflows/archon-assist/run")
    assert m.call_args.kwargs["json"] == {
        "conversationId": "orch-1",
        "message": "the approved PRD body",
    }
    assert out["status"] == "started"


def test_register_codebase_body() -> None:
    """POST /api/codebases sends only the local {path}; engine derives the name."""
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body={"id": "cb-9", "name": "linardsb/merkle-email-hub"})
        out = api.register_codebase("/Users/x/Desktop/merkle-email-hub")
    method, url = m.call_args.args
    assert method == "POST"
    assert url.endswith("/api/codebases")
    assert m.call_args.kwargs["json"] == {"path": "/Users/x/Desktop/merkle-email-hub"}
    assert out["id"] == "cb-9"


def test_approve_and_reject_bodies() -> None:
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body={"success": True, "message": "ok"})
        api.approve_run("run-1", "lgtm")
        assert m.call_args.args[1].endswith("/api/workflows/runs/run-1/approve")
        assert m.call_args.kwargs["json"] == {"comment": "lgtm"}

        api.reject_run("run-1", "not yet")
        assert m.call_args.args[1].endswith("/api/workflows/runs/run-1/reject")
        assert m.call_args.kwargs["json"] == {"reason": "not yet"}

        api.approve_run("run-1")  # no comment -> empty body
        assert m.call_args.kwargs["json"] == {}


def test_latest_run_correlates_on_conversation_id() -> None:
    rows = [
        {"id": "run-a", "conversation_id": "other"},
        {"id": "run-b", "conversation_id": "orch-1"},
    ]
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(body=rows)
        run = api.latest_run_for_conversation("orch-1")
    assert run is not None
    assert run["id"] == "run-b"


def test_unreachable_raises_clean_error() -> None:
    with patch("integrations.archon_api.requests.request") as m:
        m.side_effect = requests.exceptions.ConnectionError("refused")
        with pytest.raises(ArchonUnreachableError, match="unreachable"):
            api.list_workflows()


def test_non_2xx_raises_archon_error() -> None:
    with patch("integrations.archon_api.requests.request") as m:
        m.return_value = _resp(status=500, text="boom")
        with pytest.raises(ArchonError, match="HTTP 500"):
            api.list_workflows()
