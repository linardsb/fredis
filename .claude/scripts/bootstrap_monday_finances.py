"""Create the new Finances Monday board + its columns.

The plan §Boards-to-add calls for one Finances board with money-event rows
(invoices, payments, expenses, subscriptions, refunds). Most columns are
API-creatable; the two FX-conversion columns (Amount in GBP / Amount in EUR)
are formulas and are listed in the post-run UI checklist.

Idempotent: if a board named 'Finances' already exists in MONDAY_BOARDS,
the script reuses it and skips create_board. Columns are checked by title
before creating.

After a successful live run, the script prints the line to add to your
environment file: MONDAY_BOARD_FINANCES=<new_id>.

Usage:
    uv run python bootstrap_monday_finances.py --dry-run
    uv run python bootstrap_monday_finances.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MONDAY_BOARDS  # noqa: E402
from integrations import monday_api  # noqa: E402

BOARD_NAME = "Finances"
BOARD_KIND = "public"

TYPE_LABELS = {
    "labels": {
        "0": "Invoice",
        "1": "Payment",
        "2": "Expense",
        "3": "Subscription",
        "4": "Refund",
    }
}
CURRENCY_LABELS = {"labels": {"0": "GBP", "1": "EUR", "2": "USD", "3": "Other"}}
STATUS_LABELS = {
    "labels": {
        "0": "Draft",
        "1": "Sent",
        "2": "Paid",
        "3": "Overdue",
        "4": "Cancelled",
    }
}
CATEGORY_LABELS = {
    "labels": {
        "0": "Retainer revenue",
        "1": "Project revenue",
        "2": "SaaS",
        "3": "Software",
        "4": "Hardware",
        "5": "Travel",
        "6": "Professional services",
        "7": "Other",
    }
}

COLUMNS: list[tuple[str, str, dict[str, Any] | None]] = [
    ("Type", "status", TYPE_LABELS),
    ("Amount", "numbers", None),
    ("Currency", "status", CURRENCY_LABELS),
    ("Status", "status", STATUS_LABELS),
    ("Issue date", "date", None),
    ("Due date", "date", None),
    ("Paid date", "date", None),
    ("Category", "status", CATEGORY_LABELS),
    ("Vault draft link", "link", None),
]

# Board_relation columns added after main columns — require target board IDs.
CONNECT_COLUMNS: list[tuple[str, str]] = [
    ("Account", "Accounts"),  # optional connect to Accounts
]

# Formulas to add in the UI by hand (plan §7 Finances + §Confirmed decisions).
# FX constants hardcoded — quarterly review (plan §What could go wrong).
_GBP_FORMULA = (
    'IF({Currency}="GBP", {Amount}, '
    'IF({Currency}="EUR", {Amount}*0.85, '
    'IF({Currency}="USD", {Amount}*0.79, {Amount})))'
)
_EUR_FORMULA = (
    'IF({Currency}="EUR", {Amount}, '
    'IF({Currency}="GBP", {Amount}/0.85, '
    'IF({Currency}="USD", {Amount}*0.93, {Amount})))'
)
FORMULA_CHECKLIST: list[tuple[str, str]] = [
    ("Amount in GBP", _GBP_FORMULA),
    ("Amount in EUR", _EUR_FORMULA),
]


def _board_id_by_name(name: str) -> str | None:
    """Case-insensitive lookup in MONDAY_BOARDS."""
    for k, v in MONDAY_BOARDS.items():
        if k.lower() == name.lower():
            return v
    return None


def run(dry_run: bool) -> int:
    board_id = _board_id_by_name(BOARD_NAME)

    if board_id is None:
        if dry_run:
            print(f"[dry-run] create_board({BOARD_NAME!r}, kind={BOARD_KIND!r})")
            board_id = "<new-id>"
        else:
            print(f"[finances] creating board {BOARD_NAME!r}...")
            board_id = monday_api.create_board(
                BOARD_NAME,
                board_kind=BOARD_KIND,
                description="Money events: invoices, payments, expenses, subscriptions",
            )
            print(f"  + created board: id={board_id}")
            print("\n  >> Add this line to your environment file:")
            print(f"     MONDAY_BOARD_FINANCES={board_id}")
    else:
        print(f"[finances] reusing existing board: id={board_id}")

    # Columns
    if dry_run or board_id == "<new-id>":
        existing_col_titles: set[str] = set()
        print("  [dry-run] (would fetch existing columns)")
    else:
        cols = monday_api.get_board_columns(board_id)
        existing_col_titles = {c["title"] for c in cols}
        print(f"  existing columns: {sorted(existing_col_titles)}")

    for title, ctype, defaults in COLUMNS:
        if title in existing_col_titles:
            print(f"  skip column (exists): {title}")
            continue
        if dry_run:
            print(f"  [dry-run] create_column {title!r} ({ctype})")
        else:
            cid = monday_api.create_column(board_id, title, ctype, defaults=defaults)
            print(f"  + column: {title} ({ctype}, id={cid})")

    # Board-relation columns (to Accounts etc.)
    # Monday's API currently rejects board_relation creation — fall through
    # to a UI-follow-up checklist when that happens.
    connect_checklist: list[tuple[str, str]] = []
    for title, target_name in CONNECT_COLUMNS:
        if title in existing_col_titles or target_name in existing_col_titles:
            print(f"  skip connect (exists): {title} or {target_name}")
            continue
        target_id = _board_id_by_name(target_name)
        if target_id is None:
            print(f"  WARN — skip connect {title!r} → {target_name} (no ID configured)")
            continue
        if dry_run:
            print(f"  [dry-run] create_column board_relation {title!r} → {target_name}")
            continue
        try:
            cid = monday_api.create_column(
                board_id,
                title,
                "board_relation",
                defaults={"boardIds": [int(target_id)]},
            )
            print(f"  + connect: {title} → {target_name} (id={cid})")
        except RuntimeError as e:
            if "not supported" in str(e).lower():
                print(
                    f"  UI follow-up — board_relation {title!r} → {target_name} "
                    "(Monday API rejects this column type)"
                )
                connect_checklist.append((title, target_name))
            else:
                raise

    if connect_checklist:
        print("\n=== UI follow-up — add these board_relation columns by hand ===")
        print("(Monday's API rejects creation of this column type.)")
        for title, target in connect_checklist:
            print(f"  Column: {title!r} → connects to board: {target}")

    # Formula checklist (UI follow-up)
    if FORMULA_CHECKLIST:
        print("\n=== UI follow-up — add these formula columns by hand ===")
        print("(Monday's API doesn't support creating formula columns.)")
        for title, formula in FORMULA_CHECKLIST:
            print(f"  Column: {title!r}")
            print(f"  Formula: {formula}")

    if dry_run:
        print("\n[dry-run] No changes were made. Re-run without --dry-run to apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the Finances Monday board")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print planned payloads; no mutations"
    )
    args = parser.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
