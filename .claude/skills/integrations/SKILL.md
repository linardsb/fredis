---
name: integrations
description: Query external platforms from Fredis — Gmail / Google Calendar / Asana / Slack / Google Sheets / Google Docs / Google Drive / HubSpot CRM / GitHub (direct Python APIs) plus any MCP server (Zapier, Sequential Thinking, filesystem, etc.) via a universal MCP client. Use when user says "check email", "show calendar", "list asana tasks", "check slack", "read this spreadsheet", "open this google doc", "find files in drive", "create hubspot contact", "move deal to signed", "my PR reviews on github", "connect to MCP server", "list MCP tools", "use sequential thinking", "call Zapier action", or any cross-platform query.
---

# integrations

TL;DR — all Fredis's external platform surfaces live here. Prefer direct Python APIs (`references/direct-integrations.md`) over MCP wherever both exist; MCP (`references/mcp-client.md`) is the fallback for platforms without a direct integration.

## Routing table

| Trigger | Reference |
|---|---|
| "check email", "show gmail", "unread", "urgent emails", "search email", "create gmail draft", "download attachment" | `references/direct-integrations.md` — Gmail section |
| "show calendar", "today's events", "upcoming events", "next meeting" | `references/direct-integrations.md` — Calendar section |
| "list asana tasks", "my tasks", "overdue", "due soon", "create task", "complete task", "move task" | `references/direct-integrations.md` — Asana section |
| "check slack", "slack messages", "slack channels", "update slack message" | `references/direct-integrations.md` — Slack section |
| "read spreadsheet", "sheets", "google sheet", "append row" | `references/direct-integrations.md` — Sheets section |
| "google doc", "read doc", "open doc" | `references/direct-integrations.md` — Docs section |
| "find in drive", "google drive", "list files" | `references/direct-integrations.md` — Drive section |
| "hubspot contacts", "create contact", "move deal", "add note on deal", "log call", "archive contact", "stale deals" | `references/direct-integrations.md` — HubSpot section |
| "github recent", "github review requests", "github mentions", "github ship" | `references/direct-integrations.md` — GitHub section |
| "lanes", "breached gates", "github project lanes" | `references/direct-integrations.md` — GitHub Projects v2 section |
| "connect to MCP server", "list MCP tools", "call Zapier action", "use sequential thinking", any generic MCP surface | `references/mcp-client.md` |

## CLI wrapper

All direct-API commands run via `python .claude/scripts/query.py <platform> <command>`. See the Gmail / Calendar / Asana / Slack / Sheets / Docs / Drive / HubSpot / GitHub sections in `references/direct-integrations.md` for the full command surface and authentication setup.

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/integrations/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub or any external comm service (Slack/Email/etc.) outside the HubSpot internal-state allowance
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

**Read-first bias.** Integrations are primarily read surfaces. Write operations (`gmail create-draft`, `asana create`, `sheets write`, `sheets append`, `asana comment`, `asana complete`, `asana move`, `slack update`, all `hubspot create-*`/`update-*`/`archive-*`/`add-note`/`create-task`/`log-*`/`associate`/`unassociate`) modify state on Linards's accounts — only run when explicitly asked and after surfacing intent.

**HubSpot write boundary.** Internal CRM mutations (contacts/companies/deals/notes/tasks/logged engagements) write directly. Outbound email through HubSpot's email tool, quotes, and invoices still route through `Fredis/Memory/drafts/active/` — **logging ≠ sending**.

## References

| File | Load when |
|---|---|
| `references/direct-integrations.md` | Querying Gmail, Calendar, Asana, Slack, Sheets, Docs, Drive, HubSpot, GitHub, GitHub Projects v2 directly |
| `references/mcp-client.md` | Connecting to an MCP server (Zapier, Sequential Thinking, filesystem, etc.) for a platform without a direct integration |
| `references/mcp-client/*` | MCP deep-reference (server catalog, example configs, Python MCP SDK guide) |
| `scripts/mcp_client.py` | Python MCP client implementation (called by `mcp-client.md` reference) |

## Anti-patterns

- Reaching for MCP when a direct integration exists. Direct integrations are faster, cheaper, and don't consume Zapier quota.
- Write operations without explicit Linards intent. All state-mutating calls are gated behind an explicit ask.
- Hardcoding account IDs / project GIDs / HubSpot record IDs in drafts. All such values live in `Fredis/Memory/USER.md` — read from there.
