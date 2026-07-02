# Skill Improvement Loop

Fredis's 24-skill stack is not frozen. The best improvements come not from sitting down to "audit the
skills" but from noticing friction *while using them* — a correction that reveals a missing rule, a
step that was slower than what emerged naturally, a section that loads into context but never changes
what Fredis does. This file is the convention that turns that noticing into an edit to the skill that
caused it — a **safe** edit Fredis applies itself, a **risky** one it drafts for Linards.

Borrowed in mechanism from the **task-observer / "One Skill to Rule Them All"** meta-skill by Eoghan
Henn ([rebelytics.com](https://rebelytics.com), CC BY 4.0) — the observe → review → improve loop,
stripped to what a single-user advisor with a deliberately-lean stack actually needs. The machinery
that solved *his* problem (parallel client sessions, a public skill marketplace) is left out; see
"What is deliberately not ported".

**Scope: improve the existing 24 only.** This loop sharpens and prunes the skills that exist. It does
**not** propose or create new skills — a 25th top-level skill needs Linards's explicit approval
(consolidate-don't-proliferate). If a repeating pattern smells like a new skill, that is a separate
manual call: name it to Linards plainly and stop; do not draft it here.

**Editing a skill is an internal action, not a send.** A `SKILL.md` is Fredis's own file, and SOUL's
rule is *be bold with internal actions, careful with external ones*. So Fredis applies **safe**
improvements to the live skill itself and commits them for Linards to review or revert; only **risky**
changes wait as drafts. The never-send boundary (email / Slack / posts / external POSTs) never applied
here — it governs external channels, not Fredis's own files. What keeps self-editing safe is the
tiering, the deploy guard below, and git: every applied edit is one labelled, revertable commit.

---

## The three moves

### 1. Capture — log at the moment of friction, not at session end

When something during work is genuinely about *how a specific skill behaved*, log it **then**, in the
same turn — not as a mental note, not batched into the session-end flush. The act of writing is the
enforcement; an unwritten observation is not an observation. (The `SessionEnd` / `PreCompact` hooks
batch context at session end — that is the wrong substrate for this, on purpose.)

Log to `Fredis/Memory/skill-observations/log.md`, appended to the end, one entry per observation:

```markdown
### 2026-07-01 — draft-reply: Slack voice-match reads too formal
**Status:** open
**Issue:** Linards rewrote two drafted Slack replies to be shorter and drop the sign-off. The skill
retrieves 3 past *email* replies for voice even when the target is Slack, so the register is off.
**Suggestion:** In `draft-reply/SKILL.md`, split voice retrieval by channel — pull Slack exemplars
from `drafts/sent/` filtered to Slack when the target is a Slack thread.
**Principle:** Voice is channel-specific; a voice-matching step should match the *channel* it drafts
for, not just the person.
```

Log an observation for any of: a correction that reveals a missing or wrong rule; a workflow that was
slower than what emerged naturally; a technique that worked well and deserves promoting from incidental
to recommended; **a section that is dead weight** (loaded but never acted on — the prune direction
matters as much as the add direction on a lean stack); a rule the skill states but the agent keeps
failing to follow (the fix is usually structural enforcement or removal, not louder prose). Do **not**
log one-off corrections that do not generalise, or preferences an existing skill already captures.

Tag every entry to the skill in its header (`<skill>:` or `<bundle>/<sub-skill>:`). If it generalises
across skills, still tag one skill and write the cross-skill takeaway in **Principle** — that is what
feeds the checklist below.

Capture runs everywhere Fredis works, including autonomous and VPS/chat sessions — observations are
vault files, so they sync. Only *applying* them is session-gated (see the Deploy guard).

### 2. Review — when observations are pending, or on request

The loop applies observations when Fredis is in a **Desktop working session** and open observations
exist (noticed at session start), or on request ("improve your skills", "review skill observations",
"act on the draft-reply observations"). Default mid-task is still *log, don't act* — capture during the
task, apply at a clean moment. Asking "any observations?" when wrapping a session is the capture
backstop; it also surfaces what is pending to apply.

To review: read `open` entries, group by skill, and for each read the target `SKILL.md` (and its
`references/`) before touching anything.

### 3. Apply — tiered: safe edits go live, risky edits become drafts

Classify each observation's change before acting:

**SAFE — apply to the live skill.** Additive, reversible, needs no testing to trust:

- add an anti-pattern, rule, or edge case to an existing list
- add a trigger phrase to a routing table or the `description`
- clarify wording that proved ambiguous
- fix a factual error
- promote a technique that worked from incidental to explicitly recommended

For a SAFE change:

1. Edit the live `SKILL.md` (and/or its `references/`) with the Edit tool.
2. **Pre-Flight** (see checklist): re-read the skill's own rules *and* the cross-cutting checklist
   against the edit; confirm it is genuinely additive and compliant. If the check raises any doubt, it
   was not SAFE — downgrade it to RISKY and draft instead.
3. Commit **only the file(s) changed** — scoped `git add .claude/skills/<skill>/SKILL.md`, **never
   `git add -A`** (the working tree carries untracked docs/scratch a broad add would sweep in). Message:
   `skill-self-improve: <skill> — <one-line what>`. **Do not push** — Linards pushes/deploys.
4. Mark the observation `applied`; post a one-line heads-up to today's daily log (and the review queue)
   so Linards sees what changed and can revert.

**RISKY — draft it, don't apply.** Escalate as a draft when the change:

- removes or substantially restructures a section
- changes core methodology or a decision framework
- is flagged uncertain by the observation itself ("not sure", "maybe", "worth discussing")
- conflicts with another observation
- touches `SOUL.md` (hook-blocked anyway) or the never-send boundary
- looks like a *new* skill (out of scope — name it plainly, do not draft the skill)

For a RISKY change: write the proposal to
`drafts/active/skill-improvement/<skill>/YYYY-MM-DD-<slug>.md` (front-matter per
[[draft-path-convention]]: `skill: skill-improvement/<skill>`, `lane: na`, `status: draft`) showing the
section, the exact **old → new**, and why; mark the observation `drafted`. Linards applies it by hand.

Observation statuses: `open` → `applied` (safe, live) | `drafted` (risky) → `applied` | `declined`.
Declined observations are how the stack stays lean — if a one-off got dressed up as a rule, say so.

### Deploy guard — where live-apply may run (hard rule)

Live-apply + commit happens **only in an interactive session on Linards's working checkout** (Desktop).
It must **never** run from the VPS or an autonomous SDK loop (heartbeat / reflection), because
`.claude/skills/` is *code*, not vault: git-sync auto-syncs only `Fredis/`, so an autonomous skill edit
on the VPS sits as a dirty tree that wedges `deploy.sh`'s `git pull --ff-only`, and an autonomous push
fights the deploy model. Autonomous and VPS/chat sessions **capture observations only**; they never
apply. Applied skill edits reach the VPS the normal way — Linards reviews the commit, pushes, deploys.

(Session-triggered is deliberate over a background daemon: a daemon would commit behaviour-changing code
while Linards is away, and cannot run safely on the always-on VPS. Being present when the edit lands is
the line between a bold internal action and unsupervised self-modification. A `SessionStart` nudge that
surfaces the pending-observation count is an easy later reliability add.)

---

## Cross-cutting principles checklist

Read this before finalising any skill-improvement — a live edit *or* a draft. It is the gate that turns
principles from good intentions into an enforced floor. (It gates this loop's edits and drafts; it does
not auto-wire into `skill-creator`, which has no pointer to it.) The four `~/.claude/CLAUDE.md`
guardrails (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution) bind already
and are not restated here; these are the skill-shaped ones.

1. **Built-in enforcement (Pre-Flight).** Every skill that states rules has a step where the agent
   re-reads its own rules and checks the output against them *before delivery*. A rule with no
   enforcement step gets violated in the creative flow; if an edit adds a rule, it adds (or points at)
   the check too. This is the highest-value principle in the loop — worth adopting even in isolation.
   The loop applies it to itself: it is Pre-Flight step 2 above.
2. **Advisor-mode never-send.** The edited skill still drafts to `drafts/active/` and never sends (see
   [[draft-path-convention]] and SOUL.md). An edit must not introduce a send-style path. (This governs
   the *skill's* outputs — distinct from the loop committing its own file edits, which is internal.)
3. **Lean content.** A skill holds only what changes behaviour at execution time. Changelogs, rationale,
   backstory, "thanks to X" belong outside the `SKILL.md`. Examples and anti-patterns are load-bearing —
   keep those. The test: would removing this line change what the agent does?
4. **British English** in all prose output (code identifiers untouched).
5. **Grounding.** Decision- and research-grade drafts cite per [[citation-and-provenance]]; lane-chain
   skills read-upstream-or-STOP per [[draft-path-convention]]. An edit must not weaken either.

The list grows only on Linards's say-so: when an observation's **Principle** turns out to apply across
skills and he approves it, add it here as a numbered item. Then every later skill edit checks against it
— that is the compounding floor.

---

## What is deliberately not ported

The source is built for a consultant publishing skills across many parallel client sessions. Fredis is
one person with one private stack, so most of its machinery is dead weight here:

- **New-skill creation / new-skill-candidate surfacing** — out of scope; improve-existing only (above).
- **The single-log numbering + collision protocol** (grep-max, pre-write assert, post-write verify,
  `sed` renumber) — that guards parallel writers on one *numbered* log. Fredis keys entries by date +
  skill, so there is no numeric key to collide on; two entries sharing a header is harmless.
- **Open-source vs internal taxonomy, author attribution, licensing, the 5-layer confidentiality
  scrub** — everything here is internal. The only confidentiality analogue (client specifics stay in
  `retainers/`, never leak into a shared primitive) already holds.
- **Handoff-doc mode** — for chat surfaces with no filesystem. Fredis always has the vault.
- **Scheduled autonomous review as a background daemon** — the apply pass is session-triggered on the
  Desktop, not a clock-driven job: a daemon would commit behaviour-changing code while Linards is away,
  and cannot run safely on the always-on VPS (Deploy guard). Capture is continuous; apply waits for a
  session. Cowork's `present_files` upload path is likewise not used — Fredis edits the file directly.

---

**Related:** [[draft-path-convention]] · [[citation-and-provenance]] · `skill-creator` (the hands that
build/edit; this loop is the eyes that notice) · `CLAUDE.md` §Skill Improvement Loop.
