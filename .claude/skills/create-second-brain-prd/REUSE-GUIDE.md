# Reuse Guide — Setting Up a Second Brain for Another Business

This skill is **portable**. You can drop the entire `create-second-brain-prd/` folder into any project and use it to generate a fresh Second Brain PRD for a new business, client, or persona.

## What's in this skill folder

| File | Purpose | Personalize per business? |
|------|---------|---|
| `SKILL.md` | The skill logic and PRD generation rules | **No** — generic, reusable as-is |
| `my-second-brain-requirements.md` | **BLANK template** — copy this, fill it out | **No** — keep blank at skill location |
| `example-my-second-brain-requirements.md` | Sample filled-out version ("Alex Rivera") for reference | **No** — teaching example |
| `references/architecture-reference.md` | Architecture blueprint the skill reads when generating the PRD | **No** — generic reference |
| `REUSE-GUIDE.md` | This file | **No** — reuse instructions |

**Nothing in this folder should contain any specific business/person's data.** If you see real names, vault names (like `Fredis`, `Dynamous`, etc.) in any file other than `example-my-second-brain-requirements.md`, that's contamination — clean it up before copying to a new project.

## The pattern (how this skill is meant to be used)

```
1. Copy `create-second-brain-prd/` folder to the new project's `.claude/skills/`
2. Copy `my-second-brain-requirements.md` OUT of the skill folder
   to the new project's workspace root (or `.agent/plans/`)
3. Fill out the copy — never edit the blank template in place
4. Run `/create-second-brain-prd <path to filled-out requirements>`
5. Skill generates PRD at `.agent/plans/second-brain-prd.md`
6. Generated PRD uses the vault name from Section 1
   ("Memory vault folder name") everywhere — no hardcoded names
```

## Setting up a Second Brain for another business — step by step

Say you're setting up a system for a client called "Acme Corp" with vault name "AcmeBrain":

### 1. Scaffold the new project

```bash
# From the new project root
mkdir -p .claude/skills .agent/plans
cp -r /path/to/this/project/.claude/skills/create-second-brain-prd .claude/skills/
cp -r /path/to/this/project/.claude/commands .claude/
```

### 2. Copy the blank requirements template out of the skill folder

```bash
cp .claude/skills/create-second-brain-prd/my-second-brain-requirements.md \
   .agent/plans/my-second-brain-requirements.md
```

**Important:** Do NOT edit the one inside `.claude/skills/...` — that's the blank template for future businesses. Always work on the copy.

### 3. Fill out the copy

Open `.agent/plans/my-second-brain-requirements.md` and fill in the business's details:
- Name, role, timezone
- Memory vault folder name (e.g., `AcmeBrain`)
- Platforms they use
- Top tasks, proactivity level, security boundaries
- etc.

### 4. Generate the PRD

```bash
# In Claude Code
/create-second-brain-prd .agent/plans/my-second-brain-requirements.md
```

Output: `.agent/plans/second-brain-prd.md` — a phased build plan personalized to that business, using their vault name (`AcmeBrain/Memory/`) everywhere.

### 5. Build from the PRD

Work through phases 1-9 of the generated PRD. At the end you'll have:
- `AcmeBrain/Memory/` vault with SOUL.md, USER.md, MEMORY.md, etc.
- Heartbeat, reflection, chat interface (all configured for their platforms)
- CLAUDE.md at repo root tuned to this client's setup

## What NOT to do

- ❌ **Don't fill out the blank template in place** at the skill folder — that permanently contaminates the reusable template with one business's data. (This is what happened with the current project — I had to move the filled version out and restore a clean blank.)
- ❌ **Don't hardcode vault names** in `SKILL.md` or `references/`. The skill is written to read the vault name from Section 1 of the filled-out requirements.
- ❌ **Don't add business-specific secrets or IDs** to the skill folder. Those belong in `.env` files, which the skill never reads.

## Reference: what happens behind the scenes

When you run `/create-second-brain-prd`:

1. SKILL.md is read by Claude
2. Claude reads your filled requirements file (path you provide as argument)
3. Claude reads `references/architecture-reference.md` for the blueprint
4. Claude does **web research** on each platform you listed (Gmail API, Slack SDK, etc.) so the generated PRD has accurate, current implementation guidance
5. Claude generates a 9-phase PRD at `.agent/plans/second-brain-prd.md` using YOUR vault name, YOUR platforms, YOUR proactivity level
6. You build phase by phase — each phase is scoped tightly enough that a coding agent can implement it without further planning

## The one file you CAN customize per business

If you want to pre-fill the example for a specific industry (e.g., always show a marketing agency example instead of the generic "Alex Rivera" engineering manager), you can:

1. Rename `example-my-second-brain-requirements.md` → `example-original.md` (keep original for reference)
2. Create a new `example-my-second-brain-requirements.md` tuned to your typical client profile

