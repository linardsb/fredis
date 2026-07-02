# Skill Observation Log

Skill-improvement observations captured during work — friction, corrections, and dead weight that
should become a reviewed edit to the skill that caused it. One entry per observation, appended to the
end, tagged to a skill. See `.claude/skills/_shared/skill-improvement.md` for the loop.

**Status key:** `open` = logged, not yet acted on · `applied` = edit is in the live skill (a safe edit
Fredis applied + committed, or a risky draft Linards merged) · `drafted` = risky change proposed in
`drafts/active/skill-improvement/`, awaiting Linards · `declined` = not pursued.

**Format:**

```markdown
### YYYY-MM-DD — <skill or bundle/sub-skill>: <short title>
**Status:** open
**Issue:** what happened — the correction, the inefficiency, or the dead-weight section
**Suggestion:** the specific SKILL.md change — which section, old → new
**Principle:** the generalisable takeaway, if any (feeds the cross-cutting checklist)
```

---

<!-- No observations logged yet. Append new entries below this line. -->

### 2026-07-02 — integrations/archon-dispatch: logic-wiring briefs need a surface-existence check + end-to-end acceptance

**Status:** open
**Issue:** Dispatch retro on PR #309 (51.3 tool-call cap, closed-inert). The brief specced the cap
onto `BaseAgentService.process()` — a single-shot surface with no tool loop — so a faithful, gate-green
implementation was functionally inert (`record_tool_call()` has zero production call sites). The brief's
acceptance tests all exercised the counter in isolation, so the gate proved "the class works", never
"the class is invoked". A unit gate is structurally blind to unwired code.
**Suggestion:** In `integrations/references/archon-dispatch.md` (PRD-gate section) or the brief-shaping
guidance it points at, add two brief-shaping rules for logic-wiring tasks: (1) **surface-existence
check** — the brief must cite the live call site (file:line) where the new code will be invoked,
verified by grep against the target repo, before HITL #1; (2) **one end-to-end acceptance test** on the
real execution path (e.g. "cap trips at N+1 on a real agentic run"), not only direct-call unit tests.
Mechanical/refactor briefs are exempt — their gate already proves completeness (mypy/pyright catch a
missed consumer).
**Principle:** For dispatched work, the brief is the only place "does this surface exist?" can be
caught — the harness gate validates the implementation against the tests, never the plan against the
codebase.

### 2026-07-02 — integrations/archon-dispatch: brief boundaries and the GitHub issue must agree (incl. repo-forced files)

**Status:** open
**Issue:** Dispatch retro on PR #310 (50.6.4 constantize, merged clean). Two brief-vs-reality mismatches
generated review-bot noise at HITL #2: (1) the brief's VSA boundary listed three dirs but deleting
config fields forces a `.env.example` sync (env-drift check) — the agent rightly touched it and Qodo
flagged a compliance breach; (2) the brief pre-authorised landing above the ≤45 field bound under
conservative-keep, but the GitHub issue carried the exact ≤45 assertion, so Qodo reported the ≤57 test
as a requirement gap.
**Suggestion:** Brief-shaping guidance: (1) boundary lists must include repo-forced companion files
(generated/synced artefacts) or say "plus files the repo's own checks force in sync"; (2) the enriched
GitHub issue must carry identical acceptance bounds/judgement clauses to the brief — the issue is what
automated reviewers treat as the contract.
**Principle:** A dispatch has two contract copies (brief + issue); any divergence turns pre-authorised
judgement calls into false findings that HITL #2 pays attention to discount.
