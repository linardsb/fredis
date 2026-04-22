"""Targeted Monday.com scans for the heartbeat.

Four read-only scans over specific boards, each returning a list of
MondayItem hits that the heartbeat agent can use to draft follow-ups:

  1. overdue_invoices()   — Finances rows with Status=Overdue (or Due date
                             past + Status not in {Paid, Cancelled}).
  2. silent_contacts()    — Contacts rows with Urgent alert=true AND last
                             contact >N days ago (default 14).
  3. stale_deals()        — Deals not in a closed stage AND not updated in
                             >N days (default 14).
  4. breached_lane_gates()— Lanes & Features lane-summary rows with
                             Kill-gate state=Breached.

All scans are gated by `MONDAY_SCANS_ENABLED` at the heartbeat call site —
this module's functions just run the queries and return.
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MONDAY_BOARDS, MONDAY_SILENT_CONTACT_DAYS, MONDAY_STALE_DEAL_DAYS  # noqa: E402
from integrations.monday_api import DEFAULT_ITEMS_LIMIT, MondayItem, board_items  # noqa: E402

CLOSED_DEAL_STAGES = {"Signed", "Closed", "Won", "Lost", "Post-delivery"}


def _board_id(name: str) -> str | None:
    """Case-insensitive lookup in MONDAY_BOARDS."""
    if name in MONDAY_BOARDS:
        return MONDAY_BOARDS[name]
    for k, v in MONDAY_BOARDS.items():
        if k.lower() == name.lower():
            return v
    return None


def overdue_invoices(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Finances rows overdue on payment.

    Treats a row as overdue when either:
      - Status column literal == "Overdue", OR
      - Due date < today AND Status not in {Paid, Cancelled}.
    """
    bid = _board_id("Finances")
    if bid is None:
        return []
    today = date.today()
    hits: list[MondayItem] = []
    for item in board_items(bid, limit=limit):
        status = (item.status or "").strip()
        due = item.due_date or _parse_date_col(item, "Due date")
        paid = status in {"Paid", "Cancelled"}
        if status == "Overdue":
            hits.append(item)
        elif due and due < today and not paid:
            hits.append(item)
    return hits


def silent_contacts(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Contacts with Urgent alert=true AND stale last-contact.

    Threshold = MONDAY_SILENT_CONTACT_DAYS (default 14).
    """
    bid = _board_id("Contacts")
    if bid is None:
        return []
    cutoff = date.today() - timedelta(days=MONDAY_SILENT_CONTACT_DAYS)
    hits: list[MondayItem] = []
    for item in board_items(bid, limit=limit):
        if not _truthy(item.column_values.get("Urgent alert", "")):
            continue
        last = _parse_date_col(item, "Last contact")
        if last is None or last <= cutoff:
            hits.append(item)
    return hits


def stale_deals(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Deals not in a closed stage and not touched in >N days.

    Uses item.updated_at (Monday-wide row update timestamp) as the activity
    signal. Threshold = MONDAY_STALE_DEAL_DAYS (default 14).
    """
    bid = _board_id("Deals")
    if bid is None:
        return []
    cutoff = datetime.now(UTC) - timedelta(days=MONDAY_STALE_DEAL_DAYS)
    hits: list[MondayItem] = []
    for item in board_items(bid, limit=limit):
        stage = (item.column_values.get("Stage") or item.status or "").strip()
        if stage in CLOSED_DEAL_STAGES:
            continue
        if item.updated_at is None or item.updated_at <= cutoff:
            hits.append(item)
    return hits


def breached_lane_gates(limit: int = DEFAULT_ITEMS_LIMIT) -> list[MondayItem]:
    """Lanes & Features lane-summary rows with Kill-gate state=Breached.

    Resolves the board by name (`Lanes Features` after the env-var rename
    from `Products`). Only rows whose name ends with '— Summary' count —
    feature rows share the board but have their own kill-gate semantics.
    """
    bid = _board_id("Lanes Features") or _board_id("Lanes & Features")
    if bid is None:
        return []
    hits: list[MondayItem] = []
    for item in board_items(bid, limit=limit):
        if "— Summary" not in item.name:
            continue
        state = (item.column_values.get("Kill-gate state") or "").strip()
        if state == "Breached":
            hits.append(item)
    return hits


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_date_col(item: MondayItem, title: str) -> date | None:
    raw = item.column_values.get(title, "").strip()
    if not raw:
        return None
    try:
        return datetime.strptime(raw.split()[0], "%Y-%m-%d").date()
    except ValueError:
        return None


def _truthy(val: str) -> bool:
    """Monday surfaces checkbox column text as 'v' (checked) or '' (unchecked)."""
    return bool(val) and val.strip().lower() in {"v", "true", "1", "checked"}
