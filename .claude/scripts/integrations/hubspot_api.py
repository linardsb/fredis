"""
HubSpot CRM Direct Integration for Second Brain.

Uses HubSpot's v3 REST API with a Private App Bearer token. Raw `requests`
for consistency with the other integration modules (no SDK dependency).

Usage:
    uv run python -m integrations.hubspot_api contacts --limit 10
    uv run python -m integrations.hubspot_api deals --stage Discovery
    uv run python -m integrations.hubspot_api pipelines
    uv run python -m integrations.hubspot_api properties contacts

Setup:
    1. HubSpot → Settings → Integrations → Private Apps → Create
    2. Scopes: crm.objects.(contacts|companies|deals|line_items).read+write,
       crm.schemas.*, crm.associations.read+write, crm.pipelines.deals.*
    3. Copy the token into HUBSPOT_API_TOKEN in .env

Auth gotcha:
    HubSpot uses `Authorization: Bearer <token>` — opposite of Monday.com.
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import HUBSPOT_API_TOKEN  # noqa: E402
from sanitize import sanitize_external_text, wrap_external_data  # noqa: E402
from shared import with_retry  # noqa: E402

HUBSPOT_API_BASE = "https://api.hubapi.com"
DEFAULT_LIMIT = 25

# Association typeIds (HubSpot v4 — fixed integers documented at
# https://developers.hubspot.com/docs/api/crm/associations/v4)
ASSOCIATION_CONTACT_TO_COMPANY = 1
ASSOCIATION_DEAL_TO_COMPANY = 5
ASSOCIATION_DEAL_TO_CONTACT = 3
# Ticket associations use a separate typeId block from the contact/company/deal
# cross-associations above.
ASSOCIATION_TICKET_TO_CONTACT = 16
ASSOCIATION_TICKET_TO_COMPANY = 26
ASSOCIATION_TICKET_TO_DEAL = 28
# Engagement → ticket associations (notes, tasks, etc. anchored on a ticket).
ASSOCIATION_NOTE_TO_TICKET = 228

FREDIS_REVIEW_PIPELINE_NAME = "Fredis Review"
# Urgency slug → HubSpot built-in priority value.
TICKET_URGENCY_TO_PRIORITY: dict[str, str] = {
    "today": "HIGH",
    "this_week": "MEDIUM",
    "whenever": "LOW",
}


@dataclass
class HubSpotObject:
    """Represents a HubSpot CRM record (contact / company / deal)."""

    id: str
    object_type: str  # "contacts" | "companies" | "deals"
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    archived: bool = False

    @property
    def name(self) -> str:
        """Best-effort human label for the record."""
        p = self.properties
        if self.object_type == "contacts":
            first = p.get("firstname", "") or ""
            last = p.get("lastname", "") or ""
            joined = f"{first} {last}".strip()
            return joined or p.get("email", "") or f"contact:{self.id}"
        if self.object_type == "companies":
            return p.get("name", "") or p.get("domain", "") or f"company:{self.id}"
        if self.object_type == "deals":
            return p.get("dealname", "") or f"deal:{self.id}"
        return f"{self.object_type}:{self.id}"


# ---------------------------------------------------------------------------
# Low-level request
# ---------------------------------------------------------------------------


def _request(
    method: str,
    path: str,
    json: Any = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call HubSpot API and return the decoded JSON body.

    Uses Bearer auth. Propagates 4xx/5xx via raise_for_status after surfacing
    a readable message. 401 maps to a rotation hint.
    """
    if not HUBSPOT_API_TOKEN:
        raise ValueError(
            "HUBSPOT_API_TOKEN not set in .env\n"
            "Create a Private App in HubSpot → Settings → Integrations → Private Apps."
        )

    url = f"{HUBSPOT_API_BASE}{path}"
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_TOKEN}",
        "Content-Type": "application/json",
    }

    def do_call() -> requests.Response:
        return requests.request(
            method=method.upper(),
            url=url,
            json=json,
            params=params,
            headers=headers,
            timeout=30,
        )

    resp: requests.Response = with_retry(do_call)
    if resp.status_code == 401:
        raise RuntimeError("HubSpot returned 401 — rotate HUBSPOT_API_TOKEN")
    if resp.status_code >= 400:
        # Try to surface the JSON error body for debuggability
        try:
            body = resp.json()
        except ValueError:
            body = {"message": resp.text}
        msg = body.get("message") or body.get("errors") or body
        raise RuntimeError(f"HubSpot {resp.status_code} on {method} {path}: {msg}")

    if resp.status_code == 204 or not resp.content:
        return {}
    body = resp.json()
    if not isinstance(body, dict):
        # Some endpoints return lists at top level (rare); wrap them.
        return {"results": body}
    return body


