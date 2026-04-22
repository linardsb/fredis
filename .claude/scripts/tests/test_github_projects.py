"""Tests for integrations.github_projects.

All HTTP is mocked — the live GitHub GraphQL API is never reached.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["GITHUB_TOKEN"] = "ghp_test_fake"
os.environ["GITHUB_PROJECT_LANES_ID"] = "PVT_test_project_id"

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.github_projects as gp  # noqa: E402

importlib.reload(_config)
importlib.reload(gp)


def _mock_response(body: dict[str, Any], status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


def _capture() -> tuple[dict[str, Any], Any]:
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
        return _mock_response(captured.get("_body") or {"data": {"node": {}}})

    return captured, fake_post


# =============================================================================
# Auth + endpoint shape
# =============================================================================


def test_auth_header_has_bearer_prefix() -> None:
    captured, fake = _capture()
    captured["_body"] = {
        "data": {"node": {"items": {"pageInfo": {"hasNextPage": False}, "nodes": []}}}
    }
    with patch("integrations.github_projects.requests.post", side_effect=fake):
        gp.list_project_items()
    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert captured["url"] == "https://api.github.com/graphql"


def test_401_surfaces_rotation_message() -> None:
    with patch(
        "integrations.github_projects.requests.post",
        return_value=_mock_response({}, status_code=401),
    ):
        with pytest.raises(RuntimeError, match="rotate GITHUB_TOKEN"):
            gp.list_project_items()


def test_graphql_errors_surface_as_runtime_error() -> None:
    with patch(
        "integrations.github_projects.requests.post",
        return_value=_mock_response({"errors": [{"message": "project not found"}]}),
    ):
        with pytest.raises(RuntimeError, match="project not found"):
            gp.list_project_items()


# =============================================================================
# Item parsing
# =============================================================================


def test_parse_item_extracts_draft_title_and_field_values() -> None:
    raw = {
        "id": "PVTI_abc",
        "updatedAt": "2026-04-22T10:00:00Z",
        "content": {"__typename": "DraftIssue", "title": "VTV — Summary"},
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "Building",
                    "field": {"name": "Lane status"},
                },
                {
                    "__typename": "ProjectV2ItemFieldSingleSelectValue",
                    "name": "Breached",
                    "field": {"name": "Kill-gate state"},
                },
                {
                    "__typename": "ProjectV2ItemFieldTextValue",
                    "text": "note",
                    "field": {"name": "Notes"},
                },
                {
                    "__typename": "ProjectV2ItemFieldNumberValue",
                    "number": 3.5,
                    "field": {"name": "RICE Impact"},
                },
                {
                    "__typename": "ProjectV2ItemFieldDateValue",
                    "date": "2026-06-01",
                    "field": {"name": "Ship target"},
                },
            ]
        },
    }
    item = gp._parse_item(raw)
    assert item.id == "PVTI_abc"
    assert item.title == "VTV — Summary"
    assert item.content_type == "DRAFTISSUE"
    assert item.field_values["Lane status"] == "Building"
    assert item.field_values["Kill-gate state"] == "Breached"
    assert item.field_values["Notes"] == "note"
    assert item.field_values["RICE Impact"] == "3.5"
    assert item.field_values["Ship target"] == "2026-06-01"
    assert item.updated_at is not None
    assert item.updated_at.year == 2026


def test_parse_item_pulls_url_from_issue() -> None:
    raw = {
        "id": "PVTI_x",
        "content": {
            "__typename": "Issue",
            "title": "Fix bug",
            "url": "https://github.com/foo/bar/issues/1",
        },
        "fieldValues": {"nodes": []},
    }
    item = gp._parse_item(raw)
    assert item.content_type == "ISSUE"
    assert item.url == "https://github.com/foo/bar/issues/1"


def test_parse_item_falls_back_to_title_field_when_content_empty() -> None:
    raw = {
        "id": "PVTI_y",
        "content": {"__typename": "DraftIssue", "title": ""},
        "fieldValues": {
            "nodes": [
                {
                    "__typename": "ProjectV2ItemFieldTextValue",
                    "text": "Fallback Title",
                    "field": {"name": "Title"},
                }
            ]
        },
    }
    item = gp._parse_item(raw)
    assert item.title == "Fallback Title"


# =============================================================================
# Pagination
# =============================================================================


def test_list_project_items_paginates() -> None:
    """The client should follow pageInfo.endCursor until hasNextPage=false."""
    call_count = {"n": 0}

    def paginated_post(
        url: str,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _mock_response(
                {
                    "data": {
                        "node": {
                            "items": {
                                "pageInfo": {"hasNextPage": True, "endCursor": "cur_1"},
                                "nodes": [
                                    {
                                        "id": "1",
                                        "content": {"__typename": "DraftIssue", "title": "A"},
                                        "fieldValues": {"nodes": []},
                                    }
                                ],
                            }
                        }
                    }
                }
            )
        return _mock_response(
            {
                "data": {
                    "node": {
                        "items": {
                            "pageInfo": {"hasNextPage": False},
                            "nodes": [
                                {
                                    "id": "2",
                                    "content": {"__typename": "DraftIssue", "title": "B"},
                                    "fieldValues": {"nodes": []},
                                }
                            ],
                        }
                    }
                }
            }
        )

    with patch("integrations.github_projects.requests.post", side_effect=paginated_post):
        items = gp.list_project_items()

    assert call_count["n"] == 2
    assert [i.id for i in items] == ["1", "2"]


def test_list_project_items_returns_empty_when_no_project_id() -> None:
    with patch.object(gp, "GITHUB_PROJECT_LANES_ID", ""):
        assert gp.list_project_items() == []


# =============================================================================
# Mutations — update + add
# =============================================================================


def test_update_project_item_field_posts_correct_variables() -> None:
    captured, fake = _capture()
    captured["_body"] = {
        "data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_1"}}}
    }
    with patch("integrations.github_projects.requests.post", side_effect=fake):
        gp.update_project_item_field(
            "PVTI_1", "PVTF_state", {"singleSelectOptionId": "opt_breached"}
        )
    variables = captured["payload"]["variables"]
    assert variables["item_id"] == "PVTI_1"
    assert variables["field_id"] == "PVTF_state"
    assert variables["value"] == {"singleSelectOptionId": "opt_breached"}


def test_add_project_item_returns_id() -> None:
    captured, fake = _capture()
    captured["_body"] = {
        "data": {"addProjectV2DraftIssue": {"projectItem": {"id": "PVTI_new"}}}
    }
    with patch("integrations.github_projects.requests.post", side_effect=fake):
        new_id = gp.add_project_item("VTV — Summary", body="Lane rollup row")
    assert new_id == "PVTI_new"


# =============================================================================
# breached_lane_gates — pure filter
# =============================================================================


def test_breached_lane_gates_requires_summary_and_breached_state() -> None:
    items = [
        gp.ProjectItem(
            id="1",
            title="VTV — Summary",
            field_values={"Kill-gate state": "Breached"},
        ),
        gp.ProjectItem(
            id="2",
            title="VTV — Summary",
            field_values={"Kill-gate state": "Green"},
        ),
        gp.ProjectItem(
            id="3",
            title="Some feature (no summary)",
            field_values={"Kill-gate state": "Breached"},
        ),
        gp.ProjectItem(
            id="4",
            title="Cab — Summary",
            field_values={"Kill-gate state": "Breached"},
        ),
    ]
    with patch.object(gp, "list_project_items", return_value=items):
        hits = gp.breached_lane_gates()
    assert {h.id for h in hits} == {"1", "4"}


# =============================================================================
# Formatter
# =============================================================================


def test_format_items_wraps_and_shows_fields() -> None:
    item = gp.ProjectItem(
        id="1",
        title="VTV — Summary",
        field_values={
            "Lane": "VTV",
            "Lane status": "Building",
            "Kill-gate state": "Green",
        },
    )
    out = gp.format_items_for_context([item])
    assert '<external_data source="github_projects"' in out
    assert "VTV — Summary" in out
    assert "Lane: VTV" in out
    assert "Kill-gate state: Green" in out


def test_format_items_empty_list_still_wraps() -> None:
    out = gp.format_items_for_context([])
    assert '<external_data source="github_projects"' in out
    assert "No GitHub project items found" in out
