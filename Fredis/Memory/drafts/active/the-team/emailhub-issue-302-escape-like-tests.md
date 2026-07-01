---
title: "Email Hub issue #302 — unit coverage for escape_like()"
approved: true        # Linards-only: set to true to arm the run (HITL #1). Fredis never sets this.
repo: merkle-email-hub
codebase_id: dee73f6cbc6ed8e6e06cc32dfea4a82a
github_issue: 302
workflow: fix-github-issue-emailhub
gate: "make lint types test"
lane: P4
created: 2026-07-01
---

# Fix merkle-email-hub issue #302 — unit coverage for `escape_like()`

You are fixing **GitHub issue #302** on `merkle-email-hub`. The issue is the contract.

- **Issue:** #302 — https://github.com/linardsb/merkle-email-hub/issues/302
- **Target file:** `app/shared/utils.py` → `escape_like(value: str) -> str`
- **Backend gate (hard):** `make lint types test` must pass before any PR.

## What to do

`escape_like()` escapes SQL `LIKE`/`ILIKE` wildcards (`\`, `%`, `_`) on user-supplied
search input and currently has **no unit tests**. Add a focused unit test that pins its
behaviour — the escaping is **order-sensitive** (backslash must be escaped first, before
`%` and `_`, or the escape characters it introduces get double-escaped).

Add `app/shared/tests/test_utils.py` covering `escape_like()`:

1. Plain input with no wildcards → returned unchanged.
2. A lone `%` → `\%`; a lone `_` → `\_`; a lone `\` → `\\`.
3. **Ordering:** an input containing `\`, `%`, and `_` together escapes correctly
   (backslash-first — no double-escaping).
4. A realistic combined search string, e.g. `50%_off\deal`.

## Acceptance criteria

- New test module `app/shared/tests/test_utils.py` with the cases above.
- `make lint types test` passes (the new test runs green; ruff + mypy + pyright clean).
- **No production-code change** — `escape_like()` behaviour is unchanged; this is coverage only.
- `format_iso()` is out of scope (follow-up).

## Scope & safety boundaries

- **Test-only.** Do not modify `escape_like()`, `format_iso()`, or anything outside `app/shared/`.
- Vertical Slice Architecture: the test lives under `app/shared/tests/`.
- **Advisor mode:** worktree-isolated; output is a **DRAFT PR** against `main` with `Fixes #302`.
  Never merge, never mark ready-for-review, never push to `main`.

_Why this issue: it proves the Email Hub harness lane (issue → worktree → `make lint types test`
gate → draft PR) at the lowest possible blast radius — a test-only change whose worst case is an
ignorable draft PR, on the primary-income repo._
