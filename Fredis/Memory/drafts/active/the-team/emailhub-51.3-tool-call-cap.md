---
title: "Email Hub — Tool-Call Cap + Planning Telemetry (51.3)"
approved: false        # Linards-only: set to true to arm the run (HITL #1). Fredis never sets this.
repo: linardsb/merkle-email-hub
codebase_id: dee73f6cbc6ed8e6e06cc32dfea4a82a
github_issue: TBD      # Fredis files the GitHub issue after HITL #1, then fills the number here before firing.
workflow: fix-github-issue-emailhub
gate: "make lint types test"
lane: P4
created: 2026-07-01
---

# Implement 51.3 — Tool-Call Cap + Planning Telemetry

You are implementing **Phase 51.3** on `merkle-email-hub`. The GitHub issue **and**
`.agents/plans/51-agentic-security-hardening.md` **§51.3** together are the contract —
read §51.3 first; it is the source of truth for file paths and test names.

- **Plan:** `.agents/plans/51-agentic-security-hardening.md` §51.3 (lines 110-133)
- **Backend gate (hard):** `make lint types test` must pass before any PR.
- **Deterministic, unit-testable, backend-only** — no DB, no network, no golden baselines.

## What to do

Complete the K_max trio (run-seconds + token caps already exist) with a **deterministic
per-session tool-call cap**, plus structured per-step planning telemetry.

1. **Config flag** — add `agent_max_tool_calls: int = 25` to `app/core/config/security.py`
   (env-exposed as `SECURITY__AGENT_MAX_TOOL_CALLS`). Default 25 is deliberately permissive —
   it must not trip any current agent.
2. **Exception** — add `ToolCapExceededError(AppError)` to the agents exceptions module
   (`app/ai/agents/exceptions.py` per the plan — reconcile against live code).
3. **Counter** — in `BaseAgentService.process()` (find its live location; place the counter
   alongside the existing run-seconds / token caps) add a per-`process()` `_ToolCallCounter`
   that raises `ToolCapExceededError` at `agent_max_tool_calls + 1`. It **must reset between
   `process()` invocations** — per-session, never a module global.
4. **HTTP mapping** — map `ToolCapExceededError` → **503** with reason `tool_cap_exceeded`
   in `app/core/exceptions.py`.
5. **Telemetry** — extend the `ai.agent_decision` audit entry **additively** with
   `tool_calls_made: int` and `planning_steps: list[str]`. Additive only — existing
   consumers (Phase 44.9 Loki dashboards) must be unaffected.

## Acceptance criteria

- New tests (~6) in `app/ai/agents/tests/test_tool_cap.py`, per plan §51.3:
  cap raises at N+1 and emits a `cap_exceeded` audit line; planning steps captured for
  structured-mode agents; counter resets between `process()`; existing `agent_decision`
  consumers unaffected (additive schema); `tool_calls_made=0` for tool-less agents.
- `make lint types test` passes (new tests green; ruff + mypy + pyright clean).
- Flag defaults to 25; behaviour is a no-op for current agents until they exceed the cap.

## Scope & safety boundaries

- **51.3 only.** Do **not** touch 51.2 (safe compaction) or 51.4 (audit hash-chain) scope —
  those are separate, serially-ordered items.
- **Additive audit schema only** — do not rename or repurpose existing `ai.agent_decision`
  fields.
- The `bench_security_envelope` case (`make bench`) is **optional and out of the gate** —
  benchmarks are deselected by the `not benchmark` marker, so don't let bench wiring block
  the PR; the core deliverable is the cap + telemetry + unit tests.
- VSA: the primitive lands in `app/ai/agents/` + `app/core/config/security.py` per the plan.
- **Advisor mode:** worktree-isolated; output is a **DRAFT PR** against `main` with
  `Fixes #<issue>`. Never merge, never mark ready-for-review, never push to `main`.

_Why this issue: real security-hardening (bounds agent drift with a deterministic stop),
fully validated by the harness gate — the cap and telemetry are pure logic with unit tests,
so a green `make lint types test` is a trustworthy RIGHT signal. Second switch-test data
point (N=2), independent of the design-sync config task._
