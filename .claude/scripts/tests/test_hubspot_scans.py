"""Tests for integrations.hubspot_scans.

Pure-filter tests — HubSpot API calls are mocked via search_objects +
list_pipelines patches. No live HTTP.
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

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.hubspot_api as hubspot_api  # noqa: E402
import integrations.hubspot_scans as scans  # noqa: E402

importlib.reload(_config)
importlib.reload(hubspot_api)
importlib.reload(scans)

PIPELINES_FIXTURE = [
    {
        "id": "pipe_1",
        "label": "Consultancy",
        "stages": [
            {"id": "stage_inbound", "label": "Inbound"},
            {"id": "stage_signed", "label": "Signed"},
            {"id": "stage_invoice", "label": "Invoice"},
            {"id": "stage_post", "label": "Post-delivery"},
        ],
    }
]


def _obj(id: str, object_type: str, **props: str) -> hubspot_api.HubSpotObject:
    return hubspot_api.HubSpotObject(
        id=id, object_type=object_type, properties=dict(props)
    )


# =============================================================================
# overdue_invoices
# =============================================================================


def test_overdue_invoices_resolves_invoice_stage_and_passes_filters() -> None:
    captured: dict[str, Any] = {}

    def fake_search(
        object_type: str,
        filter_groups: Any,
        properties: Any = None,
        limit: int = 100,
        after: Any = None,
        sorts: Any = None,
    ) -> list[hubspot_api.HubSpotObject]:
        captured["object_type"] = object_type
        captured["filter_groups"] = filter_groups
        return [_obj("1", "deals", dealname="Overdue SaaS")]

    with (
        patch.object(scans, "list_pipelines", return_value=PIPELINES_FIXTURE),
        patch.object(scans, "search_objects", side_effect=fake_search),
    ):
        hits = scans.overdue_invoices()
    assert len(hits) == 1
    fg = captured["filter_groups"]
    # Filter includes the resolved stage id, not the label
    filters = fg[0]["filters"]
    stage_filter = next(f for f in filters if f["propertyName"] == "dealstage")
    assert stage_filter["value"] == "stage_invoice"
    assert stage_filter["operator"] == "EQ"
    closedate_filter = next(f for f in filters if f["propertyName"] == "closedate")
    assert closedate_filter["operator"] == "LT"


def test_overdue_invoices_returns_empty_when_invoice_stage_missing() -> None:
    missing_stage_pipelines = [
        {
            "id": "pipe_1",
            "label": "Consultancy",
            "stages": [{"id": "stage_inbound", "label": "Inbound"}],
        }
    ]
    with patch.object(scans, "list_pipelines", return_value=missing_stage_pipelines):
        hits = scans.overdue_invoices()
    assert hits == []


def test_overdue_invoices_swallows_runtime_errors() -> None:
    with (
        patch.object(scans, "list_pipelines", return_value=PIPELINES_FIXTURE),
        patch.object(
            scans, "search_objects", side_effect=RuntimeError("HubSpot 500")
        ),
    ):
        hits = scans.overdue_invoices()
    assert hits == []


# =============================================================================
# silent_contacts
# =============================================================================


def test_silent_contacts_or_groups_cover_stale_and_never_contacted() -> None:
    captured: dict[str, Any] = {}

    def fake_search(
        object_type: str,
        filter_groups: Any,
        properties: Any = None,
        limit: int = 100,
        after: Any = None,
        sorts: Any = None,
    ) -> list[hubspot_api.HubSpotObject]:
        captured["object_type"] = object_type
        captured["filter_groups"] = filter_groups
        return [_obj("7", "contacts", email="ana@x.com", urgent_alert="true")]

    with patch.object(scans, "search_objects", side_effect=fake_search):
        scans.silent_contacts()

    assert captured["object_type"] == "contacts"
    groups = captured["filter_groups"]
    assert len(groups) == 2
    # First group: urgent + stale last-contacted
    g1_props = {f["propertyName"] for f in groups[0]["filters"]}
    assert g1_props == {"urgent_alert", "notes_last_contacted"}
    # Second group: urgent + no last-contacted property
    g2_ops = {f["operator"] for f in groups[1]["filters"]}
    assert "NOT_HAS_PROPERTY" in g2_ops


# =============================================================================
# stale_deals
# =============================================================================


def test_stale_deals_excludes_closed_stages_when_resolved() -> None:
    captured: dict[str, Any] = {}

    def fake_search(
        object_type: str,
        filter_groups: Any,
        properties: Any = None,
        limit: int = 100,
        after: Any = None,
        sorts: Any = None,
    ) -> list[hubspot_api.HubSpotObject]:
        captured["object_type"] = object_type
        captured["filter_groups"] = filter_groups
        return []

    with (
        patch.object(scans, "list_pipelines", return_value=PIPELINES_FIXTURE),
        patch.object(scans, "search_objects", side_effect=fake_search),
    ):
        scans.stale_deals()

    filters = captured["filter_groups"][0]["filters"]
    # hs_lastmodifieddate filter always present
    assert any(
        f["propertyName"] == "hs_lastmodifieddate" and f["operator"] == "LT"
        for f in filters
    )
    # Closed-stage exclusion only added when resolution succeeded
    exclusion = next(f for f in filters if f["propertyName"] == "dealstage")
    assert exclusion["operator"] == "NOT_IN"
    # Signed + Post-delivery resolve; closedwon/closedlost do NOT match the
    # pipelines fixture and are dropped silently.
    assert set(exclusion["values"]) == {"stage_signed", "stage_post"}


def test_stale_deals_survives_pipeline_lookup_failure() -> None:
    def fake_search(
        object_type: str,
        filter_groups: Any,
        properties: Any = None,
        limit: int = 100,
        after: Any = None,
        sorts: Any = None,
    ) -> list[hubspot_api.HubSpotObject]:
        return []

    with (
        patch.object(scans, "list_pipelines", side_effect=RuntimeError("timeout")),
        patch.object(scans, "search_objects", side_effect=fake_search),
    ):
        # Should not raise — just run with a looser filter.
        scans.stale_deals()
