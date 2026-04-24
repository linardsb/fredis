"""
GitHub Projects v2 Integration for Second Brain.

Projects v2 is GraphQL-only — there is no REST endpoint. This module is a
thin client over `https://api.github.com/graphql` using the shared
GITHUB_TOKEN. Separate from `github_api.py` (REST, for commits / PRs /
review requests) because the two surfaces share no code.

Used by the heartbeat's `breached_lane_gates` scan to detect Breached
kill-gate states on lane-summary project items (VTV, Cab, Email Hub,
UGOKI, GERBONI).

Usage:
    uv run python -m integrations.github_projects items
    uv run python -m integrations.github_projects fields
    uv run python -m integrations.github_projects breached
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import GITHUB_PROJECT_LANES_ID, GITHUB_TOKEN  # noqa: E402
from sanitize import sanitize_external_text, wrap_external_data  # noqa: E402
from shared import with_retry  # noqa: E402

GRAPHQL_URL = "https://api.github.com/graphql"


@dataclass
class ProjectItem:
    """A Projects v2 item (draft, linked issue, or linked PR)."""

    id: str
    title: str
    content_type: str = ""  # "DRAFT_ISSUE" | "ISSUE" | "PULL_REQUEST"
    field_values: dict[str, str] = field(default_factory=dict)
    url: str = ""
    updated_at: datetime | None = None


# ---------------------------------------------------------------------------
# Low-level
# ---------------------------------------------------------------------------


def _gql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST a GraphQL query to GitHub.

    GitHub returns 200 with `{"errors": [...]}` on query errors, so we must
    check the body. Auth header uses the shared GITHUB_TOKEN.
    """
    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN not set in .env — reuse the classic PAT that "
            "github_api.py uses."
        )

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "fredis-secondbrain",
    }
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    def do_post() -> requests.Response:
        return requests.post(GRAPHQL_URL, json=payload, headers=headers, timeout=30)

    resp: requests.Response = with_retry(do_post)
    if resp.status_code == 401:
        raise RuntimeError("GitHub returned 401 — rotate GITHUB_TOKEN")
    resp.raise_for_status()
    body = resp.json()
    if isinstance(body, dict) and body.get("errors"):
        msgs = "; ".join(str(e.get("message", e)) for e in body["errors"])
        raise RuntimeError(f"GitHub GraphQL error: {msgs}")
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        raise RuntimeError(f"GitHub returned unexpected body: {body!r}")
    return data


# ---------------------------------------------------------------------------
# Field value parsing
# ---------------------------------------------------------------------------


def _extract_field_value(node: dict[str, Any]) -> tuple[str, str] | None:
    """Pull (field_name, value) out of a Projects v2 fieldValue node.

    Projects v2 field values are a tagged union by __typename:
      - ProjectV2ItemFieldTextValue    → text
      - ProjectV2ItemFieldNumberValue  → number
      - ProjectV2ItemFieldDateValue    → date
      - ProjectV2ItemFieldSingleSelectValue → name (the select label)
      - ProjectV2ItemFieldIterationValue → title
    """
    field_obj = node.get("field") or {}
    name = field_obj.get("name") or ""
    if not name:
        return None
    typename = node.get("__typename") or ""
    if typename == "ProjectV2ItemFieldSingleSelectValue":
        value = node.get("name") or ""
    elif typename == "ProjectV2ItemFieldTextValue":
        value = node.get("text") or ""
    elif typename == "ProjectV2ItemFieldNumberValue":
        value = str(node.get("number") or "")
    elif typename == "ProjectV2ItemFieldDateValue":
        value = node.get("date") or ""
    elif typename == "ProjectV2ItemFieldIterationValue":
        value = node.get("title") or ""
    else:
        value = ""
    return name, value


