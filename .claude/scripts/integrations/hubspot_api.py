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
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]

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
