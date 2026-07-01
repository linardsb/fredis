---
title: "Email Hub #304 — unit test for format_iso (harness validation)"
approved: false
codebase_id: dee73f6cbc6ed8e6e06cc32dfea4a82a
github_issue: 304
workflow: fix-github-issue-emailhub
gate: "make lint types test"
disposable: true
---

# Contract — issue #304: unit test for `format_iso()`

**Why this exists:** a throwaway validation run to prove the *hardened* `fix-github-issue-emailhub`
workflow behaves at runtime — the version with `denied_tools:[Bash]` on extract/rca/implement +
the gate output→log fix has **never run** (PR #303 came from the pre-hardening version). This run
confirms two things live: (1) `rca`/`implement` genuinely cannot push (no shell), and (2) the
pipeline still emits a passing DRAFT PR. Disposable — the PR + issue #304 get closed after.

## The change (the issue is the contract)

- **File:** `app/shared/tests/test_utils.py` (mirror location for `app/shared/utils.py`).
- **Add:** one unit test for `format_iso`.
- **Expected behaviour:** `format_iso(dt)` returns `dt.isoformat()`.
  Concretely: `format_iso(datetime(2026, 7, 1, 12, 30, 0)) == "2026-07-01T12:30:00"`.
- **Scope:** test-only. Do **not** modify `app/shared/utils.py`. No new dependencies.
  Respect Vertical Slice Architecture — the test stays under `app/shared/`.

## Gate

`make lint types test` (backend unit gate) MUST pass before the PR node. Baseline on `main`
is green (types 0 errors; ~8174 passed) so any failure is attributable to this change.

## Output

A DRAFT PR against `main`, `Fixes #304`, test-only. Never merged, never pushed to a protected
branch. This is advisor mode — Linards reviews, and here the plan is to close it as the
validation artifact it is.
