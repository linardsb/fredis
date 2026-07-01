---
title: "Email Hub — DESIGN_SYNC flag cull, PR-1 constantize subset (50.6.4)"
approved: false        # Linards-only: set to true to arm the run (HITL #1). Fredis never sets this.
repo: linardsb/merkle-email-hub
codebase_id: dee73f6cbc6ed8e6e06cc32dfea4a82a
github_issue: TBD      # Fredis files the GitHub issue after HITL #1, then fills the number here before firing.
workflow: fix-github-issue-emailhub
gate: "make lint types test"
lane: P4
created: 2026-07-01
---

# Implement 50.6.4 PR-1 — DESIGN_SYNC constantize subset (PR-1 ONLY)

You are implementing **Phase 50.6.4, PR-1 only** on `merkle-email-hub`. The GitHub issue
**and** `.agents/plans/tech-debt-19-deferred-items-cleanup.md` **§50.6.4** together are the
contract — read §50.6.4 first.

- **Plan:** `.agents/plans/tech-debt-19-deferred-items-cleanup.md` §50.6.4 (lines 171-215)
- **Backend gate (hard):** `make lint types test` must pass before any PR.
- **This is PR-1 (constantize) only** — the additive half. PR-2 (retire-feature) is a
  separate, later PR and is **out of scope here**.

## What to do

`app/core/config/design_sync.py` carries ≈62 `DesignSyncConfig` fields today (count live).
PR-1 trims the **constantize** subset — over-engineered knobs on keeper features become
`Final` constants. No behaviour change, no deletions of features/tests/flags.

1. **Inventory.** Read `app/core/config/design_sync.py` and `feature-flags.yaml`. For each
   field, classify into (constantize) / (retire-feature) / (keep). You have **no shell** —
   use the Read / Grep / Glob tools (not Bash) to search each field name across `app/`
   *excluding* `tests/` to see its real, non-test usage.
2. **Constantize (PR-1 action).** For each field that is **both** (a) clearly an
   over-engineered knob on a keeper feature **and** (b) not plausibly a per-deployment env
   override: move it to a `Final` constant in `app/design_sync/tuning.py`, update **every**
   consumer to reference the constant, then delete the config field.
3. **Conservative-keep default (HARD RULE).** *"If unsure on any specific field, leave it in
   PR-1's keep list."* (plan §50.6.4, verbatim.) If you cannot prove a field is only ever
   read internally, or it looks like a real per-deployment knob, **leave it alone**.
   Under-delivering on the count is correct and safe; silently killing a production knob is
   not — err to keep.
4. **Bounded-count test.** Add to `app/core/tests/test_config_design_sync.py`:
   ```python
   def test_design_sync_field_count_bounded():
       from app.core.config.design_sync import DesignSyncConfig
       assert len(DesignSyncConfig.model_fields) <= 45  # PR-1 target; PR-2 tightens to <=30
   ```

## Acceptance criteria

- `make lint types test` passes. Note: mypy + pyright are the mechanical check here — a
  constantized field whose consumer you missed becomes an attribute/type error and the gate
  fails. A green gate means the refactor is **mechanically complete**.
- Field count lands **≤45** (PR-1 target; ≈15-17 constantized). **But** if conservative-keep
  leaves you above 45 while behaviourally safe, ship what is safe and state the shortfall in
  the PR description — do **not** force the count by constantizing an ambiguous field.
- **No behaviour change:** no test deletions, no `feature-flags.yaml` edits, no
  retire-feature deletions.

## Scope & safety boundaries

- **PR-1 = constantize ONLY.** Never retire/delete a feature, its tests, or its flag this
  round — that is PR-2.
- **Do NOT touch these retire-feature candidates this round:** `custom_component_*`,
  `wrapper_unwrap`, `vlm_verify_*`, `sibling_*`, `regression_strict`,
  `vlm_low_confidence_threshold`, `vlm_verify_client`. Leave every one alone.
- **No Bash** — the implement node runs with `denied_tools: [Bash]`; do the usage analysis
  with Read / Grep / Glob.
- VSA: changes stay under `app/core/config/`, `app/design_sync/`, and the config test dir.
- **Advisor mode:** worktree-isolated; output is a **DRAFT PR** against `main` with
  `Fixes #<issue>`. Never merge, never mark ready-for-review, never push to `main`.

_Why this issue: a real, representative refactor — a heavier, more honest second switch-test
data point than a test-only change. The gate validates the refactor is mechanically complete
(all consumers updated); **Linards validates at HITL #2 that the field SELECTION is
semantically safe** — eyeball the constantized-field list against the live deployment env,
since any field set via `DESIGN_SYNC__*` in production must not have been constantized._
