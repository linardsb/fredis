"""
Monday.com Direct Integration for Second Brain.

Uses Monday.com API v2 (GraphQL over HTTPS). Raw `requests` rather than an SDK
for consistency with asana_api.py's move_task() pattern and to avoid an extra
dependency.

Usage:
    uv run python -m integrations.monday_api boards
    uv run python -m integrations.monday_api board <board_id> --limit 25
    uv run python -m integrations.monday_api my-items --limit 25
    uv run python -m integrations.monday_api overdue
    uv run python -m integrations.monday_api search "invoice"

Setup:
    1. Monday.com → avatar → Admin → API → generate v2 token
    2. Find your user ID: query { me { id } } in the Monday API playground
    3. Find each board ID from its URL (/boards/<id>)
    4. Add MONDAY_API_TOKEN, MONDAY_USER_ID, MONDAY_BOARD_IDS to .env

Auth gotcha:
    Monday.com uses `Authorization: <token>` WITHOUT the `Bearer ` prefix.
    This is a common mistake when mirroring other APIs.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

import requests  # type: ignore[import-untyped]

# Add parent dir for config imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (  # noqa: E402
    MONDAY_API_TOKEN,
    MONDAY_BOARDS,
    MONDAY_USER_ID,
)
from sanitize import sanitize_external_text, wrap_external_data  # noqa: E402
from shared import with_retry  # noqa: E402

MONDAY_API_URL = "https://api.monday.com/v2"
# items_page caps at 500; we default much lower to protect the complexity budget.
DEFAULT_ITEMS_LIMIT = 25


@dataclass
class MondayItem:
    """Represents a single Monday.com item (board row)."""

    id: str
    name: str
    board_id: str
    board_name: str = ""
    assignees: list[str] = field(default_factory=list)
    due_date: date | None = None
    status: str | None = None
    column_values: dict[str, str] = field(default_factory=dict)
    updated_at: datetime | None = None
    url: str = ""


# ---------------------------------------------------------------------------
# Low-level GraphQL
# ---------------------------------------------------------------------------


def _gql(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """POST a GraphQL query to Monday.com and return the `data` block.

    Monday returns 200 with `{"errors": [...]}` on query errors, so we check
    the body rather than relying on HTTP status. Token is sent WITHOUT a
    Bearer prefix — Monday's auth scheme expects the raw token.
    """
    if not MONDAY_API_TOKEN:
        raise ValueError(
            "MONDAY_API_TOKEN not set in .env\n"
            "Get one from Monday.com → avatar menu → Admin → API."
        )

    headers = {
        "Authorization": MONDAY_API_TOKEN,
        "Content-Type": "application/json",
        "API-Version": "2024-01",
    }
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    def do_post() -> requests.Response:
        return requests.post(MONDAY_API_URL, json=payload, headers=headers, timeout=30)

    resp: requests.Response = with_retry(do_post)
    if resp.status_code == 401:
        raise RuntimeError("Monday.com returned 401 — rotate MONDAY_API_TOKEN")
    resp.raise_for_status()

    body = resp.json()
    if isinstance(body, dict) and body.get("errors"):
        msgs = "; ".join(str(e.get("message", e)) for e in body["errors"])
        raise RuntimeError(f"Monday GraphQL error: {msgs}")
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        raise RuntimeError(f"Monday returned unexpected body: {body!r}")
    return data


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _parse_item(raw: dict[str, Any], board_name: str = "") -> MondayItem:
    """Parse a GraphQL item node into a MondayItem."""
    import json

    assignees: list[str] = []
    due_date: date | None = None
    status: str | None = None
    column_values: dict[str, str] = {}

    for col in raw.get("column_values", []) or []:
        title = ((col.get("column") or {}).get("title") or col.get("id") or "").strip()
        text = (col.get("text") or "").strip()
        value = col.get("value")

        if text:
            column_values[title] = text

        col_type = (col.get("type") or col.get("column", {}).get("type") or "").lower()
        # People column → assignees
        if col_type in ("people", "multiple-person") and value:
            try:
                parsed = json.loads(value)
                for entry in parsed.get("personsAndTeams", []) or []:
                    name = entry.get("name") or entry.get("id")
                    if name:
                        assignees.append(str(name))
            except (ValueError, TypeError):
                pass
        # Date column
        elif col_type == "date" and text:
            try:
                due_date = datetime.strptime(text.split()[0], "%Y-%m-%d").date()
            except ValueError:
                pass
        # Status column — surface the label
        elif col_type in ("status", "color") and text:
            status = text

    updated_at: datetime | None = None
    updated_str = raw.get("updated_at")
    if updated_str and isinstance(updated_str, str):
        try:
            updated_at = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    board_block = raw.get("board") or {}
    return MondayItem(
        id=str(raw.get("id", "")),
        name=str(raw.get("name", "")),
        board_id=str(board_block.get("id", "")),
        board_name=board_name or str(board_block.get("name", "")),
        assignees=assignees,
        due_date=due_date,
        status=status,
        column_values=column_values,
        updated_at=updated_at,
        url=str(raw.get("url", "")),
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_boards() -> list[dict[str, str]]:
    """Return metadata for the configured boards.

    Reads board IDs from MONDAY_BOARDS (env-derived) and hydrates names via a
    single boards(ids: [...]) call. If no boards are configured, returns [].
    """
    if not MONDAY_BOARDS:
        return []

    ids = list(MONDAY_BOARDS.values())
    query = """
    query ($ids: [ID!]) {
      boards (ids: $ids) { id name items_count }
    }
    """
    data = _gql(query, {"ids": ids})
    out: list[dict[str, str]] = []
    for b in data.get("boards", []) or []:
        out.append(
            {
                "id": str(b.get("id", "")),
                "name": str(b.get("name", "")),
                "items_count": str(b.get("items_count", "")),
            }
        )
    return out


def board_items(board_id: str, limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Fetch items from a single board (newest first)."""
    query = """
    query ($id: ID!, $limit: Int!) {
      boards (ids: [$id]) {
        id
        name
        items_page (limit: $limit) {
          items {
            id
            name
            url
            updated_at
            column_values {
              id
              text
              value
              type
              column { title }
            }
          }
        }
      }
    }
    """
    data = _gql(query, {"id": board_id, "limit": limit})
    boards = data.get("boards") or []
    if not boards:
        return []
    board = boards[0]
    board_name = str(board.get("name", ""))
    items = (board.get("items_page") or {}).get("items") or []
    parsed: list[MondayItem] = []
    for raw in items:
        item = _parse_item(raw, board_name=board_name)
        # The item's board_id may be missing from the node; populate from query context
        item.board_id = str(board.get("id", board_id))
        parsed.append(item)
    return parsed