# ---------------------------------------------------------------------------
# Object parsing
# ---------------------------------------------------------------------------


def _parse_object(raw: dict[str, Any], object_type: str) -> HubSpotObject:
    """Parse a HubSpot API object payload into a HubSpotObject."""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    for key, tgt in (("createdAt", "created_at"), ("updatedAt", "updated_at")):
        raw_v = raw.get(key)
        if isinstance(raw_v, str):
            try:
                parsed = datetime.fromisoformat(raw_v.replace("Z", "+00:00"))
                if tgt == "created_at":
                    created_at = parsed
                else:
                    updated_at = parsed
            except ValueError:
                pass
    return HubSpotObject(
        id=str(raw.get("id", "")),
        object_type=object_type,
        properties=dict(raw.get("properties") or {}),
        created_at=created_at,
        updated_at=updated_at,
        archived=bool(raw.get("archived", False)),
    )


# ---------------------------------------------------------------------------
# CRM Objects — list / get / search / create / update / batch
# ---------------------------------------------------------------------------


def list_objects(
    object_type: str,
    limit: int = DEFAULT_LIMIT,
    properties: list[str] | None = None,
    after: str | None = None,
) -> list[HubSpotObject]:
    """GET /crm/v3/objects/{object_type} — page of records."""
    params: dict[str, Any] = {"limit": limit}
    if properties:
        params["properties"] = ",".join(properties)
    if after:
        params["after"] = after
    data = _request("GET", f"/crm/v3/objects/{object_type}", params=params)
    return [_parse_object(r, object_type) for r in data.get("results", [])]


def get_object(
    object_type: str,
    object_id: str,
    properties: list[str] | None = None,
) -> HubSpotObject | None:
    """GET a single record by ID."""
    params: dict[str, Any] = {}
    if properties:
        params["properties"] = ",".join(properties)
    try:
        data = _request(
            "GET", f"/crm/v3/objects/{object_type}/{object_id}", params=params
        )
    except RuntimeError as e:
        if "404" in str(e):
            return None
        raise
    return _parse_object(data, object_type)


def search_objects(
    object_type: str,
    filter_groups: list[dict[str, Any]],
    properties: list[str] | None = None,
    limit: int = 100,
    after: str | None = None,
    sorts: list[dict[str, str]] | None = None,
) -> list[HubSpotObject]:
    """POST /crm/v3/objects/{object_type}/search — CRM search API.

    filter_groups follows HubSpot's shape:
        [{"filters": [{"propertyName": ..., "operator": ..., "value": ...}, ...]}, ...]
    Multiple filters in one group = AND; multiple groups = OR.
    """
    body: dict[str, Any] = {
        "filterGroups": filter_groups,
        "limit": limit,
    }
    if properties:
        body["properties"] = properties
    if after:
        body["after"] = after
    if sorts:
        body["sorts"] = sorts
    data = _request("POST", f"/crm/v3/objects/{object_type}/search", json=body)
    return [_parse_object(r, object_type) for r in data.get("results", [])]


def create_object(object_type: str, properties: dict[str, Any]) -> HubSpotObject:
    """POST /crm/v3/objects/{object_type} — single record."""
    data = _request(
        "POST", f"/crm/v3/objects/{object_type}", json={"properties": properties}
    )
    return _parse_object(data, object_type)


def update_object(
    object_type: str, object_id: str, properties: dict[str, Any]
) -> HubSpotObject:
    """PATCH /crm/v3/objects/{object_type}/{id}."""
    data = _request(
        "PATCH",
        f"/crm/v3/objects/{object_type}/{object_id}",
        json={"properties": properties},
    )
    return _parse_object(data, object_type)


def batch_create(
    object_type: str, records: list[dict[str, Any]]
) -> list[HubSpotObject]:
    """POST /crm/v3/objects/{object_type}/batch/create.

    Each record is a `{"properties": {...}}` dict.
    """
    body = {"inputs": records}
    data = _request("POST", f"/crm/v3/objects/{object_type}/batch/create", json=body)
    return [_parse_object(r, object_type) for r in data.get("results", [])]


