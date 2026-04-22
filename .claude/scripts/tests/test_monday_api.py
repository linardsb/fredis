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


# =============================================================================
# Mutation helpers (write path — bootstrap scripts)
# =============================================================================


def _capture_post(
    response_body: dict[str, Any],
) -> tuple[dict[str, Any], Any]:
    """Return a (captured, side_effect) pair for patching requests.post.

    captured["payload"] holds the last GraphQL payload (query + variables).
    captured["headers"] holds the request headers.
    """
    captured: dict[str, Any] = {}

    def fake_post(
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        captured["url"] = url
        captured["payload"] = json
        captured["headers"] = headers
        return _mock_response(response_body)

    return captured, fake_post


def test_create_board_returns_id_and_sends_name() -> None:
    captured, fake = _capture_post({"data": {"create_board": {"id": "9999"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        board_id = monday_api.create_board("Finances", board_kind="public")
    assert board_id == "9999"
    variables = captured["payload"]["variables"]
    assert variables["name"] == "Finances"
    assert variables["kind"] == "public"


def test_create_board_rejects_bad_kind() -> None:
    with pytest.raises(ValueError, match="board_kind"):
        monday_api.create_board("x", board_kind="weird")


def test_rename_board_sends_plain_string() -> None:
    """update_board's new_value for `name` is a plain String (not JSON-encoded)."""
    captured, fake = _capture_post({"data": {"update_board": '{"success":true}'}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        ok = monday_api.rename_board("100", "Lanes & Features")
    assert ok is True
    variables = captured["payload"]["variables"]
    assert variables["val"] == "Lanes & Features"  # plain string, no JSON quotes


def test_create_column_serializes_status_defaults() -> None:
    """Status columns need a JSON-string `defaults` payload with labels."""
    captured, fake = _capture_post({"data": {"create_column": {"id": "status_x"}}})
    labels = {
        "labels": {
            "0": "Inbound",
            "1": "Discovery",
            "2": "Proposal",
        }
    }
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        col_id = monday_api.create_column("100", "Stage", "status", defaults=labels)
    assert col_id == "status_x"
    variables = captured["payload"]["variables"]
    # defaults must arrive as a JSON string (Monday's JSON scalar)
    assert isinstance(variables["defaults"], str)
    assert "Inbound" in variables["defaults"]
    assert variables["type"] == "status"


def test_create_column_passes_null_defaults_when_missing() -> None:
    captured, fake = _capture_post({"data": {"create_column": {"id": "t1"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        monday_api.create_column("100", "Notes", "long_text")
    variables = captured["payload"]["variables"]
    assert variables["defaults"] is None


def test_create_group_returns_id() -> None:
    captured, fake = _capture_post({"data": {"create_group": {"id": "group_vtv"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        gid = monday_api.create_group("100", "VTV")
    assert gid == "group_vtv"
    assert captured["payload"]["variables"]["name"] == "VTV"


def test_create_item_serializes_column_values() -> None:
    captured, fake = _capture_post({"data": {"create_item": {"id": "77"}}})
    col_vals = {"status": {"label": "New"}, "date4": {"date": "2026-04-22"}}
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        item_id = monday_api.create_item(
            "100", "Call Atis", group_id="topics", column_values=col_vals
        )
    assert item_id == "77"
    variables = captured["payload"]["variables"]
    assert variables["name"] == "Call Atis"
    assert variables["group_id"] == "topics"
    assert isinstance(variables["col_vals"], str)
    assert "Call Atis" not in variables["col_vals"]  # name is not in col values
    assert "2026-04-22" in variables["col_vals"]


def test_create_item_without_group_or_columns() -> None:
    captured, fake = _capture_post({"data": {"create_item": {"id": "78"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        monday_api.create_item("100", "Bare item")
    variables = captured["payload"]["variables"]
    assert variables["group_id"] is None
    assert variables["col_vals"] is None


def test_update_column_value_serializes_value() -> None:
    captured, fake = _capture_post({"data": {"change_column_value": {"id": "77"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        ok = monday_api.update_column_value("100", "77", "date4", {"date": "2026-04-22"})
    assert ok is True
    variables = captured["payload"]["variables"]
    assert variables["col_id"] == "date4"
    assert variables["val"] == '{"date": "2026-04-22"}'


def test_add_update_returns_id() -> None:
    captured, fake = _capture_post({"data": {"create_update": {"id": "upd_5"}}})
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        uid = monday_api.add_update("77", "Following up on this")
    assert uid == "upd_5"
    assert captured["payload"]["variables"]["body"] == "Following up on this"


def test_get_board_columns_shapes_response() -> None:
    _, fake = _capture_post(
        {
            "data": {
                "boards": [
                    {
                        "columns": [
                            {
                                "id": "status",
                                "title": "Status",
                                "type": "status",
                                "settings_str": "{}",
                            },
                            {
                                "id": "date4",
                                "title": "Due",
                                "type": "date",
                                "settings_str": "",
                            },
                        ]
                    }
                ]
            }
        }
    )
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        cols = monday_api.get_board_columns("100")
    assert len(cols) == 2
    titles = [c["title"] for c in cols]
    assert "Status" in titles and "Due" in titles


def test_get_board_groups_shapes_response() -> None:
    _, fake = _capture_post(
        {
            "data": {
                "boards": [
                    {
                        "groups": [
                            {"id": "topics", "title": "VTV"},
                            {"id": "topics2", "title": "Cab"},
                        ]
                    }
                ]
            }
        }
    )
    with patch("integrations.monday_api.requests.post", side_effect=fake):
        groups = monday_api.get_board_groups("100")
    assert [g["title"] for g in groups] == ["VTV", "Cab"]


def test_graphql_error_surfaces_on_mutation() -> None:
    """Mutation failures still surface via the shared _gql error handler."""
    with patch(
        "integrations.monday_api.requests.post",
        return_value=_mock_response({"errors": [{"message": "duplicate board name"}]}),
    ):
        with pytest.raises(RuntimeError, match="duplicate board name"):
            monday_api.create_board("Finances")
