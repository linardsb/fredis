---
title: merkle-email-hub
type: entity
category: repository
github: linardsb/merkle-email-hub
visibility: public
default_branch: main
local_path: "/Users/Berzins/Desktop/merkle-email-hub"
archon_enabled: false
tags: [repository, email-platform, fastapi, nextjs, postgres, python, productisation-lane]
related:
  - "[[REPOSITORIES]]"
created: 2026-06-30
updated: 2026-06-30
---

# merkle-email-hub (codebase)

Email Innovation Hub — a centralised email-development platform with AI agents. Build, preview, QA, and export HTML emails from one workspace; CMS-agnostic, security-first, GDPR-compliant. Linards's own IP. **Productisation lane P4.**

## Identity

- **Stack:** FastAPI (Python, `uv`) + Next.js 16 / React 19 / Tailwind / shadcn-ui; PostgreSQL + pgvector; Redis. Vertical Slice Architecture — each feature owns its models / schemas / routes / logic under `app/{feature}/`. Docker Compose for local services; Alembic migrations; CI via GitHub Actions (`ci.yml`).
- **Purpose:** Email engine + AI orchestrator + QA engine + CMS / Figma / Litmus connectors. ~95% built; ship-first lane toward revenue.

## Archon Configuration

- **Archon-enabled:** no — no `.archon/` directory. Stays `archon_enabled: false` until a lane build adds one.
- **Lane gate:** P4 (not yet green) → **not in Active Pages**; coding stays in-session / advisor-draft for now.
- **Default workflows that will fit when the lane opens:** issue-fix, feature-development, PIV-loop, comprehensive-PR-review. Dispatch mechanics: `integrations` skill + `query.py workflow` (P2 — not built).

## Workflow Preferences