def batch_upsert(
    object_type: str,
    records: list[dict[str, Any]],
    id_property: str = "email",
) -> list[HubSpotObject]:
    """POST /crm/v3/objects/{object_type}/batch/upsert.

    Each record is `{"idProperty": "<key>", "id": "<value>", "properties": {...}}`
    — we fill in idProperty + id from the caller-supplied records. Callers pass
    `{"id": "<lookup value>", "properties": {...}}`.
    """
    inputs: list[dict[str, Any]] = []
    for r in records:
        inputs.append(
            {
                "idProperty": id_property,
                "id": r["id"],
                "properties": r["properties"],
            }
        )
    body = {"inputs": inputs}
    data = _request("POST", f"/crm/v3/objects/{object_type}/batch/upsert", json=body)
    return [_parse_object(r, object_type) for r in data.get("results", [])]


# ---------------------------------------------------------------------------
# Associations
# ---------------------------------------------------------------------------


def create_association(
    from_type: str,
    from_id: str,
    to_type: str,
    to_id: str,
    category: str = "HUBSPOT_DEFINED",
    type_id: int = ASSOCIATION_CONTACT_TO_COMPANY,
) -> dict[str, Any]:
    """PUT /crm/v4/objects/{fromType}/{fromId}/associations/{toType}/{toId}."""
    body: Any = [{"associationCategory": category, "associationTypeId": type_id}]
    return _request(
        "PUT",
        f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}",
        json=body,
    )


def list_associations(
    from_type: str, from_id: str, to_type: str
) -> list[dict[str, Any]]:
    """GET /crm/v4/objects/{from_type}/{from_id}/associations/{to_type}."""
    data = _request(
        "GET",
        f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}",
    )
    results = data.get("results", [])
    return [r for r in results if isinstance(r, dict)]


def delete_association(
    from_type: str, from_id: str, to_type: str, to_id: str
) -> dict[str, Any]:
    """DELETE /crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}.

    Removes all associations between the two records (every typeId).
    """
    return _request(
        "DELETE",
        f"/crm/v4/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}",
    )


# ---------------------------------------------------------------------------
# Archive (soft-delete — recoverable for 90 days via HubSpot UI)
# ---------------------------------------------------------------------------


def archive_object(object_type: str, object_id: str) -> dict[str, Any]:
    """DELETE /crm/v3/objects/{object_type}/{id} — archives, not hard-delete."""
    return _request("DELETE", f"/crm/v3/objects/{object_type}/{object_id}")


def batch_archive(object_type: str, ids: list[str]) -> dict[str, Any]:
    """POST /crm/v3/objects/{object_type}/batch/archive."""
    body = {"inputs": [{"id": i} for i in ids]}
    return _request(
        "POST", f"/crm/v3/objects/{object_type}/batch/archive", json=body
    )


# ---------------------------------------------------------------------------
# Schema — properties
# ---------------------------------------------------------------------------


def list_properties(object_type: str) -> list[dict[str, Any]]:
    """GET /crm/v3/properties/{object_type}."""
    data = _request("GET", f"/crm/v3/properties/{object_type}")
    results = data.get("results", [])
    return [r for r in results if isinstance(r, dict)]


def create_property(object_type: str, spec: dict[str, Any]) -> dict[str, Any]:
    """POST /crm/v3/properties/{object_type} — create a custom property.

    Spec shape (per HubSpot docs):
        {
          "name": "urgent_alert",
          "label": "Urgent alert",
          "type": "bool",             # string | number | date | datetime | enumeration | bool
          "fieldType": "booleancheckbox",
          "groupName": "contactinformation",
          "options": [{"label": "...", "value": "...", "displayOrder": 0}]  # for enum
        }
    """
    return _request("POST", f"/crm/v3/properties/{object_type}", json=spec)


def update_property(
    object_type: str, name: str, patch: dict[str, Any]
) -> dict[str, Any]:
    """PATCH /crm/v3/properties/{object_type}/{name} — mutate an existing property.

    HubSpot merges `options` by full replacement (not append), so the caller
    must pass the full desired option list. Other fields (label, description)
    patch in place. Used for enum evolution when new skill values are added
    after initial bootstrap.
    """
    return _request(
        "PATCH", f"/crm/v3/properties/{object_type}/{name}", json=patch
    )


# ---------------------------------------------------------------------------
# Pipelines
# ---------------------------------------------------------------------------


