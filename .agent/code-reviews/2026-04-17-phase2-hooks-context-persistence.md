# Code Review — Phase 2: Hooks & Context Persistence

**Date:** 2026-04-17
**Scope:** Implementation of `.agent/plans/phase2-hooks-context-persistence.md`
**Reviewer:** code-review (automated)

## Stats

- Files Modified: 9
- Files Added: 2
- Files Deleted: 0
- Approximate new lines: ~280
- Approximate deleted lines: ~30

**Modified**
- `.claude/scripts/shared.py` (atomic `save_state`, `invocation_source()`)
- `.claude/scripts/memory_flush.py` (env var + priority-signals prompt bullet + invariant comment)
- `.claude/scripts/heartbeat.py` (env var)
- `.claude/scripts/memory_reflect.py` (env var)
- `.claude/chat/engine.py` (env var)
- `.claude/hooks/pre-compact-flush.py` (recursion guard)
- `.claude/hooks/session-end-flush.py` (recursion guard)
- `.claude/hooks/session-start-context.py` (3-day daily-log window)
- `CLAUDE.md` (hook convention bullet)
- `.agent/plans/second-brain-prd.md` (Phase 2 ✅ DONE marker)

**Added**
- `.claude/scripts/tests/test_shared.py` (13 unit tests)
- `.claude/scripts/tests/test_hooks.py` (6 subprocess tests)

---

## Issues

```
severity: medium
file: .claude/scripts/memory_flush.py
line: 27
issue: Module-top env var assignment unconditionally overwrites existing CLAUDE_INVOKED_BY
detail: If a test or script imports memory_flush while another Agent SDK caller was
        already imported (e.g., `import heartbeat; import memory_flush`), the later
        import silently changes the process-wide env to "memory_flush". The recursion
        guard still fires correctly (any truthy value skips), but the observability
        label in hook-execution.log (`invoked_by=...`) will be wrong — you'd think
        heartbeat's sub-session triggered the skip, when it was actually memory_flush.
        Same pattern applies to heartbeat.py:30, memory_reflect.py:25, engine.py:16.
suggestion: Set only if unset, preserving the first caller's label:
        `os.environ.setdefault("CLAUDE_INVOKED_BY", "memory_flush")`
        Applies identically to all four entry points.
```

```
severity: low
file: .claude/scripts/shared.py
line: 133-139
issue: invocation_source() returns "" (empty string) when env var is set to empty
detail: `os.environ.get("CLAUDE_INVOKED_BY")` returns "" when the var is set to empty,
        not None. Hooks rely on `if invoked:` truthiness, so "" bypasses the guard.
        The plan documented this as acceptable ("nothing in the codebase sets it to
        empty"), but the helper's contract is subtle — a future caller that does
        `os.environ["CLAUDE_INVOKED_BY"] = ""` (e.g. a test trying to "clear" the
        guard) would silently disable recursion protection.
suggestion: Return None for empty strings to make the contract explicit:
        `val = os.environ.get("CLAUDE_INVOKED_BY"); return val if val else None`
        Or document the empty-string semantics in the docstring.
```

```
severity: low
file: .claude/scripts/shared.py
line: 117-130
issue: save_state is no longer atomic under concurrent writers
detail: Two processes calling save_state(state, same_path) simultaneously will race on
        `tmp_file.write_text()` — both write to `foo.json.tmp`, the second overwrites
        the first, then both os.replace. Only one state survives. In practice this
        doesn't happen today (each state file has a single writer: heartbeat-state is
        only written by heartbeat.py, flush-state has file_lock around it). But the
        new atomicity claim in the docstring is single-writer atomicity only, not
        multi-writer safety.
suggestion: Either (a) clarify the docstring to "single-writer atomicity — callers are
        responsible for serialization across processes", or (b) use a per-pid tmp suffix
        like `f"{state_file.suffix}.{os.getpid()}.tmp"` so concurrent writers don't
        collide on the tmp path. Option (a) is cheaper and matches current call sites.
```

