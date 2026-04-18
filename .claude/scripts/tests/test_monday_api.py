"""Tests for integrations.monday_api.

All HTTP is mocked. The live Monday.com API is intentionally never reached;
the heartbeat's non-fatal try/except protects against outages in production.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure env has the token for these tests (value itself is fake).
import os  # noqa: E402

os.environ["MONDAY_API_TOKEN"] = "test-token-not-real"
os.environ["MONDAY_USER_ID"] = "999"
os.environ["MONDAY_BOARD_IDS"] = "Deals:100,Leads:200"

# Module must be re-imported after env tweak so config.py picks it up.
import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.monday_api as monday_api  # noqa: E402

importlib.reload(_config)
importlib.reload(monday_api)


def _mock_response(json_body: dict[str, Any], status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# =============================================================================
# Auth header shape
# =============================================================================


def test_auth_header_has_no_bearer_prefix() -> None:
    """Monday uses `Authorization: <token>` — never `Bearer <token>`."""
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        captured["headers"] = headers
        return _mock_response({"data": {"boards": []}})

    with patch("integrations.monday_api.requests.post", side_effect=fake_post):
        monday_api.list_boards()

    assert "Authorization" in captured["headers"]
    auth = captured["headers"]["Authorization"]
    assert not auth.lower().startswith("bearer "), f"Bearer prefix snuck in: {auth!r}"


# =============================================================================
# GraphQL error shape
# =============================================================================


def test_graphql_errors_block_surface_as_runtime_error() -> None:
    """A 200 response with `errors` in the body is a failure, not success."""
    with patch(
        "integrations.monday_api.requests.post",
        return_value=_mock_response({"errors": [{"message": "board not found"}]}),
    ):
        with pytest.raises(RuntimeError, match="board not found"):
            monday_api.list_boards()


def test_401_surfaces_rotation_message() -> None:
    with patch(
        "integrations.monday_api.requests.post",
        return_value=_mock_response({"error": "unauthorized"}, status_code=401),
    ):
        with pytest.raises(RuntimeError, match="rotate MONDAY_API_TOKEN"):
            monday_api.list_boards()


# =============================================================================
# Item parsing
# =============================================================================


def test_parse_item_extracts_date_column() -> None:
    raw = {
        "id": "42",
        "name": "Invoice #4501",
        "column_values": [
            {
                "id": "date4",
                "text": "2026-04-20",
                "value": None,
                "type": "date",
                "column": {"title": "Due"},
            }
        ],
    }
    item = monday_api._parse_item(raw, board_name="Deals")
    assert item.id == "42"
    assert item.name == "Invoice #4501"
    assert item.due_date is not None
    assert item.due_date.isoformat() == "2026-04-20"
    assert item.board_name == "Deals"


def test_parse_item_extracts_people_assignees() -> None:
    raw = {
        "id": "7",
        "name": "Call Atis",
        "column_values": [
            {
                "id": "people",
                "text": "Linards",
                "value": '{"personsAndTeams":[{"id":999,"kind":"person","name":"Linards"}]}',
                "type": "people",
                "column": {"title": "Owner"},
            }
        ],
    }
    item = monday_api._parse_item(raw)
    assert "Linards" in item.assignees


def test_parse_item_ignores_malformed_people_value() -> None:
    raw = {
        "id": "8",
        "name": "Broken",
        "column_values": [
            {
                "id": "people",
                "text": "",
                "value": "{this is not json",
                "type": "people",
                "column": {"title": "Owner"},
            }
        ],
    }
    item = monday_api._parse_item(raw)
    assert item.assignees == []


# =============================================================================
# Formatter
# =============================================================================


def test_format_items_wraps_in_external_data_tag() -> None:
    from datetime import date

    item = monday_api.MondayItem(
        id="1",
        name="Call Šlesers",
        board_id="100",
        board_name="Leads",
        assignees=["Linards"],
        due_date=date(2026, 5, 1),
        status="In progress",
    )
    out = monday_api.format_items_for_context([item])
    assert '<external_data source="monday"' in out
    assert "</external_data>" in out
    assert "Call Šlesers" in out
    assert "Leads" in out


def test_format_items_empty_list_still_wraps() -> None:
    out = monday_api.format_items_for_context([])
    assert '<external_data source="monday"' in out
    assert "No Monday.com items found" in out
