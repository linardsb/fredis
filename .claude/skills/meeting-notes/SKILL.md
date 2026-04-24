---
name: meeting-notes
description: |
  Structured meeting-note capture. Prompts for attendees, agenda, decisions, action
  items with owners + due dates, writes to Fredis/Memory/meetings/. Use when user
  says: "capture meeting", "meeting notes for <X>", "log the meeting with <Y>",
  "take notes on this call", "write up the <X> meeting", "Atis call notes".
---

# meeting-notes

Structured meeting-note capture. Linards summarises or dictates; Fredis fills a
template and writes to `Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md`.

## When to use

- Linards just finished (or is mid-) a meeting and wants a retrievable record.
- The meeting had decisions, action items, or context worth surfacing in later
  heartbeat / memory-search queries.
- One-line reminders belong in a daily log, not here. Meeting-notes are for
  multi-paragraph captures with action items.

## Shared primer

- Lane taxonomy — `_shared/lanes.md`. The `lane:` frontmatter field maps to a
  product line so later searches can filter by lane.
- Draft path convention — `_shared/draft-path-convention.md`. **This skill is a
  documented carve-out** — see §Path below.

## Path — capture-mode carve-out

```
Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md
```

Example:
```
Fredis/Memory/meetings/2026-04-23_atis-cab-rollout.md
```

Slug: kebab-case, 2–5 words, usually `<counterparty>-<topic>` or `<topic>-<type>`.

### Why this breaks the drafts/active/ convention

The drafts-path convention exists to gate external sends — every file in
`drafts/active/` is a send-candidate awaiting Linards's review. Meeting notes
never send. They're captured artefacts, full stop.

Routing meeting notes through `drafts/active/meeting-notes/` would add a pointless
review step (Linards moves files manually with no decision to make) and bury
them under a retrieval prefix that means "unsent reply drafts". Searches like
`memory_search.py --path-prefix meetings/` work naturally because meeting notes
live at the top-level `meetings/` folder.

The carve-out is documented in `_shared/draft-path-convention.md` under *Capture-mode
exceptions*. `client-log` follows the same pattern for the same reason.

## First-run scaffold

If `Fredis/Memory/meetings/` does not yet exist, create it with a `README.md`
placeholder:

```markdown
# Meetings

Structured meeting captures written by the `meeting-notes` skill.

- One file per meeting, named `YYYY-MM-DD_<slug>.md`.
- Frontmatter: `type: meeting`, `date`, `attendees`, `lane`, `tags`.
- Body sections: Attendees, Agenda, Discussion, Decisions, Action items, Open questions.

Query via `memory_search.py --path-prefix meetings/` or read directly in Obsidian.
```

Only create the README on the very first invocation. Subsequent invocations land
alongside existing meeting files.

## Capture flow

1. **Parse invocation** for obvious fields. `capture meeting with Atis — Cab rollout`
   → attendees include Atis, topic is Cab rollout, lane is likely `cab`.
2. **Ask once, multi-part.** Don't serial-interrogate. Single question:
   *"Date (default today), other attendees, agenda bullets, decisions, action items
   with owner + due date. Anything I missed?"*
3. **Fill the template** below from the reply. Leave empty sections empty — don't
   invent content. A meeting note with `## Open questions` absent because there
   are none is cleaner than one with `None.` filler.
4. **Write the file** to `Fredis/Memory/meetings/YYYY-MM-DD_<slug>.md`.
5. **Confirm the path** back in Slack:
   > Captured to `Fredis/Memory/meetings/2026-04-23_atis-cab-rollout.md`.

## Template

```markdown
---
type: meeting
date: 2026-04-23
attendees: [Linards, Atis]
lane: cab                  # email-hub | vtv | cab | other | na
tags: [q3-scope, rollout]  # optional, kebab-case
---

# <Counterparty or topic> — <short framing>

## Attendees

- Linards
- Atis

## Agenda

- Q3 scope review
- Rollout timeline

## Discussion

<free-form narrative — 2–6 paragraphs. Capture what was actually said,
not a summary of the summary. Include disagreements where they happened.>

## Decisions

- Cut feature X from Q3 scope. Reason: <brief>.
- Move Latvia rollout to Q4.

## Action items

- [ ] @Linards — Draft revised scope doc by 2026-04-30
- [ ] @Atis — Confirm LV partner availability by 2026-04-28

## Open questions

- <only include if there genuinely are open questions — skip the section otherwise>
```

## Boundary — what this skill does not do

- No calendar integration in Phase 12. Future work: pull attendees from the
  corresponding Google Calendar event if we pass an event ID.
- No auto-transcription. Linards types or dictates; Fredis structures.
- No action-item dispatch to HubSpot. Action items are recorded in the markdown;
  Linards creates HubSpot tasks / tickets himself from the file if needed.
- Never writes to `drafts/`, `MEMORY.md`, `USER.md`, or other vault top-level
  files. `meetings/` only.

## Tests

See `.claude/scripts/tests/test_meeting_notes_skill.py` — path convention test
(path matches `meetings/YYYY-MM-DD_<slug>.md`, frontmatter fields present).
