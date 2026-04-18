"""Tests for integrations.github_api."""

from __future__ import annotations

import importlib
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["GITHUB_TOKEN"] = "ghp_faketokenforunittests000000000000000000"
os.environ["GITHUB_USERNAME"] = "linardsb"

import config as _config  # noqa: E402  — must follow os.environ override
import integrations.github_api as github_api  # noqa: E402

importlib.reload(_config)
importlib.reload(github_api)


def _mock_response(
    json_body: Any,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.headers = headers or {}
    resp.raise_for_status = MagicMock()
    if status_code >= 400 and status_code != 403:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# =============================================================================
# Auth header
# =============================================================================


def test_headers_use_bearer_token() -> None:
    captured: dict[str, Any] = {}

    def fake_get(
        url: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> MagicMock:
        captured["headers"] = headers
        return _mock_response([])

    with patch("integrations.github_api.requests.get", side_effect=fake_get):
        github_api.recent_commits(hours=1)

    assert captured["headers"]["Authorization"].startswith("Bearer ")
    assert captured["headers"]["Accept"] == "application/vnd.github+json"
    assert captured["headers"]["X-GitHub-Api-Version"] == "2022-11-28"


# =============================================================================
# Event filtering
# =============================================================================


def _push_event(created_at: str, repo: str = "linardsb/test-repo") -> dict[str, Any]:
    return {
        "id": "123",
        "type": "PushEvent",
        "created_at": created_at,
        "repo": {"name": repo},
        "payload": {
            "ref": "refs/heads/main",
            "commits": [{"sha": "abc123", "message": "fix thing"}],
        },
    }


def _watch_event(created_at: str) -> dict[str, Any]:
    return {
        "id": "456",
        "type": "WatchEvent",
        "created_at": created_at,
        "repo": {"name": "anyone/else"},
        "payload": {},
    }


def test_recent_commits_filters_only_push_events() -> None:
    now = datetime.now(UTC)
    recent_iso = now.isoformat().replace("+00:00", "Z")
    events = [_push_event(recent_iso), _watch_event(recent_iso)]
    with patch("integrations.github_api.requests.get", return_value=_mock_response(events)):
        commits = github_api.recent_commits(hours=24)
    assert len(commits) == 1
    assert commits[0].type == "PushEvent"
    assert "linardsb/test-repo" in commits[0].repo


def test_recent_commits_respects_hours_cutoff() -> None:
    now = datetime.now(UTC)
    old_iso = (now - timedelta(hours=48)).isoformat().replace("+00:00", "Z")
    fresh_iso = now.isoformat().replace("+00:00", "Z")
    events = [_push_event(old_iso), _push_event(fresh_iso)]
    with patch("integrations.github_api.requests.get", return_value=_mock_response(events)):
        commits = github_api.recent_commits(hours=24)
    assert len(commits) == 1


def test_ship_signal_true_when_any_push_in_window() -> None:
    now = datetime.now(UTC)
    with patch(
        "integrations.github_api.requests.get",
        return_value=_mock_response([_push_event(now.isoformat().replace("+00:00", "Z"))]),
    ):
        assert github_api.ship_signal(hours=24) is True


def test_ship_signal_false_when_no_pushes() -> None:
    with patch("integrations.github_api.requests.get", return_value=_mock_response([])):
        assert github_api.ship_signal(hours=24) is False


# =============================================================================
# Error handling
# =============================================================================


def test_401_surfaces_rotation_message() -> None:
    with patch(
        "integrations.github_api.requests.get",
        return_value=_mock_response({"message": "Bad credentials"}, status_code=401),
    ):
        with pytest.raises(RuntimeError, match="rotate GITHUB_TOKEN"):
            github_api.recent_commits(hours=24)


def test_rate_limit_exhausted_surfaces_reset_time() -> None:
    resp = _mock_response(
        {"message": "API rate limit exceeded"},
        status_code=403,
        headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1712345678"},
    )
    with patch("integrations.github_api.requests.get", return_value=resp):
        with pytest.raises(RuntimeError, match="rate limit exhausted"):
            github_api.recent_commits(hours=24)


# =============================================================================
# Formatter
# =============================================================================


def test_format_events_wraps_in_external_data_tag() -> None:
    ev = github_api.GitHubEvent(
        id="1",
        type="PushEvent",
        repo="linardsb/VTV",
        created_at=datetime.now(UTC),
        summary="3 commit(s) → linardsb/VTV@main",
    )
    out = github_api.format_events_for_context([ev])
    assert '<external_data source="github"' in out
    assert "</external_data>" in out
    assert "linardsb/VTV" in out


def test_format_events_empty_still_wraps() -> None:
    out = github_api.format_events_for_context([])
    assert '<external_data source="github"' in out
    assert "No GitHub activity" in out
