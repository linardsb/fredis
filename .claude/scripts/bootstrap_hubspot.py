"""
Bootstrap HubSpot CRM schema for the Second Brain.

Idempotent: every operation first checks whether the target resource already
exists. Safe to re-run after partial failure.

Usage:
    uv run python bootstrap_hubspot.py --dry-run    # print planned ops, no writes
    uv run python bootstrap_hubspot.py              # live — create missing resources

What it creates:
    - Deal pipeline "Consultancy" with 8 stages
    - Contact custom properties: urgent_alert, conflict_node, conflict_reason,
      preferred_channel
    - Company custom properties: engagement_type, retainer_gbp_mo, contract_end_date
    - Deal custom properties: service_line, source, currency

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

CONSULTANCY_PIPELINE_NAME = "Consultancy"
CONSULTANCY_STAGES: list[dict[str, Any]] = [
    {"label": "Inbound", "displayOrder": 0,
     "metadata": {"probability": "0.1", "isClosed": "false"}},
    {"label": "Discovery", "displayOrder": 1,
     "metadata": {"probability": "0.2", "isClosed": "false"}},
    {"label": "Proposal", "displayOrder": 2,
     "metadata": {"probability": "0.4", "isClosed": "false"}},
    {"label": "Signed", "displayOrder": 3,
     "metadata": {"probability": "0.7", "isClosed": "false"}},
    {"label": "Kickoff", "displayOrder": 4,
     "metadata": {"probability": "0.85", "isClosed": "false"}},
    {"label": "Delivery", "displayOrder": 5,
     "metadata": {"probability": "0.9", "isClosed": "false"}},
    {"label": "Invoice", "displayOrder": 6,
     "metadata": {"probability": "0.95", "isClosed": "false"}},
    {"label": "Post-delivery", "displayOrder": 7,
     "metadata": {"probability": "1.0", "isClosed": "true"}},
]


# ---------------------------------------------------------------------------
# Custom-property specs
# ---------------------------------------------------------------------------

CONTACT_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "urgent_alert",
        "label": "Urgent alert",
        "type": "bool",
        "fieldType": "booleancheckbox",
        "groupName": "contactinformation",
        "description": "Flag contacts who need urgent follow-up when silent.",
        "options": [
            {"label": "Yes", "value": "true", "displayOrder": 0},
            {"label": "No", "value": "false", "displayOrder": 1},
        ],
    },
    {
        "name": "conflict_node",
        "label": "Conflict node",
        "type": "bool",
        "fieldType": "booleancheckbox",
        "groupName": "contactinformation",
        "description": "Marks contacts where there's an active conflict or sensitive context.",
        "options": [
            {"label": "Yes", "value": "true", "displayOrder": 0},
            {"label": "No", "value": "false", "displayOrder": 1},
        ],
    },
    {
        "name": "conflict_reason",
        "label": "Conflict reason",
        "type": "string",
        "fieldType": "textarea",
        "groupName": "contactinformation",
        "description": "Plain-text explanation of the conflict, if any.",
    },
    {
        "name": "preferred_channel",
        "label": "Preferred channel",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "contactinformation",
        "options": [
            {"label": "WhatsApp", "value": "whatsapp", "displayOrder": 0},
            {"label": "Email", "value": "email", "displayOrder": 1},
            {"label": "Slack", "value": "slack", "displayOrder": 2},
            {"label": "Facebook DM", "value": "facebook_dm", "displayOrder": 3},
        ],
    },
]

COMPANY_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "engagement_type",
        "label": "Engagement type",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "companyinformation",
        "options": [
            {"label": "Retainer", "value": "retainer", "displayOrder": 0},
            {"label": "Project", "value": "project", "displayOrder": 1},
            {"label": "Prospect", "value": "prospect", "displayOrder": 2},
            {"label": "Dormant", "value": "dormant", "displayOrder": 3},
        ],
    },
    {
        "name": "retainer_gbp_mo",
        "label": "Retainer (GBP/mo)",
        "type": "number",
        "fieldType": "number",
        "groupName": "companyinformation",
        "description": "Monthly retainer in GBP, when applicable.",
    },
    {
        "name": "contract_end_date",
        "label": "Contract end date",
        "type": "date",
        "fieldType": "date",
        "groupName": "companyinformation",
    },
]

DEAL_PROPERTIES: list[dict[str, Any]] = [
    {
        "name": "service_line",
        "label": "Service line",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "dealinformation",
        "options": [
            {"label": "AI-agentic build", "value": "ai_agentic", "displayOrder": 0},
            {"label": "Custom app", "value": "custom_app", "displayOrder": 1},
            {"label": "SaaS", "value": "saas", "displayOrder": 2},
            {"label": "Marketing-ops", "value": "marketing_ops", "displayOrder": 3},
            {"label": "Agri×AI", "value": "agri_ai", "displayOrder": 4},
            {"label": "Advisory", "value": "advisory", "displayOrder": 5},
        ],
    },
    {
        "name": "source",
        "label": "Source",
        "type": "enumeration",
        "fieldType": "select",
        "groupName": "dealinformation",
        "options": [
            {"label": "Cold outreach", "value": "cold", "displayOrder": 0},
            {"label": "Inbound", "value": "inbound", "displayOrder": 1},
            {"label": "Referral", "value": "referral", "displayOrder": 2},
            {"label": "Content", "value": "content", "displayOrder": 3},
        ],
    },
    # Note: HubSpot has a built-in `deal_currency_code` property that covers
    # currency natively — no need to add a custom enum.
]


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def ensure_pipeline(dry_run: bool) -> tuple[str, bool]:
    """Ensure the Consultancy pipeline exists. Returns (id, created_bool)."""
    existing = hubspot_api.list_pipelines("deals")
    name = CONSULTANCY_PIPELINE_NAME
    for p in existing:
        if p.get("label") == name:
            print(f"  [skip] pipeline '{name}' already exists (id={p.get('id')})")
            return str(p.get("id")), False
    if dry_run:
        print(f"  [dry] would create pipeline '{name}' with {len(CONSULTANCY_STAGES)} stages")
        return "", False
    result = hubspot_api.create_pipeline("deals", name, CONSULTANCY_STAGES)
    pid = str(result.get("id", ""))
    print(f"  [ok] created pipeline '{name}' (id={pid})")
    return pid, True


def ensure_properties(
    object_type: str,
    specs: list[dict[str, Any]],
    dry_run: bool,
) -> tuple[int, int]:
    """Ensure each property spec exists for the given object type.

    Returns (created_count, skipped_count).
    """
    existing_names = {p.get("name") for p in hubspot_api.list_properties(object_type)}
    created = skipped = 0
    for spec in specs:
        name = spec["name"]
        if name in existing_names:
            print(f"  [skip] {object_type} property '{name}' already exists")
            skipped += 1
            continue
        if dry_run:
            kind = f"{spec['type']}/{spec['fieldType']}"
            print(f"  [dry] would create {object_type} property '{name}' ({kind})")
            created += 1
            continue
        hubspot_api.create_property(object_type, spec)
        print(f"  [ok] created {object_type} property '{name}'")
        created += 1
    return created, skipped


def main(dry_run: bool) -> int:
    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"=== HubSpot bootstrap ({mode}) ===\n")

    print("Pipeline:")
    try:
        ensure_pipeline(dry_run)
    except RuntimeError as e:
        # HubSpot Free caps custom pipelines at 1 — if a default already
        # exists, creation fails. Properties don't depend on the pipeline,
        # so continue. Rename / reshape the default pipeline in the UI later.
        print(f"  [warn] pipeline step skipped: {e}")

    totals: dict[str, tuple[int, int]] = {}
    for ot, specs in (
        ("contacts", CONTACT_PROPERTIES),
        ("companies", COMPANY_PROPERTIES),
        ("deals", DEAL_PROPERTIES),
    ):
        print(f"\n{ot.title()} properties:")
        try:
            totals[ot] = ensure_properties(ot, specs, dry_run)
        except RuntimeError as e:
            # Don't bail — partial progress is useful; next run will catch up.
            print(f"  [warn] {ot} properties step errored: {e}")
            totals[ot] = (0, 0)

    print("\n=== Summary ===")
    for ot, (c, s) in totals.items():
        print(f"  {ot}: {c} created/planned, {s} skipped")
    if dry_run:
        print("\nNothing written. Re-run without --dry-run to apply.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bootstrap HubSpot schema")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned operations without writing to HubSpot.")
    args = parser.parse_args()
    raise SystemExit(main(dry_run=args.dry_run))
