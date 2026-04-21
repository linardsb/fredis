# Threat Model — MCP Servers

Audit + keep/remove decision for every MCP server currently configured,
per Phase 9.1 of `.agent/plans/phase8-security-hardening.md`.

Captured via `claude mcp list` on 2026-04-21:

```
claude.ai Google Drive     — https://drivemcp.googleapis.com/mcp/v1     — ! Needs authentication
claude.ai Gmail            — https://gmailmcp.googleapis.com/mcp/v1     — ! Needs authentication
claude.ai Google Calendar  — https://calendarmcp.googleapis.com/mcp/v1  — ! Needs authentication
claude.ai Figma            — https://mcp.figma.com/mcp                  — ✗ Failed to connect
inspector-gateway          — http://127.0.0.1:7778/mcp (HTTP)           — ✗ Failed to connect
pencil                     — /Applications/Pencil.app/.../mcp-server    — ✓ Connected
jcodemunch                 — uvx jcodemunch-mcp                         — ✓ Connected
jdocmunch                  — uvx jdocmunch-mcp                          — ✓ Connected
```

## Per-server decision table

| Server | Can read | Can write | Why installed | Decision | Rationale |
|--------|----------|-----------|---------------|----------|-----------|
| `pencil` | Local `.pen` design files via Pencil.app API | Yes — `batch_design` edits `.pen` files in place | Design tooling for Linards's product work | **Keep** | Local-only process (`/Applications/Pencil.app/...`); writes confined to `.pen` files which are not part of Fredis's threat surface. |
| `jcodemunch` | Repo code (via `uvx jcodemunch-mcp`); token-efficient code search (`search_symbols`, `find_references`, `get_file_outline`, etc.) | No — read-only | Auto-index + structured code queries; referenced in user-level `CLAUDE.md` as the default token-efficient research tool | **Keep** | Read-only; local `uvx` process; saves significant tokens on research queries. |
| `jdocmunch` | Documentation files (markdown, HTML); section-level retrieval (`search_sections`, `get_section`, `get_toc_tree`) | No — read-only | Doc search for skill references + vault docs | **Keep** | Same as jcodemunch — read-only, local, token-efficient. |
| `claude.ai Gmail` | Gmail (authenticated via Claude.ai OAuth) | Yes — if authenticated and scopes allow | Duplicate of the `direct-integrations` Gmail path in `.claude/scripts/integrations/gmail_api.py` + `query.py gmail` CLI | **Remove** | **Duplicates existing direct OAuth integration.** `USER.md` already states "always prefer direct integrations over Zapier" — same logic applies here. The direct path is audited, has advisor-mode controls (no send without `--i-confirm-send` flag), and is wired into the heartbeat. The MCP path bypasses those controls. |
| `claude.ai Google Calendar` | Calendar | Yes — if authenticated | Duplicate of `integrations/calendar_api.py` | **Remove** | Same rationale as Gmail — duplicate. |
| `claude.ai Google Drive` | Drive | Yes — if authenticated | Duplicate of `integrations/drive_api.py` + `query.py drive` CLI | **Remove** | Same rationale. |
| `claude.ai Figma` | Figma (not authenticated, failing to connect) | — | Unclear (likely an auto-added connector from Claude.ai) | **Remove** | Not in use (failing to connect), not referenced anywhere in the repo. Prune to shrink attack surface. |
| `inspector-gateway` | `http://127.0.0.1:7778/mcp` | Unknown (not connecting) | Local HTTP gateway — purpose unclear | **Remove (pending confirmation)** | Not connecting; not referenced anywhere in the repo. If Linards confirms no active use, remove. If it's an in-development tool, leave and document in a follow-up. |

## Trust-boundary summary (for the three to KEEP)

- **pencil** — writes bounded to `.pen` files. Threat model: a malicious
  `.pen` file could be crafted to feed the MCP invalid data, but that
  doesn't cross into Fredis's memory / Slack / email surface.
- **jcodemunch** — read-only. Zero-write means no direct mutation risk.
  The MCP's responses are already passed through the hooks on the parent
  tool call (Bash, Read) because they're just text returned to Claude.
- **jdocmunch** — read-only. Same as jcodemunch.

## Removal mechanics

Removal happens via `claude mcp remove <name>` (user-level config). Example:
```
claude mcp remove "claude.ai Gmail"
claude mcp remove "claude.ai Google Calendar"
claude mcp remove "claude.ai Google Drive"
claude mcp remove "claude.ai Figma"
claude mcp remove "inspector-gateway"
```

**GATE:** Do NOT execute these commands without Linards's explicit
approval. Removal is reversible (`claude mcp add` re-adds) but could
break a workflow the audit missed. Approve this table first.

## Verification after removal

1. Run `claude mcp list` — confirm only `pencil`, `jcodemunch`,
   `jdocmunch` remain.
2. Restart Claude Code in this repo — confirm session-start auto-index
   (jcodemunch + jdocmunch) still works per global `CLAUDE.md`.
3. Spot-check heartbeat run — confirm direct-integrations path still
   queries Gmail / Calendar without depending on the removed MCPs.
