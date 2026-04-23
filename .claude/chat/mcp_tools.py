"""In-process MCP tools for chat engine — Gmail first.

Wrapped directly around the Python functions in `integrations.gmail` so
the chat engine's Agent SDK sees them as callable tools in its schema
rather than having to remember a skill exists. Runs in-process (same
event loop as the engine) — no subprocess, no path issues on the VPS.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Any

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from claude_agent_sdk import create_sdk_mcp_server, tool  # noqa: E402

from integrations.gmail import (  # noqa: E402
    check_for_urgent_emails,
    create_gmail_draft,
    format_emails_for_context,
    format_thread_for_context,
    get_email_details,
    get_gmail_service,
    get_thread_messages,
    get_unread_count,
    list_emails,
)

SERVER_NAME = "fredis"


def _text_response(text: str, is_error: bool = False) -> dict[str, Any]:
    """Shape a tool return value per MCP content-block spec."""
    result: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        result["is_error"] = True
    return result


@tool(
    "gmail_list",
    "List recent emails from the user's Gmail inbox. Default: last 24h of "
    "inbox. Pass a `query` to search the whole mailbox (Gmail search syntax: "
    "`from:ryan@x.com`, `subject:proposal`, `is:unread newer_than:7d`, etc.) "
    "— when `query` is set, the time filter is dropped. Returns formatted "
    "text: sender, subject, snippet, date, message_id (use with gmail_read).",
    {
        "max_results": Annotated[int, "Max emails to return (default 10)"],
        "query": Annotated[str, "Gmail search query; empty string for recent inbox"],
        "unread_only": Annotated[bool, "Only return unread emails"],
        "hours_ago": Annotated[
            int, "Restrict to last N hours; -1 to disable (default 24 when no query)"
        ],
    },
)
async def _gmail_list(args: dict[str, Any]) -> dict[str, Any]:
    query = args.get("query") or ""
    hours_raw = args.get("hours_ago", -1)
    if hours_raw is None or hours_raw < 0:
        hours = None if query else 24
    else:
        hours = hours_raw
    try:
        emails = list_emails(
            max_results=int(args.get("max_results") or 10),
            query=query,
            unread_only=bool(args.get("unread_only", False)),
            hours_ago=hours,
        )
    except Exception as e:
        return _text_response(f"gmail_list failed: {e}", is_error=True)
    return _text_response(format_emails_for_context(emails) or "No emails found.")


@tool(
    "gmail_unread_count",
    "Return the total count of unread emails in the user's Gmail inbox.",
    {},
)
async def _gmail_unread_count(args: dict[str, Any]) -> dict[str, Any]:
    try:
        count = get_unread_count()
    except Exception as e:
        return _text_response(f"gmail_unread_count failed: {e}", is_error=True)
    return _text_response(f"Unread emails: {count}")


@tool(
    "gmail_urgent",
    "Scan recent emails for ones that look urgent (important senders, "
    "priority keywords, reply-expected signals). Default window: last 2h.",
    {"hours_ago": Annotated[int, "How far back to look, in hours (default 2)"]},
)
async def _gmail_urgent(args: dict[str, Any]) -> dict[str, Any]:
    try:
        emails = check_for_urgent_emails(hours_ago=int(args.get("hours_ago") or 2))
    except Exception as e:
        return _text_response(f"gmail_urgent failed: {e}", is_error=True)
    if not emails:
        return _text_response("No urgent emails found.")
    return _text_response(
        f"Found {len(emails)} potentially urgent email(s):\n\n"
        + format_emails_for_context(emails)
    )


@tool(
    "gmail_read",
    "Fetch the full body + metadata for a single email by message_id. "
    "Use message_ids returned by gmail_list or gmail_urgent.",
    {"message_id": Annotated[str, "Gmail message ID"]},
)
async def _gmail_read(args: dict[str, Any]) -> dict[str, Any]:
    message_id = args.get("message_id")
    if not message_id:
        return _text_response("message_id is required", is_error=True)
    try:
        service = get_gmail_service()
        email = get_email_details(service, message_id, include_body=True)
    except Exception as e:
        return _text_response(f"gmail_read failed: {e}", is_error=True)
    if not email:
        return _text_response(f"Email {message_id} not found.", is_error=True)
    body = email.body or email.snippet or ""
    return _text_response(
        f"Subject: {email.subject}\n"
        f"From: {email.sender} <{email.sender_email}>\n"
        f"Date: {email.date}\n"
        f"Labels: {', '.join(email.labels)}\n"
        f"Message-ID: {email.message_id}\n"
        f"Thread-ID: {email.thread_id}\n\n"
        f"{body}"
    )


@tool(
    "gmail_thread",
    "Fetch all messages in a Gmail thread by thread_id — full conversation "
    "history, useful before drafting a reply.",
    {"thread_id": Annotated[str, "Gmail thread ID"]},
)
async def _gmail_thread(args: dict[str, Any]) -> dict[str, Any]:
    thread_id = args.get("thread_id")
    if not thread_id:
        return _text_response("thread_id is required", is_error=True)
    try:
        messages = get_thread_messages(thread_id)
    except Exception as e:
        return _text_response(f"gmail_thread failed: {e}", is_error=True)
    if not messages:
        return _text_response(f"Thread {thread_id} not found or empty.", is_error=True)
    return _text_response(format_thread_for_context(messages))


@tool(
    "gmail_create_draft",
    "Create a Gmail draft in the user's Gmail Drafts folder (NEVER sent). "
    "USE THIS for ALL email drafts — both brand-new emails and replies. "
    "Do not write email drafts to the filesystem; they belong in Gmail. "
    "thread_id and message_id are optional — omit them for new emails, "
    "pass them only when replying so Gmail threads the reply correctly. "
    "Advisor-mode path: Linards reviews the draft in Gmail and sends himself.",
    {
        "to": Annotated[str, "Recipient email address"],
        "subject": Annotated[str, "Subject line"],
        "body": Annotated[str, "Email body (plain text; line breaks preserved)"],
        "thread_id": Annotated[str, "Optional — Gmail thread_id for a reply"],
        "message_id": Annotated[
            str, "Optional — RFC Message-ID header of the email being replied to"
        ],
    },
)
async def _gmail_create_draft(args: dict[str, Any]) -> dict[str, Any]:
    to = args.get("to")
    subject = args.get("subject")
    body = args.get("body")
    if not (to and subject is not None and body is not None):
        return _text_response(
            "to, subject, and body are all required", is_error=True
        )
    thread_id = args.get("thread_id") or None
    message_id = args.get("message_id") or None
    try:
        result = create_gmail_draft(
            to=to,
            subject=subject,
            body=body,
            thread_id=thread_id,
            message_id=message_id,
        )
    except Exception as e:
        return _text_response(f"gmail_create_draft failed: {e}", is_error=True)
    return _text_response(
        "Draft created in Gmail Drafts folder (not sent).\n"
        f"draft_id: {result.get('id', '?')}\n"
        f"message_id: {result.get('message_id', '?')}\n"
        f"thread_id: {result.get('thread_id', '?')}"
    )


GMAIL_TOOLS = [
    _gmail_list,
    _gmail_unread_count,
    _gmail_urgent,
    _gmail_read,
    _gmail_thread,
    _gmail_create_draft,
]


def build_server() -> Any:
    """Build the in-process MCP server with all Fredis tools."""
    return create_sdk_mcp_server(name=SERVER_NAME, tools=GMAIL_TOOLS)


def allowed_tool_names() -> list[str]:
    """MCP tool names the Agent SDK will expose. Format: mcp__<server>__<tool>."""
    return [f"mcp__{SERVER_NAME}__{t.name}" for t in GMAIL_TOOLS]
