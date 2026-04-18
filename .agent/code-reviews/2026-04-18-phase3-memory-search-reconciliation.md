# Code Review — Phase 3 Memory Search Reconciliation

Scope: the files changed/added by `/core_piv_loop:execute` against
`.agent/plans/phase-3-memory-search-reconciliation.md`. Unrelated pre-existing
working-tree changes (brand rename, content-ideation commands, `setup_workspace.py`)
are out of scope.

## Stats (Phase 3 surfaces only)

- Files Modified: 4 — `config.py`, `embeddings.py`, `memory_search.py`, `CLAUDE.md`
- Files Added: 6 — `schedule/com.linards.ssh-tunnel.plist`, `schedule/README.md`,
  `tests/test_db.py`, `tests/test_embeddings.py`, `tests/test_memory_index.py`,
  `tests/test_memory_search.py`
- Files Deleted: 0
- New lines: ~380
- Deleted lines: ~15
- Tests: 113 → 132 passing (+19). 0 ruff errors, 0 new mypy errors
  (one pre-existing `unused-ignore` in `integrations/asana_api.py:487`, confirmed
  present on clean HEAD — out of scope).

---

## Issues

### 1. Redundant `_prior()` call in `search_semantic`

```
severity: low
file: .claude/scripts/memory_search.py
line: 109-114
issue: _prior(r["file_path"]) computed twice per row — once for score, once for the min_score filter.
detail: The list comprehension multiplies `r["score"] * _prior(r["file_path"])`
  at line 109 (score field) and again at line 114 (filter condition). For every
  row, `_prior` walks the SEARCH_PATH_PRIORS dict. Correctness is fine — same
  value both times — but it's a needless recomputation and a minor DRY violation
  that the equivalent hybrid/keyword paths don't exhibit.
suggestion: Hoist into a generator before the comprehension, or use a walrus:
    results = [
        SearchResult(..., score=boosted, ...)
        for r in rows
        for boosted in [r["score"] * _prior(r["file_path"])]
        if boosted >= min_score
    ]
  Or split into an explicit loop — the existing file isn't shy about loops.
```

### 2. `SEARCH_PATH_PRIORS` iteration order is prefix-order-sensitive

```
severity: low
file: .claude/scripts/memory_search.py
line: 33-38
issue: _prior returns the first matching prefix, not the longest.
detail: If a future edit adds `"drafts/"` alongside `"drafts/sent/"`, the
  multiplier that wins depends on Python dict insertion order, not on which
  prefix is more specific. A path like `drafts/sent/a.md` would pick up the
  first-inserted prefix even if the more-specific `drafts/sent/` entry exists
  later.
suggestion: Sort prefixes by length (desc) on lookup, or document the invariant
  at the config site:
      for prefix, mult in sorted(SEARCH_PATH_PRIORS.items(), key=lambda kv: -len(kv[0])):
  Current config has no overlapping prefixes so this is latent, not live —
  but cheap to lock in before someone adds a second draft bucket.
```

### 3. Plist hard-codes a `Desktop/claude-code-second-brain` log path

```
severity: medium
file: .claude/scripts/schedule/com.linards.ssh-tunnel.plist
line: 35, 38
issue: StandardOutPath/StandardErrorPath assume the repo lives at
  `__HOME__/Desktop/claude-code-second-brain/.claude/data/logs/`.
detail: The README install step only sed-replaces `__HOME__`, `__KEY_PATH__`,
  `__VPS_USER__`, `__VPS_HOST__`. The path segment after `__HOME__/` is baked
  in. If the user (now or on a future machine) clones this repo anywhere else
  — e.g., `~/code/second-brain` — launchctl will silently try to write to a
  non-existent directory and the tunnel will still run but log nothing.
  The README says `mkdir -p .claude/data/logs` relative to CWD, so an operator
  who follows the README from a different clone path gets a mismatch between
  "where I made the log dir" and "where launchd writes logs".
suggestion: Either (a) replace the hard-coded path fragment with a placeholder
  like `__REPO_ROOT__/.claude/data/logs/ssh-tunnel.{out,err}.log` and extend
  the README's sed block, or (b) drop the two StandardOutPath/StandardErrorPath
  keys entirely and let launchd default to syslog — logs are still reachable
  via `log show --predicate 'subsystem == "com.linards.ssh-tunnel"'`.
  Option (a) is more discoverable; option (b) is one less thing to get wrong.
```

