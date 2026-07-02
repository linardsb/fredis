"""
Interactive CLI wrapper for direct platform integrations.

Used by the direct-integrations Claude Code skill to query Gmail, Calendar,
Slack, Google Sheets, Google Docs, and Google Drive from interactive sessions.

Usage:
    python query.py gmail list --max 5
    python query.py calendar today
    python query.py slack channels
    python query.py sheets read <spreadsheet_id> [--range "Sheet1!A1:Z100"]
    python query.py docs read <document_id>
    python query.py drive find "search term" [--type spreadsheet]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def cmd_gmail(args: argparse.Namespace) -> None:
    """Handle Gmail commands."""
    from integrations.gmail import (
        check_for_urgent_emails,
        create_gmail_draft,
        create_gmail_draft_from_file,
        download_attachment,
        format_emails_for_context,
        format_thread_for_context,
        get_email_details,
        get_gmail_service,
        get_thread_messages,
        get_unread_count,
        list_attachments,
        list_emails,
    )

    if args.action == "list":
        # Default to 24h window when no query specified (recent inbox view)
        # but no time filter when searching (user wants to find old emails too)
        hours = args.hours if args.hours is not None else (None if args.query else 24)
        emails = list_emails(
            max_results=args.max,
            query=args.query or "",
            unread_only=args.unread,
            hours_ago=hours,
        )
        print(format_emails_for_context(emails))

    elif args.action == "urgent":
        urgent = check_for_urgent_emails(hours_ago=args.hours)
        if urgent:
            print(f"Found {len(urgent)} potentially urgent emails:\n")
            print(format_emails_for_context(urgent))
        else:
            print("No urgent emails found")

    elif args.action == "unread":
        count = get_unread_count()
        print(f"Unread emails: {count}")

    elif args.action == "read":
        if not args.message_id:
            print("Error: message_id required for read command")
            sys.exit(1)
        service = get_gmail_service()
        email = get_email_details(service, args.message_id, include_body=True)
        if email:
            print(f"Subject: {email.subject}")
            print(f"From: {email.sender} <{email.sender_email}>")
            print(f"Date: {email.date}")
            print(f"Labels: {', '.join(email.labels)}")
            print(f"\n{email.body or email.snippet}")
        else:
            print("Email not found")

    elif args.action == "thread":
        if not args.message_id:
            print("Error: thread_id required for thread command")
            sys.exit(1)
        emails = get_thread_messages(args.message_id)
        print(format_thread_for_context(emails))

    elif args.action == "search":
        if not args.message_id:
            print("Error: search query required for search command")
            sys.exit(1)
        emails = list_emails(
            max_results=args.max,
            query=args.message_id,
        )
        print(format_emails_for_context(emails))

    elif args.action == "attachments":
        if not args.message_id:
            print("Error: message_id required for attachments command")
            sys.exit(1)
        atts = list_attachments(args.message_id)
        if not atts:
            print("No attachments found on this message.")
        else:
            print(f"Found {len(atts)} attachment(s):\n")
            for a in atts:
                size_kb = a.size / 1024
                print(f"  - {a.filename} ({a.mime_type}, {size_kb:.1f} KB)")
                print(f"    attachment_id: {a.id}")

    elif args.action == "download-attachment":
        if not args.message_id:
            print("Error: message_id required for download-attachment command")
            sys.exit(1)
        att_id = getattr(args, "attachment_id", None)
        if not att_id:
            print("Error: --attachment-id required for download-attachment command")
            sys.exit(1)
        # Determine output path
        output_dir = Path(getattr(args, "output_dir", None) or ".")
        # Get filename from the attachment metadata
        atts = list_attachments(args.message_id)
        filename = "attachment"
        for a in atts:
            if a.id == att_id:
                filename = a.filename
                break
        output_path = output_dir / filename
        result_path = download_attachment(args.message_id, att_id, output_path)
        print(f"Downloaded: {result_path}")

    elif args.action == "create-draft":
        from_file = getattr(args, "from_file", None)
        if from_file:
            # Read everything from the markdown draft file
            result = create_gmail_draft_from_file(from_file)
        else:
            # Manual mode: all args required
            to = getattr(args, "to", None)
            subject = getattr(args, "draft_subject", None)
            body = getattr(args, "body", None)
            thread_id = getattr(args, "thread_id", None)
            msg_id = args.message_id
            if not to or not subject or not body:
                print("Error: --from-file or (--to, --subject, --body) required")
                sys.exit(1)
            attachment_list = getattr(args, "attachment", None) or []
            result = create_gmail_draft(
                to=to,
                subject=subject,
                body=body,
                thread_id=thread_id,
                message_id=msg_id,
                attachments=attachment_list if attachment_list else None,
            )
        print(json.dumps(result, indent=2))


def cmd_calendar(args: argparse.Namespace) -> None:
    """Handle Calendar commands."""
    from integrations.calendar_api import (
        check_for_upcoming_meetings,
        format_events_for_context,
        get_today_events,
        get_upcoming_events,
    )

    if args.action == "today":
        events = get_today_events()
        print(format_events_for_context(events))

    elif args.action == "upcoming":
        events = get_upcoming_events(hours_ahead=args.hours)
        print(format_events_for_context(events))

    elif args.action == "soon":
        events = check_for_upcoming_meetings(hours_ahead=4)
        print(format_events_for_context(events))


def cmd_slack(args: argparse.Namespace) -> None:
    """Handle Slack commands."""
    from integrations.slack_api import (
        check_for_important_messages,
        format_messages_for_context,
        get_channel_id,
        get_recent_messages,
        get_slack_client,
        send_notification,
        update_message,
    )

    if args.action == "channels":
        client = get_slack_client()
        result = client.conversations_list(types="public_channel", limit=100)
        for ch in result.get("channels", []):
            print(f"  #{ch['name']} ({ch['id']})")

    elif args.action == "messages":
        if not args.channel:
            print("Error: channel name required")
            sys.exit(1)
        ch_id = get_channel_id(args.channel)
        if not ch_id:
            print(f"Channel not found: {args.channel}")
            sys.exit(1)
        msgs = get_recent_messages(ch_id, hours_ago=args.hours, limit=20)
        print(format_messages_for_context(msgs))

    elif args.action == "send":
        if not getattr(args, "i_confirm_send", False):
            print(
                "Advisor mode: `slack send` is gated to prevent drift from the draft workflow.\n"
                "Pass --i-confirm-send if you genuinely want this command to post to Slack."
            )
            sys.exit(1)
        if not args.channel or not args.message:
            print("Error: channel and message required")
            sys.exit(1)
        result = send_notification(args.channel, args.message)
        print(f"Sent! (ts={result['ts']})" if result else "Failed to send")

    elif args.action == "update":
        if not args.channel or not args.ts or not args.message:
            print("Error: channel, --ts, and message required")
            sys.exit(1)
        result = update_message(args.channel, args.ts, args.message)
        print(f"Updated! (ts={result['ts']})" if result else "Failed to update")

    elif args.action == "check":
        important, warnings = check_for_important_messages(hours_ago=args.hours)
        for w in warnings:
            print(f"WARN: {w}", file=sys.stderr)
        if important:
            print(f"Found {len(important)} important messages:\n")
            print(format_messages_for_context(important))
        else:
            print("No important messages found")


def cmd_sheets(args: argparse.Namespace) -> None:
    """Handle Google Sheets commands."""
    from integrations.sheets_api import (
        append_to_spreadsheet,
        format_spreadsheet_for_context,
        get_spreadsheet_info,
        read_spreadsheet,
        write_spreadsheet,
    )

    if args.action == "read":
        if not args.target_id:
            print("Error: spreadsheet_id required")
            sys.exit(1)
        data = read_spreadsheet(
            args.target_id,
            range_notation=args.range or "",
            max_rows=args.max_rows,
        )
        print(format_spreadsheet_for_context(data))

    elif args.action == "info":
        if not args.target_id:
            print("Error: spreadsheet_id required")
            sys.exit(1)
        info = get_spreadsheet_info(args.target_id)
        print(format_spreadsheet_for_context(info))

    elif args.action == "write":
        if not args.target_id or not args.values or not args.range:
            print("Error: spreadsheet_id, --range, and --values required")
            sys.exit(1)
        parsed = json.loads(args.values)
        result = write_spreadsheet(args.target_id, args.range, parsed)
        print(json.dumps(result, indent=2))

    elif args.action == "append":
        if not args.target_id or not args.values or not args.range:
            print("Error: spreadsheet_id, --range, and --values required")
            sys.exit(1)
        parsed = json.loads(args.values)
        result = append_to_spreadsheet(args.target_id, args.range, parsed)
        print(json.dumps(result, indent=2))


def cmd_docs(args: argparse.Namespace) -> None:
    """Handle Google Docs commands."""
    from integrations.docs_api import (
        format_document_for_context,
        get_document_info,
        read_document,
    )

    if args.action == "read":
        if not args.target_id:
            print("Error: document_id required")
            sys.exit(1)
        data = read_document(args.target_id)
        print(format_document_for_context(data, max_chars=args.max_chars))

    elif args.action == "info":
        if not args.target_id:
            print("Error: document_id required")
            sys.exit(1)
        data = get_document_info(args.target_id)
        char_count = len(data.body_text)
        print(f"Title: {data.title}")
        print(f"ID: {data.id}")
        print(f"URL: {data.url}")
        print(f"Content length: ~{char_count} chars")


# ---------------------------------------------------------------------------
# HubSpot helpers — key / stage / association resolution
# ---------------------------------------------------------------------------

# Default v4 association typeIds for engagement → target. Source of truth:
# https://developers.hubspot.com/docs/api/crm/associations/v4
_ENGAGEMENT_ASSOC_TYPE_IDS: dict[tuple[str, str], int] = {
    ("notes", "contacts"): 202,
    ("notes", "companies"): 190,
    ("notes", "deals"): 214,
    ("tasks", "contacts"): 204,
    ("tasks", "companies"): 192,
    ("tasks", "deals"): 216,
    ("calls", "contacts"): 194,
    ("calls", "companies"): 182,
    ("calls", "deals"): 206,
    ("meetings", "contacts"): 200,
    ("meetings", "companies"): 188,
    ("meetings", "deals"): 212,
    ("emails", "contacts"): 198,
    ("emails", "companies"): 186,
    ("emails", "deals"): 210,
}

_OBJECT_ASSOC_TYPE_IDS: dict[tuple[str, str], int] = {
    ("contacts", "companies"): 1,
    ("companies", "contacts"): 2,
    ("deals", "companies"): 5,
    ("companies", "deals"): 6,
    ("deals", "contacts"): 3,
    ("contacts", "deals"): 4,
}

_HUBSPOT_PRIMARY_KEY: dict[str, str] = {
    "contacts": "email",
    "companies": "domain",
    "deals": "dealname",
}

_HUBSPOT_TYPE_ALIASES: dict[str, str] = {
    "contact": "contacts",
    "contacts": "contacts",
    "company": "companies",
    "companies": "companies",
    "deal": "deals",
    "deals": "deals",
}


def _hubspot_normalize_type(t: str) -> str:
    """Singular or plural → plural HubSpot object type."""
    norm = _HUBSPOT_TYPE_ALIASES.get(t.lower())
    if norm is None:
        raise ValueError(f"Unknown object type '{t}'. Use contact/company/deal.")
    return norm


def _hubspot_resolve_key(object_type: str, key: str) -> str:
    """Resolve email / domain / dealname → HubSpot ID. Pure digits pass through."""
    from integrations.hubspot_api import search_objects

    if key.isdigit():
        return key
    pk = _HUBSPOT_PRIMARY_KEY[object_type]
    matches = search_objects(
        object_type,
        [{"filters": [{"propertyName": pk, "operator": "EQ", "value": key}]}],
        limit=2,
    )
    if not matches:
        raise ValueError(f"No {object_type[:-1]} with {pk}='{key}'.")
    if len(matches) > 1:
        ids = ", ".join(m.id for m in matches)
        raise ValueError(
            f"Found {len(matches)} {object_type} matching '{key}' "
            f"(IDs: {ids}); use the HubSpot ID instead."
        )
    return matches[0].id


def _hubspot_pipeline(pipeline_name: str = "Consultancy") -> dict[str, Any]:
    """Look up a deal pipeline by case-insensitive label, fall back to the first."""
    from integrations.hubspot_api import list_pipelines

    pipelines = list_pipelines("deals")
    if not pipelines:
        raise ValueError("No deal pipelines defined in HubSpot.")
    for p in pipelines:
        if str(p.get("label", "")).lower() == pipeline_name.lower():
            return p
    return pipelines[0]


def _hubspot_resolve_stage_id(
    stage_label: str, pipeline_name: str = "Consultancy"
) -> str:
    """Case-insensitive stage label → internal stage ID."""
    pipe = _hubspot_pipeline(pipeline_name)
    for s in pipe.get("stages", []):
        if str(s.get("label", "")).lower() == stage_label.lower():
            return str(s.get("id", ""))
    raise ValueError(
        f"Stage '{stage_label}' not in pipeline '{pipe.get('label')}'."
    )


def _hubspot_resolve_closed_stage_id(
    status: str, pipeline_name: str = "Consultancy"
) -> str:
    """Find the closed-won (highest probability) or closed-lost (zero/lost label) stage ID."""
    pipe = _hubspot_pipeline(pipeline_name)
    closed = [
        s for s in pipe.get("stages", [])
        if str(s.get("metadata", {}).get("isClosed", "")).lower() == "true"
    ]
    if not closed:
        raise ValueError(
            f"Pipeline '{pipe.get('label')}' has no closed stages — "
            f"mark a stage closed in HubSpot UI first."
        )
    if status == "won":
        won = max(
            closed,
            key=lambda s: float(s.get("metadata", {}).get("probability", 0) or 0),
        )
        return str(won.get("id", ""))
    if status == "lost":
        lost = [
            s for s in closed
            if float(s.get("metadata", {}).get("probability", 0) or 0) == 0
            or "lost" in str(s.get("label", "")).lower()
        ]
        if not lost:
            raise ValueError(
                f"No closed-lost stage in '{pipe.get('label')}' — "
                f"add one in HubSpot UI first."
            )
        return str(lost[0].get("id", ""))
    raise ValueError(f"--as must be 'won' or 'lost', got '{status}'.")


def _hubspot_engagement_assoc(
    engagement_type: str, target_type: str, target_id: str
) -> list[dict[str, Any]]:
    """Build the v4 associations payload for an engagement (note/task/call/...)."""
    from integrations.hubspot_api import build_associations

    type_id = _ENGAGEMENT_ASSOC_TYPE_IDS.get((engagement_type, target_type))
    if type_id is None:
        raise ValueError(
            f"No default association typeId for {engagement_type}→{target_type}."
        )
    return build_associations([(target_type, target_id, type_id)])


def _hubspot_parse_about(about: str) -> tuple[str, str]:
    """Parse '<type>:<key>' → (plural_type, key)."""
    if ":" not in about:
        raise ValueError(
            "expected '<type>:<key>' (e.g. contact:tim@walking.vc, deal:Acme)."
        )
    t, k = about.split(":", 1)
    return _hubspot_normalize_type(t), k.strip()


def _bool_arg(val: str | None) -> str | None:
    """Argparse-friendly bool: 'true'/'false'/'yes'/'no'/'1'/'0' → 'true'/'false'."""
    if val is None:
        return None
    v = val.strip().lower()
    if v in ("true", "yes", "1", "y"):
        return "true"
    if v in ("false", "no", "0", "n"):
        return "false"
    raise ValueError(f"expected true/false, got '{val}'.")


def cmd_hubspot(args: argparse.Namespace) -> None:
    """Handle HubSpot commands (CRM read + write)."""
    from datetime import datetime

    from integrations.hubspot_api import (
        archive_object,
        create_association,
        create_note,
        create_object,
        create_task,
        delete_association,
        format_objects_for_context,
        list_objects,
        list_pipelines,
        list_properties,
        log_call,
        log_email,
        log_meeting,
        search_objects,
        update_object,
    )

    if args.action == "contacts":
        prop_names = ["email", "firstname", "lastname", "hs_lead_status",
                      "lifecyclestage", "urgent_alert"]
        print(format_objects_for_context(
            list_objects("contacts", limit=args.max, properties=prop_names)
        ))

    elif args.action == "companies":
        prop_names = ["name", "domain", "engagement_type", "retainer_gbp_mo"]
        print(format_objects_for_context(
            list_objects("companies", limit=args.max, properties=prop_names)
        ))

    elif args.action == "deals":
        prop_names = ["dealname", "dealstage", "amount", "closedate"]
        if args.stage:
            filter_groups = [
                {"filters": [
                    {"propertyName": "dealstage", "operator": "EQ", "value": args.stage}
                ]}
            ]
            results = search_objects("deals", filter_groups, properties=prop_names,
                                     limit=args.max)
        else:
            results = list_objects("deals", limit=args.max, properties=prop_names)
        print(format_objects_for_context(results))

    elif args.action == "overdue-invoices":
        from integrations.hubspot_scans import overdue_invoices
        print(format_objects_for_context(overdue_invoices(limit=args.max)))

    elif args.action == "silent-contacts":
        from integrations.hubspot_scans import silent_contacts
        print(format_objects_for_context(silent_contacts(limit=args.max)))

    elif args.action == "stale-deals":
        from integrations.hubspot_scans import stale_deals
        print(format_objects_for_context(stale_deals(limit=args.max)))

    elif args.action == "search":
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        filter_groups = [
            {"filters": [
                {"propertyName": "email", "operator": "CONTAINS_TOKEN", "value": args.query}
            ]}
        ]
        print(format_objects_for_context(
            search_objects("contacts", filter_groups, limit=args.max)
        ))

    elif args.action == "pipelines":
        for p in list_pipelines("deals"):
            print(f"- {p.get('label')} (id: {p.get('id')})")
            for s in p.get("stages", []):
                meta = s.get("metadata", {})
                closed = meta.get("isClosed")
                print(f"    · {s.get('label')} — closed={closed}")

    elif args.action == "properties":
        target = args.target_id or "contacts"
        for prop in list_properties(target):
            kind = f"{prop.get('type')}/{prop.get('fieldType')}"
            print(f"- {prop.get('name')} ({kind}): {prop.get('label')}")

    # ----- writes ---------------------------------------------------------

    elif args.action == "create-contact":
        if not args.email:
            raise ValueError("--email required for create-contact.")
        props: dict[str, Any] = {"email": args.email}
        if args.firstname:
            props["firstname"] = args.firstname
        if args.lastname:
            props["lastname"] = args.lastname
        if args.phone:
            props["phone"] = args.phone
        if args.urgent is not None:
            props["urgent_alert"] = _bool_arg(args.urgent)
        if args.conflict is not None:
            props["conflict_node"] = _bool_arg(args.conflict)
        if args.conflict_reason:
            props["conflict_reason"] = args.conflict_reason
        if args.preferred_channel:
            props["preferred_channel"] = args.preferred_channel
        if args.lifecyclestage:
            props["lifecyclestage"] = args.lifecyclestage
        obj = create_object("contacts", props)
        if args.company_domain:
            company_id = _hubspot_resolve_key("companies", args.company_domain)
            create_association(
                "contacts", obj.id, "companies", company_id,
                type_id=_OBJECT_ASSOC_TYPE_IDS[("contacts", "companies")],
            )
        print(f"Created contact: {obj.name} (ID: {obj.id})")

    elif args.action == "update-contact":
        if not args.target_id:
            raise ValueError("contact id|email required as positional arg.")
        cid = _hubspot_resolve_key("contacts", args.target_id)
        props = {}
        if args.urgent is not None:
            props["urgent_alert"] = _bool_arg(args.urgent)
        if args.conflict is not None:
            props["conflict_node"] = _bool_arg(args.conflict)
        if args.conflict_reason is not None:
            props["conflict_reason"] = args.conflict_reason
        if args.phone:
            props["phone"] = args.phone
        if args.preferred_channel:
            props["preferred_channel"] = args.preferred_channel
        if args.lifecyclestage:
            props["lifecyclestage"] = args.lifecyclestage
        if args.firstname:
            props["firstname"] = args.firstname
        if args.lastname:
            props["lastname"] = args.lastname
        if not props:
            raise ValueError("no fields to update.")
        obj = update_object("contacts", cid, props)
        print(f"Updated contact: {obj.name} (ID: {obj.id})")

    elif args.action == "archive-contact":
        if not args.target_id:
            raise ValueError("contact id|email required as positional arg.")
        cid = _hubspot_resolve_key("contacts", args.target_id)
        archive_object("contacts", cid)
        print(f"Archived contact ID: {cid}")

    elif args.action == "create-company":
        if not args.name or not args.domain:
            raise ValueError("--name and --domain required for create-company.")
        props = {"name": args.name, "domain": args.domain}
        if args.engagement:
            props["engagement_type"] = args.engagement
        if args.retainer_gbp is not None:
            props["retainer_gbp_mo"] = args.retainer_gbp
        if args.contract_end:
            props["contract_end_date"] = args.contract_end
        obj = create_object("companies", props)
        print(f"Created company: {obj.name} (ID: {obj.id})")

    elif args.action == "update-company":
        if not args.target_id:
            raise ValueError("company id|domain required as positional arg.")
        cid = _hubspot_resolve_key("companies", args.target_id)
        props = {}
        if args.name:
            props["name"] = args.name
        if args.engagement:
            props["engagement_type"] = args.engagement
        if args.retainer_gbp is not None:
            props["retainer_gbp_mo"] = args.retainer_gbp
        if args.contract_end:
            props["contract_end_date"] = args.contract_end
        if not props:
            raise ValueError("no fields to update.")
        obj = update_object("companies", cid, props)
        print(f"Updated company: {obj.name} (ID: {obj.id})")

    elif args.action == "archive-company":
        if not args.target_id:
            raise ValueError("company id|domain required as positional arg.")
        cid = _hubspot_resolve_key("companies", args.target_id)
        archive_object("companies", cid)
        print(f"Archived company ID: {cid}")

    elif args.action == "create-deal":
        if not args.name or args.amount is None or not args.stage:
            raise ValueError(
                "--name, --amount, and --stage required for create-deal."
            )
        stage_id = _hubspot_resolve_stage_id(args.stage, args.pipeline)
        pipe = _hubspot_pipeline(args.pipeline)
        props = {
            "dealname": args.name,
            "amount": str(args.amount),
            "dealstage": stage_id,
            "pipeline": str(pipe.get("id")),
        }
        if args.currency:
            props["deal_currency_code"] = args.currency.upper()
        if args.service_line:
            props["service_line"] = args.service_line
        if args.source:
            props["source"] = args.source
        if args.close_date:
            props["closedate"] = args.close_date
        if args.probability is not None:
            props["hs_deal_stage_probability"] = str(args.probability)
        deal = create_object("deals", props)
        if args.contact_email:
            cid = _hubspot_resolve_key("contacts", args.contact_email)
            create_association(
                "deals", deal.id, "contacts", cid,
                type_id=_OBJECT_ASSOC_TYPE_IDS[("deals", "contacts")],
            )
        if args.company_domain:
            coid = _hubspot_resolve_key("companies", args.company_domain)
            create_association(
                "deals", deal.id, "companies", coid,
                type_id=_OBJECT_ASSOC_TYPE_IDS[("deals", "companies")],
            )
        print(f"Created deal: {deal.name} (ID: {deal.id})")

    elif args.action == "move-deal":
        if not args.target_id or not args.to_stage:
            raise ValueError("deal id and --to-stage required.")
        stage_id = _hubspot_resolve_stage_id(args.to_stage, args.pipeline)
        obj = update_object("deals", args.target_id, {"dealstage": stage_id})
        print(f"Moved deal {obj.id} to stage '{args.to_stage}'.")

    elif args.action == "update-deal":
        if not args.target_id:
            raise ValueError("deal id required as positional arg.")
        props = {}
        if args.amount is not None:
            props["amount"] = str(args.amount)
        if args.close_date:
            props["closedate"] = args.close_date
        if args.probability is not None:
            props["hs_deal_stage_probability"] = str(args.probability)
        if args.service_line:
            props["service_line"] = args.service_line
        if args.source:
            props["source"] = args.source
        if not props:
            raise ValueError("no fields to update.")
        obj = update_object("deals", args.target_id, props)
        print(f"Updated deal: {obj.name} (ID: {obj.id})")

    elif args.action == "close-deal":
        if not args.target_id or not args.close_as:
            raise ValueError("deal id and --as won|lost required.")
        stage_id = _hubspot_resolve_closed_stage_id(args.close_as, args.pipeline)
        obj = update_object("deals", args.target_id, {"dealstage": stage_id})
        print(f"Closed deal {obj.id} as {args.close_as}.")

    elif args.action == "archive-deal":
        if not args.target_id:
            raise ValueError("deal id required as positional arg.")
        archive_object("deals", args.target_id)
        print(f"Archived deal ID: {args.target_id}")

    elif args.action == "add-note":
        if not args.about or not args.text:
            raise ValueError("--about and --text required.")
        target_type, target_key = _hubspot_parse_about(args.about)
        target_id = _hubspot_resolve_key(target_type, target_key)
        assoc = _hubspot_engagement_assoc("notes", target_type, target_id)
        result = create_note(args.text, associations=assoc)
        print(f"Added note (ID: {result.get('id')}) to {target_type[:-1]} {target_id}.")

    elif args.action == "create-task":
        if not args.about or not args.title or not args.due:
            raise ValueError("--about, --title, --due required.")
        target_type, target_key = _hubspot_parse_about(args.about)
        target_id = _hubspot_resolve_key(target_type, target_key)
        assoc = _hubspot_engagement_assoc("tasks", target_type, target_id)
        due_date = datetime.strptime(args.due, "%Y-%m-%d").date()
        result = create_task(
            args.title, body=args.notes or "", due_date=due_date, associations=assoc,
        )
        print(f"Created task (ID: {result.get('id')}) due {args.due}.")

    elif args.action == "log-call":
        if not args.with_target or not args.summary:
            raise ValueError("--with and --summary required.")
        target_type, target_key = _hubspot_parse_about(args.with_target)
        target_id = _hubspot_resolve_key(target_type, target_key)
        assoc = _hubspot_engagement_assoc("calls", target_type, target_id)
        duration_ms = (args.duration_min * 60 * 1000) if args.duration_min else None
        direction = (args.direction or "out").lower()
        direction = "INBOUND" if direction.startswith("in") else "OUTBOUND"
        result = log_call(
            args.summary,
            duration_ms=duration_ms,
            disposition=args.disposition,
            direction=direction,
            body=args.notes or "",
            associations=assoc,
        )
        print(f"Logged call (ID: {result.get('id')}) to {target_type[:-1]} {target_id}.")

    elif args.action == "log-meeting":
        if not args.with_target or not args.title or not args.start or not args.end:
            raise ValueError("--with, --title, --start, --end required.")
        target_type, target_key = _hubspot_parse_about(args.with_target)
        target_id = _hubspot_resolve_key(target_type, target_key)
        assoc = _hubspot_engagement_assoc("meetings", target_type, target_id)
        start = datetime.fromisoformat(args.start)
        end = datetime.fromisoformat(args.end)
        result = log_meeting(
            args.title, start, end, body=args.notes or "", associations=assoc,
        )
        print(f"Logged meeting (ID: {result.get('id')}).")

    elif args.action == "log-email":
        if (
            not args.with_target or not args.subject or not args.direction
            or not args.sent_at
        ):
            raise ValueError("--with, --subject, --direction, --sent-at required.")
        target_type, target_key = _hubspot_parse_about(args.with_target)
        target_id = _hubspot_resolve_key(target_type, target_key)
        assoc = _hubspot_engagement_assoc("emails", target_type, target_id)
        sent_at = datetime.fromisoformat(args.sent_at)
        direction = (
            "INCOMING_EMAIL" if args.direction.lower().startswith("in") else "EMAIL"
        )
        result = log_email(
            args.subject, args.body or "",
            direction=direction, sent_at=sent_at, associations=assoc,
        )
        print(f"Logged email (ID: {result.get('id')}).")

    elif args.action == "associate":
        if not args.assoc_from or not args.assoc_to:
            raise ValueError("--from and --to required.")
        from_type, from_key = _hubspot_parse_about(args.assoc_from)
        to_type, to_key = _hubspot_parse_about(args.assoc_to)
        from_id = _hubspot_resolve_key(from_type, from_key)
        to_id = _hubspot_resolve_key(to_type, to_key)
        type_id = (
            args.type_id
            if args.type_id is not None
            else _OBJECT_ASSOC_TYPE_IDS.get((from_type, to_type))
        )
        if type_id is None:
            raise ValueError(
                f"No default typeId for {from_type}→{to_type}; pass --type-id."
            )
        create_association(from_type, from_id, to_type, to_id, type_id=type_id)
        print(f"Associated {from_type[:-1]} {from_id} ↔ {to_type[:-1]} {to_id}.")

    elif args.action == "unassociate":
        if not args.assoc_from or not args.assoc_to:
            raise ValueError("--from and --to required.")
        from_type, from_key = _hubspot_parse_about(args.assoc_from)
        to_type, to_key = _hubspot_parse_about(args.assoc_to)
        from_id = _hubspot_resolve_key(from_type, from_key)
        to_id = _hubspot_resolve_key(to_type, to_key)
        delete_association(from_type, from_id, to_type, to_id)
        print(f"Removed association {from_type[:-1]} {from_id} ↮ {to_type[:-1]} {to_id}.")

    # ------------------------------------------------------------------
    # Tickets — Fredis Review queue
    # ------------------------------------------------------------------
    elif args.action == "create-ticket":
        from integrations.hubspot_api import create_ticket
        if not args.subject:
            raise ValueError("--subject required.")
        created = create_ticket(
            subject=args.subject,
            content=args.content or "",
            lane=args.lane,
            skill_source=args.skill_source,
            urgency=args.urgency,
            draft_path=args.draft_path,
            dedupe_key=args.dedupe_key,
            heartbeat_run_id=args.heartbeat_run,
            slack_thread_url=args.slack_thread,
            contact_ids=[args.contact_id] if args.contact_id else None,
            company_ids=[args.company_id] if args.company_id else None,
            deal_ids=[args.deal_id] if args.deal_id else None,
        )
        print(f"Created ticket {created.id}: {args.subject!r}")

    elif args.action == "get-ticket":
        from integrations.hubspot_api import get_ticket
        if not args.target_id:
            raise ValueError("Ticket id required as positional argument.")
        found = get_ticket(
            args.target_id,
            properties=[
                "subject", "content", "hs_pipeline_stage",
                "lane", "skill_source", "urgency", "draft_path",
                "hs_ticket_priority", "dedupe_key",
                "heartbeat_run_id", "slack_thread_url",
            ],
        )
        if found is None:
            print(f"Ticket {args.target_id} not found.")
        else:
            print(f"Ticket {found.id}:")
            for k, v in sorted(found.properties.items()):
                if v:
                    print(f"  {k}: {v}")

    elif args.action == "move-ticket":
        from integrations.hubspot_api import move_ticket
        if not args.target_id or not args.to_stage:
            raise ValueError("Ticket id (positional) and --to-stage required.")
        moved = move_ticket(args.target_id, args.to_stage)
        print(f"Moved ticket {moved.id} → {args.to_stage!r}.")

    elif args.action == "close-ticket":
        from integrations.hubspot_api import close_ticket
        if not args.target_id:
            raise ValueError("Ticket id required as positional argument.")
        if args.close_as not in ("actioned", "rejected"):
            raise ValueError("--as must be 'actioned' or 'rejected' for close-ticket.")
        closed = close_ticket(
            args.target_id, as_=args.close_as, note=args.note
        )
        print(f"Closed ticket {closed.id} as {args.close_as}.")

    elif args.action in ("list-tickets", "queue"):
        from integrations.hubspot_api import list_open_tickets
        tickets = list_open_tickets(
            lane=args.lane, urgency=args.urgency, limit=args.max
        )
        if not tickets:
            print("No open tickets.")
        elif args.action == "queue":
            # Group by urgency for quick scan.
            order = ("today", "this_week", "whenever", "")
            groups: dict[str, list[Any]] = {k: [] for k in order}
            for t in tickets:
                groups.setdefault(t.properties.get("urgency", "") or "", []).append(t)
            for urg in order:
                if not groups[urg]:
                    continue
                print(f"\n## {urg or 'unscheduled'}")
                for t in groups[urg]:
                    p = t.properties
                    lane = p.get("lane", "?")
                    skill = p.get("skill_source", "?")
                    subject = p.get("subject", "")
                    print(f"  - [{lane}] {subject} (id={t.id}, skill={skill})")
        else:
            print(f"Open tickets ({len(tickets)}):")
            for t in tickets:
                p = t.properties
                print(
                    f"  - {t.id} | {p.get('lane', '?')} | "
                    f"{p.get('urgency', '?')} | {p.get('subject', '')}"
                )


def cmd_lanes(args: argparse.Namespace) -> None:
    """Handle GitHub Projects v2 lane queries."""
    from integrations.github_projects import (
        breached_lane_gates,
        format_items_for_context,
        list_project_items,
    )

    if args.action == "list":
        print(format_items_for_context(list_project_items()))
    elif args.action == "breached":
        print(format_items_for_context(breached_lane_gates()))


def cmd_github(args: argparse.Namespace) -> None:
    """Handle GitHub commands (read-only)."""
    from integrations.github_api import (
        format_events_for_context,
        issues_mentioning_me,
        recent_commits,
        review_requests,
        ship_signal,
    )

    if args.action == "recent":
        print(format_events_for_context(recent_commits(hours=args.hours)))

    elif args.action == "review-requests":
        print(format_events_for_context(review_requests()))

    elif args.action == "mentions":
        print(format_events_for_context(issues_mentioning_me(hours=args.hours)))

    elif args.action == "ship":
        print("ship_signal:", ship_signal(hours=args.hours))


def cmd_drive(args: argparse.Namespace) -> None:
    """Handle Google Drive commands."""
    from integrations.drive_api import (
        find_files,
        format_files_for_context,
        get_file_by_id,
        list_files,
    )

    if args.action == "find":
        if not args.query:
            print("Error: search query required")
            sys.exit(1)
        files = find_files(args.query, file_type=args.file_type, max_results=args.max)
        print(format_files_for_context(files))

    elif args.action == "list":
        files = list_files(file_type=args.file_type, max_results=args.max)
        print(format_files_for_context(files))

    elif args.action == "get":
        if not args.query:
            print("Error: file ID required")
            sys.exit(1)
        file = get_file_by_id(args.query)
        if file:
            print(format_files_for_context([file]))
        else:
            print("File not found")


def _print_workflows(data: Any) -> None:
    """Render the /api/workflows response (list of objects or a dict wrapper)."""
    items = data.get("workflows", data) if isinstance(data, dict) else data
    if isinstance(items, list) and items:
        for w in items:
            if isinstance(w, dict):
                # Engine wraps each entry as {"workflow": {name, description}, "source"}.
                raw_wf = w.get("workflow")
                wf = raw_wf if isinstance(raw_wf, dict) else w
                name = wf.get("name", "?")
                desc_lines = (wf.get("description") or "").strip().splitlines()
                summary = desc_lines[0][:100] if desc_lines else ""
                source = w.get("source")
                label = f"- {name}" + (f"  [{source}]" if source else "")
                print(label + (f" — {summary}" if summary else ""))
            else:
                print(f"- {w}")
    else:
        print(json.dumps(data, indent=2))


def cmd_workflow(args: argparse.Namespace) -> None:
    """Archon build-harness dispatch — the SINGLE path into the engine.

    list / status / approve / reject speak HTTP to the loopback engine. `run` is
    PRD-GATED: it refuses unless an approved artifact resolves from
    drafts/active/the-team/, then requires --i-confirm-run to actually fire
    (firing pushes a branch + opens a DRAFT PR on the target remote).
    """
    from integrations import archon_api

    if args.action == "list":
        _print_workflows(archon_api.list_workflows())

    elif args.action == "status":
        if not args.target:
            print("Error: run id required — query.py workflow status <runId>")
            sys.exit(1)
        print(json.dumps(archon_api.get_run(args.target), indent=2))

    elif args.action == "approve":
        if not args.target:
            print("Error: run id required — query.py workflow approve <runId>")
            sys.exit(1)
        print(json.dumps(archon_api.approve_run(args.target, args.comment), indent=2))

    elif args.action == "reject":
        if not args.target:
            print("Error: run id required — query.py workflow reject <runId>")
            sys.exit(1)
        print(json.dumps(archon_api.reject_run(args.target, args.reason), indent=2))

    elif args.action == "run":
        from integrations.archon_gate import GateError, resolve_prd

        if not args.target:
            print(
                "Error: workflow name required — "
                "query.py workflow run <name> --prd <slug>"
            )
            sys.exit(1)

        # --- Gate FIRST (offline, no engine): no approved PRD -> no run. ---
        try:
            prd = resolve_prd(args.prd)
        except GateError as exc:
            print(f"REFUSED (PRD gate): {exc}")
            sys.exit(1)
        print(
            f"PRD gate PASSED: {prd.path.name} "
            f"({len(prd.message)} chars of run input)."
        )

        # --- Confirm gate (offline): firing is outward-facing. ---
        if not getattr(args, "i_confirm_run", False):
            print(
                "Nothing fired. `workflow run` dispatches an agentic run that "
                "pushes a branch and opens a DRAFT PR on the target remote via "
                "the engine.\nRe-run with --i-confirm-run to dispatch."
            )
            sys.exit(0)

        # --- Resolve the target codebase (needs the engine). ---
        if not args.codebase_id and not args.repo:
            print("Error: --repo <slug> or --codebase-id <id> required to fire.")
            sys.exit(1)
        codebase_id = args.codebase_id or archon_api.resolve_codebase_id(args.repo)

        # --- Fire: idle conversation -> run -> correlate runId. ---
        conv = archon_api.create_conversation(codebase_id)
        conv_id = conv.get("conversationId") or conv.get("id", "")
        fire = archon_api.run_workflow(args.target, conv_id, prd.message)
        print(json.dumps({"fired": fire, "conversationId": conv_id}, indent=2))
        run = archon_api.latest_run_for_conversation(conv_id)
        if run:
            run_id = run.get("id") or run.get("runId") or "(unknown)"
            print(f"runId: {run_id} — track with `query.py workflow status {run_id}`")
        else:
            print(
                "Run fired; runId not yet correlatable — "
                "poll `query.py workflow status` / GET /api/workflows/runs."
            )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Direct Platform Integrations")
    subparsers = parser.add_subparsers(dest="service", required=True)

    # Gmail
    gmail_parser = subparsers.add_parser("gmail", help="Gmail operations")
    gmail_parser.add_argument("action", choices=["list", "urgent", "unread", "read", "thread", "search", "attachments", "download-attachment", "create-draft"])
    gmail_parser.add_argument("message_id", nargs="?", default=None, help="Message/thread ID, or message being replied to (for create-draft)")
    gmail_parser.add_argument("--max", type=int, default=10)
    gmail_parser.add_argument("--query", default=None)
    gmail_parser.add_argument("--hours", type=int, default=None)
    gmail_parser.add_argument("--unread", action="store_true")
    gmail_parser.add_argument("--from-file", default=None, help="Path to markdown draft file (auto-reads recipient, subject, body, thread)")
    gmail_parser.add_argument("--to", default=None, help="Recipient for create-draft (manual mode)")
    gmail_parser.add_argument("--subject", dest="draft_subject", default=None, help="Subject for create-draft (manual mode)")
    gmail_parser.add_argument("--body", default=None, help="Body text for create-draft (manual mode)")
    gmail_parser.add_argument("--thread-id", default=None, help="Thread ID for threading the draft (manual mode)")
    gmail_parser.add_argument("--attachment", action="append", default=None, help="File path to attach to draft (can be used multiple times)")
    gmail_parser.add_argument("--attachment-id", default=None, help="Attachment ID for download-attachment command")
    gmail_parser.add_argument("--output-dir", default=None, help="Output directory for download-attachment command")

    # Calendar
    cal_parser = subparsers.add_parser("calendar", help="Calendar operations")
    cal_parser.add_argument("action", choices=["today", "upcoming", "soon"])
    cal_parser.add_argument("--hours", type=int, default=24)

    # Slack
    slack_parser = subparsers.add_parser("slack", help="Slack operations")
    # `send` stays in choices so programmatic callers can invoke it, but it's
    # gated behind --i-confirm-send in cmd_slack (advisor mode).
    slack_parser.add_argument("action", choices=["channels", "messages", "send", "update", "check"])
    slack_parser.add_argument("channel", nargs="?", default=None)
    slack_parser.add_argument("message", nargs="?", default=None)
    slack_parser.add_argument("--ts", default=None, help="Message timestamp for update")
    slack_parser.add_argument("--hours", type=int, default=2)
    slack_parser.add_argument(
        "--i-confirm-send",
        dest="i_confirm_send",
        action="store_true",
        help="Required to run `slack send`. Advisor mode — draft-first by default.",
    )

    # Google Sheets
    sheets_parser = subparsers.add_parser("sheets", help="Google Sheets operations")
    sheets_parser.add_argument("action", choices=["read", "info", "write", "append"])
    sheets_parser.add_argument("target_id", nargs="?", default=None, help="Spreadsheet ID")
    sheets_parser.add_argument("--range", default=None, help="A1 notation range")
    sheets_parser.add_argument("--values", default=None, help="JSON 2D array for write/append")
    sheets_parser.add_argument("--max-rows", type=int, default=500)

    # Google Docs
    docs_parser = subparsers.add_parser("docs", help="Google Docs operations")
    docs_parser.add_argument("action", choices=["read", "info"])
    docs_parser.add_argument("target_id", nargs="?", default=None, help="Document ID")
    docs_parser.add_argument("--max-chars", type=int, default=4000)

    # HubSpot CRM
    hubspot_parser = subparsers.add_parser(
        "hubspot", help="HubSpot CRM operations (read + write)"
    )
    hubspot_parser.add_argument(
        "action",
        choices=[
            # reads
            "contacts", "companies", "deals",
            "overdue-invoices", "silent-contacts", "stale-deals",
            "search", "pipelines", "properties",
            # writes — contacts / companies / deals
            "create-contact", "update-contact", "archive-contact",
            "create-company", "update-company", "archive-company",
            "create-deal", "update-deal", "move-deal", "close-deal",
            "archive-deal",
            # writes — engagements
            "add-note", "create-task",
            "log-call", "log-meeting", "log-email",
            # writes — associations
            "associate", "unassociate",
            # tickets — Fredis Review queue
            "create-ticket", "get-ticket", "move-ticket", "close-ticket",
            "list-tickets", "queue",
        ],
    )
    hubspot_parser.add_argument(
        "target_id", nargs="?", default=None,
        help=(
            "Positional ID/key (object type for 'properties'; record id|email "
            "for update/archive/move/close)"
        ),
    )
    hubspot_parser.add_argument("--max", type=int, default=25)
    hubspot_parser.add_argument(
        "--stage", default=None,
        help="Filter deals by stage ID (read), or stage label (create-deal)",
    )
    hubspot_parser.add_argument(
        "--query", default=None, help="Search query for 'search' action"
    )
    # Contact properties
    hubspot_parser.add_argument("--email", default=None)
    hubspot_parser.add_argument("--firstname", default=None)
    hubspot_parser.add_argument("--lastname", default=None)
    hubspot_parser.add_argument("--phone", default=None)
    hubspot_parser.add_argument("--urgent", default=None,
                                help="true/false — sets urgent_alert")
    hubspot_parser.add_argument("--conflict", default=None,
                                help="true/false — sets conflict_node")
    hubspot_parser.add_argument("--conflict-reason", default=None)
    hubspot_parser.add_argument(
        "--preferred-channel", default=None,
        choices=["whatsapp", "email", "slack", "facebook_dm"],
    )
    hubspot_parser.add_argument(
        "--lifecyclestage", default=None,
        help="lead|marketingqualifiedlead|salesqualifiedlead|customer|...",
    )
    # Company properties
    hubspot_parser.add_argument("--name", default=None,
                                help="Company name (create-company) or deal name")
    hubspot_parser.add_argument("--domain", default=None,
                                help="Company domain (create-company)")
    hubspot_parser.add_argument(
        "--engagement", default=None,
        choices=["retainer", "project", "prospect", "dormant"],
    )
    hubspot_parser.add_argument("--retainer-gbp", type=float, default=None)
    hubspot_parser.add_argument("--contract-end", default=None,
                                help="YYYY-MM-DD")
    # Deal properties
    hubspot_parser.add_argument("--amount", type=float, default=None)
    hubspot_parser.add_argument("--pipeline", default="Consultancy",
                                help="Pipeline label (default: Consultancy)")
    hubspot_parser.add_argument("--currency", default=None,
                                help="GBP|EUR|USD — sets deal_currency_code")
    hubspot_parser.add_argument("--contact-email", default=None,
                                help="Contact email/id to associate (create-deal)")
    hubspot_parser.add_argument("--company-domain", default=None,
                                help="Company domain/id to associate")
    hubspot_parser.add_argument(
        "--service-line", default=None,
        choices=["ai_agentic", "custom_app", "saas",
                 "marketing_ops", "agri_ai", "advisory"],
    )
    hubspot_parser.add_argument(
        "--source", default=None,
        choices=["cold", "inbound", "referral", "content"],
    )
    hubspot_parser.add_argument("--close-date", default=None,
                                help="YYYY-MM-DD")
    hubspot_parser.add_argument("--probability", type=float, default=None)
    hubspot_parser.add_argument("--to-stage", default=None,
                                help="Stage label for move-deal")
    hubspot_parser.add_argument("--as", dest="close_as", default=None,
                                choices=["won", "lost", "actioned", "rejected"])
    # Ticket-specific flags
    hubspot_parser.add_argument(
        "--lane", default=None,
        choices=["email_hub", "vtv", "cab", "content", "ops", "client", "admin"],
        help="Ticket lane (Fredis Review queue)",
    )
    hubspot_parser.add_argument(
        "--urgency", default=None,
        choices=["today", "this_week", "whenever"],
        help="Ticket urgency (auto-derives hs_ticket_priority)",
    )
    hubspot_parser.add_argument(
        "--skill", dest="skill_source", default=None,
        help="Skill or subsystem creating the ticket",
    )
    hubspot_parser.add_argument("--draft-path", default=None,
                                help="Repo-relative path to the draft markdown")
    hubspot_parser.add_argument("--dedupe-key", default=None)
    hubspot_parser.add_argument("--heartbeat-run", default=None,
                                help="heartbeat_run_id for heartbeat-sourced tickets")
    hubspot_parser.add_argument("--slack-thread", default=None,
                                help="slack_thread_url if ticket born from Slack")
    hubspot_parser.add_argument("--content", default=None,
                                help="Ticket body / description")
    hubspot_parser.add_argument("--contact-id", default=None,
                                help="Associate ticket with a HubSpot contact id")
    hubspot_parser.add_argument("--company-id", default=None,
                                help="Associate ticket with a HubSpot company id")
    hubspot_parser.add_argument("--deal-id", default=None,
                                help="Associate ticket with a HubSpot deal id")
    hubspot_parser.add_argument("--note", default=None,
                                help="Rejection note (close-ticket --as rejected)")
    # Engagement args
    hubspot_parser.add_argument("--about", default=None,
                                help="<type>:<id|email|domain|dealname>")
    hubspot_parser.add_argument("--text", default=None,
                                help="Note body for add-note")
    hubspot_parser.add_argument("--title", default=None,
                                help="Title for create-task / log-meeting")
    hubspot_parser.add_argument("--due", default=None,
                                help="YYYY-MM-DD for create-task")
    hubspot_parser.add_argument("--notes", default=None,
                                help="Body/notes for task/call/meeting")
    hubspot_parser.add_argument(
        "--status", default=None,
        choices=["not_started", "in_progress", "waiting", "completed"],
    )
    hubspot_parser.add_argument("--with", dest="with_target", default=None,
                                help="<type>:<id|email> for log-* commands")
    hubspot_parser.add_argument("--summary", default=None)
    hubspot_parser.add_argument("--duration-min", type=int, default=None)
    hubspot_parser.add_argument("--disposition", default=None)
    hubspot_parser.add_argument("--direction", default=None,
                                help="in|out for log-call / log-email")
    hubspot_parser.add_argument("--start", default=None, help="ISO datetime")
    hubspot_parser.add_argument("--end", default=None, help="ISO datetime")
    hubspot_parser.add_argument("--subject", default=None)
    hubspot_parser.add_argument("--sent-at", default=None, help="ISO datetime")
    hubspot_parser.add_argument("--body", default=None,
                                help="Body for log-email")
    # Association args
    hubspot_parser.add_argument("--from", dest="assoc_from", default=None,
                                help="<type>:<id|key> for associate/unassociate")
    hubspot_parser.add_argument("--to", dest="assoc_to", default=None,
                                help="<type>:<id|key> for associate/unassociate")
    hubspot_parser.add_argument("--type-id", type=int, default=None,
                                help="Override default association typeId")

    # GitHub Projects v2 — lanes
    lanes_parser = subparsers.add_parser(
        "lanes", help="GitHub Projects v2 — Lanes & Features (read-only)"
    )
    lanes_parser.add_argument("action", choices=["list", "breached"])

    # GitHub
    github_parser = subparsers.add_parser("github", help="GitHub operations (read-only)")
    github_parser.add_argument("action", choices=["recent", "review-requests", "mentions", "ship"])
    github_parser.add_argument("--hours", type=int, default=24)

    # Google Drive
    drive_parser = subparsers.add_parser("drive", help="Google Drive operations")
    drive_parser.add_argument("action", choices=["find", "list", "get"])
    drive_parser.add_argument("query", nargs="?", default=None, help="Search term or file ID")
    drive_parser.add_argument("--type", dest="file_type", default=None,
                              choices=["spreadsheet", "document", "folder", "presentation", "pdf"])
    drive_parser.add_argument("--max", type=int, default=10)

    # Archon build-harness dispatch — the SINGLE path into the engine
    wf_parser = subparsers.add_parser(
        "workflow", help="Archon build-harness dispatch (PRD-gated single path)"
    )
    wf_parser.add_argument(
        "action", choices=["list", "run", "status", "approve", "reject"]
    )
    wf_parser.add_argument(
        "target", nargs="?", default=None,
        help="workflow name (run) or run id (status/approve/reject)",
    )
    wf_parser.add_argument(
        "--prd", default=None,
        help=("Approved PRD slug|path in drafts/active/the-team/ (run). "
              "Omit to auto-pick the single approved artifact."),
    )
    wf_parser.add_argument("--repo", default=None,
                           help="Target codebase slug to resolve (run)")
    wf_parser.add_argument("--codebase-id", dest="codebase_id", default=None,
                           help="Explicit codebase id (run)")
    wf_parser.add_argument(
        "--i-confirm-run", dest="i_confirm_run", action="store_true",
        help=("Required to actually fire — a run opens a DRAFT PR on the "
              "target remote via the engine."),
    )
    wf_parser.add_argument("--comment", default=None,
                           help="Approval comment (approve)")
    wf_parser.add_argument("--reason", default=None,
                           help="Rejection reason (reject)")

    args = parser.parse_args()

    try:
        if args.service == "gmail":
            cmd_gmail(args)
        elif args.service == "calendar":
            cmd_calendar(args)
        elif args.service == "slack":
            cmd_slack(args)
        elif args.service == "sheets":
            cmd_sheets(args)
        elif args.service == "docs":
            cmd_docs(args)
        elif args.service == "hubspot":
            cmd_hubspot(args)
        elif args.service == "lanes":
            cmd_lanes(args)
        elif args.service == "github":
            cmd_github(args)
        elif args.service == "drive":
            cmd_drive(args)
        elif args.service == "workflow":
            cmd_workflow(args)
    except Exception as e:
        print(json.dumps({"error": str(e), "type": "runtime"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