def list_pipelines(object_type: str = "deals") -> list[dict[str, Any]]:
    """GET /crm/v3/pipelines/{object_type}."""
    data = _request("GET", f"/crm/v3/pipelines/{object_type}")
    results = data.get("results", [])
    return [r for r in results if isinstance(r, dict)]


def create_pipeline(
    object_type: str, name: str, stages: list[dict[str, Any]]
) -> dict[str, Any]:
    """POST /crm/v3/pipelines/{object_type} — create a pipeline with stages.

    stages: [{"label": "Inbound", "metadata": {"probability": 0.1, "isClosed": false},
              "displayOrder": 0}, ...]
    """
    body = {"label": name, "displayOrder": 0, "stages": stages}
    return _request("POST", f"/crm/v3/pipelines/{object_type}", json=body)


def update_pipeline(
    object_type: str,
    pipeline_id: str,
    name: str,
    stages: list[dict[str, Any]],
) -> dict[str, Any]:
    """PUT /crm/v3/pipelines/{object_type}/{pipeline_id} — replace label + stages.

    Destructive: stages whose IDs are not in the new payload are deleted.
    Use when you want to repurpose an existing pipeline (e.g. on tiers that cap
    the pipeline count at 1).
    """
    body = {"label": name, "displayOrder": 0, "stages": stages}
    return _request(
        "PUT", f"/crm/v3/pipelines/{object_type}/{pipeline_id}", json=body
    )


# ---------------------------------------------------------------------------
# Engagements (tasks / notes)
# ---------------------------------------------------------------------------


