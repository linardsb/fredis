# Voice-matching — contract

How `draft-reply` selects 3 prior replies from `drafts/sent/` so the new draft sounds like Linards.

## Invocation

```bash
cd .claude/scripts && uv run python memory_search.py "<topic descriptor>" --mode hybrid --path-prefix drafts/sent --limit 3
```

- `--mode hybrid` — combines keyword FTS (0.3) with vector similarity (0.7). Keyword alone misses paraphrases; vector alone misses rare domain words. Hybrid beats either.
- `--path-prefix drafts/sent` — restricts the corpus to sent replies. Never matches against active drafts or non-reply memory.
- `--limit 3` — three references is the sweet spot. One is noisy, five eats too much context.

## Topic descriptor

3–8 words. Goal: encode who the recipient is, what the message is about, and the register. Examples:

| Source | Topic descriptor |
|---|---|
| Pricing-change email to a retainer client | `pricing change notice retainer client` |
| VAT filing question from an accountant | `VAT filing question to accountant` |
| Cousin asking about a family visit | `family visit planning casual latvian` |
| Slack thread with a prospect, casual register | `prospect Slack follow-up casual` |

Not the subject line. Not the full first sentence. The smallest descriptor that retrieves something useful. If the first search returns nothing or returns noise, re-run with a narrower / broader descriptor — two tries max, then fall back to no voice reference.

## Trim strategy

Raw matches can be long. Cap the total voice-reference block at ~400 tokens (roughly 2000 characters of English prose, less for Latvian). Strategy:

1. Read each match's full content.
2. Keep the opening paragraph of each match. Usually sufficient to convey register + phrasing.
3. If still over budget, drop the lowest-scoring match and keep two.

Record the source path in the draft's `voice_refs:` frontmatter list — future queries see which prior replies shaped this one.

## Language routing

Check the recipient against `USER.md` → *Key Contacts* section. If the recipient is flagged Latvian-speaking:

```bash
cd .claude/scripts && uv run python memory_search.py "<topic descriptor>" --mode hybrid --path-prefix drafts/sent/lv-seed --limit 3
```

The `lv-seed/` subfolder is Linards's pre-seeded Latvian email corpus. Narrowing to it avoids the hybrid search pulling English matches that would dilute Latvian voice.

If `USER.md` doesn't resolve the contact cleanly:
- Recipient email domain ends in `.lv` → treat as Latvian.
- Recipient name on the `Collaborators/` file (e.g. `atis-vikis.md`) with `Language: Latvian` field → treat as Latvian.
- Otherwise → default English.

## When voice-match returns nothing

- First retry: broaden the descriptor (drop the most specific word).
- Second retry: swap `--path-prefix drafts/sent` for no prefix — query across all memory. This pulls in any source-material that mentions similar topics, imperfect but still better than generic assistant voice.
- Third and final: write the draft in neutral SOUL voice. Note `voice_refs: []` in the frontmatter so the failure is visible in post-hoc review.

Never make up voice references that don't exist. Empty `voice_refs:` is an honest signal; fabricated paths poison the audit trail.

## Budget

A voice-match round adds ~1–2 seconds (embedding the query) and costs one `memory_search.py` invocation. Do not cache — the corpus grows every time Linards sends a reply, and a cache would freeze voice drift. Re-run every invocation.
