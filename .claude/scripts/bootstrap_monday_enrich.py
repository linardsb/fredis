"""Enrich existing Monday boards with the columns the plan requires.

Idempotent: fetches each board's existing columns and only creates the
missing ones. Formula columns are listed in a post-run checklist (Monday's
API cannot create them — they're UI-only).

Usage:
    uv run python bootstrap_monday_enrich.py --dry-run   # preview only
    uv run python bootstrap_monday_enrich.py             # live run

Boards touched: Contacts, Accounts, Client Projects, Activities, Deals, Leads.
Board IDs are read from the MONDAY_BOARDS dict in config.py (populated from
MONDAY_BOARD_<NAME> environment variables).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MONDAY_BOARDS  # noqa: E402
from integrations import monday_api  # noqa: E402


@dataclass
class ColumnSpec:
    """One column to ensure on a board."""

    title: str
    column_type: str
    defaults: dict[str, Any] | None = None
    description: str | None = None


@dataclass
class BoardSpec:
    """One board to enrich + its formula-column checklist (for UI follow-up)."""

    board_key: str  # Title-cased key in MONDAY_BOARDS (e.g. "Contacts")
    columns: list[ColumnSpec] = field(default_factory=list)
    formulas: list[tuple[str, str]] = field(default_factory=list)  # (title, formula)
    connect_after: list[tuple[str, str]] = field(default_factory=list)
    # connect_after = (column_title, target_board_key) — created only after
    # both boards exist and the target board's ID is resolvable.


# ---------------------------------------------------------------------------
# Column label palettes (reused across boards)
# ---------------------------------------------------------------------------

CHANNEL_LABELS = {"labels": {"0": "WhatsApp", "1": "Email", "2": "Slack", "3": "Facebook DM"}}
ENGAGEMENT_LABELS = {
    "labels": {"0": "Retainer", "1": "Project", "2": "Prospect", "3": "Dormant"}
}
PROJECT_STATUS_LABELS = {
    "labels": {
        "0": "Kickoff",
        "1": "In flight",
        "2": "Blocked",
        "3": "Delivered",
        "4": "Invoiced",
        "5": "Closed",
    }
}
DEAL_STAGE_LABELS = {
    "labels": {
        "0": "Inbound",
        "1": "Discovery",
        "2": "Proposal",
        "3": "Signed",
        "4": "Kickoff",
        "5": "Delivery",
        "6": "Invoice",
        "7": "Post-delivery",
    }
}
DEAL_SERVICE_LABELS = {
    "labels": {
        "0": "AI-agentic build",
        "1": "Custom app",
        "2": "SaaS",
        "3": "Marketing-ops",
        "4": "Agri×AI",
        "5": "Advisory",
    }
}
SOURCE_LABELS = {
    "labels": {"0": "Cold outreach", "1": "Inbound", "2": "Referral", "3": "Content"}
}
LEAD_STATUS_LABELS = {
    "labels": {
        "0": "New",
        "1": "Contacted",
        "2": "Qualified",
        "3": "Converted to Deal",
        "4": "Disqualified",
    }
}
ACTIVITY_TYPE_LABELS = {
    "labels": {"0": "Call", "1": "Email", "2": "Meeting", "3": "DM"}
}
CURRENCY_LABELS = {"labels": {"0": "GBP", "1": "EUR", "2": "USD", "3": "Other"}}


# ---------------------------------------------------------------------------
# Per-board specs
# ---------------------------------------------------------------------------

BOARDS: list[BoardSpec] = [
    BoardSpec(
        board_key="Contacts",
        columns=[
            ColumnSpec("Urgent alert", "checkbox"),
            ColumnSpec("Conflict node", "checkbox"),
            ColumnSpec("Conflict reason", "long_text"),
            ColumnSpec("Last contact", "date"),
            ColumnSpec("Preferred channel", "status", defaults=CHANNEL_LABELS),
        ],
        formulas=[
            ("Days since contact", "DAYS_BETWEEN({Last contact}, TODAY())"),
            (
                "Silent?",
                'IF(AND({Days since contact}>14, {Urgent alert}=true), "⚠️", "")',
            ),
        ],
        connect_after=[("Linked Account", "Accounts")],
    ),
    BoardSpec(
        board_key="Accounts",
        columns=[
            ColumnSpec("Engagement type", "status", defaults=ENGAGEMENT_LABELS),
            ColumnSpec("Retainer £/mo", "numbers"),
            ColumnSpec("Contract end date", "date"),
            ColumnSpec("Notes", "long_text"),
        ],
        connect_after=[("Linked Deal", "Deals")],
    ),
    BoardSpec(
        board_key="Client Projects",
        columns=[
            ColumnSpec("Status", "status", defaults=PROJECT_STATUS_LABELS),
            ColumnSpec("Start date", "date"),
            ColumnSpec("Target delivery", "date"),
            ColumnSpec("Actual delivery", "date"),
            ColumnSpec("Fee", "numbers"),
            ColumnSpec("Currency", "status", defaults=CURRENCY_LABELS),
            ColumnSpec("Vault drafts link", "link"),
        ],
        connect_after=[
            ("Account", "Accounts"),
            # Linked invoice → Finances (connected after Finances board exists).
        ],
    ),
    BoardSpec(
        board_key="Activities",
        columns=[
            ColumnSpec("Type", "status", defaults=ACTIVITY_TYPE_LABELS),
            ColumnSpec("Date", "date"),
            ColumnSpec("Outcome", "long_text"),
            ColumnSpec("Next step", "long_text"),
        ],
        connect_after=[
            ("Contact", "Contacts"),
            ("Account", "Accounts"),
            ("Deal", "Deals"),
        ],
    ),
    BoardSpec(
        board_key="Deals",
        columns=[
            ColumnSpec("Stage", "status", defaults=DEAL_STAGE_LABELS),
            ColumnSpec("Service line", "status", defaults=DEAL_SERVICE_LABELS),
            ColumnSpec("Value", "numbers"),
            ColumnSpec("Currency", "status", defaults=CURRENCY_LABELS),
            ColumnSpec("Close date", "date"),
            ColumnSpec("Probability", "numbers"),
            ColumnSpec("Next step", "long_text"),
            ColumnSpec("Source", "status", defaults=SOURCE_LABELS),
        ],
        formulas=[
            ("Weighted value", "{Value} * {Probability} / 100"),
        ],
        connect_after=[("Account", "Accounts")],
    ),
    BoardSpec(
        board_key="Leads",
        columns=[
            ColumnSpec("Status", "status", defaults=LEAD_STATUS_LABELS),
            ColumnSpec("Source", "status", defaults=SOURCE_LABELS),
            ColumnSpec("Service line", "status", defaults=DEAL_SERVICE_LABELS),
            ColumnSpec("First contact", "date"),
            ColumnSpec("Last contact", "date"),
            ColumnSpec("Notes", "long_text"),
        ],
        connect_after=[("Account", "Accounts")],
    ),
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def _board_id(board_key: str) -> str | None:
    """Resolve a board ID from MONDAY_BOARDS (case-insensitive fallback)."""
    if board_key in MONDAY_BOARDS:
        return MONDAY_BOARDS[board_key]
    for k, v in MONDAY_BOARDS.items():
        if k.lower() == board_key.lower():
            return v
    return None


def _connect_defaults(linked_board_id: str) -> dict[str, Any]:
    """Shape for board_relation column's `defaults` argument."""
    return {"boardIds": [int(linked_board_id)]}