```
severity: low
file: .claude/scripts/tests/test_shared.py
line: 84-89
issue: Test asserts the empty-string edge case without flagging it as a surprise
detail: test_invocation_source_empty_string_is_falsy documents that `""` is returned
        unchanged, but if invocation_source is fixed to return None for empty (see
        issue above), this test will fail. Tying a test to the subtler behavior
        locks in the foot-gun.
suggestion: Rename to test_invocation_source_normalises_empty_to_none and flip the
        assertion if adopting the fix. Or remove this test — the hook's truthy check
        makes the empty-vs-None distinction irrelevant to actual behavior.
```

```
severity: low
file: .claude/hooks/session-start-context.py
line: 45
issue: `from datetime import timedelta` imported inside function body
detail: Ruff clean, but stylistically inconsistent with the rest of the codebase
        where imports live at module top. Kept at function scope because the
        previous implementation had it there (in the fallback branch). Now that
        timedelta is used on every call, the function-scope import is no longer
        conditional.
suggestion: Move to the module-level datetime import: `from datetime import datetime, timedelta`.
        Minor cleanup, non-blocking.
```

```
severity: low
file: .claude/scripts/tests/test_hooks.py
line: 39
issue: timeout=30 on subprocess.run may be tight on cold uv starts in CI
detail: First `uv run python` invocation on a fresh CI runner can take 5-15s before
        pytest starts. Running 6 subprocess tests sequentially is ~60-90s of
        `uv run` overhead. Tests pass locally in 0.65s (venv is warm), but this
        could flake on a cold CI cache.
suggestion: Either (a) share a single subprocess invocation per test via a module-scoped
        fixture that reuses the interpreter, or (b) bump timeout to 60 and accept the
        slower test run. (a) is non-trivial; (b) is a one-line change. Ship (b) if
        flakes appear; otherwise leave as-is.
```

```
severity: informational
file: .claude/hooks/pre-compact-flush.py
line: 114-120
file: .claude/hooks/session-end-flush.py
line: 119-125
issue: Guard runs before ensure_directories() — confirmed intentional per plan
detail: Not a bug — the plan explicitly specified this order so the skip path
        writes zero files. Noting for future maintainers: if ensure_directories()
        grows side effects beyond `mkdir`, the skip path may need to call a
        no-op-safe initializer first.
suggestion: None. Preserve current order.
```

```
severity: informational
file: .claude/scripts/memory_flush.py
line: 163-166
issue: The no-setting_sources invariant comment is correctly placed and worded
detail: The comment explicitly calls out that omitting setting_sources is the
        primary recursion firewall and that CLAUDE_INVOKED_BY is defense-in-depth.
        Future maintainers copying this pattern into a new caller should preserve
        this reasoning.
suggestion: None — good defensive commenting.
```

---

## Positive Observations

- **Test coverage is proportional to risk surface.** 13 tests for shared.py helpers (atomic save, lock, daily log, invocation source) and 6 subprocess tests for hooks' skip paths. Happy-path spawn is deliberately out of scope (covered by Level 4 manual validation per plan). No over-testing.
- **Atomic save correctly handles orphan .tmp files.** `test_save_state_atomic_leaves_original_intact` verifies that a malformed tmp from a prior crash doesn't corrupt the real state file, and that the next successful save cleans up the orphan.
- **Trust-boundary escape in `append_to_daily_log` is covered by a dedicated test.** Pre-existing behavior, but now regression-protected.
- **Recursion guard uses a single shared helper (`invocation_source`)** rather than duplicating `os.environ.get` across both hooks — good DRY hygiene.
- **Test env isolation is explicit.** `test_hooks.py::_run_hook` pops CLAUDE_INVOKED_BY before spawning, preventing parent env leakage. `test_shared.py` uses `monkeypatch` with automatic restore.
- **Priority-signals bullet uses implicit string concatenation to stay under line-length limit** rather than suppressing the lint rule.

---

## Summary

No critical or high-severity issues. Two medium/low items worth considering before merge:

1. **`os.environ.setdefault`** instead of unconditional assignment (medium) — makes observability labels stable and prevents test-order-dependent behavior.
2. **`invocation_source()` normalising empty → None** (low) — tightens the contract; optional.

Everything else is informational or style. The implementation matches the plan, tests cover the critical paths, and pre-existing patterns (logging, error handling, file locking) are preserved faithfully.

**Recommendation:** Ship as-is, or apply fix #1 first (3-line change across 4 files).
