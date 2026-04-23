# Slack integration — thread confirmation format

How `draft-reply` tells Linards, in the thread he's working from, that a draft is ready.

## Principle

The Slack post from Fredis contains **only** a short confirmation note — path to the markdown, Gmail draft ID if applicable. Never the draft body itself. Two reasons:

1. Advisor-mode boundary — the draft sits in `drafts/active/` until Linards reviews. Posting the body in Slack would duplicate content in an ephemeral surface (search-indexed thread history) where revision becomes fragmented.
2. Voice-matching integrity — when Linards copy-edits before sending, the posted-in-Slack version would lie about what actually went out. The draft file + eventual move to `drafts/sent/` is the audit trail.

## Confirmation payload — email flavour

Posted as a reply in the same Slack thread that invoked the skill:

```
Drafted to `Fredis/Memory/drafts/active/draft-reply/2026-04-23-email-atis-cab-q3-scope.md`
— Gmail draft created (id `abc123`).
```

If Gmail surfacing failed:
```
Drafted to `Fredis/Memory/drafts/active/draft-reply/2026-04-23-email-atis-cab-q3-scope.md`
— Gmail surfacing failed (<short reason>). Copy-paste manually.
```

## Confirmation payload — Slack flavour

Posted as a reply in the same thread:

```
Drafted to `Fredis/Memory/drafts/active/draft-reply/2026-04-23-slack-atis-cab-update.md`
— copy + paste into the thread when you're ready.
```

No bot-side ephemeral message, no DM, no thread-duplication. Match the existing heartbeat summary convention.

## Slack-type draft frontmatter

For `type: slack`, the frontmatter differs from email in two fields:

```yaml
---
skill: draft-reply
lane: cab
created: 2026-04-23
status: active
type: slack
source_id: C01234ABCD:1713880000.123456   # <channel_id>:<thread_ts>
channel: C01234ABCD                        # for faster Slack URL reconstruction
language: lv
voice_refs:
  - drafts/sent/lv-seed/2026-02-12-atis-invoice.md
  - drafts/sent/2026-03-08-retainer-scope-change.md
---
```

- `recipient` and `subject` are not required for Slack drafts (no email-style addressing).
- The body template keeps the same section order: `# Reply draft`, `## Original Message`, `## Voice References`, `## Draft Reply`, `## Notes`. The `## Draft Reply` section header is preserved even though there's no Gmail surfacing — the heartbeat reconciler uses the same marker for both flavours.

## Sent-detection for Slack drafts

The heartbeat's `reconcile_active_drafts` only reconciles `type: email` currently. Slack drafts sit in `drafts/active/draft-reply/` until Linards manually moves them to `drafts/sent/` after copying into Slack. Future phase: Slack-side sent detection (look for Linards's own subsequent message in the thread) — out of Phase 12 scope.

## Confirmation-note length budget

One or two sentences. Emoji-free. If Gmail surfacing failed, the reason fits inline — don't dump the full traceback. Full error goes to today's daily log under `### draft-reply — Gmail surfacing`, short reason goes to the Slack note.
