# Phase 1 Ready — Runbook

Per-file mapping between interview answers (in
`.agent/plans/phase1-onboarding-interview.md`) and the five target memory files.
This is the recipe the `phase1-ready` skill follows when drafting personalised
content. It is a **living document** — future sessions can edit this without
touching the skill's trigger.

Notation: `A1` means the answer to question A1. `A1+A4` means synthesise across
both. If a referenced answer is empty, leave the corresponding section as a
TBD placeholder rather than inventing content.

---

## SOUL.md

Preserve every existing `h2` section. Replace placeholder bullets with content
synthesised from the answers below. Keep the file ≤ 300 lines.

| Section (h2 in current SOUL.md) | Source questions |
|---|---|
| Core Identity → Name | A4 (what the agent calls itself) + A5 (how it addresses Linards) |
| Core Identity → Vibe | D1, D4, D5, D6, E1, E5, E8 — synthesise into 2–3 sentences |
| Communication Style | D1, D2, D3, D4, D5, D10, D11 |
| Proactive Behavior | H1, H2, H3, H4, H5, H7, H8, H9 |
| Boundaries → Always Ask First | AA1, AA2 |
| Boundaries → Safe to Do Freely | AA3 |

Add two new `h2` sections at the end if the source answers are non-empty:

- **`## Working Principles`** — from R1, R2, R4
- **`## How to Push Back`** — from E2, E3, E6, E7

---

## USER.md

Preserve existing `h2` sections. Mark unknown integration fields as `TBD` rather
than inventing values.

| Section (h2) | Source |
|---|---|
| Basic Info | A1, A2, B1, B2 |
| Professional Context → Current Role | C1 (first paragraph only) |
| Key Projects | C2 (3 entries), J2 |
| Content Calendar | O1, O3 |
| Working Style → Communication Preferences | condensed D1–D11 |
| Schedule Patterns | B3, B4, B5, B6, B8 |
| Team | C7 |
| Integrations & Accounts | F1–F13 (factual dump; empty → `TBD`) |
| Proactivity Preferences | H3, H4 |

Add three new `h2` sections at the end:

- **`## Service Lines`** — from K1–K8
- **`## Geography & Dual Operations`** — from L1–L8
- **`## Key Contacts`** — from C8, G1, W1

---

## MEMORY.md

Hard ceiling: **200 lines**. If the drafted content overflows, spill the excess
into topic files under `Fredis/Memory/` and leave a wiki-link pointer
(`See [[topic-file]]`).

| Section (h2) | Source |
|---|---|
| Key Decisions | J4 |
| Lessons Learned | J5 |
| Important Facts | anything the user flagged as important across any section |
| Active Projects | J1, J2 |
| Upcoming Events | B8 (recurring commitments), Y2 |
| Preferences Confirmed | unambiguous rules from D, E, H, AA |

---

## HABITS.md

Replace the five Pillar templates with content from Section I.

- **Pillar names** — from I1 (3–5 names).
- **"A win today looks like…"** — from I2 (one sentence per pillar).
- **Auto-detection rules** — from I3 (e.g., git commit = ship-work).
- **Late-day nudge threshold** — I7.
- **Weekly Sunday roll-up** — I8.
- **Reset the `Today: YYYY-MM-DD` line** to the current date in `HEARTBEAT_TIMEZONE`.

If I4 (the neglected pillar) is non-empty, mark that pillar with a
`[priority]` tag so the heartbeat amplifies nudges for it.

---

## HEARTBEAT.md

Tailor the existing checklist:

- **Remove integration checks** for any platform Linards did not list as active
  in F1–F13.
- **Add custom checks** from H3 (extra proactivity behaviours he asked for).
- **Adjust notification thresholds** from H9 (when to escalate vs stay silent).
- **Deep-work quiet hours** — from H5: insert a "do not nudge between {start}
  and {end}" rule near the top.
- Active-hours window comes from B4; if it differs from the `.env` default
  (08:00–22:00 America/Chicago → likely Europe/London or Europe/Riga),
  call this out in the PRD addendum too.

---

## investors/ — VC / angel / PE pipeline (CRM-style)

This is an **operational** folder, not a research folder. It tracks relationships and pipeline state, not domain knowledge.

**Scaffold:**

```
Fredis/Memory/investors/
├── README.md              — one-liner describing purpose
├── _pipeline.md           — master table (name · stage · last contact · next action)
└── {investor-name}.md     — per-investor profile (warm/active contacts only)
```

