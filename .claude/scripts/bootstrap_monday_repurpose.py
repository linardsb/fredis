"""Repurpose the 'Products & Services' Monday board into 'Lanes & Features'.

Steps (idempotent):
  1. Rename the board.
  2. Add columns — two status columns (Lane status + Feature status), plus
     Phase, Kill-gate metric, Kill-gate state, IP-overhang flag,
     RICE (Reach/Impact/Confidence/Effort), Ship target, GitHub PR, Notes.
  3. Create one group per lane (VTV, Cab, Email Hub, UGOKI, GERBONI).
  4. Create one lane-summary row at the top of each group with default
     status per the plan: VTV / Cab / Email Hub = Building;
     UGOKI / GERBONI = Paused.

Usage:
    uv run python bootstrap_monday_repurpose.py --dry-run   # preview
    uv run python bootstrap_monday_repurpose.py             # live
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import MONDAY_BOARDS  # noqa: E402
from integrations import monday_api  # noqa: E402

BOARD_KEY = "Products"  # current MONDAY_BOARD_PRODUCTS var maps to this key
NEW_BOARD_NAME = "Lanes & Features"

# Lanes — plan §Confirmed decisions (2026-04-22):
# VTV / Cab / Email Hub = Building; UGOKI / GERBONI = Paused.
LANES: list[tuple[str, str]] = [
    ("VTV", "Building"),
    ("Cab", "Building"),
    ("Email Hub", "Building"),
    ("UGOKI", "Paused"),
    ("GERBONI", "Paused"),
]

LANE_STATUS_LABELS = {
    "labels": {
        "0": "Idea",
        "1": "Validating",
        "2": "Building",
        "3": "Launched",
        "4": "Paused",
        "5": "Killed",
    }
}
FEATURE_STATUS_LABELS = {
    "labels": {
        "0": "Backlog",
        "1": "Spec",
        "2": "Building",
        "3": "Shipped",
        "4": "Cut",
    }
}
KILL_GATE_STATE_LABELS = {
    "labels": {"0": "Green", "1": "Yellow", "2": "Breached"}
}
PHASE_LABELS = {
    "labels": {"0": "Idea", "1": "Validate", "2": "Build", "3": "Ship", "4": "Scale"}
}

COLUMNS: list[tuple[str, str, dict[str, Any] | None]] = [
    # (title, column_type, defaults)
    ("Lane status", "status", LANE_STATUS_LABELS),
    ("Feature status", "status", FEATURE_STATUS_LABELS),
    ("Phase", "status", PHASE_LABELS),
    ("Kill-gate metric", "long_text", None),
    ("Kill-gate state", "status", KILL_GATE_STATE_LABELS),
    ("IP-overhang flag", "checkbox", None),
    ("RICE Reach", "numbers", None),
    ("RICE Impact", "numbers", None),
    ("RICE Confidence", "numbers", None),
    ("RICE Effort", "numbers", None),
    ("Ship target", "date", None),
    ("GitHub PR", "link", None),
    ("Notes", "long_text", None),
]


def _board_id(board_key: str) -> str | None:
    if board_key in MONDAY_BOARDS:
        return MONDAY_BOARDS[board_key]
    for k, v in MONDAY_BOARDS.items():
        if k.lower() == board_key.lower():
            return v
    return None


def run(dry_run: bool) -> int:
    board_id = _board_id(BOARD_KEY)
    if board_id is None:
        print(f"[repurpose] ERROR — no MONDAY_BOARD_{BOARD_KEY.upper()} configured")
        return 1

    print(f"\n=== Repurpose board {board_id} → {NEW_BOARD_NAME!r} ===")

    # 1. Rename
    if dry_run:
        print(f"  [dry-run] rename_board({board_id}, {NEW_BOARD_NAME!r})")
    else:
        ok = monday_api.rename_board(board_id, NEW_BOARD_NAME)
        print(f"  renamed: ok={ok}")

    # 2. Columns
    if dry_run:
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

    # 3. Groups (per lane)
    if dry_run:
        existing_groups: dict[str, str] = {}
        print("  [dry-run] (would fetch existing groups)")
    else:
        groups = monday_api.get_board_groups(board_id)
        existing_groups = {g["title"]: g["id"] for g in groups}
        print(f"  existing groups: {sorted(existing_groups)}")

    group_ids: dict[str, str] = dict(existing_groups)
    for lane_name, _default_status in LANES:
        if lane_name in group_ids:
            print(f"  skip group (exists): {lane_name} (id={group_ids[lane_name]})")
            continue
        if dry_run:
            print(f"  [dry-run] create_group {lane_name!r}")
            group_ids[lane_name] = f"dry_{lane_name.lower().replace(' ', '_')}"
        else:
            gid = monday_api.create_group(board_id, lane_name)
            group_ids[lane_name] = gid
            print(f"  + group: {lane_name} (id={gid})")

    # 4. Lane-summary rows (one top row per group)
    # Idempotent marker: item_name "{Lane} — Summary".
    if dry_run:
        print("  [dry-run] (would scan existing items for summary rows)")
        existing_summary_names: set[str] = set()
    else:
        items = monday_api.board_items(board_id, limit=200)
        existing_summary_names = {i.name for i in items if "— Summary" in i.name}
        print(f"  existing summary rows: {sorted(existing_summary_names)}")

    for lane_name, default_status in LANES:
        item_name = f"{lane_name} — Summary"
        if item_name in existing_summary_names:
            print(f"  skip summary (exists): {item_name}")
            continue
        group_id = group_ids.get(lane_name)
        if dry_run:
            print(
                f"  [dry-run] create_item {item_name!r} in group {group_id!r} "
                f"(Lane status='{default_status}')"
            )
        else:
            # In live mode, map title → id so column_values keys work.
            live_cols = monday_api.get_board_columns(board_id)
            title_to_id = {c["title"]: c["id"] for c in live_cols}
            col_vals_live: dict[str, Any] = {}
            if "Lane status" in title_to_id:
                col_vals_live[title_to_id["Lane status"]] = {"label": default_status}
            item_id = monday_api.create_item(
                board_id,
                item_name,
                group_id=group_id,
                column_values=col_vals_live or None,
            )
            print(f"  + summary row: {item_name} (id={item_id})")

    if dry_run:
        print("\n[dry-run] No changes were made. Re-run without --dry-run to apply.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rename Products & Services → Lanes & Features, seed lane groups"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print planned payloads; no mutations"
    )
    args = parser.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
