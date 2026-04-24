---
name: client-log
description: |
  Append a dated entry to a client's retainer file (context, decisions, open items).
  Creates the client file if it does not exist. Use when user says: "log client <X>",
  "client-log <Y>", "client update for <Z>", "note on <client>", "record for <X> —
  <message>".
---

# client-log

Appends dated entries to `Fredis/Memory/retainers/<client-slug>.md`. Creates the
file on first use. Keeps retainer context retrievable without manual folder
hygiene.

## When to use

- Linards just had a meaningful client interaction (call, decision, scope change,
  invoice event) and wants it recorded against the client.
- A heartbeat or meeting-note uncovered a client-relevant fact Linards wants
  promoted to the client's permanent record.
- One-sentence "spoke to Client X" pings go in the daily log, not here. Client-log
  entries are multi-field (context + decisions + open items).

## Shared primer

- Draft path convention — `_shared/draft-path-convention.md`. **This skill is a
  documented carve-out**, same pattern as `meeting-notes` — capture-mode files
  land in their topical folder, not under `drafts/active/`.

## Path — capture-mode carve-out

```
Fredis/Memory/retainers/<client-slug>.md
```

Slug: kebab-case, lowercase, ASCII. Derived from the client's canonical name.

The `retainers/` folder already exists in the vault. First-time clients get a new
file created; returning clients get appended to.

Rationale for breaking the `drafts/active/` convention: same as `meeting-notes`.
Retainer files are not send-candidates — they're the permanent record of a client
relationship. Routing through `drafts/active/client-log/` would force manual
moves with no review decision. Searches like
`memory_search.py --path-prefix retainers/` work naturally when the files live
under `retainers/` directly.

## Client-slug resolution

1. **Exact match.** Check for `retainers/<slug>.md` where slug matches the
   client identifier Linards used (after kebab-case normalisation).
2. **Fuzzy match.** If multiple retainer files could match (e.g. Linards said
   "Ana" and both `ana-suarez.md` and `ana-gomez.md` exist), ask once:
   *"Which client? Existing: ana-suarez, ana-gomez. Or new?"*
3. **New client.** If Linards confirms a new client, prompt once for the
   canonical display name, slugify it, create the file with the first-entry
   header (see §First-entry format below), then append the entry.

Never silently overwrite. If `retainers/<slug>.md` exists and the invocation is
ambiguous, ask. Better to burn one message than merge two clients' records.

## Append format

Every entry is a dated block separated by two blank lines + `---` so visual
scanning in Obsidian stays easy.

```markdown
## 2026-04-23

**Context:** Call re Q3 scope. Client wants to cut feature X; happy with
April deliverable; asked about invoicing cadence.

**Decisions:**
- Cut feature X from Q3 scope.
- Keep monthly invoice rhythm (first of month).

**Open items:**
- Revised scope doc — Linards, due 2026-04-30
- Feature X removal impact on pricing — needs confirmation before next invoice

**Sources:** gmail thread `<thread_id>`, meeting-notes `meetings/2026-04-23_client-cab.md`


---
```

The `**Context:** ... **Decisions:** ... **Open items:** ... **Sources:** ...`
structure is the contract. Leave a section out entirely if it's empty — don't
write `None.` filler. `**Sources:**` is optional but useful when the entry
references other vault files.

## First-entry format (new client)

When `retainers/<slug>.md` doesn't exist, create it with a frontmatter header,
name, short overview, then the first dated entry:

```markdown
---
type: retainer
client: Ana Suarez
lane: other             # email-hub | vtv | cab | other | na
engaged: 2026-04-23
status: active          # active | paused | ended
---

# Ana Suarez

<2–3 sentence overview pulled from the first entry's context — who the client
is, what the engagement is, how Fredis knows about it. Not a sales pitch.>

## Log

## 2026-04-23

**Context:** <first entry body>

**Decisions:**
- <...>

**Open items:**
- <...>


---
```

The `## Log` heading is a stable anchor — future appends go after it. The
overview paragraph is written once and may drift over time; Linards updates it
manually when the engagement changes significantly.

## Boundary — what this skill does not do

- Never creates HubSpot tasks or tickets from `**Open items:**`. Those stay as
  markdown checkboxes; Linards creates tasks himself.
- Never posts to Slack beyond the short confirmation note:
  > Logged to `Fredis/Memory/retainers/ana-suarez.md`.
- Never writes to `drafts/`, `MEMORY.md`, `USER.md`, or other vault top-level
  files. `retainers/` only.
- Never modifies the frontmatter or overview of an existing retainer file on an
  append — only the body after the `## Log` anchor.

## Tests

See `.claude/scripts/tests/test_client_log_skill.py`:
- append-to-existing — new entry lands after `## Log`, existing content intact
- create-new-file — frontmatter + overview + first entry written correctly
- slug-collision — ambiguous invocation prompts rather than overwriting