### 4. `test_prior_boost_reorders_results` is deterministic but relies on identical FTS rank

```
severity: low
file: .claude/scripts/tests/test_memory_search.py
line: 79-85
issue: Test depends on both rows returning identical raw FTS5 `rank` + identical
  vector distance.
detail: Both seeded chunks have the same content ("client reply draft voice")
  and same embedding vector, so FTS5 rank and cosine distance are the same —
  therefore priors alone determine order. This is the intended setup, but it's
  implicit. If a future change to `_quote_fts_query` or FTS5 scoring introduces
  per-row path-dependent terms, the test could pass or fail for the wrong
  reason.
suggestion: Add an explicit assertion that the non-boosted scores are equal,
  so the failure mode is diagnosable:
      drafts_pre = results[0].score / 1.5
      research_pre = results[1].score / 1.0
      assert abs(drafts_pre - research_pre) < 1e-6, "raw scores should match — prior alone should reorder"
  Optional — the test passes today and the setup is documented.
```

### 5. `_seed_chunk` accepts `np.ndarray | None` instead of `NDArray[np.float32]`

```
severity: low
file: .claude/scripts/tests/test_db.py
line: 19
issue: Test helper uses the un-parameterised `np.ndarray` type instead of the
  `numpy.typing.NDArray[np.float32]` alias that the rest of the codebase uses.
detail: `db.insert_vector` is typed `NDArray[np.float32]`. The test helper
  widens that to plain `np.ndarray`, which mypy treats as `ndarray[Any, Any]`.
  The helper casts with `.astype(np.float32)` so runtime is fine — it's a
  typing-hygiene nit, not a bug.
suggestion: Import and use the existing alias:
      from numpy.typing import NDArray
      def _seed_chunk(..., embedding: NDArray[np.float32] | None = None, ...)
  Drop the `.astype(np.float32)` cast since callers already pass float32.
```

### 6. CLAUDE.md `launchctl kickstart` suggestion uses `$UID` from bash, not the user's shell

```
severity: low
file: CLAUDE.md
line: ~265 (inside the "If memory_search.py fails with a connection error" block)
issue: `launchctl kickstart -k gui/$UID/com.linards.ssh-tunnel` is the shell
  form; users reading the doc might paste it into zsh or another shell where
  `$UID` is not set (zsh does set UID by default, but fish does not).
detail: Low practical risk — macOS default shells all export `UID` — but
  copy-paste into fish or a plain `sh -c '...'` without the bash preamble
  will silently expand to `gui//com.linards.ssh-tunnel` and fail with an
  obscure error.
suggestion: Replace with `gui/$(id -u)/com.linards.ssh-tunnel` which is
  portable across shells. Alternatively `launchctl unload ... && launchctl load ...`
  is what the README already documents, so just link to the README instead
  of introducing a second invocation style.
```

---

## Not Flagged (verified, intentional)

- **Search-time vs index-time priors** — documented plan deviation from PRD
  wording, with rationale in the plan's NOTES section. Pragmatic reading wins.
- **SQL in `db.py` uses parameterised queries** for `path_prefix LIKE ?` —
  no injection surface. FTS queries are quoted term-by-term via
  `_quote_fts_query`.
- **`pytest.importorskip("sqlite_vec")`** guards the three DB-backed test files
  so CI without the extension degrades gracefully.
- **Monkeypatch strategy in `test_memory_search.py` / `test_memory_index.py`** —
  patches `db.DATABASE_URL` and `db.DATABASE_PATH` at module scope, which is
  the correct level given how `get_memory_db()` resolves the factory. Verified
  by 132/132 passing including the two new fixtures.
- **Plist uses placeholders for secrets** (`__KEY_PATH__`, `__VPS_USER__`,
  `__VPS_HOST__`) — no leaked hostnames/usernames in the committed file.
  `plutil -lint` returns OK.
- **`embed_batch` batch_size 32 → 256** — PRD-aligned; callers with explicit
  batch_size are unaffected; `memory_index.index_file` now throughput-bumps
  automatically.

---

## Summary

No critical or high-severity issues. The implementation faithfully executes the
plan with one pragmatic PRD deviation that is itself documented in the plan.

The flagged items are incremental improvements — none block commit. The plist's
hard-coded log path (#3) is the most worth fixing before someone clones this
repo to a non-`~/Desktop/` location; everything else is minor.

**Recommendation: commit as-is; open a follow-up for #3** (log path
parameterisation) if a second-machine setup is imminent.
