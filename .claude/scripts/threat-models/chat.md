# Threat Model — `chat/engine.py`

Interactive Slack-driven Agent SDK session. One thread = one session.
Socket-mode WebSocket in; persisted via `chat.db`. Advisor-mode
invariants: never send, never edit SOUL, never leave sandbox.

## 1. Inputs

- **Inbound Slack text** (user's DM / @mention / thread reply). This is
  the primary untrusted input surface — it's human-typed AND can be a
  pasted email / thread / prompt-engineering snippet.
- **Slack attachments** (image files). Saved to `inbox/YYYY-MM-DD/`,
  paths are harness-generated and sit OUTSIDE the trust boundary.
- **Heartbeat thread context** — when replying to a heartbeat alert
  thread, `engine.py` fetches the original alert text from
  `session_store.get_heartbeat_thread()`.

**Trust boundary (Phase 3):** inbound user text is now wrapped in
`<external_data source="slack_inbound">` + `TRUST_BOUNDARY_INSTRUCTION`
before it reaches `query()`. A flagged-notice is prepended inside the wrap
when `check_injection_patterns` returns any hit. **No short-circuit** —
the agent still runs; the wrap + notice are the defense (advisor-mode
policy for a single-user system with real false-positive shapes in
Linards's forwarded emails).

## 2. Tools

`allowed_tools = ["Read", "Write", "Edit", "Bash", "Glob", "Grep",
"Skill", "WebSearch", "WebFetch", "NotebookEdit"]`.

Blast radius same as heartbeat (identical hook stack). Additionally:
- `WebSearch` / `WebFetch` — can pull untrusted web content; the prompt
  already tells Claude responses are shown directly, so a web-sourced
  injection would still land inside the already-wrapped user inbound
  turn.

## 3. Writes

- **Drafts** (`Fredis/Memory/drafts/active/`) — advisor-mode approval gate.
- **Daily log** — append-only via the same `append_to_daily_log` helper.
- **chat.db** — session store (local file).
- **File system** — sandbox-gated by `block-dangerous-commands.check_write_target`.

Approval gate: advisor mode. Slack sends happen through the legitimate
`adapters/slack.py:send()` path — the bot itself is allowed to post to
the single user channel because that is the user's chat surface.
Mention-neutralisation in Phase 4 prevents broadcast notifications.

## 4. Memory reads

- Session history via `ClaudeAgentOptions.resume=agent_session_id`.
  Past-turn content is trusted because the caller is Linards only
  (CHAT_ALLOWED_USERS enforced).
- `Fredis/Memory/*.md` — read via the `Read` tool. Hooks gate sensitive
  paths; injection pipeline is not re-applied on these internal reads
  (they're own-authored, not external-sourced).

## 5. Outputs

- **Slack DM / thread** to the authorised user only.
  - Allowlist check: `SlackAdapter._is_allowed(user_id)` — fail closed
    when list is empty.
  - Output filter (Phase 4): `_neutralise_mentions` zero-width-joins
    `<!channel>`, `<!here>`, `<!everyone>`, `<@USER_ID>`,
    `<!subteam^…>` so a Claude reply quoting one of these doesn't
    fire a Slack mention.
- **Image uploads** via `files_upload_v2` — scoped to the current
  thread.

## 6. Failure mode

- **Injection verdict=fail on inbound:** Phase 3 policy is **wrap +
  prepend flag note, not short-circuit**. Defense: trust boundary +
  harness instruction + Claude's own refusal. Advisor-mode tool-gate
  catches any comply-attempt (send, SOUL, secrets).
- **Heartbeat-context branch:** alert text is separately wrapped as a
  distinct `<external_data source="heartbeat_alert">` layer; does not
  double-wrap with the inbound layer.
- **SDK error:** caught, user sees `"Sorry, I hit an error: <e>"`.
- **Mention-filter miss:** even if a new broadcast shape is added by
  Slack, the `@`-less zero-width-joined form still reads correctly
  for the user.

Invariants preserved under all failure modes:
- Slack posts only to the authorised user's thread / DM.
- No SOUL edit (standalone hook).
- No outbound mutation APIs (`block-dangerous-commands`).
- `@channel`-class broadcasts neutralised.
