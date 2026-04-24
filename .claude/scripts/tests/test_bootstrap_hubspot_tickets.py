"""Tests for bootstrap_hubspot_tickets.ensure_properties — specifically the
enum option diff-and-patch path.

Covers three cases:
  1. Addition-only — desired has values current lacks.
  2. Removal-only — current has values desired lacks (Phase-12+ case:
     skill retired from SKILL_SOURCE_VALUES).
  3. No-change — desired == current, patch suppressed.

All HubSpot API calls mocked. No network.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["HUBSPOT_API_TOKEN"] = "pat-test-fake"

import bootstrap_hubspot_tickets as bootstrap  # noqa: E402


def _opt(value: str, order: int = 0) -> dict[str, Any]:
    return {"label": value, "value": value, "displayOrder": order}


def _spec(name: str, values: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "label": name,
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "ticketinformation",
        "options": [_opt(v, i) for i, v in enumerate(values)],
    }


def test_ensure_properties_patches_when_options_added(capsys: Any) -> None:
    existing = [{"name": "skill_source", "options": [_opt("heartbeat")]}]
    spec = _spec("skill_source", ["heartbeat", "draft-reply", "client-log"])
    with (
        patch("integrations.hubspot_api.list_properties",
              return_value=existing),
        patch("integrations.hubspot_api.update_property") as update,
    ):
        bootstrap.ensure_properties("tickets", [spec], dry_run=False)
    update.assert_called_once()
    args, kwargs = update.call_args
    assert args[0] == "tickets"
    assert args[1] == "skill_source"
    patched_values = {o["value"] for o in args[2]["options"]}
    assert patched_values == {"heartbeat", "draft-reply", "client-log"}
    out = capsys.readouterr().out
    assert "synced tickets property 'skill_source'" in out
    assert "+2 / -0" in out
    assert "client-log" in out
    assert "draft-reply" in out


def test_ensure_properties_patches_when_options_removed(capsys: Any) -> None:
    existing = [{
        "name": "skill_source",
        "options": [_opt("heartbeat"), _opt("legacy-skill"), _opt("dead-skill")],
    }]
    spec = _spec("skill_source", ["heartbeat"])
    with (
        patch("integrations.hubspot_api.list_properties",
              return_value=existing),
        patch("integrations.hubspot_api.update_property") as update,
    ):
        bootstrap.ensure_properties("tickets", [spec], dry_run=False)
    update.assert_called_once()
    args, _ = update.call_args
    patched_values = {o["value"] for o in args[2]["options"]}
    assert patched_values == {"heartbeat"}
    out = capsys.readouterr().out
    assert "synced tickets property 'skill_source'" in out
    assert "+0 / -2" in out
    assert "legacy-skill" in out
    assert "dead-skill" in out


def test_ensure_properties_skips_when_options_unchanged(capsys: Any) -> None:
    existing = [{
        "name": "skill_source",
        "options": [_opt("heartbeat"), _opt("draft-reply")],
    }]
    spec = _spec("skill_source", ["heartbeat", "draft-reply"])
    with (
        patch("integrations.hubspot_api.list_properties",
              return_value=existing),
        patch("integrations.hubspot_api.update_property") as update,
    ):
        bootstrap.ensure_properties("tickets", [spec], dry_run=False)
    update.assert_not_called()
    out = capsys.readouterr().out
    assert "already exists" in out
    assert "synced" not in out


def test_ensure_properties_dry_run_logs_without_patching(capsys: Any) -> None:
    existing = [{"name": "skill_source", "options": [_opt("heartbeat")]}]
    spec = _spec("skill_source", ["heartbeat", "new-skill"])
    with (
        patch("integrations.hubspot_api.list_properties",
              return_value=existing),
        patch("integrations.hubspot_api.update_property") as update,
    ):
        bootstrap.ensure_properties("tickets", [spec], dry_run=True)
    update.assert_not_called()
    out = capsys.readouterr().out
    assert "would sync" in out
    assert "+1 / -0" in out
    assert "new-skill" in out
