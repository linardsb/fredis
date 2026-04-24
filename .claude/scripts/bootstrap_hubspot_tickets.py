"""
Bootstrap HubSpot Tickets schema for the Fredis Review queue.

Idempotent: every operation first checks whether the target resource already
exists. Safe to re-run after partial failure.

Usage:
    uv run python bootstrap_hubspot_tickets.py --dry-run    # print planned ops, no writes
    uv run python bootstrap_hubspot_tickets.py              # live — create missing resources

What it creates:
    - Ticket pipeline "Fredis Review" with 5 stages (Drafted → In review →
      Needs send → Actioned / Rejected)
    - Ticket custom properties: lane, skill_source, draft_path, urgency,
      slack_thread_url, heartbeat_run_id, dedupe_key

Skipped automatically when already present. Prints a summary at the end.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from integrations import hubspot_api  # noqa: E402

# ---------------------------------------------------------------------------
# Pipeline spec
# ---------------------------------------------------------------------------

FREDIS_REVIEW_PIPELINE_NAME = "Fredis Review"

# Ticket pipeline stages use `ticketState` (OPEN / CLOSED) in metadata.
# `probability` / `isClosed` are included for cross-compatibility — HubSpot
# accepts them but only `ticketState` is semantically meaningful for tickets.
FREDIS_REVIEW_STAGES: list[dict[str, Any]] = [
    {"label": "Drafted", "displayOrder": 0,
     "metadata": {"ticketState": "OPEN", "isClosed": "false", "probability": "0.1"}},
    {"label": "In review", "displayOrder": 1,
     "metadata": {"ticketState": "OPEN", "isClosed": "false", "probability": "0.3"}},
    {"label": "Needs send", "displayOrder": 2,
     "metadata": {"ticketState": "OPEN", "isClosed": "false", "probability": "0.7"}},
    {"label": "Actioned", "displayOrder": 3,
     "metadata": {"ticketState": "CLOSED", "isClosed": "true", "probability": "1.0"}},
    {"label": "Rejected", "displayOrder": 4,
     "metadata": {"ticketState": "CLOSED", "isClosed": "true", "probability": "0.0"}},
]


# ---------------------------------------------------------------------------
# Custom ticket properties
# ---------------------------------------------------------------------------

LANE_OPTIONS: list[dict[str, Any]] = [
    {"label": "Email Hub", "value": "email_hub", "displayOrder": 0},
    {"label": "VTV", "value": "vtv", "displayOrder": 1},
    {"label": "Cab", "value": "cab", "displayOrder": 2},
    {"label": "Content", "value": "content", "displayOrder": 3},
    {"label": "Ops", "value": "ops", "displayOrder": 4},
    {"label": "Client", "value": "client", "displayOrder": 5},
    {"label": "Admin", "value": "admin", "displayOrder": 6},
]

SKILL_SOURCE_VALUES: list[str] = [
    "heartbeat",
    "integrations",
    "content-social",
    "content-artifacts",
    "launch-governance",
    "idea-validation",
    "product-shape",
    "engineering",
    "product-management",
    "technical-leadership",
    "executive-leadership",
    "data-and-experimentation",
    "ciso-advisor",
    "security-engineering",
    "ip-overhang-guard",
    "business-cycle-analyst",
    "org-design",
    "robotics-engineer",
    "obsidian-vault-structure",
    "phase1-ready",
    "skill-creator",
    # Phase 12 starter-pack skills (2026-04-23)
    "draft-reply",
    "meeting-notes",
    "client-log",
    "uk-latvia-context",
]

SKILL_SOURCE_OPTIONS: list[dict[str, Any]] = [
    {"label": v, "value": v, "displayOrder": i}
    for i, v in enumerate(SKILL_SOURCE_VALUES)
]

URGENCY_OPTIONS: list[dict[str, Any]] = [
    {"label": "Today", "value": "today", "displayOrder": 0},
    {"label": "This week", "value": "this_week", "displayOrder": 1},
    {"label": "Whenever", "value": "whenever", "displayOrder": 2},
]


TICKET_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "lane",
        "label": "Lane",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "ticketinformation",
        "description": "Which Fredis lane this ticket belongs to.",
        "options": LANE_OPTIONS,
    },
    {
        "name": "skill_source",
        "label": "Skill source",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "ticketinformation",
        "description": "Which Fredis skill or subsystem created this ticket.",
        "options": SKILL_SOURCE_OPTIONS,
    },
    {
        "name": "draft_path",
        "label": "Draft path",
        "type": "string",
        "fieldType": "text",
        "groupName": "ticketinformation",
        "description": (
            "Repo-relative path to the draft this ticket wraps "
            "(e.g. Fredis/Memory/drafts/active/<skill>/<file>.md)."
        ),
    },
    {
        "name": "urgency",
        "label": "Urgency",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "ticketinformation",
        "description": "How soon this ticket needs Linards's attention.",
        "options": URGENCY_OPTIONS,
    },
    {
        "name": "slack_thread_url",
        "label": "Slack thread URL",
        "type": "string",
        "fieldType": "text",
        "groupName": "ticketinformation",
        "description": "Back-link to a Slack thread that spawned this ticket (if any).",
    },
    {
        "name": "heartbeat_run_id",
        "label": "Heartbeat run ID",
        "type": "string",
        "fieldType": "text",
        "groupName": "ticketinformation",
        "description": "Links heartbeat-sourced tickets to a specific run in the daily log.",
    },
    {
        "name": "dedupe_key",
        "label": "Dedupe key",
        "type": "string",
        "fieldType": "text",
        "groupName": "ticketinformation",
        "description": (
            "Deterministic hash of skill_source + subject + draft_path. "
            "Used by heartbeat to prevent duplicate tickets on repeat ticks."
        ),
    },
]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def _pipeline_has_tickets(pipeline_id: str) -> bool:
    """True if any ticket currently references this pipeline."""
    hits = hubspot_api.search_objects(
        "tickets",
        filter_groups=[{
            "filters": [{
                "propertyName": "hs_pipeline",
                "operator": "EQ",
                "value": pipeline_id,
            }],
        }],
        properties=["subject"],
        limit=1,
    )
    return len(hits) > 0


def ensure_pipeline(dry_run: bool) -> tuple[str, bool]:
    """Ensure the Fredis Review ticket pipeline exists. Returns (id, created_bool).

    HubSpot Free caps ticket pipelines at 1. If a single non-matching pipeline
    exists and carries zero tickets, repurpose it in-place rather than failing.
    """
    existing = hubspot_api.list_pipelines("tickets")
    name = FREDIS_REVIEW_PIPELINE_NAME
    for p in existing:
        if p.get("label") == name:
            print(f"  [skip] ticket pipeline '{name}' already exists (id={p.get('id')})")
            return str(p.get("id")), False

    stage_count = len(FREDIS_REVIEW_STAGES)

    # If one other pipeline exists and the portal caps us at 1, try to
    # repurpose it — but only when it's safe (no tickets attached).
    if len(existing) == 1:
        other = existing[0]
        other_id = str(other.get("id", ""))
        other_label = other.get("label", "?")
        if dry_run:
            print(
                f"  [dry] would repurpose existing pipeline '{other_label}' "
                f"(id={other_id}) → '{name}' with {stage_count} stages"
            )
            for s in FREDIS_REVIEW_STAGES:
                state = s["metadata"].get("ticketState", "?")
                print(f"          · {s['label']} ({state})")
            return other_id, False
        if _pipeline_has_tickets(other_id):
            raise RuntimeError(
                f"pipeline '{other_label}' (id={other_id}) has tickets attached — "
                "refusing to repurpose. Archive its tickets manually, then re-run."
            )
        result = hubspot_api.update_pipeline(
            "tickets", other_id, name, FREDIS_REVIEW_STAGES
        )
        pid = str(result.get("id", other_id))
        print(f"  [ok] repurposed pipeline '{other_label}' → '{name}' (id={pid})")
        return pid, True

    if dry_run:
        print(f"  [dry] would create ticket pipeline '{name}' with {stage_count} stages")
        for s in FREDIS_REVIEW_STAGES:
            state = s["metadata"].get("ticketState", "?")
            print(f"          · {s['label']} ({state})")
        return "", False
    result = hubspot_api.create_pipeline("tickets", name, FREDIS_REVIEW_STAGES)
    pid = str(result.get("id", ""))
    print(f"  [ok] created ticket pipeline '{name}' (id={pid})")
    return pid, True


def ensure_properties(
    object_type: str,
    specs: list[dict[str, Any]],
    dry_run: bool,
) -> tuple[int, int]:
    """Ensure each property spec exists for the given object type.

    Returns (created_count, skipped_count).
    """
    existing_by_name: dict[str, dict[str, Any]] = {
        p["name"]: p for p in hubspot_api.list_properties(object_type) if p.get("name")
    }
    created = skipped = 0
    for spec in specs:
        name = spec["name"]
        if name in existing_by_name:
            # Enum options evolve (new skill values added). Diff and patch if needed.
            desired = spec.get("options") or []
            if desired:
                current = existing_by_name[name].get("options") or []
                desired_values = {o["value"] for o in desired}
                current_values = {o.get("value") for o in current if isinstance(o, dict)}
                missing = desired_values - current_values
                if missing:
                    if dry_run:
                        print(
                            f"  [dry] would patch {object_type} property '{name}' — "
                            f"add {len(missing)} option(s): {sorted(missing)}"
                        )
                    else:
                        hubspot_api.update_property(
                            object_type, name, {"options": desired}
                        )
                        print(
                            f"  [ok] patched {object_type} property '{name}' — "
                            f"added {len(missing)} option(s): {sorted(missing)}"
                        )
                    skipped += 1
                    continue
            print(f"  [skip] {object_type} property '{name}' already exists")
            skipped += 1
            continue
        if dry_run:
            kind = f"{spec['type']}/{spec['fieldType']}"
            print(f"  [dry] would create {object_type} property '{name}' ({kind})")
            if spec.get("options"):
                opts = ", ".join(o["value"] for o in spec["options"])
                print(f"          options: {opts}")
            created += 1
            continue
        hubspot_api.create_property(object_type, spec)
        print(f"  [ok] created {object_type} property '{name}'")
        created += 1
    return created, skipped


def main(dry_run: bool) -> int:
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"=== HubSpot tickets bootstrap ({mode}) ===\n")

    print("Pipeline:")
    try:
        ensure_pipeline(dry_run)
    except RuntimeError as e:
        # HubSpot Free caps ticket pipelines at 2 — if the cap is hit,
        # surface the error but don't block property creation (which
        # is independent of the pipeline).
        print(f"  [warn] pipeline step skipped: {e}")

    totals: dict[str, tuple[int, int]] = {}
    print("\nTickets properties:")
    try:
        totals["tickets"] = ensure_properties("tickets", TICKET_PROPERTIES, dry_run)
    except RuntimeError as e:
        print(f"  [warn] tickets properties step errored: {e}")
        totals["tickets"] = (0, 0)

    print("\n=== Summary ===")
    for ot, (c, s) in totals.items():
        print(f"  {ot}: {c} created/planned, {s} skipped")
    if dry_run:
        print("\nNothing written. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap HubSpot tickets schema")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned operations without writing to HubSpot.")
    args = parser.parse_args()
    raise SystemExit(main(dry_run=args.dry_run))
