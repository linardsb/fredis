# Direct Platform Integrations (Gmail / Calendar / Slack / HubSpot / GitHub / Sheets / Docs / Drive)


# Direct Platform Integrations

Query Gmail, Calendar, Slack, HubSpot, GitHub, Sheets, Docs, and Drive directly — no Zapier/MCP needed.

## Script Path

`.claude/scripts/query.py` (relocated from the skill directory in Phase 4; now sibling to `integrations/`).

## Running Commands

```bash
# Gmail
python .claude/scripts/query.py gmail list [--max N] [--query Q] [--unread] [--hours N]
python .claude/scripts/query.py gmail urgent [--hours N]
python .claude/scripts/query.py gmail unread
python .claude/scripts/query.py gmail read <message_id>
python .claude/scripts/query.py gmail thread <thread_id>
python .claude/scripts/query.py gmail search "subject or query" [--max N]
python .claude/scripts/query.py gmail attachments <message_id>
python .claude/scripts/query.py gmail download-attachment <message_id> --attachment-id <id> [--output-dir <path>]

# Calendar
python .claude/scripts/query.py calendar today
python .claude/scripts/query.py calendar upcoming [--hours N]
python .claude/scripts/query.py calendar soon

# Slack
python .claude/scripts/query.py slack channels
python .claude/scripts/query.py slack messages <channel> [--hours N]
python .claude/scripts/query.py slack send <channel> <message>
python .claude/scripts/query.py slack check

# Google Sheets
python .claude/scripts/query.py sheets read <spreadsheet_id> [--range "Sheet1!A1:Z100"] [--max-rows N]
python .claude/scripts/query.py sheets info <spreadsheet_id>
python .claude/scripts/query.py sheets write <spreadsheet_id> --range "A1" --values '[["a","b"]]'
python .claude/scripts/query.py sheets append <spreadsheet_id> --range "A:Z" --values '[["new","row"]]'

# Google Docs
python .claude/scripts/query.py docs read <document_id> [--max-chars N]
python .claude/scripts/query.py docs info <document_id>

# Google Drive
python .claude/scripts/query.py drive find "search term" [--type spreadsheet|document|folder|presentation|pdf] [--max N]
python .claude/scripts/query.py drive list [--type TYPE] [--max N]
python .claude/scripts/query.py drive get <file_id>

# HubSpot CRM — reads
python .claude/scripts/query.py hubspot contacts [--max N]
python .claude/scripts/query.py hubspot companies [--max N]
python .claude/scripts/query.py hubspot deals [--max N] [--stage <stage_id>]
python .claude/scripts/query.py hubspot search --query "example.com"
python .claude/scripts/query.py hubspot pipelines
python .claude/scripts/query.py hubspot properties [contacts|companies|deals]
python .claude/scripts/query.py hubspot overdue-invoices
python .claude/scripts/query.py hubspot silent-contacts
python .claude/scripts/query.py hubspot stale-deals

# HubSpot CRM — writes (internal CRM state — Advisor-mode allows direct writes)
python .claude/scripts/query.py hubspot create-contact --email X [--firstname Y] [--lastname Z] \
    [--phone P] [--company-domain D] [--urgent true|false] [--conflict true|false] \
    [--conflict-reason "..."] [--preferred-channel email|whatsapp|slack|facebook_dm] \
    [--lifecyclestage lead|...]
python .claude/scripts/query.py hubspot update-contact <id|email> [--urgent ...] [--phone ...] \
    [--firstname ...] [--lastname ...] [--lifecyclestage ...]
python .claude/scripts/query.py hubspot archive-contact <id|email>
python .claude/scripts/query.py hubspot create-company --name "..." --domain D \
    [--engagement retainer|project|prospect|dormant] [--retainer-gbp N] [--contract-end YYYY-MM-DD]
python .claude/scripts/query.py hubspot update-company <id|domain> [...]
python .claude/scripts/query.py hubspot archive-company <id|domain>
python .claude/scripts/query.py hubspot create-deal --name "..." --amount N --stage <label> \
    [--pipeline Consultancy] [--currency GBP|EUR|USD] [--contact-email X] [--company-domain D] \
    [--service-line ai_agentic|custom_app|saas|marketing_ops|agri_ai|advisory] \
    [--source cold|inbound|referral|content] [--close-date YYYY-MM-DD] [--probability 0..1]
python .claude/scripts/query.py hubspot move-deal <id> --to-stage <label>
python .claude/scripts/query.py hubspot update-deal <id> [--amount N] [--close-date ...] [--probability ...]
python .claude/scripts/query.py hubspot close-deal <id> --as won|lost
python .claude/scripts/query.py hubspot archive-deal <id>
python .claude/scripts/query.py hubspot add-note --about <type>:<id|key> --text "..."
python .claude/scripts/query.py hubspot create-task --about <type>:<id|key> --title "..." --due YYYY-MM-DD [--notes "..."]
python .claude/scripts/query.py hubspot log-call --with contact:<id|email> --summary "..." [--duration-min N] [--disposition "..."] [--direction in|out]
python .claude/scripts/query.py hubspot log-meeting --with contact:<id|email> --title "..." --start <iso> --end <iso> [--notes "..."]
python .claude/scripts/query.py hubspot log-email --with contact:<id|email> --subject "..." --direction in|out --sent-at <iso> [--body "..."]
python .claude/scripts/query.py hubspot associate --from <type>:<id|key> --to <type>:<id|key> [--type-id N]
python .claude/scripts/query.py hubspot unassociate --from <type>:<id> --to <type>:<id>

# HubSpot tickets — Fredis Review queue
python .claude/scripts/query.py hubspot create-ticket --subject "..." \
    [--content "..."] [--lane email_hub|vtv|cab|content|ops|client|admin] \
    [--urgency today|this_week|whenever] [--skill <name>] \
    [--draft-path "Fredis/Memory/drafts/active/<skill>/<file>.md"] \
    [--contact-id <id>] [--company-id <id>] [--deal-id <id>]
python .claude/scripts/query.py hubspot get-ticket <ticket_id>
python .claude/scripts/query.py hubspot move-ticket <ticket_id> --to-stage "Drafted|In review|Needs send"
python .claude/scripts/query.py hubspot close-ticket <ticket_id> --as actioned
python .claude/scripts/query.py hubspot close-ticket <ticket_id> --as rejected [--note "..."]
python .claude/scripts/query.py hubspot list-tickets [--lane <lane>] [--urgency <urgency>] [--max N]
python .claude/scripts/query.py hubspot queue   # shortcut: open tickets grouped by urgency

# GitHub — read-only
python .claude/scripts/query.py github recent [--hours N]
python .claude/scripts/query.py github review-requests
python .claude/scripts/query.py github mentions [--hours N]
python .claude/scripts/query.py github ship

# GitHub Projects v2 — Lanes
python .claude/scripts/query.py lanes list
python .claude/scripts/query.py lanes breached
```

## HubSpot writes — Advisor-mode boundary

Writing **internal CRM state** (contacts/companies/deals/notes/tasks/logged engagements) is permitted directly — these are equivalent to taking notes on Linards's behalf inside his own system.

What still routes through `Fredis/Memory/drafts/active/` and is **never** sent via HubSpot:
- Outbound email via HubSpot's email tool → `drafts/active/client-comms/`
- Quotes / invoices to clients → `drafts/active/finance/`

Principle: **logging ≠ sending**. Recording that a call happened is internal state. Sending a new message is external comm. If in doubt, draft it.

## Setup

If integrations aren't configured yet:
```bash
cd .claude/scripts && uv run python setup_auth.py --check
```

## Notes

- Gmail + Calendar + Sheets + Docs + Drive share a single Google OAuth token
- Sheets has read/write access; Docs and Drive are read-only
- Slack uses Bot Token from .env
- Use `drive find` to locate file IDs by name, then pass to `sheets read` or `docs read`
- Gmail attachments: use `gmail attachments` to list, then `gmail download-attachment` to save to disk. Once downloaded, use the Read tool (images) or pdf skill (PDFs) to process the file content.
