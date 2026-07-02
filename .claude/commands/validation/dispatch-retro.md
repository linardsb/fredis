---
description: Post-dispatch retro — analyse a completed Archon run against its brief and route system improvements
---

# Dispatch Retro

Run after HITL #2 on an Archon dispatch — after Linards has reviewed and merged or closed
the draft PR. Compares what the run produced against what the approved brief asked for,
finds defects in the *system* (brief, workflow YAML, gate, dispatch decision), and routes
each improvement to its rail. Don't fix just the PR; fix the system that allowed it.

## Purpose

**This is NOT code review of the PR.** HITL #2 already judged the code. You are looking
for defects in the process that produced it, so the next dispatch is cheaper and safer.

- A faithful implementation of a wrong brief is a **brief defect**, not an agent failure
  (PR #309: the agent built exactly what §51.3 specced; the spec targeted a surface that
  doesn't exist).
- A green gate that hid a real problem is a **gate blind spot**, not a pass.
- A run that needed a fixup the workflow recovered from (gate1→fix→gate2) is the system
  *working* — record it as evidence, not a defect.

## Hard guards

- Runs **in-session on the Desktop checkout only** — never autonomously, never from the
  VPS, never inside heartbeat/reflection. Same rationale as the Skill Improvement Loop's
  deploy guard: rail (b) edits `.claude/` code, which git-sync does not cover.
- Advisor mode holds: nothing here pushes, merges, or sends. Rail (a) outputs are drafts;
  rail (b) edits are local scoped commits Linards reviews.

## Inputs

`$1` = brief slug → `Fredis/Memory/drafts/active/the-team/$1.md` (if moved, search
`Fredis/Memory/drafts/` by slug before giving up)
`$2` = PR reference — `<repo-slug>#<n>`, or a bare number if the brief names the repo

Gather four artefacts. For each, if missing, do what the fallback says — never silently skip:

1. **The approved brief** ($1) — the contract the run was judged against.
   **Missing → STOP** and ask Linards; a retro without the brief has no baseline.
2. **PR diff + review outcome** — `gh pr view <n> --json state,mergedAt,reviews,comments`
   and `gh pr diff <n>` against the target repo (`gh pr diff` works on closed PRs).
   Truly gone → reconstruct from the Dispatch History entry; mark `evidence: partial`.
3. **Gate logs** — the workflow tees gate output to a log in the run worktree
   (`~/.archon/…`); worktrees may be disposed. Fallback: gate verdicts recorded in
   Dispatch History + the PR's checks. Absent → mark `gate evidence: secondhand`.
4. **The run record** — the Dispatch History bullets in
   `Fredis/Memory/repositories/<slug>.md`, plus `query.py workflow status <runId>` only
   if the engine is already up (**never boot the engine for a retro**). No entry yet →
   proceed from brief + PR; the close-out below creates the daily-log line reflection
   will promote.

## Analysis

**1. Reconstruct intent.** From the brief: what change, on what surface, with what
acceptance signal?

**2. Reconstruct outcome.** From diff + review: what landed? Merged / closed-inert /
closed-superseded? How many fixup cycles? What did HITL #2 catch that the gate did not?

**3. Classify every divergence by defect locus** (including "merged clean, zero gaps" —
say so explicitly):

```yaml
finding: [one line]
locus: brief | workflow | gate | dispatch-decision | none
evidence: [file:line, PR comment, gate-log line, Dispatch History bullet]
```

- **brief** — spec wrong or under-specified: wrong surface, false codebase assumption,
  missing acceptance check
- **workflow** — a YAML node misbehaved: timeout, tool scope, retry logic, prompt gap
- **gate** — passed something it should catch, or failed on something not the fix's fault
- **dispatch-decision** — shouldn't have been dispatched (logic-wiring past the trust
  ceiling) or wrong workflow chosen
- **none** — expected non-determinism; evidence only

**4. Route each improvement (tiered):**

| Locus | Rail | Action |
|---|---|---|
| workflow | **(a) YAML draft** | Write the hardened YAML to `Fredis/Memory/drafts/active/the-team/workflows/<name>.yaml` with a `# Placement:` header comment giving the exact `cp` into the target repo's `.archon/workflows/` — Fredis is sandbox-blocked from writing target repos; Linards places it. |
| brief / dispatch-decision, when the fix is command or prompt text | **(b) live command edit** | Edit the file under `.claude/commands/`. Commit scoped to the changed file(s) only, message `dispatch-retro: <what>`, **no push**. Desktop-session-only (hard guard). |
| skill-shaped (integrations skill behaviour, brief-shaping skills) | **(c) skill observation** | Append to `Fredis/Memory/skill-observations/log.md` per the Skill Improvement Loop — do not edit a SKILL.md from here. |
| run outcome / repo history | **(d) Dispatch History** | Existing convention — reflection promotes daily-log dispatch references into the repo page. Write the retro line into today's daily log; do **not** hand-append the history section. Factual corrections to the repo page's Workflow Preferences (a discovered gate quirk, a branch fact) may be edited directly — those are vault facts, not history. |

One finding may route to two rails (e.g. a gate blind spot → YAML draft **and** a skill
observation about task selection).

**5. Verdict.**

- **Trust read:** did this run move the mechanical-vs-logic-wiring trust ceiling? Evidence.
- **System delta:** what changed on each rail, with paths.
- **Not taken:** improvements considered and dropped, one line each — so the next retro
  doesn't re-derive them.

## Output

Write the retro to `Fredis/Memory/drafts/active/the-team/retros/YYYY-MM-DD-<brief-slug>-retro.md`
(frontmatter: `skill: integrations/dispatch-retro`, `status: draft`). Then:

1. Append a one-line summary to today's daily log (feeds rail (d)).
2. Report in chat: verdict, finding count by locus, what routed where.

## Important

- **Be specific:** not "the brief was unclear" — "the brief assumed an in-process tool
  loop in `BaseAgentService`; none exists (`base.py` `process()` is single-shot)".
- **Patterns over one-offs:** N=1 noise is evidence; the same locus twice across runs is
  a finding.
- **No orphan analysis:** every finding ends on a rail or in Not-taken.
