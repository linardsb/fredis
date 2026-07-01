# Plan-update review prompt (reusable)

**Use this whenever you have a change/suggestion for the "Fredis + The Team" plans.** Paste it into a **fresh Claude window** (no context rot), drop your update into the placeholder, and run it from Fredis. It re-reads the *current* plans, checks your update against them, flags any conflict with a locked decision, and proposes surgical edits — **without changing anything until you say go.**

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base; the plans live here)

You are reviewing a proposed UPDATE to the "Fredis + The Team" plans. Do NOT build anything and do NOT edit any plan yet — first reconcile the update against the CURRENT plans, then propose changes for my approval.

THE UPDATE / SUGGESTION (from Linards):
<<PASTE YOUR UPDATE HERE — one point or many>>

READ FIRST (the current plan set — the source of truth, not your memory):
1. docs/agents/fredis-agent-architecture.md          (architecture + locked decisions + phasing)
2. .agent/plans/fredis-archon-mission-control.md     (engine/cockpit spec + containment + resolved repo identity)
3. docs/agents/the-team-build-playbook.md            (the P0–P8 run-sheet)
4. docs/agents/the-team-phase1-build-prompt.md       (the P1 prompt)
5. docs/PRD/prd-as-project-start-condition.md + docs/PRD/prd-best-practices.md  (the PRD gate + method)
6. CLAUDE.md + Fredis/Memory/SOUL.md                 (guardrails, advisor mode, 24-skill cap)

BEFORE calling anything "new" or "needs changing", run the repo's Audit Conventions:
- git log since each doc's date (plans are snapshots, not current state)
- grep Fredis/Memory/daily/ for "deferred / dropped / out of scope" on anything the update touches
- read the relevant SKILL.md / references for scope decisions

THEN produce a RECONCILIATION (no edits yet):
A. For EACH point in the update: is it ALREADY covered / DEFERRED / DECIDED, genuinely NEW, or in CONFLICT with a locked decision? Cite file + line.
B. If it CONFLICTS with or REVERSES a locked decision (Opus-everywhere, hybrid architecture, draft-only/never-send, containment, Saulera-Cockpit naming, the phasing), say so EXPLICITLY — don't silently overturn it; surface the trade-off.
C. Propose the exact edits: which file, what change, why. Smallest surgical diff.
D. Flag knock-on effects on the P0–P8 prompts (do any need updating too?).

OUTPUT → a reconciliation summary in chat. Make NO file edits until I say go. Then STOP.
```