def create_note(
    body: str,
    associations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /crm/v3/objects/notes — log a note and associate it with records.

    associations: [{"to": {"id": "<id>"}, "types": [{"associationCategory": "HUBSPOT_DEFINED",
                     "associationTypeId": <typeId>}]}]
    """
    payload: dict[str, Any] = {
        "properties": {
            "hs_note_body": body,
            "hs_timestamp": int(datetime.now(UTC).timestamp() * 1000),
        }
    }
    if associations:
        payload["associations"] = associations
    return _request("POST", "/crm/v3/objects/notes", json=payload)


def create_task(
    subject: str,
    body: str = "",
    due_date: date | None = None,
    associations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /crm/v3/objects/tasks — a followup task on a record."""
    props: dict[str, Any] = {
        "hs_task_subject": subject,
        "hs_task_body": body,
        "hs_task_status": "NOT_STARTED",
        "hs_timestamp": int(datetime.now(UTC).timestamp() * 1000),
    }
    if due_date is not None:
        props["hs_task_due_date"] = int(
            datetime.combine(due_date, datetime.min.time()).timestamp() * 1000
        )
    payload: dict[str, Any] = {"properties": props}
    if associations:
        payload["associations"] = associations
    return _request("POST", "/crm/v3/objects/tasks", json=payload)


def log_call(
    summary: str,
    duration_ms: int | None = None,
    disposition: str | None = None,
    direction: str = "OUTBOUND",
    body: str = "",
    associations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /crm/v3/objects/calls — record a past call.

    Logging only — does not place a call. `direction` is "INBOUND" or "OUTBOUND".
    """
    props: dict[str, Any] = {
        "hs_call_title": summary,
        "hs_call_body": body,
        "hs_call_direction": direction,
        "hs_timestamp": int(datetime.now(UTC).timestamp() * 1000),
    }
    if duration_ms is not None:
        props["hs_call_duration"] = duration_ms
    if disposition:
        props["hs_call_disposition"] = disposition
    payload: dict[str, Any] = {"properties": props}
    if associations:
        payload["associations"] = associations
    return _request("POST", "/crm/v3/objects/calls", json=payload)


def log_meeting(
    title: str,
    start: datetime,
    end: datetime,
    body: str = "",
    associations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /crm/v3/objects/meetings — record a past meeting."""
    props: dict[str, Any] = {
        "hs_meeting_title": title,
        "hs_meeting_body": body,
        "hs_meeting_start_time": int(start.timestamp() * 1000),
        "hs_meeting_end_time": int(end.timestamp() * 1000),
        "hs_timestamp": int(start.timestamp() * 1000),
    }
    payload: dict[str, Any] = {"properties": props}
    if associations:
        payload["associations"] = associations
    return _request("POST", "/crm/v3/objects/meetings", json=payload)


def log_email(
    subject: str,
    body: str,
    direction: str,
    sent_at: datetime,
    associations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """POST /crm/v3/objects/emails — record past correspondence.

    Logging only — does not send. `direction` is "INCOMING_EMAIL" or "EMAIL"
    (HubSpot's outbound value).
    """
    props: dict[str, Any] = {
        "hs_email_subject": subject,
        "hs_email_text": body,
        "hs_email_direction": direction,
        "hs_timestamp": int(sent_at.timestamp() * 1000),
    }
    payload: dict[str, Any] = {"properties": props}
    if associations:
        payload["associations"] = associations
    return _request("POST", "/crm/v3/objects/emails", json=payload)


def build_associations(
    pairs: list[tuple[str, str, int]],
) -> list[dict[str, Any]]:
    """Build the v4 associations payload for engagement creation.

    Each pair is (to_type, to_id, association_type_id). Only `to_id` and
    `type_id` end up in the wire shape — `to_type` is included so callers
    can keep their tuples self-documenting.
    """
    out: list[dict[str, Any]] = []
    for _to_type, to_id, type_id in pairs:
        out.append(
            {
                "to": {"id": to_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": type_id,
                    }
                ],
            }
        )
    return out


# ---------------------------------------------------------------------------
# Tickets — Fredis Review queue
# ---------------------------------------------------------------------------

# Open stages (labels) within the Fredis Review pipeline.
TICKET_OPEN_STAGE_LABELS = ("Drafted", "In review", "Needs send")
TICKET_CLOSED_STAGE_LABELS = ("Actioned", "Rejected")


def resolve_ticket_stage_id(
    label: str,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> str:
    """Look up a ticket stage ID by label within the named pipeline.

    HubSpot stores pipeline stages by numeric ID; labels are the user-facing
    names. Most callers pass a label (e.g. "Drafted") and let this helper
    resolve the ID.
    """
    for p in list_pipelines("tickets"):
        if p.get("label") != pipeline_name:
            continue
        for s in p.get("stages", []):
            if str(s.get("label", "")).lower() == label.lower():
                return str(s.get("id"))
        raise ValueError(
            f"ticket stage {label!r} not found in pipeline {pipeline_name!r}"
        )
    raise ValueError(f"ticket pipeline {pipeline_name!r} not found")


def _resolve_pipeline_and_stage(
    stage_label: str,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> tuple[str, str]:
    """Return (pipeline_id, stage_id) for a named pipeline + stage label."""
    for p in list_pipelines("tickets"):
        if p.get("label") != pipeline_name:
            continue
        pipeline_id = str(p.get("id"))
        for s in p.get("stages", []):
            if str(s.get("label", "")).lower() == stage_label.lower():
                return pipeline_id, str(s.get("id"))
        raise ValueError(
            f"ticket stage {stage_label!r} not found in pipeline {pipeline_name!r}"
        )
    raise ValueError(f"ticket pipeline {pipeline_name!r} not found")


def _build_ticket_associations(
    contact_ids: list[str] | None,
    company_ids: list[str] | None,
    deal_ids: list[str] | None,
) -> list[dict[str, Any]]:
    """Translate per-object ID lists into the v4 associations payload."""
    pairs: list[tuple[str, str, int]] = []
    for cid in contact_ids or []:
        pairs.append(("contacts", cid, ASSOCIATION_TICKET_TO_CONTACT))
    for cid in company_ids or []:
        pairs.append(("companies", cid, ASSOCIATION_TICKET_TO_COMPANY))
    for did in deal_ids or []:
        pairs.append(("deals", did, ASSOCIATION_TICKET_TO_DEAL))
    return build_associations(pairs)


def create_ticket(
    subject: str,
    content: str = "",
    *,
    lane: str | None = None,
    skill_source: str | None = None,
    urgency: str | None = None,
    draft_path: str | None = None,
    dedupe_key: str | None = None,
    heartbeat_run_id: str | None = None,
    slack_thread_url: str | None = None,
    stage_label: str = "Drafted",
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
) -> HubSpotObject:
    """Create a Fredis Review ticket.

    Subject and content use HubSpot's built-in properties; `lane`,
    `skill_source`, `urgency`, `draft_path`, `heartbeat_run_id`,
    `slack_thread_url`, and `dedupe_key` are the custom properties created
    by `bootstrap_hubspot_tickets.py`. `hs_ticket_priority` is auto-derived
    from urgency (today→HIGH, this_week→MEDIUM, whenever→LOW).
    """
    pipeline_id, stage_id = _resolve_pipeline_and_stage(stage_label, pipeline_name)
    # `source_type` omitted — HubSpot tickets restrict it to CHAT/EMAIL/FORM/PHONE,
    # none of which honestly describe an API-created review ticket. Leaving null.
    props: dict[str, Any] = {
        "subject": subject,
        "content": content,
        "hs_pipeline": pipeline_id,
        "hs_pipeline_stage": stage_id,
    }
    if lane:
        props["lane"] = lane
    if skill_source:
        props["skill_source"] = skill_source
    if urgency:
        props["urgency"] = urgency
        priority = TICKET_URGENCY_TO_PRIORITY.get(urgency)
        if priority:
            props["hs_ticket_priority"] = priority
    if draft_path:
        props["draft_path"] = draft_path
    if dedupe_key:
        props["dedupe_key"] = dedupe_key
    if heartbeat_run_id:
        props["heartbeat_run_id"] = heartbeat_run_id
    if slack_thread_url:
        props["slack_thread_url"] = slack_thread_url

    payload: dict[str, Any] = {"properties": props}
    associations = _build_ticket_associations(contact_ids, company_ids, deal_ids)
    if associations:
        payload["associations"] = associations
    data = _request("POST", "/crm/v3/objects/tickets", json=payload)
    return _parse_object(data, "tickets")


def get_ticket(
    ticket_id: str,
    properties: list[str] | None = None,
) -> HubSpotObject | None:
    """GET a ticket by ID. Returns None on 404."""
    return get_object("tickets", ticket_id, properties=properties)


def move_ticket(
    ticket_id: str,
    to_stage_label: str,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> HubSpotObject:
    """PATCH a ticket to a new stage. Resolves stage label → ID first."""
    _, stage_id = _resolve_pipeline_and_stage(to_stage_label, pipeline_name)
    return update_object("tickets", ticket_id, {"hs_pipeline_stage": stage_id})


def close_ticket(
    ticket_id: str,
    as_: str = "actioned",
    note: str | None = None,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> HubSpotObject:
    """Close a ticket as `actioned` or `rejected`. Optional note creates a
    NOTE engagement associated with the ticket — used for capturing the
    rejection reason on `close_ticket(..., as_="rejected", note="...")`.
    """
    mapping = {"actioned": "Actioned", "rejected": "Rejected"}
    try:
        label = mapping[as_.lower()]
    except KeyError as e:
        raise ValueError(
            f"close_ticket as_={as_!r}: must be 'actioned' or 'rejected'"
        ) from e

    result = move_ticket(ticket_id, label, pipeline_name=pipeline_name)
    if note:
        create_note(
            body=note,
            associations=build_associations(
                [("tickets", ticket_id, ASSOCIATION_NOTE_TO_TICKET)]
            ),
        )
    return result


def list_open_tickets(
    lane: str | None = None,
    urgency: str | None = None,
    limit: int = 100,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> list[HubSpotObject]:
    """Search for open Fredis Review tickets, optionally filtered by lane/urgency."""
    open_stage_ids = [
        resolve_ticket_stage_id(label, pipeline_name)
        for label in TICKET_OPEN_STAGE_LABELS
    ]
    filters: list[dict[str, Any]] = [
        {
            "propertyName": "hs_pipeline_stage",
            "operator": "IN",
            "values": open_stage_ids,
        }
    ]
    if lane:
        filters.append({"propertyName": "lane", "operator": "EQ", "value": lane})
    if urgency:
        filters.append(
            {"propertyName": "urgency", "operator": "EQ", "value": urgency}
        )
    return search_objects(
        "tickets",
        filter_groups=[{"filters": filters}],
        properties=[
            "subject",
            "content",
            "hs_pipeline_stage",
            "lane",
            "skill_source",
            "urgency",
            "draft_path",
            "hs_ticket_priority",
        ],
        limit=limit,
    )


def search_tickets_by_dedupe_key(
    dedupe_key: str,
    open_only: bool = True,
    pipeline_name: str = FREDIS_REVIEW_PIPELINE_NAME,
) -> list[HubSpotObject]:
    """Return tickets matching a dedupe_key. Used by heartbeat to skip
    creating duplicate tickets on repeat ticks.
    """
    filters: list[dict[str, Any]] = [
        {"propertyName": "dedupe_key", "operator": "EQ", "value": dedupe_key}
    ]
    if open_only:
        open_stage_ids = [
            resolve_ticket_stage_id(label, pipeline_name)
            for label in TICKET_OPEN_STAGE_LABELS
        ]
        filters.append(
            {
                "propertyName": "hs_pipeline_stage",
                "operator": "IN",
                "values": open_stage_ids,
            }
        )
    return search_objects(
        "tickets",
        filter_groups=[{"filters": filters}],
        properties=[
            "subject",
            "dedupe_key",
            "hs_pipeline_stage",
            "hs_lastmodifieddate",
        ],
        limit=50,
    )


# ---------------------------------------------------------------------------
# Habit-signal helpers — client-engagement detection for HABITS.md Ship pillar
# ---------------------------------------------------------------------------


# Cached (id, domain) pairs for active-client companies (engagement_type IN
# retainer / project). Cache avoids a per-heartbeat roundtrip — the client
# list changes rarely.
_CLIENT_COMPANIES_CACHE: tuple[float, list[tuple[str, str]]] | None = None
_CLIENT_COMPANIES_TTL_SECONDS = 600  # 10 minutes

# Engagement object types to sweep for the Ship signal.
_CLIENT_ENGAGEMENT_TYPES: tuple[str, ...] = ("notes", "calls", "meetings", "emails")


def _get_client_companies(
    ttl_seconds: int = _CLIENT_COMPANIES_TTL_SECONDS,
) -> list[tuple[str, str]]:
    """Return [(id, domain_lowercase), ...] for retainer + project companies.

    Result is cached in-process for ttl_seconds. On API error, serves the
    last good cache if available; otherwise returns [].
    """
    global _CLIENT_COMPANIES_CACHE

    now = time.monotonic()
    if _CLIENT_COMPANIES_CACHE is not None:
        ts, cached = _CLIENT_COMPANIES_CACHE
        if (now - ts) < ttl_seconds:
            return cached

    try:
        companies = search_objects(
            object_type="companies",
            filter_groups=[
                {
                    "filters": [
                        {
                            "propertyName": "engagement_type",
                            "operator": "IN",
                            "values": ["retainer", "project"],
                        }
                    ]
                }
            ],
            properties=["domain", "name", "engagement_type"],
            limit=100,
        )
    except Exception as e:
        print(f"[hubspot] error fetching client companies: {e}")
        if _CLIENT_COMPANIES_CACHE is not None:
            # Stale-but-last-known beats empty for habit signals.
            return _CLIENT_COMPANIES_CACHE[1]
        return []

    result: list[tuple[str, str]] = []
    for c in companies:
        domain = c.properties.get("domain") or ""
        if isinstance(domain, str):
            domain = domain.strip().lower()
        else:
            domain = ""
        result.append((c.id, domain))

    _CLIENT_COMPANIES_CACHE = (now, result)
    return result


def get_client_domains(ttl_seconds: int = _CLIENT_COMPANIES_TTL_SECONDS) -> set[str]:
    """Set of active-client company domains. Used by habit_signals.ship_tick
    to filter Gmail sent-messages to client-facing ones."""
    return {domain for _id, domain in _get_client_companies(ttl_seconds) if domain}


@dataclass
class ClientEngagement:
    """A recent engagement (note / call / meeting / email) logged against a
    client company. Surface this as a Ship pillar reason."""

    engagement_type: str  # "notes" | "calls" | "meetings" | "emails"
    engagement_id: str
    company_id: str
    created_at_ms: int


def recent_client_engagements(hours: int = 24) -> list[ClientEngagement]:
    """Engagements logged against retainer / project clients in the last N hours.

    Used by habit_signals.ship_tick per HABITS.md auto-detection (logged call
    / meeting / email / note on a client counts as "one concrete artifact
    forward").

    Approach: for each engagement object type, search by hs_createdate > cutoff,
    then fetch associated companies per result and keep matches against the
    client-company id set. Per-engagement association lookup keeps the query
    simple; cost stays low because engagement volume per 24h is small.
    """
    client_pairs = _get_client_companies()
    if not client_pairs:
        return []
    client_ids = {cid for cid, _domain in client_pairs}

    cutoff_ms = int((datetime.now(UTC) - timedelta(hours=hours)).timestamp() * 1000)

    hits: list[ClientEngagement] = []
    for engagement_type in _CLIENT_ENGAGEMENT_TYPES:
        try:
            results = search_objects(
                object_type=engagement_type,
                filter_groups=[
                    {
                        "filters": [
                            {
                                "propertyName": "hs_createdate",
                                "operator": "GTE",
                                "value": str(cutoff_ms),
                            }
                        ]
                    }
                ],
                properties=["hs_createdate"],
                limit=50,
            )
        except Exception as e:
            print(f"[hubspot] error fetching recent {engagement_type}: {e}")
            continue

        for eng in results:
            try:
                associations = list_associations(
                    from_type=engagement_type, from_id=eng.id, to_type="companies"
                )
            except Exception:
                continue

            for assoc in associations:
                assoc_id = str(assoc.get("toObjectId") or "")
                if assoc_id and assoc_id in client_ids:
                    created_raw = eng.properties.get("hs_createdate") or cutoff_ms
                    try:
                        created_ms = int(created_raw)
                    except (TypeError, ValueError):
                        created_ms = cutoff_ms
                    hits.append(
                        ClientEngagement(
                            engagement_type=engagement_type,
                            engagement_id=eng.id,
                            company_id=assoc_id,
                            created_at_ms=created_ms,
                        )
                    )
                    break  # one client association per engagement is enough

    # Most recent first so the Ship reason reflects the latest action.
    hits.sort(key=lambda h: h.created_at_ms, reverse=True)
    return hits


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_objects_for_context(objects: list[HubSpotObject]) -> str:
    """Format HubSpot records for Claude's context, wrapped in external_data."""
    if not objects:
        return wrap_external_data("No HubSpot records found.", "hubspot")

    by_type: dict[str, list[HubSpotObject]] = {}
    for obj in objects:
        by_type.setdefault(obj.object_type, []).append(obj)

    sections: list[str] = []
    for ot in sorted(by_type):
        sections.append(f"## {ot.title()}")
        for obj in by_type[ot]:
            name = sanitize_external_text(obj.name, "hubspot")
            line = f"- **{name}** (ID: {obj.id})"
            extras: list[str] = []
            p = obj.properties
            # Contacts
            if ot == "contacts":
                if p.get("email"):
                    extras.append(
                        f"email: {sanitize_external_text(str(p['email']), 'hubspot')}"
                    )
                if p.get("hs_lead_status"):
                    val = sanitize_external_text(str(p["hs_lead_status"]), "hubspot")
                    extras.append(f"lead status: {val}")
                if p.get("lifecyclestage"):
                    val = sanitize_external_text(str(p["lifecyclestage"]), "hubspot")
                    extras.append(f"lifecycle: {val}")
            # Deals
            elif ot == "deals":
                if p.get("dealstage"):
                    extras.append(
                        f"stage: {sanitize_external_text(str(p['dealstage']), 'hubspot')}"
                    )
                if p.get("amount"):
                    extras.append(f"amount: {p['amount']}")
                if p.get("closedate"):
                    extras.append(
                        f"close: {sanitize_external_text(str(p['closedate']), 'hubspot')}"
                    )
            # Companies
            elif ot == "companies":
                if p.get("domain"):
                    extras.append(
                        f"domain: {sanitize_external_text(str(p['domain']), 'hubspot')}"
                    )
                if p.get("engagement_type"):
                    val = sanitize_external_text(str(p["engagement_type"]), "hubspot")
                    extras.append(f"engagement: {val}")
            if extras:
                line += "\n  " + " | ".join(extras)
            sections.append(line)

    return wrap_external_data("\n".join(sections), "hubspot")


# ---------------------------------------------------------------------------
# CLI for manual testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HubSpot integration")
    parser.add_argument(
        "command",
        choices=["contacts", "companies", "deals", "pipelines", "properties"],
    )
    parser.add_argument("target", nargs="?", default=None, help="Object type for properties")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    args = parser.parse_args()

    if args.command in ("contacts", "companies", "deals"):
        props_by_type = {
            "contacts": ["email", "firstname", "lastname", "hs_lead_status", "lifecyclestage"],
            "companies": ["name", "domain", "engagement_type"],
            "deals": ["dealname", "dealstage", "amount", "closedate"],
        }
        rows = list_objects(args.command, limit=args.limit, properties=props_by_type[args.command])
        print(format_objects_for_context(rows))
    elif args.command == "pipelines":
        for p in list_pipelines("deals"):
            print(f"- {p.get('label')} (id: {p.get('id')})")
            for s in p.get("stages", []):
                print(f"    · {s.get('label')} — closed={s.get('metadata', {}).get('isClosed')}")
    elif args.command == "properties":
        target = args.target or "contacts"
        for prop in list_properties(target):
            label = prop.get("label")
            kind = f"{prop.get('type')}/{prop.get('fieldType')}"
            print(f"- {prop.get('name')} ({kind}): {label}")