def run(dry_run: bool) -> int:
    """Enrich every spec'd board. Returns 0 on success, 1 if any board is missing."""
    missing = [spec.board_key for spec in BOARDS if _board_id(spec.board_key) is None]
    if missing:
        print(f"[enrich] ERROR — board IDs not configured: {missing}")
        print("[enrich] Add MONDAY_BOARD_<NAME> variables for each missing board.")
        return 1

    formula_checklist: list[tuple[str, str, str]] = []  # (board, title, formula)
    connect_checklist: list[tuple[str, str, str]] = []  # (board, title, target)
    summary: list[str] = []

    for spec in BOARDS:
        board_id = _board_id(spec.board_key)
        assert board_id is not None  # checked above
        print(f"\n=== Enrich: {spec.board_key} (board {board_id}) ===")

        if dry_run:
            existing_titles: set[str] = set()
            print("  [dry-run] (would fetch existing columns)")
        else:
            cols = monday_api.get_board_columns(board_id)
            existing_titles = {c["title"] for c in cols}
            print(f"  existing columns: {sorted(existing_titles)}")

        created = 0
        skipped = 0
        for col in spec.columns:
            if col.title in existing_titles:
                print(f"  skip (exists): {col.title}")
                skipped += 1
                continue
            if dry_run:
                payload = {
                    "board_id": board_id,
                    "title": col.title,
                    "type": col.column_type,
                    "defaults": col.defaults,
                }
                print(f"  [dry-run] create_column {payload}")
            else:
                new_id = monday_api.create_column(
                    board_id,
                    col.title,
                    col.column_type,
                    defaults=col.defaults,
                    description=col.description,
                )
                print(f"  + created: {col.title} ({col.column_type}, id={new_id})")
            created += 1

        # board_relation (connect boards) — Monday's API rejects creation of
        # this column type ("not supported yet"). Also, the built-in Sales CRM
        # template already wires Contacts ↔ Accounts ↔ Deals ↔ Activities via
        # auto-generated columns (titled after the target board), so many of
        # these connects already exist. Treat any miss as UI follow-up.
        for title, target_key in spec.connect_after:
            # Idempotent skip — either our proposed title or the auto-template
            # title (matching the target board's name) counts as "exists".
            if title in existing_titles or target_key in existing_titles:
                print(f"  skip connect (exists): {title} or {target_key}")
                skipped += 1
                continue
            target_id = _board_id(target_key)
            if target_id is None:
                print(f"  WARN — skip connect {title!r} → {target_key} (no ID yet)")
                continue
            if dry_run:
                print(
                    f"  [dry-run] create_column board_relation {title!r} → "
                    f"{target_key} ({target_id})"
                )
                created += 1
                continue
            try:
                new_id = monday_api.create_column(
                    board_id,
                    title,
                    "board_relation",
                    defaults=_connect_defaults(target_id),
                )
                print(f"  + created connect: {title} → {target_key} (id={new_id})")
                created += 1
            except RuntimeError as e:
                if "not supported" in str(e).lower():
                    print(
                        f"  UI follow-up — board_relation {title!r} → {target_key} "
                        "(Monday API rejects this column type)"
                    )
                    connect_checklist.append((spec.board_key, title, target_key))
                else:
                    raise

        for ftitle, fformula in spec.formulas:
            formula_checklist.append((spec.board_key, ftitle, fformula))

        summary.append(f"{spec.board_key}: +{created} / skipped {skipped}")

    print("\n=== Summary ===")
    for line in summary:
        print(f"  {line}")

    if formula_checklist:
        print("\n=== UI follow-up — add these formula columns by hand ===")
        print("(Monday's API doesn't support creating formula columns.)")
        for board, title, formula in formula_checklist:
            print(f"  [{board}] Column: {title!r}")
            print(f"           Formula: {formula}")

    if connect_checklist:
        print("\n=== UI follow-up — add these board_relation columns by hand ===")
        print("(Monday's API rejects creation of this column type.)")
        for board, title, target in connect_checklist:
            print(f"  [{board}] Column: {title!r} → connects to board: {target}")

    if dry_run:
        print("\n[dry-run] No changes were made. Re-run without --dry-run to apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Enrich existing Monday boards with missing columns"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print planned payloads; no mutations"
    )
    args = parser.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