def my_items(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Items across all configured boards assigned to MONDAY_USER_ID."""
    if not MONDAY_USER_ID:
        return []

    results: list[MondayItem] = []
    for _board_name, board_id in MONDAY_BOARDS.items():
        try:
            items = board_items(board_id, limit=limit)
        except RuntimeError as e:
            print(f"[monday] board {board_id} error (non-fatal): {e}")
            continue
        for item in items:
            if any(MONDAY_USER_ID == a or MONDAY_USER_ID in a for a in item.assignees):
                results.append(item)
    return results


def overdue_items(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Items across configured boards whose Date column is past today."""
    today = date.today()
    results: list[MondayItem] = []
    for _board_name, board_id in MONDAY_BOARDS.items():
        try:
            items = board_items(board_id, limit=limit)
        except RuntimeError as e:
            print(f"[monday] board {board_id} error (non-fatal): {e}")
            continue
        for item in items:
            if item.due_date and item.due_date < today:
                results.append(item)
    return results


def search(
    query: str,
    board_ids: list[str] | None = None,
    limit: int = DEFAULT_ITEMS_LIMIT,
) -> list[MondayItem]:
    """Client-side substring search across items on the given (or all configured) boards."""
    targets = board_ids or list(MONDAY_BOARDS.values())
    q = query.lower().strip()
    results: list[MondayItem] = []
    for board_id in targets:
        try:
            items = board_items(board_id, limit=limit)
        except RuntimeError as e:
            print(f"[monday] board {board_id} error (non-fatal): {e}")
            continue
        for item in items:
            haystack = " ".join([item.name] + list(item.column_values.values())).lower()
            if q in haystack:
                results.append(item)
    return results


# ---------------------------------------------------------------------------
# Mutations (write path — used by bootstrap scripts, not heartbeat)
# ---------------------------------------------------------------------------
#
# Monday's API rejects `formula` as a column_type in create_column. Formula
# columns exist in the schema once a user creates them in the UI, but they
# can't be created via mutation. Bootstrap scripts list them as a post-run
# manual checklist. Everything else below is API-creatable.


def get_board_columns(board_id: str) -> list[dict[str, str]]:
    """Fetch existing columns on a board.

    Used by bootstrap scripts for idempotency — check a column's title isn't
    already present before calling create_column.
    """
    query = """
    query ($id: [ID!]) {
      boards (ids: $id) { columns { id title type settings_str } }
    }
    """
    data = _gql(query, {"id": [board_id]})
    boards = data.get("boards") or []
    if not boards:
        return []
    cols = boards[0].get("columns") or []
    return [
        {
            "id": str(c.get("id", "")),
            "title": str(c.get("title", "")),
            "type": str(c.get("type", "")),
            "settings_str": str(c.get("settings_str", "")),
        }
        for c in cols
    ]


def get_board_groups(board_id: str) -> list[dict[str, str]]:
    """Fetch existing groups on a board (for idempotency)."""
    query = """
    query ($id: [ID!]) {
      boards (ids: $id) { groups { id title } }
    }
    """
    data = _gql(query, {"id": [board_id]})
    boards = data.get("boards") or []
    if not boards:
        return []
    groups = boards[0].get("groups") or []
    return [
        {"id": str(g.get("id", "")), "title": str(g.get("title", ""))} for g in groups
    ]


def create_board(
    board_name: str,
    board_kind: str = "public",
    description: str | None = None,
) -> str:
    """Create a new board, return its ID.

    board_kind: "public" | "private" | "share". Default public — the workspace
    owner has access; other members follow workspace permissions.
    """
    if board_kind not in ("public", "private", "share"):
        raise ValueError(f"board_kind must be public/private/share, got {board_kind!r}")
    query = """
    mutation ($name: String!, $kind: BoardKind!, $desc: String) {
      create_board (board_name: $name, board_kind: $kind, description: $desc) {
        id
      }
    }
    """
    variables: dict[str, Any] = {"name": board_name, "kind": board_kind, "desc": description}
    data = _gql(query, variables)
    board = data.get("create_board") or {}
    board_id = str(board.get("id", ""))
    if not board_id:
        raise RuntimeError(f"create_board returned no id: {data!r}")
    return board_id


def rename_board(board_id: str, new_name: str) -> bool:
    """Rename a board. Returns True on success.

    Uses update_board mutation with board_attribute=name. new_value is a
    plain String for the name attribute (not a JSON-encoded value).
    """
    query = """
    mutation ($id: ID!, $val: String!) {
      update_board (board_id: $id, board_attribute: name, new_value: $val)
    }
    """
    data = _gql(query, {"id": board_id, "val": new_name})
    return bool(data.get("update_board"))


def create_column(
    board_id: str,
    title: str,
    column_type: str,
    defaults: dict[str, Any] | None = None,
    description: str | None = None,
) -> str:
    """Create a column on a board, return its column id.

    column_type must match Monday's ColumnType enum — examples:
      text, long_text, numbers, date, checkbox, status, dropdown, people,
      link, email, phone, board_relation, file, tags, timeline, week, world_clock

    `formula` is NOT accepted by this mutation — add those in the UI.

    For status/dropdown, `defaults` carries the label set. For board_relation,
    `defaults` carries the linked board IDs. Shape is documented at
    https://developer.monday.com/api-reference/reference/create-a-column.
    """
    import json as _json

    query = """
    mutation ($board_id: ID!, $title: String!, $type: ColumnType!, $defaults: JSON, $desc: String) {
      create_column (
        board_id: $board_id,
        title: $title,
        column_type: $type,
        defaults: $defaults,
        description: $desc
      ) { id }
    }
    """
    variables: dict[str, Any] = {
        "board_id": board_id,
        "title": title,
        "type": column_type,
        "defaults": _json.dumps(defaults) if defaults else None,
        "desc": description,
    }
    data = _gql(query, variables)
    col = data.get("create_column") or {}
    col_id = str(col.get("id", ""))
    if not col_id:
        raise RuntimeError(f"create_column returned no id: {data!r}")
    return col_id


def create_group(board_id: str, group_name: str) -> str:
    """Create a group on a board, return its group id."""
    query = """
    mutation ($board_id: ID!, $name: String!) {
      create_group (board_id: $board_id, group_name: $name) { id }
    }
    """
    data = _gql(query, {"board_id": board_id, "name": group_name})
    group = data.get("create_group") or {}
    group_id = str(group.get("id", ""))
    if not group_id:
        raise RuntimeError(f"create_group returned no id: {data!r}")
    return group_id


def create_item(
    board_id: str,
    item_name: str,
    group_id: str | None = None,
    column_values: dict[str, Any] | None = None,
) -> str:
    """Create an item (row) on a board, return its item id.

    column_values is a {column_id: value} map; values are Monday's native
    column-value shapes (e.g. {"label": "In progress"} for status).
    """
    import json as _json

    query = """
    mutation ($board_id: ID!, $name: String!, $group_id: String, $col_vals: JSON) {
      create_item (
        board_id: $board_id,
        item_name: $name,
        group_id: $group_id,
        column_values: $col_vals
      ) { id }
    }
    """
    variables: dict[str, Any] = {
        "board_id": board_id,
        "name": item_name,
        "group_id": group_id,
        "col_vals": _json.dumps(column_values) if column_values else None,
    }
    data = _gql(query, variables)
    item = data.get("create_item") or {}
    item_id = str(item.get("id", ""))
    if not item_id:
        raise RuntimeError(f"create_item returned no id: {data!r}")
    return item_id


def update_column_value(
    board_id: str,
    item_id: str,
    column_id: str,
    value: Any,
) -> bool:
    """Update a single column value on an existing item.

    `value` is passed through JSON serialization — Monday's native column-value
    shape applies (e.g. {"date": "2026-04-22"} for date columns).
    """
    import json as _json

    query = """
    mutation ($board_id: ID!, $item_id: ID!, $col_id: String!, $val: JSON!) {
      change_column_value (
        board_id: $board_id,
        item_id: $item_id,
        column_id: $col_id,
        value: $val
      ) { id }
    }
    """
    data = _gql(
        query,
        {
            "board_id": board_id,
            "item_id": item_id,
            "col_id": column_id,
            "val": _json.dumps(value),
        },
    )
    return bool((data.get("change_column_value") or {}).get("id"))


def add_update(item_id: str, body: str) -> str:
    """Post an update (comment) on an item, return the update id."""
    query = """
    mutation ($item_id: ID!, $body: String!) {
      create_update (item_id: $item_id, body: $body) { id }
    }
    """
    data = _gql(query, {"item_id": item_id, "body": body})
    update = data.get("create_update") or {}
    update_id = str(update.get("id", ""))
    if not update_id:
        raise RuntimeError(f"create_update returned no id: {data!r}")
    return update_id


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_items_for_context(items: list[MondayItem]) -> str:
    """Format items for Claude's context, grouped by board, wrapped in XML boundary."""
    if not items:
        return wrap_external_data("No Monday.com items found.", "monday")

    by_board: dict[str, list[MondayItem]] = {}
    for item in items:
        key = item.board_name or item.board_id or "Unknown board"
        by_board.setdefault(key, []).append(item)

    sections: list[str] = []
    for board_name in sorted(by_board):
        sections.append(f"## {sanitize_external_text(board_name, 'monday')}")
        for item in by_board[board_name]:
            name = sanitize_external_text(item.name, "monday")
            line = f"- **{name}** (ID: {item.id})"
            extras: list[str] = []
            if item.due_date:
                extras.append(f"due {item.due_date.isoformat()}")
            if item.status:
                extras.append(f"status: {sanitize_external_text(item.status, 'monday')}")
            if item.assignees:
                extras.append(
                    "assignees: "
                    + ", ".join(sanitize_external_text(a, "monday") for a in item.assignees[:3])
                )
            if extras:
                line += "\n  " + " | ".join(extras)
            sections.append(line)

    return wrap_external_data("\n".join(sections), "monday")


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Monday.com integration")
    parser.add_argument(
        "command", choices=["boards", "board", "my-items", "overdue", "search"]
    )
    parser.add_argument("target_id", nargs="?", default=None, help="Board ID for board cmd")
    parser.add_argument("--limit", type=int, default=DEFAULT_ITEMS_LIMIT)
    parser.add_argument("--query", default="")
    args = parser.parse_args()

    if args.command == "boards":
        for b in list_boards():
            print(f"- {b['name']} (id: {b['id']}, items: {b['items_count']})")
    elif args.command == "board":
        if not args.target_id:
            print("Board ID required, e.g. `board 123456`")
            sys.exit(1)
        print(format_items_for_context(board_items(args.target_id, limit=args.limit)))
    elif args.command == "my-items":
        print(format_items_for_context(my_items(limit=args.limit)))
    elif args.command == "overdue":
        print(format_items_for_context(overdue_items(limit=args.limit)))
    elif args.command == "search":
        if not args.query:
            print("--query required")
            sys.exit(1)
        print(format_items_for_context(search(args.query, limit=args.limit)))