**Seed `_pipeline.md` from the interview:**

- Scan **C8** (professional service providers / contacts) and **C2** (recent client engagements) for anyone who has invested or expressed investor-style interest.
- Known warm contacts to seed as of this drafting (verify against current interview state — do not fabricate):
  - **Tim Jackson** (Walking Ventures) — 2018 UGOKI interest, 2026 Email Hub cold re-engagement. Status: awaiting response. Create `investors/tim-jackson.md` as a warm profile.
- Do **not** create per-investor profiles for anyone still cold or speculative — the pipeline table captures them with status `cold` and that's enough until real engagement.

**Per-investor file template:**

```markdown
# {Name} — {Firm}

**Thesis fit:** {what kind of companies they back}

**History:**
- {date}: {what happened}

**Intros available:** {if any — who they know that could be useful}
**Temperature:** {cold / warm / active / closed}
**Next action:** {one concrete next step + due date}
```

**Heartbeat integration:** once the folder exists, the heartbeat scans `_pipeline.md` daily and surfaces any row where `next action due date ≤ today` or any warm contact with >10 business days since last touch.

---

## collaborators/ — Strategic technical collaborators / network (CRM-style)

Parallel to `investors/` but for non-investor strategic relationships — technical co-collaborators, sector experts, sounding boards, potential pilot partners, anyone Linards would actually rope into work (not casual contacts).

**Scaffold:**

```
Fredis/Memory/collaborators/
├── README.md              — one-liner describing purpose
├── _network.md            — master table (name · domain · status · last contact · next action)
└── {person-name}.md       — per-person profile (warm/active relationships only)
```

**Seed `_network.md` from the interview:**

- Scan **C8** (professional service providers / contacts), **G1**, **W1** for technical collaborators, sector experts, or strategic non-investor relationships.
- Known warm contacts to seed as of this drafting (verify against current interview state — do not fabricate):
  - **Pierre Laquintinie** — engineer, sensor + analog-NN + embedded systems + AFNOR standards background. Strategic value: hardware/edge-compute capability for the agriculture lane (electronic-nose tech → barn air quality, livestock health monitoring; analog NN → ultra-low-power on-device AI for remote farms; AFNOR → standards portability across CAP/SFI/AR; French background adds 4th jurisdiction angle). Status: warm — long-term known contact. Create `collaborators/pierre-laquintinie.md`.
- Do **not** create per-person profiles for casual or speculative contacts — the table captures them with status `cold` until real engagement.

**Per-person file template:**

```markdown
# {Name} — {Role / Org}

**Domain:** {what they specialise in}

**Strategic value:** {what unique angle / capability they bring to one or more of Linards' service lines}

**History:**
- {date}: {what happened}

**Intros available:** {who they know that could be useful}
**Status:** {cold / warm / active}
**Next action:** {one concrete next step + due date — or `none — passive` if just keeping warm}
```

**Heartbeat integration:** once the folder exists, the heartbeat scans `_network.md` daily and surfaces any row where `next action due date ≤ today` or any warm contact with >30 business days since last touch (looser than investors' 10-day threshold — collaborator relationships run on slower cadence).

---

## PRD Addendum — `## Addendum — Context Deltas`

Append a bullet list at the end of `.agent/plans/second-brain-prd.md`. Each
bullet captures **(a)** a PRD assumption and **(b)** the interview answer that
contradicts, narrows, or extends it.

Focus on these high-leverage deltas:

- **Timezone:** PRD defaults to UK (`Europe/London`) for some scheduling
  examples — confirm against B1.
- **Pillar names:** PRD lists default proposals (Ship-client-work,
  Grow-community, Market-learning, AI-frontier-learning, Health/Relationships).
  If I1 names different pillars, capture the override.
- **Integration priority order:** PRD assumes Gmail → Asana → Slack. If F1–F13
  reorder this (e.g., Discord before Slack), record it.
- **Active-hours window:** PRD assumes 08:00–22:00; B4 may narrow.
- **Proactivity level:** PRD assumes "moderate, ask-before-act"; H1, H7, AA1
  may push toward more autonomous or more cautious.
- **Geography:** PRD doesn't model dual-jurisdiction (UK/LV); L1–L8 may
  introduce constraints worth surfacing.

**Idempotency:** before appending, search the PRD for the heading
`## Addendum — Context Deltas`. If it exists, **replace** the section in-place
rather than appending a duplicate.
