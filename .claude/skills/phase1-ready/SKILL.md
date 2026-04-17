---
name: phase1-ready
description: |
  Trigger the Phase 1 memory-layer personalisation pipeline when the user signals
  the onboarding interview is complete. Reads .agent/plans/phase1-onboarding-interview.md,
  drafts the five personalised memory files (SOUL.md, USER.md, MEMORY.md, HABITS.md,
  HEARTBEAT.md), shows each draft for review, writes only after explicit approval,
  scaffolds new topic folders, appends a "Context Deltas" addendum to the PRD, and
  deletes BOOTSTRAP.md.

  TRIGGER PHRASES (case-insensitive): "phase 1 answers ready", "phase1 answers ready",
  "phase 1 complete", "onboarding interview done", "onboard me" (only when the
  interview file already has answers filled in).
---

# Phase 1 Ready — Memory-Layer Personalisation

Fires when the user signals the onboarding interview at
`.agent/plans/phase1-onboarding-interview.md` is filled in (typically after they
finish a session of `.claude/scripts/onboard.py`). The job is to convert the 103
free-form interview answers into five personalised memory files **without writing
anything until the user has reviewed each draft**.

## When to invoke

Only on the trigger phrases listed in the front-matter. Do **not** speculatively
fire if the user mentions onboarding in passing — wait for the explicit phrase.

## Preconditions (check first, abort if any fail)

1. `.agent/plans/phase1-onboarding-interview.md` exists.
2. Parse it via `.claude/scripts/interview_parser.py` and confirm at least
   **25 ★ (core) questions** have non-empty answers. If fewer, list the missing
   core questions to the user and stop — do not draft anything yet.
3. `.claude/skills/phase1-ready/runbook.md` exists (the per-file mapping recipe).
4. The five memory files exist under `Fredis/Memory/` (templates count — they will
   be rewritten in place).

## Workflow

Execute in this exact order. Do **not** skip the review steps.

1. **Parse the interview.** Use `interview_parser.parse_interview` to load the
   typed model. Build a dict `{question_id: answer_text}` for the agent's own
   reasoning convenience.
2. **Read the runbook.** Open the sibling `runbook.md` for the section-by-section
   mapping between interview answers and target memory-file content.
3. **Read the current memory files** to learn the structural h2 sections that
   must be preserved (only the placeholder bullets get rewritten):
   - `Fredis/Memory/SOUL.md`
   - `Fredis/Memory/USER.md`
   - `Fredis/Memory/MEMORY.md`
   - `Fredis/Memory/HABITS.md`
   - `Fredis/Memory/HEARTBEAT.md`
4. **Draft all five files in memory** (do not write yet). For each file, follow
   the runbook mapping. Preserve the existing h2 section ordering; only
   substitute the placeholder content under each h2.
5. **Show each draft for review, one at a time.** For each file, print the
   proposed full contents and ask: "Approve, edit, or skip?" The user may:
   - **Approve** — proceed to write this file.
   - **Edit** — apply their inline corrections to the draft, then re-show.
   - **Skip** — leave the existing file untouched and move on.
6. **Write approved drafts via the Edit tool.** All writes go through the
   allowlist enforced by `drafting_hook.py` (see Safety below).
7. **Scaffold new topic folders** under `Fredis/Memory/`:
   - `research/` — content monitoring + research watchlists (per-lane subfolders: markets, policy, ai, robotics, materials, agriculture — each with its own README)
   - `competitors/` — competitor profiles
   - `retainers/` — recurring-client engagement notes
   - `case-studies/` — public-facing engagement write-ups
   - `investors/` — VC / angel / PE pipeline (CRM-style). Seed `_pipeline.md` master table from C8 contacts + any investor history in C2/J5. Create per-investor markdown files for warm/active relationships only (e.g., `tim-jackson.md`).
   - `collaborators/` — strategic technical collaborators / network (CRM-style, parallel to investors/). Seed `_network.md` from C8/G1/W1 non-investor strategic contacts. Create per-person markdown files for warm/active relationships only (e.g., `pierre-laquintinie.md`). See runbook for details and known seed contacts.

   Each new folder gets a one-line `README.md` describing its purpose. Use
   `mkdir -p` and `Write` (not Bash `echo`) for the README.
8. **Append the PRD addendum.** Compute deltas between interview answers and
   `.agent/plans/second-brain-prd.md` assumptions (timezone defaults, default
   pillar names, integration priority order, active-hours window, proactivity
   level). Append `## Addendum — Context Deltas` to the PRD with one bullet per
   delta. **Idempotency:** if the section already exists, replace it in-place
   rather than appending a duplicate.
9. **Delete `Fredis/Memory/BOOTSTRAP.md`** via `Bash` (`rm Fredis/Memory/BOOTSTRAP.md`).
   This is the single allowed `rm` invocation in this workflow.
10. **Append a summary entry to today's daily log** (use
    `shared.append_to_daily_log`) — list which files were written, which were
    skipped, and which folders were created.

## Safety

`drafting_hook.py` (sibling file) is the **reference allowlist** for what
`Edit` / `Write` / `Bash` calls this skill is permitted to make. Important
caveat: skills in this project are markdown instructions Claude reads — the
hook is **not** automatically wired up unless the skill spawns a sub-agent SDK
session that registers it via `HookMatcher`. In the default in-conversation
flow, the main session enforces the allowlist by manually following the rules
described in `drafting_hook.py`:

- **Edit/Write allowed only on:**
  - `Fredis/Memory/{SOUL,USER,MEMORY,HABITS,HEARTBEAT}.md`
  - `Fredis/Memory/{research,competitors,retainers,case-studies,investors,collaborators}/README.md`
  - `Fredis/Memory/investors/_pipeline.md` and `Fredis/Memory/investors/*.md` (per-investor profiles)
  - `Fredis/Memory/collaborators/_network.md` and `Fredis/Memory/collaborators/*.md` (per-person profiles)
  - `Fredis/Memory/research/{markets,policy,ai,robotics,materials,agriculture}/README.md`
  - `Fredis/Memory/daily/YYYY-MM-DD.md` (append-only)
  - `.agent/plans/second-brain-prd.md` (append/replace addendum only)
- **Bash allowed only for:**
  - `mkdir -p Fredis/Memory/{research,competitors,retainers,case-studies,investors,collaborators}`
  - `mkdir -p Fredis/Memory/research/{markets,policy,ai,robotics,materials,agriculture}`
  - `rm Fredis/Memory/BOOTSTRAP.md` (exactly once)
- **Anything else:** stop and ask the user before proceeding.

## Re-runs

If the skill fires a second time (BOOTSTRAP.md already deleted), detect that
state and respond: "Phase 1 already complete. Re-run `onboard.py` to update the
interview, then ask for specific memory-file refreshes — I won't auto-rewrite
all five again."

## Exit message

After step 10, post a confirmation in this shape:

```
Phase 1 personalisation complete.
  Written:  SOUL.md · USER.md · MEMORY.md · HABITS.md · HEARTBEAT.md
  Folders:  research/ (+ 6 lane subfolders) · competitors/ · retainers/ · case-studies/ · investors/ · collaborators/
  Seeded:   investors/_pipeline.md (N contacts from C8) · collaborators/_network.md (N contacts from C8/G1/W1)
  PRD:      Appended Context Deltas addendum (N items)
  Cleanup:  Deleted BOOTSTRAP.md

Next: configure integrations via `cd .claude/scripts && uv run python setup_auth.py`.
```
