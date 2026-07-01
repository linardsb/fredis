# Phase 1 — Fredis build harness + cockpit + PRD gate — Lean PRD

**Status:** Advisor-mode draft (P1 handoff artifact). Intent + falsifiable hypothesis only — engineering detail lives in `.agent/plans/the-team/phase1-implementation.md` (the spec/roadmap stage). The hypothesis below is what the first Email Hub runs (P4) empirically test. **No build until an explicit go-ahead.**
**Date:** 2026-07-01 · **Companion spec:** `.agent/plans/the-team/phase1-implementation.md`

---

## Problem statement

Saulera is run solo; the binding constraint is Linards's **review attention, not compute** (MEMORY.md; archon-plan Addendum-2 §B). Today every build/delivery task runs as **in-session Claude Code, one at a time, attended** — fixing an Email Hub issue or building a client site occupies a live session start-to-finish. There is no fire-and-forget: he cannot dispatch a build and step away, and cannot safely run builds against his primary-income repo without babysitting them.

Evidence this is real and ongoing: Email Hub is the most-referenced repo in the vault (**28 distinct daily-logs** to 2026-06-30; `repositories/merkle-email-hub.md`), ~95% built toward revenue. The engine (P0 spike, GATE PASS) and the addressing layer (P0b repo-memory) already landed — what is unproven is whether wiring them into a dispatch loop actually buys attention back.

**The switch test (honest framing):** in-session Claude Code *already works*. So the question is not "can we build?" but **"is a contained harness + one cockpit enough better than in-session that he actually switches to it?"** If that answer isn't a clear yes, the harness shouldn't be built out.

## Why now

- **P0 spike = GATE PASS** — the one unbuilt piece (the engine) is de-risked enough to wire a single seam.
- **P0b repo-memory layer is live** — the lookup/sink a dispatch loop needs already exists.
- **Email Hub is ship-first, ~95% built** — a stream of small, real, low-blast-radius issues to test on.
- **Opus-everywhere makes the Phase-2 roster's cost case weak** (architecture doc's "honest tension") — so proving Phase-1 friction-reduction *first*, lean-PRD style, is the disciplined move.

## Hypothesis

We believe that giving Fredis a **contained build harness** (engine pointed only at the target repo, worktree-isolated, draft-PR-only) + a **single cockpit** (chat + a read-only run view) + a **PRD/issue gate** will let Linards **dispatch** build work and get back **validated draft PRs** — moving his attention from *babysitting* an in-session build to *intent* (approving the enriched issue) and *review* (the draft PR) — resulting in **more build throughput per unit of his review attention, with no loss of safety.**

