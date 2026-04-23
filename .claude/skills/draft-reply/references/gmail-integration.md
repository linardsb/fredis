# Gmail integration — `query.py gmail create-draft --from-file`

How `draft-reply` surfaces email drafts into Gmail's native Drafts folder so Linards can review and send from the inbox.

## Invocation

```bash
cd .claude/scripts && uv run python query.py gmail create-draft --from-file <absolute-path-to-draft>
```

- Positional `message_id` is not required — `--from-file` parses the `source_id` frontmatter field for reply-threading.
- The script wraps `integrations.gmail.create_gmail_draft_from_file` (gmail.py:516).
- Runs once per draft. A second invocation against the same file will raise `ValueError: Gmail draft already exists: <id>` — that's deliberate, it prevents duplicate Gmail drafts stacking up in the Drafts folder.

## Frontmatter contract

`create_gmail_draft_from_file` reads these keys from the markdown draft:

| Key | Required | Role |
|---|---|---|
| `type` | yes | Must equal `email`. Function raises `ValueError` otherwise. |
| `recipient` | yes | Plain email (`atis@example.lv`) or `Name <email>` — passed as the `To:` header. |
| `subject` | yes | Gmail Subject header. Function raises `ValueError` if missing. |
| `source_id` | recommended | Gmail message ID or thread ID of the message being replied to. Used to set the Gmail draft's `threadId` so it attaches to the original conversation. |
| `gmail_draft_id` | written on success | The function writes `gmail_draft_id: <id>` back into the frontmatter to mark the draft as already surfaced. Re-running raises `ValueError` to prevent duplicates. |

If `source_id` is missing or invalid, the Gmail draft is created as a standalone message (no thread attachment) — not an error, but Linards will need to remember what it replied to.

## Body contract

The function extracts reply text from the `## Draft Reply` section of the markdown file. Exactly that heading — capital R, no trailing whitespace. Anything before this heading (original message, voice references, notes) is ignored. Anything after this heading up to the next top-level heading becomes the Gmail body.

If the section is missing, the function raises `ValueError: No '## Draft Reply' section found in <filename>`.

## Threading behaviour

If `source_id` is present, the function resolves it to a thread ID, then finds the last message in that thread so Gmail attaches the draft at the bottom of the conversation (not a reply to an old message). This matters when you forward-and-reply loops have multiple messages in the thread — the draft shows up threaded to the latest, not buried mid-thread.

## Error handling

Fredis catches the subprocess error and:

1. Logs `Gmail create-draft failed for <path>: <error>` to today's daily log under `### draft-reply — Gmail surfacing`.
2. Posts a Slack confirmation note that includes the failure reason: *"Drafted to \<path\>. Gmail surfacing failed (auth error) — copy-paste manually."*
3. Leaves the markdown file in place. Linards can retry after fixing auth, or copy the draft directly.

Never retry automatically — auth errors need Linards to re-run `setup_auth.py`. A retry loop in the skill just burns tokens.

## What about the `--to` / `--subject` / `--body` flags?

Those are for manual-mode invocation (bypass the markdown file entirely). `draft-reply` never uses manual mode — the markdown file is the source of truth and the Gmail draft is a surfaced copy. Manual mode is reserved for the heartbeat's older one-shot draft path.

## Duplicate-prevention lifecycle

1. First invocation: writes markdown, calls `create-draft --from-file`, function writes `gmail_draft_id: abc123` back into frontmatter.
2. Linards reviews and sends from Gmail.
3. Heartbeat reconciles on the next tick (`_update_draft_and_move_to_sent`), sees a matching sent reply, moves the markdown to `drafts/sent/`.
4. `gmail_draft_id` is retained in the sent record — useful for audit (which Gmail draft did this correspond to).

If Linards deletes the Gmail draft manually without sending, the `gmail_draft_id` is stale. Re-running `draft-reply` against the same source would see the `source_id` and create a new markdown file with a fresh slug (or collision-suffixed slug), not re-use the stale one. The old markdown file sits in `drafts/active/` until Linards moves it to `drafts/expired/`.