But this is optional. The generic example works for any profession.

---

# Phase 1 Build Guide — Beyond the PRD

The PRD tells you **what** to build. This section captures what's actually required to build Phase 1 (the `<Vault>/Memory/` foundation) without stalling — because the PRD alone is not enough input to produce personalized memory files.

## Why PRD-alone is insufficient for Phase 1

The requirements template has ~15 top-level questions. Phase 1 needs to populate 5–6 memory files that collectively want ~110 distinct fields of personal/business data.

- ~50–60 fields come directly from the requirements file / PRD
- ~40–50 fields are **not** asked by the PRD at all (communication style, account IDs, habit pillars, drafting criteria, preferences)
- ~30–40 additional fields only surface when the "What I do daily" paragraph is rich (multiple service lines, geographies, research interests, languages) — the PRD generator doesn't derive these unless explicitly prompted

Skipping the gap means memory files end up either (a) byte-identical to the templates, or (b) filled with placeholders that make the agent ineffective from day one.

## The three-input model for Phase 1

| Input | Role | Produces |
|-------|------|----------|
| Requirements file | Skeleton answers | Feeds PRD generator |
| Generated PRD | Build plan + folder map | Phase ordering, file list |
| **Gap interview** (this guide) | Remaining memory content | Personalized file bodies |

All three are required. Phase 1 is "complete" only when the gap interview is done and the memory files reflect it.

## Gap map — which file needs what beyond PRD

| File | PRD covers | Gap interview must supply |
|------|------------|--------------------------|
| `USER.md` | name, role, vault, platforms, top tasks, memory categories | email, precise IANA timezone, account IDs per platform, drafting criteria, communication style, team, proactivity preferences (welcome/annoying), decision patterns |
| `SOUL.md` | proactivity level → bold/ask behavior, security → "always ask first" list | agent name, tone (detailed vs concise, formal vs casual, emoji use), opinion dial (1–5), push-back style, humor tolerance |
| `HEARTBEAT.md` | platforms to check, draft-mode on/off | active-hours window, weekend variant, important-contacts list, monitored channels per platform, notification channel, notify-immediately thresholds |
| `HABITS.md` | nothing useful | all 5 pillars, per-pillar "what counts as a win", auto-detectable vs self-report, late-day nudge threshold |
| `MEMORY.md` | nothing | 3–5 active clients, 3–5 active projects, 5–10 key people, 3–5 early decisions, 5–10 day-one lessons |

## Baseline gap questionnaire (~50 questions)

Use this for any business, regardless of context depth.

- **A. Identity & Basics** (5) — legal name, email, agent name, pronouns, address preference
- **B. Location & Timezone** (6) — primary + secondary IANA tz, city, travel frequency, active hours, weekend variant
- **C. Working Context** (8) — legal entity, client sectors, engagement lengths, co-founders/contractors, accountant, hiring state, biggest-focus engagement, personal brand
- **D. Communication Style** (7) — length default, formality, emoji, push-back style, correction style, languages, chat-vs-terminal variance
- **E. Agent Personality** (5) — opinion dial, off-limits topics, humor, first-person voice, unknown-handling style
- **F. Accounts & Integration IDs** (10–13) — one block per platform in their stack
- **G. Drafting Criteria** (6) — important-contacts list, per-platform "draft vs skip" rules, tone template
- **H. Proactivity Preferences** (5) — welcome vs annoying help, deep-work hours, notification channel, morning-brief contents
- **I. Habit Pillars** (6) — 5 pillars, win-definition per pillar, auto vs self-report, review time, nudge threshold, weekly roll-up
- **J. MEMORY.md Seed** (5) — clients, projects, people, decisions, lessons

## Context-adjusted questionnaire additions (~40 more questions)

**Trigger:** the requirements file's "What I do daily" field is more than one sentence — i.e., it lists service lines, geographies, languages, research interests, or stakeholder types.

If triggered, add these sections:

- **K. Service Lines** (7) — revenue split by line, active vs dormant, pricing model per line, deal-flow stages, lead sources, high-priority lines, per-line tagging in drafts
- **L. Geography & Operations** (8) — client split by region, legal entities per country, billing currencies, languages, local sample drafts for voice-matching, local network contacts, cross-border compliance flags
- **M. Research & Knowledge Pipeline** (9) — which stated interests get dedicated folders, sources per area, daily pulls vs on-demand, legislation jurisdictions, markets watchlist, paper/article workflow, summarisation depth, public-vs-private default, hobby-vs-prospecting split
- **N. Competitive & Market Intelligence** (5) — competitors per region, monitoring depth, market-signal watch, referral partners
- **O. Content & Positioning** (6) — cadence, pitch, channels, topics, case-study auto-harvest, testimonial pipeline
- **P. Deliverable Portfolio Tracking** (4) — portfolio location, case-study-worthy threshold, post-delivery windows, retainer tracking
- **Q. Admin & Time** (5) — time-tracking tool, monthly rhythm (invoicing, VAT), reminder scope, expense policy, personal-finance boundary

