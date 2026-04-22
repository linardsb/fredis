"""Tests for integrations.monday_scans.

All HTTP is mocked — scans are pure filters on top of monday_api.board_items.
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["MONDAY_API_TOKEN"] = "test-token-not-real"
os.environ["MONDAY_USER_ID"] = "999"
os.environ["MONDAY_BOARD_IDS"] = (
    "Contacts:100,Deals:200,Finances:300,Lanes Features:400"
)

import importlib  # noqa: E402

import config as _config  # noqa: E402
import integrations.monday_api as monday_api  # noqa: E402
import integrations.monday_scans as scans  # noqa: E402

importlib.reload(_config)
importlib.reload(monday_api)
importlib.reload(scans)


def _item(
    *,
    id: str,
    name: str = "row",
    board_id: str = "0",
    board_name: str = "",
    status: str | None = None,
    due_date: date | None = None,
    updated_at: datetime | None = None,
    column_values: dict[str, str] | None = None,
) -> monday_api.MondayItem:
    return monday_api.MondayItem(
        id=id,
        name=name,
        board_id=board_id,
        board_name=board_name,
        status=status,
        due_date=due_date,
        updated_at=updated_at,
        column_values=column_values or {},
    )


# =============================================================================
# overdue_invoices
# =============================================================================


def test_overdue_invoices_picks_explicit_status() -> None:
    items = [
        _item(id="1", status="Overdue"),
        _item(id="2", status="Paid"),
        _item(id="3", status="Draft"),
    ]
    with patch.object(scans, "board_items", return_value=items):
        hits = scans.overdue_invoices()
    assert {h.id for h in hits} == {"1"}


def test_overdue_invoices_infers_from_due_date_minus_paid() -> None:
    today = date.today()
    items = [
        _item(id="past_unpaid", status="Sent", due_date=today - timedelta(days=5)),
        _item(id="past_paid", status="Paid", due_date=today - timedelta(days=5)),
        _item(id="future", status="Sent", due_date=today + timedelta(days=3)),
    ]
    with patch.object(scans, "board_items", return_value=items):
        hits = scans.overdue_invoices()
    assert {h.id for h in hits} == {"past_unpaid"}


# =============================================================================
# silent_contacts
# =============================================================================


def test_silent_contacts_requires_urgent_flag_and_staleness() -> None:
    today = date.today()
    items = [
        _item(
            id="urgent_silent",
            column_values={
                "Urgent alert": "v",
                "Last contact": (today - timedelta(days=30)).isoformat(),
            },
        ),
        _item(
            id="urgent_fresh",
            column_values={
                "Urgent alert": "v",
                "Last contact": today.isoformat(),
            },
        ),
        _item(
            id="not_urgent",
            column_values={
                "Urgent alert": "",
                "Last contact": (today - timedelta(days=30)).isoformat(),
            },
        ),
        _item(
            id="urgent_no_last_contact",
            column_values={"Urgent alert": "v"},
        ),
    ]
    with patch.object(scans, "board_items", return_value=items):
        hits = scans.silent_contacts()
    # Urgent + stale OR urgent + never-contacted
    assert {h.id for h in hits} == {"urgent_silent", "urgent_no_last_contact"}


# =============================================================================
# stale_deals
# =============================================================================


def test_stale_deals_skips_closed_and_fresh() -> None:
    now = datetime.now(UTC)
    items = [
        _item(id="stale_open", column_values={"Stage": "Discovery"},
              updated_at=now - timedelta(days=30)),
        _item(id="fresh_open", column_values={"Stage": "Proposal"},
              updated_at=now - timedelta(days=3)),
        _item(id="stale_closed", column_values={"Stage": "Signed"},
              updated_at=now - timedelta(days=90)),
        _item(id="never_updated", column_values={"Stage": "Inbound"},
              updated_at=None),
    ]
    with patch.object(scans, "board_items", return_value=items):
        hits = scans.stale_deals()
    # stale_open: open + old => hit
    # fresh_open: updated recently => skip
    # stale_closed: Signed is closed => skip
    # never_updated: no timestamp => counts as stale
    assert {h.id for h in hits} == {"stale_open", "never_updated"}


# =============================================================================
# breached_lane_gates
# =============================================================================


def test_breached_lane_gates_requires_summary_row_and_breached_state() -> None:
    items = [
        _item(
            id="vtv_summary",
            name="VTV — Summary",
            column_values={"Kill-gate state": "Breached"},
        ),
        _item(
            id="vtv_summary_green",
            name="VTV — Summary",
            column_values={"Kill-gate state": "Green"},
        ),
        _item(
            id="feature_breached",
            name="Some feature (not a summary)",
            column_values={"Kill-gate state": "Breached"},
        ),
        _item(
            id="cab_summary",
            name="Cab — Summary",
            column_values={"Kill-gate state": "Breached"},
        ),
    ]
    with patch.object(scans, "board_items", return_value=items):
        hits = scans.breached_lane_gates()
    assert {h.id for h in hits} == {"vtv_summary", "cab_summary"}


# =============================================================================
# Guards — no board configured → empty list, never crash
# =============================================================================


def test_scans_return_empty_when_board_missing(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr(scans, "MONDAY_BOARDS", {})
    assert scans.overdue_invoices() == []
    assert scans.silent_contacts() == []
    assert scans.stale_deals() == []
    assert scans.breached_lane_gates() == []
