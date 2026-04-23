---
name: draft-reply
description: |
  Draft a voice-matched email or Slack reply. Retrieves 3 similar past replies from
  drafts/sent/ for style, writes a structured draft to drafts/active/draft-reply/,
  and for Gmail also creates a native Gmail draft via query.py so it's visible in
  Linards's inbox. Advisor-mode — never sends; Linards reviews and sends himself.
  Use when user says: "draft a reply to <X>", "reply to this", "draft a response",
  "voice-match a reply", "write a draft for <email/slack thread>", "@Fredis draft
  this", "help me reply to <X>".
---

# draft-reply

Voice-matched email or Slack reply drafting. Advisor-mode — writes markdown to
`drafts/active/draft-reply/`; for email, also creates a native Gmail draft so the
reply lands in the inbox for manual review + send.

## When to use

- Linards has a Gmail thread or Slack thread open and wants Fredis to draft a reply
- The reply should sound like *him*, not like generic assistant output
- The draft needs to survive review — he'll tweak and send from Gmail / Slack himself

Fredis never sends. `_update_draft_and_move_to_sent` (heartbeat.py:1086) handles
sent-detection on the next heartbeat tick and moves the draft to `drafts/sent/` — the
voice corpus grows as Linards sends replies.

## Shared primer

- Draft path convention — `_shared/draft-path-convention.md`.
- Lane taxonomy — `_shared/lanes.md`.
- Advisor-mode never-send boundary — `Fredis/Memory/SOUL.md`.

## Workflow

### 1. Detect reply type

- Gmail message ID / thread link in the user message → `type: email`.
- Slack thread with email-forward content Fredis already has in context → `type: email`.
- Slack thread with regular chat content → `type: slack`.
- Ambiguous → ask once: *"Email or Slack?"* Don't guess.

### 2. Retrieve source content

- **Email:** `cd .claude/scripts && uv run python query.py gmail thread <thread_id>` — pull the full thread. The last message from someone-not-Linards is what we're replying to. Keep the thread text for the `## Original Message` section.
- **Slack:** already in-context (Fredis is replying in the thread).

### 3. Voice-match

See `references/voice-matching.md` for the full contract. Summary:

- Construct a 3–8-word topic descriptor (e.g. `pricing change notice to retainer client`, `VAT filing question from accountant`).
- `cd .claude/scripts && uv run python memory_search.py "<descriptor>" --mode hybrid --path-prefix drafts/sent --limit 3`.
- Cap voice-reference text at ~400 tokens total. Trim each match to its opening paragraph if needed.

### 4. Language routing

- Recipient email domain or Slack username matches a Latvian contact flagged in `USER.md` → draft in Latvian, narrow voice-match to `--path-prefix drafts/sent/lv-seed`.
- Default: English.

See `references/voice-matching.md` §Language routing for the recipient-lookup rule.

### 5. Write the draft file

Path:
```
Fredis/Memory/drafts/active/draft-reply/YYYY-MM-DD-<type>-<slug>.md
```

Slug convention: `<recipient-or-thread-hint>-<topic>`, kebab-case, 2–5 words, ASCII only. Example: `atis-cab-q3-scope`. If the same recipient / topic combination has already landed today, append a short disambiguator (`-v2`) rather than collide.

Example path:
```
Fredis/Memory/drafts/active/draft-reply/2026-04-23-email-atis-cab-q3-scope.md
```

**Frontmatter (exact field names — consumed by gmail-integration and heartbeat reconciler):**
```yaml
---
skill: draft-reply
lane: cab                          # email-hub | vtv | cab | other | na
created: 2026-04-23
status: active                     # MUST be "active" — heartbeat replaces with "sent" on reconcile
type: email                        # email | slack
source_id: <gmail-message-id or slack-channel:thread_ts>
recipient: Atis <atis@example.lv>  # required for type: email
subject: Re: Cab Q3 scope          # required for type: email
language: lv                       # en | lv
voice_refs:
  - drafts/sent/lv-seed/2026-02-12-atis-invoice.md
  - drafts/sent/2026-03-08-retainer-scope-change.md
---
```

Reasons for the `status: active` choice (against the `_shared` convention's default `status: draft`): `heartbeat.py:1096` does an exact `status: active` → `status: sent` replacement. Writing `status: draft` here would leave the frontmatter stale after Linards sends the reply. The convention's `draft` default applies to skills whose drafts Fredis never reconciles automatically; `draft-reply` is reconciled, so it must match the reconciler's contract.

**Body sections (fixed order, exact headings):**

```markdown
# Reply draft: <subject or thread topic>

## Original Message

<verbatim, quote-blocked — the message we're replying to>

## Voice References

- `drafts/sent/.../<file1>.md` — *"<1-line excerpt>"*
- `drafts/sent/.../<file2>.md` — *"<1-line excerpt>"*
- `drafts/sent/.../<file3>.md` — *"<1-line excerpt>"*

## Draft Reply

<the actual draft — this section is consumed by both
`create_gmail_draft_from_file` (Gmail draft body) and
`_update_draft_and_move_to_sent` (replaced with `## Actual Reply` on reconcile).
Section header MUST be exactly `## Draft Reply` — capital R.>

## Notes

<optional — caveats, alternative phrasings, things Linards might want to tweak>
```

### 6. Surface to Gmail (email only)

After the markdown file is written:
```bash
cd .claude/scripts && uv run python query.py gmail create-draft --from-file <absolute-path-to-draft>
```

The script reads `recipient`, `subject`, `source_id` from frontmatter and the body from the `## Draft Reply` section. Reply-threading is derived from `source_id`. A successful call writes `gmail_draft_id: <id>` back into the frontmatter — that's how Fredis prevents duplicate Gmail drafts on re-invocation.

If the Gmail create-draft call fails (auth error, API timeout): the markdown file still exists. Log the failure to today's daily log under a `### draft-reply` heading and surface the path back to Linards so he can copy-paste manually. Don't retry — auth failures need his attention.

### 7. Surface to Slack

Slack flavour: markdown file only. No bot post of the draft content itself. Confirmation note in the thread, short:

> Drafted to `drafts/active/draft-reply/2026-04-23-email-atis-cab-q3-scope.md`
> — Gmail draft created (id `abc123`).

For Slack-type drafts:
> Drafted to `drafts/active/draft-reply/2026-04-23-slack-atis-cab-update.md`
> — copy + paste into the thread when you're ready.

## Boundary — what this skill does not do

- Creates Gmail *drafts* only. Never invokes any Gmail send endpoint. The send happens from Gmail's UI when Linards is ready.
- For Slack, only posts the short confirmation note — not the draft body. See `references/slack-integration.md` for the exact confirmation payload.
- Never writes to `drafts/sent/` directly. Only the heartbeat's reconciler moves files there.
- Never auto-picks between email and Slack when ambiguous. Asks once.
- Never writes to `MEMORY.md`, `USER.md`, or other top-level vault files. Drafts folder only.

## References

| File | Load when |
|---|---|
| `references/voice-matching.md` | Picking topic descriptor, path-prefix, LV/EN corpus split, trim strategy |
| `references/gmail-integration.md` | Frontmatter contract with `query.py gmail create-draft --from-file`, error modes, duplicate prevention |
| `references/slack-integration.md` | Slack-thread confirmation format, Slack draft frontmatter |

## Tests

See `.claude/scripts/tests/test_draft_reply_skill.py` — convention test (path shape, frontmatter keys, section headings) and Latvian-routing test (path-prefix narrows to `drafts/sent/lv-seed`).