- **RIGHT if**, across the first **3 Email Hub issues (P4)**: each run yields a **draft PR that passes the type/lint/test gate** (`make lint types test` — this is `make ci` minus the repo-wide coverage-% floor and the network pip-audit, the two checks a small fix doesn't control; see impl plan) with **≤1 round of human fixup**, **AND** Linards judges the **dispatch→review** loop **lower-attention** than fixing that issue in-session, **AND** he **chooses to dispatch** issue #2/#3 rather than hand-fix.
- **WRONG if any one of**: the cockpit/harness **adds** attention (standing it up + monitoring costs more than it saves across the 3 runs); the draft PRs **routinely need full rework** (≳50% rewritten on ≥2 of 3); or **any containment breach** (engine writes to Fredis/the vault, or anything auto-sends / auto-merges / auto-pushes).
- **Ambiguous middle = not-yet-proven → hold, don't expand.** (E.g. passes the gate but neutral on attention, or 1 clean run + 2 mediocre.) Neither open Phase 2 nor P4b nor widen the cockpit — run more, or reassess. Only a clear RIGHT opens P4b; any WRONG stops the build.

## Target user

- **Primary:** Linards — solo operator dispatching build work on his own repos (Email Hub first).
- **Secondary (directional, not a Phase-1 goal):** future Saulera clients — "we run on what we sell"; the cockpit is a demoable surface.
- **Explicitly NOT:** a team; multiple concurrent human reviewers; anyone but Linards approving sends/merges. Not built for scale or handoff.

## Non-goals (v1)

- The Team (PA / Marketing / Sales on Eve), the "The Team" rename, the Slack-for-phone channel — **Phase 2, gated.**
- `@delegate` one-click launch from the board — single-dispatch rule; **chat is the only trigger.**
- Auto-merge / auto-send / auto-push on any channel — **permanently out (advisor mode)**, not just v1.
- Re-skinning the engine's own web UI — kept behind a generic "Engine debug (advanced)" link.
- Building the repositories memory layer — **already shipped (P0b)**; Phase 1 only verifies + writes to it.
- VPS / cloud hosting — **local-first.**
- The client-site lane (P4b) before Email Hub (P4) is green — **sequential, never parallel.**

## Risks & assumptions (top 3 — full register in the impl plan)

- **Harness adds more friction than it removes** ← assumes dispatch→review < in-session babysitting. *De-risk:* N=3 real issues with an explicit WRONG condition; kill if it trips.
- **Containment breach** (the engine runs `bypassPermissions`, so Fredis's hooks protect nothing it does) ← assumes loopback bind + target-only workspace + state-outside-the-tree holds. *De-risk:* a pre-run containment checklist that must be green before any run; Fredis + vault marked "never a target".
- **Draft PRs fail the repo gate for reasons the fix doesn't control** (coverage ≥88%, network pip-audit) ← assumes a scoped gate isolates fix quality. *De-risk:* measure the hypothesis on the type/lint/test subset; full `make ci` / GitHub CI is the review-time gate, not the harness signal.

## Open questions (resolved in build; detail in impl plan §5)

1. **Reuse vs author-fresh:** Fredis already owns Cole's PIV commands (`core_piv_loop/*`, `github_bug_fix/*`, `validation/*`, imported April). Should P4's molded fix-issue workflow **reuse** them as nodes rather than write new ones? (Daily 2026-06-30/07-01: "decision pending Linards's go-ahead.") — his call at P2/P4.
2. **Gate subset** for the P4 node — recommended `make lint types test`; full `make ci` at review. Confirm.
3. **Concurrency** — locked default 3–5; recommend the first lane runs effectively at 1 (shared Claude subscription). Confirm.

## Success metrics

- **Primary (effort / throughput):** on **≥2 of the first 3** Email Hub issues, the draft PR passes the type/lint/test gate with ≤1 fixup **and** Linards rates dispatch→review lower-attention than in-session. *Window:* the P4 run-set, before P4b opens.
- **Secondary (switch — revealed, not surveyed):** he chooses to dispatch #2 and #3 rather than hand-fix.
- **Guardrail (safety — must hold):** zero containment breaches; zero auto-send / auto-merge / auto-push; every output is a **draft PR** (+ `drafts/active/` + HubSpot/[DRAFT] Slack where outward). **A single breach = WRONG regardless of speed.**

## Experiments (the thinnest slice that proves/refutes)

The thinnest slice **is P4 itself**: one small Email Hub issue → enriched input (HITL #1) → dispatched via `query.py workflow` → worktree run → type/lint/test gate node → **draft PR** (HITL #2). If that one loop beats hand-fixing that one issue, do 2 more; if it's worse, stop — don't build P4b, don't extend the cockpit. P2 (gate/CLI) + P3 (cockpit) are the **minimum** scaffolding for that slice — nothing more (no `@delegate`, no Team panel, no engine re-skin). **Cheapest falsification:** if standing up P2 + P3 already feels like more attention than it will ever save, that's an early WRONG signal to record at the P2/P3 handoff — don't push on to P4.

---

_NOT in this PRD (they belong to the spec / impl plan): the engine's API surface, the `query.py workflow` CLI design, the cockpit JS, the workflow-YAML nodes, the containment-checklist mechanics, the build sequencing._
