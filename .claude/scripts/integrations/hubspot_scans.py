"""Targeted HubSpot scans for the heartbeat.

Three read-only scans plus the shared formatter, ported 1:1 from
monday_scans.py but re-expressed against HubSpot's Search API.

  1. overdue_invoices()   — Deals in dealstage='Invoice' with closedate < today
                             (HubSpot Free has no first-class Invoice object).
  2. silent_contacts()    — Contacts with urgent_alert=true AND
                             notes_last_contacted older than N days.
                             (notes_last_contacted is auto-maintained by
                              HubSpot's Gmail integration.)
  3. stale_deals()        — Deals not in a closed stage AND
                             hs_lastmodifieddate older than N days.

The fourth historical scan (`breached_lane_gates`) moved to
`integrations/github_projects.py` — lanes now live there.

All scans are gated by HUBSPOT_SCANS_ENABLED at the heartbeat call site —
this module just runs the queries.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import HUBSPOT_SILENT_CONTACT_DAYS, HUBSPOT_STALE_DEAL_DAYS  # noqa: E402
from integrations.hubspot_api import (  # noqa: E402
    HubSpotObject,
    list_pipelines,
    search_objects,
)

# Invoice stage label must match the pipeline stage the bootstrap creates.
# The search uses the stage ID, not the label — HubSpot's pipeline stages
# have an `id` in the Stages response; we look it up by label at call time.
INVOICE_STAGE_LABEL = "Invoice"
CLOSED_STAGE_LABELS = {"Signed", "Post-delivery", "closedwon", "closedlost"}

CONTACT_PROPS = ["email", "firstname", "lastname", "urgent_alert", "notes_last_contacted"]
DEAL_PROPS = ["dealname", "dealstage", "amount", "closedate", "hs_lastmodifieddate"]


def _ms_now() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


def _ms_days_ago(days: int) -> int:
    return int((datetime.now(UTC) - timedelta(days=days)).timestamp() * 1000)


def _deal_stage_id(label: str) -> str | None:
    """Resolve a stage label to its HubSpot stage id via the pipelines API.

    We cache nothing — pipeline config is tiny and rarely queried. A missing
    pipeline or missing label returns None so the scan silently returns [].
    """
    try:
        pipelines = list_pipelines("deals")
    except RuntimeError:
        return None
    for p in pipelines:
        for stage in p.get("stages", []) or []:
            if stage.get("label") == label:
                return str(stage.get("id") or "")
    return None


def overdue_invoices(limit: int = 50) -> list[HubSpotObject]:
    """Deals at the Invoice stage whose closedate is before today."""
    stage_id = _deal_stage_id(INVOICE_STAGE_LABEL)
    if not stage_id:
        return []
    filter_groups = [
        {
            "filters": [
                {"propertyName": "dealstage", "operator": "EQ", "value": stage_id},
                {"propertyName": "closedate", "operator": "LT", "value": _ms_now()},
            ]
        }
    ]
    try:
        return search_objects("deals", filter_groups, properties=DEAL_PROPS, limit=limit)
    except RuntimeError:
        return []


def silent_contacts(limit: int = 50) -> list[HubSpotObject]:
    """Urgent-flagged contacts who haven't been contacted in N days."""
    cutoff = _ms_days_ago(HUBSPOT_SILENT_CONTACT_DAYS)
    # Two groups OR'd together:
    #   (urgent=true AND notes_last_contacted < cutoff)
    #   (urgent=true AND notes_last_contacted has no value)
    filter_groups: list[dict[str, Any]] = [
        {
            "filters": [
                {"propertyName": "urgent_alert", "operator": "EQ", "value": "true"},
                {
                    "propertyName": "notes_last_contacted",
                    "operator": "LT",
                    "value": cutoff,
                },
            ]
        },
        {
            "filters": [
                {"propertyName": "urgent_alert", "operator": "EQ", "value": "true"},
                {"propertyName": "notes_last_contacted", "operator": "NOT_HAS_PROPERTY"},
            ]
        },
    ]
    try:
        return search_objects(
            "contacts", filter_groups, properties=CONTACT_PROPS, limit=limit
        )
    except RuntimeError:
        return []


def stale_deals(limit: int = 50) -> list[HubSpotObject]:
    """Open deals not modified in N days."""
    cutoff = _ms_days_ago(HUBSPOT_STALE_DEAL_DAYS)
    # Resolve closed stage IDs so we can filter them out. If lookup fails, we
    # fall back to just the lastmodified filter — better to surface a few
    # closed deals than nothing.
    closed_ids = [
        sid
        for sid in (_deal_stage_id(lbl) for lbl in CLOSED_STAGE_LABELS)
        if sid
    ]
    filters: list[dict[str, Any]] = [
        {
            "propertyName": "hs_lastmodifieddate",
            "operator": "LT",
            "value": cutoff,
        }
    ]
    if closed_ids:
        filters.append(
            {"propertyName": "dealstage", "operator": "NOT_IN", "values": closed_ids}
        )
    filter_groups: list[dict[str, Any]] = [{"filters": filters}]
    try:
        return search_objects(
            "deals", filter_groups, properties=DEAL_PROPS, limit=limit
        )
    except RuntimeError:
        return []