def _parse_item(raw: dict[str, Any]) -> ProjectItem:
    content = raw.get("content") or {}
    content_type = content.get("__typename") or ""
    if content_type == "DraftIssue":
        title = content.get("title") or ""
        url = ""
    elif content_type in ("Issue", "PullRequest"):
        title = content.get("title") or ""
        url = content.get("url") or ""
    else:
        title = ""
        url = ""

    field_values: dict[str, str] = {}
    fv_nodes = (raw.get("fieldValues") or {}).get("nodes") or []
    for fv in fv_nodes:
        kv = _extract_field_value(fv)
        if kv:
            field_values[kv[0]] = kv[1]

    updated_at: datetime | None = None
    updated_raw = raw.get("updatedAt")
    if isinstance(updated_raw, str):
        try:
            updated_at = datetime.fromisoformat(updated_raw.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Title override — if content didn't yield one, use the Title field value
    if not title and "Title" in field_values:
        title = field_values["Title"]

    return ProjectItem(
        id=str(raw.get("id", "")),
        title=title,
        content_type=content_type.upper() if content_type else "",
        field_values=field_values,
        url=url,
        updated_at=updated_at,
    )


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------

_LIST_ITEMS_QUERY = """
query ($project_id: ID!, $after: String) {
  node(id: $project_id) {
    ... on ProjectV2 {
      items(first: 100, after: $after) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          updatedAt
          content {
            __typename
            ... on DraftIssue { title }
            ... on Issue { title url }
            ... on PullRequest { title url }
          }
          fieldValues(first: 50) {
            nodes {
              __typename
              ... on ProjectV2ItemFieldTextValue {
                text
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldNumberValue {
                number
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldDateValue {
                date
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldSingleSelectValue {
                name
                field { ... on ProjectV2FieldCommon { name } }
              }
              ... on ProjectV2ItemFieldIterationValue {
                title
                field { ... on ProjectV2FieldCommon { name } }
              }
            }
          }
        }
      }
    }
  }
}
"""


_FIELDS_QUERY = """
query ($project_id: ID!) {
  node(id: $project_id) {
    ... on ProjectV2 {
      fields(first: 50) {
        nodes {
          ... on ProjectV2Field { id name dataType }
          ... on ProjectV2SingleSelectField {
            id name dataType options { id name }
          }
          ... on ProjectV2IterationField { id name dataType }
        }
      }
    }
  }
}
"""


_UPDATE_FIELD_MUTATION = """
mutation ($project_id: ID!, $item_id: ID!, $field_id: ID!, $value: ProjectV2FieldValue!) {
  updateProjectV2ItemFieldValue(input: {
    projectId: $project_id,
    itemId: $item_id,
    fieldId: $field_id,
    value: $value
  }) { projectV2Item { id } }
}
"""


_ADD_DRAFT_MUTATION = """
mutation ($project_id: ID!, $title: String!, $body: String) {
  addProjectV2DraftIssue(input: {projectId: $project_id, title: $title, body: $body}) {
    projectItem { id }
  }
}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_project_items(project_node_id: str | None = None) -> list[ProjectItem]:
    """Return every item on the project (paginates to completion)."""
    pid = project_node_id or GITHUB_PROJECT_LANES_ID
    if not pid:
        return []
    items: list[ProjectItem] = []
    after: str | None = None
    while True:
        data = _gql(_LIST_ITEMS_QUERY, {"project_id": pid, "after": after})
        node = data.get("node") or {}
        items_block = (node.get("items") or {})
        for raw in items_block.get("nodes") or []:
            items.append(_parse_item(raw))
        page_info = items_block.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        after = page_info.get("endCursor")
    return items


def get_project_fields(project_node_id: str | None = None) -> list[dict[str, Any]]:
    """Return the project's field metadata (id, name, dataType, options?)."""
    pid = project_node_id or GITHUB_PROJECT_LANES_ID
    if not pid:
        return []
    data = _gql(_FIELDS_QUERY, {"project_id": pid})
    node = data.get("node") or {}
    fields = (node.get("fields") or {}).get("nodes") or []
    return [f for f in fields if isinstance(f, dict)]


def update_project_item_field(
    item_id: str,
    field_id: str,
    value: dict[str, Any],
    project_node_id: str | None = None,
) -> dict[str, Any]:
    """Set a field value on an item.

    `value` follows GitHub's `ProjectV2FieldValue` union:
      - text:          {"text": "..."}
      - number:        {"number": 1.0}
      - date:          {"date": "2026-05-01"}
      - single select: {"singleSelectOptionId": "<option id>"}
      - iteration:     {"iterationId": "<iteration id>"}
    """
    pid = project_node_id or GITHUB_PROJECT_LANES_ID
    data = _gql(
        _UPDATE_FIELD_MUTATION,
        {"project_id": pid, "item_id": item_id, "field_id": field_id, "value": value},
    )
    return (data.get("updateProjectV2ItemFieldValue") or {}).get("projectV2Item") or {}


def add_project_item(
    title: str,
    body: str | None = None,
    project_node_id: str | None = None,
) -> str:
    """Add a draft item to the project, return its node id."""
    pid = project_node_id or GITHUB_PROJECT_LANES_ID
    data = _gql(
        _ADD_DRAFT_MUTATION, {"project_id": pid, "title": title, "body": body or ""}
    )
    return (
        ((data.get("addProjectV2DraftIssue") or {}).get("projectItem") or {}).get("id")
        or ""
    )


# ---------------------------------------------------------------------------
# Scans — heartbeat-facing
# ---------------------------------------------------------------------------


def breached_lane_gates(project_node_id: str | None = None) -> list[ProjectItem]:
    """Lane-summary items whose `Kill-gate state` field == 'Breached'.

    A lane-summary item is one whose title contains '— Summary' (em-dash).
    Feature items live on the same board but have their own gate semantics
    and are intentionally excluded here.
    """
    hits: list[ProjectItem] = []
    for item in list_project_items(project_node_id):
        if "— Summary" not in item.title:
            continue
        state = (item.field_values.get("Kill-gate state") or "").strip()
        if state == "Breached":
            hits.append(item)
    return hits


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_items_for_context(items: list[ProjectItem]) -> str:
    """Format project items for Claude's context, wrapped in external_data."""
    if not items:
        return wrap_external_data("No GitHub project items found.", "github_projects")

    lines: list[str] = ["## GitHub Projects — Lanes & Features"]
    for item in items:
        title = sanitize_external_text(item.title, "github_projects")
        line = f"- **{title}** (ID: {item.id})"
        extras: list[str] = []
        for key in ("Lane", "Lane status", "Kill-gate state", "Phase"):
            val = item.field_values.get(key)
            if val:
                extras.append(
                    f"{key}: {sanitize_external_text(val, 'github_projects')}"
                )
        if extras:
            line += "\n  " + " | ".join(extras)
        lines.append(line)
    return wrap_external_data("\n".join(lines), "github_projects")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub Projects v2 integration")
    parser.add_argument("command", choices=["items", "fields", "breached"])
    args = parser.parse_args()

    if args.command == "items":
        print(format_items_for_context(list_project_items()))
    elif args.command == "fields":
        for f in get_project_fields():
            opts = f.get("options") or []
            opt_str = f" [{', '.join(o.get('name', '') for o in opts)}]" if opts else ""
            print(f"- {f.get('name')} ({f.get('dataType')}) id={f.get('id')}{opt_str}")
    elif args.command == "breached":
        print(format_items_for_context(breached_lane_gates()))
