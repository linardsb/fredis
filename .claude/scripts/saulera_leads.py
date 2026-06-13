"""Detect saulera contact-form leads in Gmail.

The saulera site (functions/api/contact.js) emails each contact-form
submission via Resend to hello@saulera.com, which Cloudflare Email Routing
forwards to the inbox Fredis already polls. The mail arrives from
``form@saulera.com`` with subject ``New enquiry — <name>`` and a fixed
plain-text body:

    New message from the saulera contact form

    Name:  <name>
    Email: <visitor email>

    <message or "(no message)">

This module queries Gmail for those mails and parses out the lead. The
heartbeat (``_dispatch_review_tickets``) turns each into a HubSpot Review
ticket + Slack ``[DRAFT]`` notice, deduped on the Gmail message id so a lead
tickets exactly once across repeat ticks.

SECURITY: the message text is attacker-controlled (public web form). It is
NEVER injected into the heartbeat's Claude-reasoning prompt — only written to
a human-reviewed draft file and the HubSpot ticket. Keep it that way.

CLI (testing only — never dispatches):
    uv run python saulera_leads.py --hours 24
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SAULERA_FORM_SENDER = "form@saulera.com"
SAULERA_SUBJECT_PREFIX = "New enquiry"
SAULERA_GMAIL_QUERY = f'from:{SAULERA_FORM_SENDER} subject:"{SAULERA_SUBJECT_PREFIX}"'

# Name/email are read from the body's labelled lines — the most reliable
# source, since they're message content and survive forwarding intact.
# No trailing `$` anchor: it would miss CRLF line endings (the `\r` sits
# between the value and the `\n`). `\S+`/`.+` stop at the `\r` naturally.
_NAME_RE = re.compile(r"^Name:\s*(.+)", re.MULTILINE)
_EMAIL_RE = re.compile(r"^Email:\s*(\S+@\S+)", re.MULTILINE)


@dataclass
class SauleraLead:
    """A parsed saulera contact-form submission."""

    name: str
    email: str
    message: str
    message_id: str
    thread_id: str
    received_at: datetime


def _name_from_subject(subject: str) -> str:
    """Fallback name source: the suffix after the dash in 'New enquiry — Jane'."""
    for sep in ("—", "–", "-"):
        if sep in subject:
            tail = subject.split(sep, 1)[1].strip()
            if tail:
                return tail
    return subject.strip()


def parse_lead_fields(subject: str, body: str) -> tuple[str, str, str]:
    """Parse (name, email, message) from a saulera contact-form email.

    Name falls back to the subject suffix. Email has no fallback — a mail with
    no parseable address returns an empty email and the caller drops it (better
    a missed lead than a ticket no one can reply to). Message is everything
    after the Email line, normalised to "(no message)" when blank.
    """
    body = body or ""
    name_m = _NAME_RE.search(body)
    email_m = _EMAIL_RE.search(body)

    name = (name_m.group(1).strip() if name_m else "") or _name_from_subject(subject)
    email = email_m.group(1).strip().lower() if email_m else ""

    message = body[email_m.end():].strip() if email_m else ""
    if not message:
        message = "(no message)"
    return name, email, message


def fetch_saulera_leads(hours_ago: int = 6, max_results: int = 25) -> list[SauleraLead]:
    """Return saulera contact-form leads from the last ``hours_ago`` hours.

    Gmail's ``after:`` filter is day-precision, so same-day mails all match;
    the heartbeat's message-id dedupe makes repeated processing harmless.
    """
    from integrations.gmail import get_email_details, get_gmail_service, list_emails

    matches = list_emails(
        max_results=max_results,
        query=SAULERA_GMAIL_QUERY,
        hours_ago=hours_ago,
    )
    if not matches:
        return []

    service = get_gmail_service()
    leads: list[SauleraLead] = []
    for m in matches:
        # Gmail's text query is fuzzy; pin to the exact sender defensively.
        if SAULERA_FORM_SENDER not in m.sender_email.lower():
            continue
        full = get_email_details(service, m.id, include_body=True)
        if not full:
            continue
        name, email, message = parse_lead_fields(full.subject, full.body or "")
        if not email:
            continue
        leads.append(
            SauleraLead(
                name=name,
                email=email,
                message=message,
                message_id=full.id,
                thread_id=full.thread_id,
                received_at=full.date,
            )
        )
    return leads


def _main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect saulera contact-form leads (read-only; never dispatches)."
    )
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()

    leads = fetch_saulera_leads(hours_ago=args.hours)
    if not leads:
        print(f"No saulera leads in the last {args.hours}h.")
        return 0

    print(f"Found {len(leads)} saulera lead(s) in the last {args.hours}h:\n")
    for ld in leads:
        print(f"- {ld.name} <{ld.email}>  ({ld.received_at:%Y-%m-%d %H:%M})")
        print(f"    msg_id={ld.message_id}")
        preview = ld.message.replace("\n", " ")
        if len(preview) > 120:
            preview = preview[:120] + "…"
        print(f"    ask: {preview}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