- **Default branch `main`.** When the lane opens, dispatch on a worktree branch — never on `main` directly.
- **IP is Linards's, owned outright** — no IP-overhang / clean-room gate applies here. The Email Hub IP question is settled; don't re-raise it.
- **VSA discipline:** new work lands self-contained under `app/{feature}/`.
- **Advisor mode:** any dispatch yields a draft PR — never auto-merge or push.
- **Harness gate (discovered 2026-07-01):** the pre-PR `bash:` validation node is **`make lint types test`** — backend-only: `ruff format` + `ruff check --fix` · `mypy app/` + `pyright app/` · `pytest -m "not integration and not benchmark and not visual_regression and not collab"`. This is `make ci` minus the repo-wide coverage floor + network pip-audit (the two a small fix doesn't control); full `make ci` / GitHub CI is the **review-time** gate, not the harness signal. `make lint` **auto-formats** (mutates the worktree) — the create-PR node must commit the formatted result. Pick **backend-scoped** issues so this gate is a valid RIGHT signal; for `cms/` work add `make check-fe`.
- **Archon codebase id:** `dee73f6cbc6ed8e6e06cc32dfea4a82a` (registered 2026-07-01, `default_cwd` = local path, `default_branch: main`). The engine names it **`linardsb/merkle-email-hub`** (slug is null) — so `--repo merkle-email-hub` will **not** resolve; fire with `--codebase-id dee73f6…` or `--repo linardsb/merkle-email-hub`.
- **Molded workflow:** `fix-github-issue-emailhub` (lean PIV mold, Opus-pinned, worktree-isolated, draft-PR-only). Draft lives at `drafts/active/the-team/workflows/fix-github-issue-emailhub.yaml`; place into `.archon/workflows/` in this repo to arm it.
- **Gate baseline (verified 2026-07-01, separate session):** `make types` → `0 errors` (mypy + pyright, ~1.5k pre-existing pyright warnings are non-fatal); `make test` → `8174 passed, 115 skipped, 58 deselected, 2 xfailed` in ~178s, **no Docker/Postgres/Redis** (the `not integration` marker deselects DB-bound suites). So a gate failure at fire time is attributable to the *fix*, not pre-existing `app/` debt.
- **Worktree-safe (proven via CI):** `ci.yml`'s `backend` job runs the identical unit gate (`ruff`·`mypy app/`·`pyright app/`·`pytest -m "not integration"`) on a **fresh checkout with no `.env` and no `env:` block** — only the DB-bound jobs (`migrations`/`integration`/`e2e-smoke`) inject env. An Archon worktree = fresh checkout; `.env`+`.venv` are gitignored (absent) but `uv sync`/`uv run` self-provisions deps from the tracked `uv.lock`, and the unit gate needs no secrets. → the gate runs in the worktree exactly as in CI's green `backend` job.

## Dispatch History

_Reflection appends date-prefixed bullets here when daily logs reference dispatches against this repo._

- (2026-06-30) Page created.
- (2026-07-01) **First harness run — issue #302 → draft [PR #303](https://github.com/linardsb/merkle-email-hub/pull/303).** Workflow `fix-github-issue-emailhub`. Run 1 failed (gate node hit Archon's 120s bash-node timeout). Run 2's `rca` agent — unrestricted tools — did the whole job and opened PR #303 (test-only, `+22/-0`, **independently validated green: 8180 passed**), after which the redundant gate re-run failed on stdout maxBuffer. **Outcome: clean mergeable draft PR delivered.** Workflow then hardened: per-node `timeout`, gate output→log (tail-on-failure), and `denied_tools:[Bash]` on extract/rca/implement so `create-pr` is the only pusher → gate-before-PR is structural. Lane proven **as a deliverable** — N=1 of the PRD's N=3 switch-test; auto-dispatch (Active Pages) still held.
- (2026-07-01) **Second run — throwaway issue [#304](https://github.com/linardsb/merkle-email-hub/issues/304) (unit test for `format_iso`) on the HARDENED workflow** (run `3bd0cbe5…`). Verdict: **hardening proven at runtime.** `rca`/`implement` made **zero Bash calls** (`denied_tools:[Bash]` held — `rca` stayed investigation-only, unlike Run 2's full-job overstep); the gate **failed gracefully** with a readable tail (no maxBuffer crash — item 2); `create-pr` was **skipped** on gate-fail (`trigger_rule`) so gate-before-PR is **structural** (item 3). The gate correctly caught **`DTZ001`** (repo forbids naive `datetime()`; not ruff-auto-fixable) in the blind-written test → `make lint` exit 1 → **no PR emitted** (fail-safe held). Surfaces the **blind-implement yield gap**: with no shell, `implement` can't run the linter, so it trips repo-specific lint/type policy it can't discover. **No PR/branch created**; #304 left open as a re-fire target. Fix under review: lint-config-aware `implement` prompt vs a gate-fail→informed-retry node.
- (2026-07-01) **Third run — #304 re-fired on the informed-retry workflow (item 4); retry PROVEN end-to-end** (run `b1d95e6a…`). `gate1` emitted `{"passed":"false"}` (pure-JSON verdict, exit 0) → `create-pr` skipped on the `when` branch → `fix` node read `gate.log`, diagnosed **`DTZ001`**, and applied the correct **two-part fix blind** (tz-aware `datetime(…, tzinfo=UTC)` + expected string `"…+00:00"`), **zero Bash calls** → `gate2` **`GATE2_PASSED`** → `create-pr-retry` opened a clean draft **PR #305** (+12/−0, MERGEABLE). Validation artifacts disposed (PR #305 closed, branch deleted, #304 closed). **Item 4 shipped & validated.** Final workflow: `extract→fetch→rca→implement→gate1→{create-pr | fix→gate2→create-pr-retry}`; every AI node but the two PR pushers carries `denied_tools:[Bash]`. Retry cost ≈19 min wall (two full gates + a `fix` Opus pass). Not taken: a soft "read `pyproject [tool.ruff]`" nudge in `implement` to cut retry frequency — dropped to keep validation deterministic; available as a later cost optimisation.
- (2026-07-01) **Switch-test N=2 — two REAL, TODO-backed issues dispatched concurrently on the hardened workflow** (HITL #1 approved both). Enriched artifacts: `drafts/active/the-team/emailhub-51.3-tool-call-cap.md` + `emailhub-50.6.4-design-sync-constantize.md`.
  - **51.3 tool-call cap** — issue #307 → draft [PR #309](https://github.com/linardsb/merkle-email-hub/pull/309) (run `70b12166…`). Path `rca→implement→gate1 ✗(lint)→fix→gate2 ✓→create-pr-retry` (**1 fixup**). Gate green but **functionally INERT**: `_ToolCallCounter.record_tool_call()` has zero production call sites (tests only), and `BaseAgentService._process_impl` is single-shot (no tool loop) → the cap never trips and `tool_calls_made` always logs 0. The gate structurally cannot see "never called on the live path." **Not merged; inert-cap finding posted as a review comment on #309.** Fix = wire the counter into the real agentic execution surface (SDK loop / BlueprintEngine), not the single-shot completion service.
  - **50.6.4 DESIGN_SYNC constantize PR-1** — issue #308 → draft [PR #310](https://github.com/linardsb/merkle-email-hub/pull/310) (run `b2575b90…`). Path `rca→implement→gate1 ✓→create-pr` (**0 fixups**). **Mechanically correct** — 8 knobs → `tuning.py` `Final`; every consumer rewired (spot-checked `fidelity_service`/`converter_service`/`layout_analyzer`/`extract`); pinning test added. **Conservative-keep held**: only 8 of the ~15 target, adjusted the test bound to ≤57 and documented the ≤45 aspiration + PR-2→≤30 path candidly, touched no retire-candidate. Linards confirmed he overrides none of the 5 env-named knobs in prod → **cleared to merge.**
  - **Switch-test read:** 3/3 gate-green with ≤1 fixup (incl. earlier #302), but the two real tasks split — refactor/mechanical work (50.6.4) = clean, low-attention win (review = the pre-scoped 5-field env check); runtime-model-dependent work (51.3) = gate-green-but-inert, high review attention (had to reverse-engineer the execution model). **P4 = green-with-caveats:** dispatch is trustworthy for mechanical/refactor tasks, NOT trust-blind for logic-wiring tasks. **Active-Pages promotion + P4b unblock deferred to Linards's judgement** — the "gate-pass ≠ correct" lesson from #309 is the reason to hold. Engine shut down post-review.

## Recent Activity

- Most-referenced repo across the daily logs (28 distinct days as of 2026-06-30). Active build toward ship; primary income candidate.

## Related

Gated behind the `product-shape` SaaS canvas and the now-settled IP question. Index: [[REPOSITORIES]].
