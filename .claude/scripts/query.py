"""
Interactive CLI wrapper for direct platform integrations.

Used by the direct-integrations Claude Code skill to query Gmail, Calendar,
Asana, Slack, Google Sheets, Google Docs, and Google Drive from interactive sessions.

Usage:
    python query.py gmail list --max 5
    python query.py calendar today
    python query.py asana overdue
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


def cmd_asana(args: argparse.Namespace) -> None:
    """Handle Asana commands."""
    from integrations.asana_api import (
        add_comment,
        add_task_to_section,
        complete_task,
        create_task,
        format_tasks_for_context,
        get_due_soon_tasks,
        get_my_tasks,
        get_overdue_tasks,
        get_project_tasks,
        get_section_tasks,
        get_sections,
        move_task,
        search_tasks_by_text,
    )

    assignee = getattr(args, "assignee", None)

    if args.action == "my-tasks":
        tasks = get_my_tasks(max_results=args.max, assignee=assignee)
        print(format_tasks_for_context(tasks))

    elif args.action == "project":
        tasks = get_project_tasks(project_gid=args.project_id, max_results=args.max)
        print(format_tasks_for_context(tasks))

    elif args.action == "overdue":
        tasks = get_overdue_tasks(assignee=assignee)
        if tasks:
            print(f"Found {len(tasks)} overdue tasks:\n")
            print(format_tasks_for_context(tasks))
        else:
            print("No overdue tasks")

    elif args.action == "due-soon":
        tasks = get_due_soon_tasks(days=args.days, assignee=assignee)
        if tasks:
            print(f"Found {len(tasks)} tasks due in next {args.days} days:\n")
            print(format_tasks_for_context(tasks))
        else:
            print(f"No tasks due in next {args.days} days")

    elif args.action == "complete":
        if not args.project_id:
            print("Error: task_gid required for complete command")
            sys.exit(1)
        task = complete_task(args.project_id)
        print(f"Completed: {task.name}")

    elif args.action == "sections":
        project_gid = args.project_id
        sections = get_sections(project_gid)
        if sections:
            for s in sections:
                print(f"- **{s['name']}** (GID: {s['gid']})")
        else:
            print("No sections found.")

    elif args.action == "section-tasks":
        section_gid = args.project_id
        if not section_gid:
            print("Error: section_gid required (positional argument)")
            sys.exit(1)
        tasks = get_section_tasks(section_gid, max_results=args.max)
        print(format_tasks_for_context(tasks))

    elif args.action == "move-to-section":
        task_gid = args.project_id
        section_gid = getattr(args, "section", None)
        insert_after = getattr(args, "insert_after", None)
        insert_before = getattr(args, "insert_before", None)
        due_str = getattr(args, "due", None)
        if not task_gid or not section_gid:
            print("Error: task_gid (positional) and --section required")
            sys.exit(1)
        auto_date = None
        if not insert_after and not insert_before and due_str:
            from datetime import datetime as _dt
            auto_date = _dt.strptime(due_str, "%Y-%m-%d").date()
        add_task_to_section(task_gid, section_gid, insert_after=insert_after, insert_before=insert_before, auto_order_date=auto_date)
        print(f"Moved task {task_gid} to section {section_gid}")

    elif args.action == "search":
        query_text = getattr(args, "query", None)
        if not query_text:
            print("Error: --query required for search command")
            sys.exit(1)
        tasks = search_tasks_by_text(query_text, max_results=args.max, assignee=assignee)
        if tasks:
            print(f"Found {len(tasks)} matching tasks:\n")
            print(format_tasks_for_context(tasks))
        else:
            print("No matching tasks found.")

    elif args.action == "create":
        name = getattr(args, "name", None)
        if not name:
            print("Error: --name required for create command")
            sys.exit(1)
        task = create_task(
            name=name,
            due_on=getattr(args, "due", None),
            assignee=assignee,
            project=getattr(args, "project", None),
            notes=getattr(args, "notes", None),
            section=getattr(args, "section", None),
            parent=getattr(args, "parent", None),
        )
        due_str = task.due_on.strftime("%Y-%m-%d") if task.due_on else "No due date"
        print(f"Created: **{task.name}** (GID: {task.gid})")
        print(f"  Assignee: {task.assignee or 'me'} | Due: {due_str}")
        if task.project:
            print(f"  Project: {task.project}")

    elif args.action == "comment":
        task_gid = args.project_id
        comment_text = getattr(args, "comment", None)
        if not task_gid or not comment_text:
            print("Error: task_gid (positional) and --comment required")
            sys.exit(1)
        story_gid = add_comment(task_gid, comment_text)
        print(f"Comment added to task {task_gid} (story GID: {story_gid})")

    elif args.action == "move":
        task_gid = args.project_id
        to_proj = getattr(args, "to_project", None)
        from_proj = getattr(args, "from_project", None)
        if not task_gid or not to_proj:
            print("Error: task_gid (positional) and --to-project required")
            sys.exit(1)
        move_task(task_gid, to_project=to_proj, from_project=from_proj)
        print(f"Moved task {task_gid} to project {to_proj}")


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


def cmd_monday(args: argparse.Namespace) -> None:
    """Handle Monday.com commands (read-only)."""
    from integrations.monday_api import (
        board_items,
        format_items_for_context,
        list_boards,
        my_items,
        overdue_items,
        search,
    )

    if args.action == "boards":
        for b in list_boards():
            print(f"- {b['name']} (id: {b['id']}, items: {b['items_count']})")

    elif args.action == "board":
        if not args.target_id:
            print("Error: board_id required. Run 'monday boards' first.")
            sys.exit(1)
        print(format_items_for_context(board_items(args.target_id, limit=args.max)))

    elif args.action == "my-items":
        print(format_items_for_context(my_items(limit=args.max)))

    elif args.action == "overdue":
        print(format_items_for_context(overdue_items(limit=args.max)))

    elif args.action == "search":
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        print(format_items_for_context(search(args.query, limit=args.max)))


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

    # Asana
    asana_parser = subparsers.add_parser("asana", help="Asana operations")
    asana_parser.add_argument("action", choices=["my-tasks", "project", "overdue", "due-soon", "complete", "sections", "section-tasks", "move-to-section", "search", "create", "comment", "move"])
    asana_parser.add_argument("project_id", nargs="?", default=None)
    asana_parser.add_argument("--max", type=int, default=20)
    asana_parser.add_argument("--days", type=int, default=3)
    asana_parser.add_argument("--assignee", type=str, default=None, help="User name or GID to filter by assignee")
    asana_parser.add_argument("--name", type=str, default=None, help="Task name for create")
    asana_parser.add_argument("--due", type=str, default=None, help="Due date YYYY-MM-DD for create")
    asana_parser.add_argument("--project", type=str, default=None, help="Project GID for create")
    asana_parser.add_argument("--notes", type=str, default=None, help="Description/notes for create")
    asana_parser.add_argument("--section", type=str, default=None, help="Section GID for create or move-to-section")
    asana_parser.add_argument("--parent", type=str, default=None, help="Parent task GID for creating subtasks")
    asana_parser.add_argument("--comment", type=str, default=None, help="Comment text for comment action")
    asana_parser.add_argument("--to-project", type=str, default=None, help="Destination project GID for move")
    asana_parser.add_argument("--from-project", type=str, default=None, help="Source project GID for move (optional)")
    asana_parser.add_argument("--insert-after", type=str, default=None, help="Task GID to insert after (for ordering in section)")
    asana_parser.add_argument("--insert-before", type=str, default=None, help="Task GID to insert before (for ordering in section)")
    asana_parser.add_argument("--query", type=str, default=None, help="Search query text for search action")

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

    # Monday.com
    monday_parser = subparsers.add_parser("monday", help="Monday.com operations (read-only)")
    monday_parser.add_argument("action", choices=["boards", "board", "my-items", "overdue", "search"])
    monday_parser.add_argument("target_id", nargs="?", default=None, help="Board ID for 'board' action")
    monday_parser.add_argument("--max", type=int, default=25)
    monday_parser.add_argument("--query", default=None, help="Search query for 'search' action")

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

    args = parser.parse_args()

    try:
        if args.service == "gmail":
            cmd_gmail(args)
        elif args.service == "calendar":
            cmd_calendar(args)
        elif args.service == "asana":
            cmd_asana(args)
        elif args.service == "slack":
            cmd_slack(args)
        elif args.service == "sheets":
            cmd_sheets(args)
        elif args.service == "docs":
            cmd_docs(args)
        elif args.service == "monday":
            cmd_monday(args)
        elif args.service == "github":
            cmd_github(args)
        elif args.service == "drive":
            cmd_drive(args)
    except Exception as e:
        print(json.dumps({"error": str(e), "type": "runtime"}, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