## Vault structure implications

### Baseline vault (no context-adjusted sections)

```
<Vault>/Memory/
├── SOUL.md USER.md MEMORY.md BOOTSTRAP.md HEARTBEAT.md HABITS.md
├── _templates/        (per-category note templates, used by Templater)
├── _frontmatter-schema.md
├── _glossary.md
├── TODO.md
├── daily/
├── drafts/{active,sent,expired}/
├── clients/           + _index.md
├── projects/          + _index.md
├── meetings/          + _index.md
├── research/          + _index.md  + _reading-queue.md
├── team/              + _index.md
└── content/           + _index.md
```

### Rich-context vault (when K–Q apply)

```
<Vault>/Memory/
├── ... baseline files ...
├── research/
│   ├── markets/
│   ├── policy/
│   ├── ai/
│   ├── <any other stated interest>/
│   └── _reading-queue.md
├── competitors/       + _index.md
├── retainers/         + _index.md
├── case-studies/      + _index.md
└── _watchlists/       (finance tickers, legislation feeds, competitor feeds)
```

## Build agent process (what to do when starting Phase 1 for a new business)

1. Read the requirements file AND the generated PRD.
2. Diff existing `<Vault>/Memory/*.md` against `templates/memory/*.md` — flag any files still byte-identical to templates.
3. Decide context depth: is the "What I do daily" paragraph one sentence or rich? Size the questionnaire accordingly (A–J only, or A–Q).
4. Force three structural decisions upfront: wiki-links vs path links, flat vs per-entity folders, Templater/Dataview use.
5. Run the gap interview — batch questions section by section, **not one at a time** (BOOTSTRAP's one-at-a-time style is slow when a requirements file already exists).
6. Before any writes: draft personalized versions of each file and present for review.
7. After user approval: write files, create category folders (with `_index.md` and `_template.md` in each), update `.gitignore`, delete `BOOTSTRAP.md`.
8. If the rich-context interview surfaced **new structural dimensions** (e.g., `competitors/` folder, language-aware RAG, service-line tagging), **append a `## Addendum — Context Deltas` section to the PRD** capturing (a) Phase 1 folder map changes and (b) which later phases are affected. Do not edit existing phase text mid-build.
9. After Phase 1 is complete and the full delta is known, do a single surgical revision pass through the PRD to absorb the addendum into each phase's body.
10. Update root `CLAUDE.md`: add the full folder map, the "no-secrets-in-vault" convention, any new naming conventions (draft file format, YAML schema), and the Phase 1 completion summary.

## Frontmatter schema (recommended minimum)

Every note in the vault should have:

```yaml
---
type: <meeting|client|project|research|draft|note|...>
created: YYYY-MM-DD
status: <active|done|archived>
tags: [flat, tags, only]
related: [[Other Note]]
---
```

If service-line tagging applies (K triggered): add `service: <line>`.
If language-aware RAG applies (L triggered): add `lang: <iso-code>`.
If drafts: add `source_id`, `recipient`, `subject`, `context`.

Document the schema in `<Vault>/Memory/_frontmatter-schema.md` so the agent (and future human editors) stay consistent.

## Things to avoid in Phase 1

- ❌ Running BOOTSTRAP's one-question-at-a-time flow when a filled requirements file already exists — it duplicates ~50% of the PRD. Use the gap interview instead.
- ❌ Leaving MEMORY.md empty or template-identical — it's injected into every conversation; an empty MEMORY.md means the agent has no long-term recall from day one.
- ❌ Silently writing `TBD` for account IDs — either capture them now or explicitly note `TBD — blocks Phase 4` in USER.md so they surface later.
- ❌ Deleting BOOTSTRAP.md before the gap interview is complete — if the session ends partway, BOOTSTRAP's existence is the signal to resume.
- ❌ Modifying existing PRD phase bodies during Phase 1 — use the addendum pattern, then do a single clean revision after the interview completes.
- ❌ Hardcoding the business's vault name (`Fredis`, `AcmeBrain`, etc.) into this guide or any skill-folder file.

## Time estimates

- Baseline gap interview (A–J, ~50 Qs): **30–45 minutes** with the user.
- Rich-context interview (A–Q, ~110 Qs): **90–120 minutes**, best split across two sessions.
- Drafting and writing files after interview: **20–30 minutes** agent time.
- PRD addendum + CLAUDE.md update: **10 minutes**.

Total Phase 1 wall-clock: **~2 hours for baseline, ~3 hours for rich-context.** Worth the investment — every subsequent phase reads these files as source of truth.
