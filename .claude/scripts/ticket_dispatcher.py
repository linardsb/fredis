"""Dispatch actionable drafts to the Fredis Review ticket queue.

Called from the heartbeat after Python-side detections (overdue invoices,
silent contacts, stale deals, breached gates). Creates a HubSpot ticket +
posts to Slack when a matching open ticket doesn't already exist.

Gated behind HUBSPOT_TICKETS_ENABLED so the rollout is dark until smoke
tests pass.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from config import (
    DRAFTS_ACTIVE_DIR,
    HUBSPOT_HUB_ID,
    HUBSPOT_TICKETS_ENABLED,
    HUBSPOT_TICKETS_PIPELINE_NAME,
    HUBSPOT_TICKETS_REOPEN_DAYS,
    HUBSPOT_TICKETS_SLACK_CHANNEL,
    PROJECT_ROOT,
)


def stable_dedupe_key(skill_source: str, subject: str, draft_path: str) -> str:
    """Deterministic 16-char hash. Callers MUST use stable subject + draft_path
    (no timestamps / run IDs in the hash input) or dedupe breaks on repeat ticks.
    """
    text = f"{skill_source}|{subject}|{draft_path}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def hubspot_ticket_url(ticket_id: str) -> str:
    """HubSpot-hosted URL for a ticket. Falls back to a path-only URL when
    HUBSPOT_HUB_ID isn't configured (unlikely but handle gracefully).
    """
    if HUBSPOT_HUB_ID:
        return f"https://app.hubspot.com/contacts/{HUBSPOT_HUB_ID}/ticket/{ticket_id}"
    return f"https://app.hubspot.com/ticket/{ticket_id}"


_SLUG_RE = re.compile(r"[^a-zA-Z0-9-]+")


def _slugify(value: str) -> str:
    slug = _SLUG_RE.sub("-", value).strip("-").lower()
    return slug or "unknown"


def write_heartbeat_draft(
    alert_type: str,
    entity_id: str,
    title: str,
    body: str,
) -> str:
    """Write a stable-name heartbeat draft and return the repo-relative path.

    The filename is `<alert_type>-<slugified-entity_id>.md` — deterministic
    per alert+entity so repeat ticks overwrite the same file instead of
    creating duplicates. Returns the repo-relative path string (what gets
    stored on the ticket's `draft_path` property).
    """
    target_dir = DRAFTS_ACTIVE_DIR / "heartbeat"
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{_slugify(alert_type)}-{_slugify(entity_id)}.md"
    target = target_dir / filename
    target.write_text(
        (
            f"---\n"
            f"alert_type: {alert_type}\n"
            f"entity_id: {entity_id}\n"
            f"title: {title}\n"
            f"---\n\n"
            f"{body}\n"
        ),
        encoding="utf-8",
    )
    return str(target.relative_to(PROJECT_ROOT))


def dispatch_ticket(
    *,
    subject: str,
    content: str,
    lane: str,
    skill_source: str,
    urgency: str,
    draft_path: str,
    heartbeat_run_id: str | None = None,
    slack_thread_url: str | None = None,
    contact_ids: list[str] | None = None,
    company_ids: list[str] | None = None,
    deal_ids: list[str] | None = None,
    dedupe_anchor: str | None = None,
) -> dict[str, Any]:
    """Idempotent dispatch — create ticket + Slack post only when no open /
    recent-closed ticket already exists for this dedupe key.

    `dedupe_anchor` overrides `draft_path` in the dedupe-key calculation
    when the draft_path itself is volatile (e.g. date-stamped filenames
    for gate breaches). Callers that use stable filenames can leave it
    unset — default falls back to draft_path.

    Return shape:
        {"skipped": "flag_off"}                         — feature flag off
        {"skipped": "dedupe_open", "ticket_id": ...}    — open match found
        {"skipped": "dedupe_recent", "ticket_id": ...}  — recent closed match
        {"created": True, "ticket_id": ...}             — new ticket created
        {"created": True, "ticket_id": ..., "slack_error": ...}  — ticket ok,
                                                          Slack post failed
        {"error": "<msg>"}                              — create failed
    """
    if not HUBSPOT_TICKETS_ENABLED:
        return {"skipped": "flag_off"}

    # Imports held inside the function so the flag-off path never reaches
    # out to hubspot_api (keeps heartbeat startup cheap + tests simple).
    from integrations.hubspot_api import (
        create_ticket,
        search_tickets_by_dedupe_key,
    )

    dedupe_key = stable_dedupe_key(
        skill_source, subject, dedupe_anchor or draft_path
    )

    # Open tickets with same key → skip outright.
    try:
        open_hits = search_tickets_by_dedupe_key(
            dedupe_key,
            open_only=True,
            pipeline_name=HUBSPOT_TICKETS_PIPELINE_NAME,
        )
    except Exception as e:
        return {"error": f"dedupe search (open): {e}"}
    if open_hits:
        return {"skipped": "dedupe_open", "ticket_id": open_hits[0].id}

    # Closed tickets — skip if any closed within the reopen window.
    try:
        all_hits = search_tickets_by_dedupe_key(
            dedupe_key,
            open_only=False,
            pipeline_name=HUBSPOT_TICKETS_PIPELINE_NAME,
        )
    except Exception as e:
        return {"error": f"dedupe search (closed): {e}"}
    if all_hits:
        now = datetime.now(UTC)
        for t in all_hits:
            raw_last = t.properties.get("hs_lastmodifieddate")
            if not raw_last:
                continue
            try:
                last_dt = datetime.fromisoformat(
                    str(raw_last).replace("Z", "+00:00")
                )
            except ValueError:
                continue
            if (now - last_dt).days < HUBSPOT_TICKETS_REOPEN_DAYS:
                return {"skipped": "dedupe_recent", "ticket_id": t.id}

    # Create fresh ticket.
    try:
        created = create_ticket(
            subject=subject,
            content=content,
            lane=lane,
            skill_source=skill_source,
            urgency=urgency,
            draft_path=draft_path,
            dedupe_key=dedupe_key,
            heartbeat_run_id=heartbeat_run_id,
            slack_thread_url=slack_thread_url,
            contact_ids=contact_ids,
            company_ids=company_ids,
            deal_ids=deal_ids,
            pipeline_name=HUBSPOT_TICKETS_PIPELINE_NAME,
        )
    except Exception as e:
        return {"error": f"create_ticket: {e}"}

    # Slack post — non-blocking. A Slack failure after ticket create is a
    # nuisance, not a reason to roll back.
    slack_error: str | None = None
    try:
        from integrations.slack_api import send_notification

        msg = _format_slack_message(
            subject=subject,
            lane=lane,
            skill_source=skill_source,
            urgency=urgency,
            draft_path=draft_path,
            ticket_id=created.id,
        )
        send_notification(HUBSPOT_TICKETS_SLACK_CHANNEL, msg)
    except Exception as e:
        slack_error = str(e)

    result: dict[str, Any] = {"created": True, "ticket_id": created.id}
    if slack_error is not None:
        result["slack_error"] = slack_error
    return result


def _format_slack_message(
    *,
    subject: str,
    lane: str,
    skill_source: str,
    urgency: str,
    draft_path: str,
    ticket_id: str,
) -> str:
    lines = [
        f"[DRAFT] {subject}",
        f"Lane: {lane} · Urgency: {urgency} · Skill: {skill_source}",
    ]
    if draft_path:
        lines.append(f"Draft: {draft_path}")
    lines.append(f"Ticket: {hubspot_ticket_url(ticket_id)}")
    return "\n".join(lines)


__all__ = [
    "dispatch_ticket",
    "hubspot_ticket_url",
    "stable_dedupe_key",
    "write_heartbeat_draft",
]
