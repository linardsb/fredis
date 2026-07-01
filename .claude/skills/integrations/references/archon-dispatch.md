# Archon build-harness dispatch

Fredis dispatches build / delivery work (fix an issue, build a client site) to the
**Archon engine** — a local, loopback-only harness that runs AI workflows in
**isolated git worktrees** and ends in a **draft PR**. This reference covers
"run workflow X on repo Y" end to end. (Dispatch knowledge is mined from the
Archon kit's `archon` skill; there is **no 25th top-level Fredis skill** — it lives
here inside `integrations`.)

## The single seam — `query.py workflow`

`python .claude/scripts/query.py workflow …` is the **ONLY** path into the engine.
Chat, Slack, and the cockpit all fire through this CLI; **nothing POSTs the engine
directly.** One seam = one place to gate, log, and contain.

```bash
python .claude/scripts/query.py workflow list                       # engine's workflow catalogue
python .claude/scripts/query.py workflow run <name> --prd <slug> --repo <slug> --i-confirm-run
python .claude/scripts/query.py workflow status <runId>             # node / status state
python .claude/scripts/query.py workflow approve <runId> [--comment "…"]   # resume an approval: node
python .claude/scripts/query.py workflow reject  <runId> [--reason  "…"]
```

`list / status / approve / reject` need the engine running (loopback `:3090`, booted
per WS1). If it's down they return a clear *"Archon engine unreachable"* message —
boot it, or point `ARCHON_BASE_URL` at the right host (e.g. `http://[::1]:3090` for
IPv6 loopback).

## The PRD gate (HITL #1) — no approved PRD, no run

`workflow run` **refuses** unless it resolves an **approved** artifact from
`Fredis/Memory/drafts/active/the-team/`:

- The run input (`$ARGUMENTS`) is **only ever** that artifact's body — never a
  free-form string. `--prd "just do X"` is refused; so is any path outside the gate
  dir.
- Approval = front-matter `approved: true`. **Only Linards sets it** — as hard a
  boundary as never-send. Fredis drafts the PRD *without* the flag; setting it is
  Linards's sign-off.
- `--prd <slug>` picks `the-team/<slug>.md`; omit `--prd` to auto-pick the single
  approved artifact (0 or >1 approved → refused, ask for `--prd`).

Shape the lean PRD in chat with the `idea-validation` + `launch-governance` skills
(`docs/PRD/prd-best-practices.md` is the shape); the approved file is the run input.
`archon-interactive-prd` stays available engine-side as an **unused fallback** — in
Phase 1 PRDs are shaped in chat, not by that workflow.

## Resolve-flow — which workflow, which repo

1. `Fredis/Memory/REPOSITORIES.md` (always in context) — the codebase index + the
   gated Default Dispatch Rule + **Active Pages** (a repo becomes a default dispatch
   target only once its lane is green).
2. `Fredis/Memory/repositories/<slug>.md` — per-repo detail: default branch,
   discovered gate, dispatch history, workflow preferences.
3. Pick the workflow (catalogue below), pass `--repo <slug>` (resolves to a
   registered codebase) or `--codebase-id <id>`.

**Fredis + the vault are NEVER dispatch targets.** Active Pages is empty until
P4 (merkle-email-hub) / P4b (saulera-client-starter) go green.

## Workflow catalogue (engine-side; `workflow list` is authoritative)

| Intent | Workflow | Notes |
|---|---|---|
| Fix issue #N | `archon-fix-github-issue` | brownfield; input = the enriched issue |
| Comprehensive PR review | `archon-comprehensive-pr-review` | |
| Quick PR review | `archon-smart-pr-review` | |
| Implement from plan | `archon-feature-development` / `archon-plan-to-pr` | |
| Plan + implement | `archon-idea-to-pr` | |
| Interactive PRD | `archon-interactive-prd` ⚡ | available fallback — NOT wired in Phase 1 |
| General / debug | `archon-assist` | fallback when nothing matches |

Molded per-lane workflows (e.g. Email Hub's `archon-fix-github-issue` with a
`make lint types test` gate node, or `saulera-client-starter/.archon/workflows/new-client-site.yaml`)
live in the **target** repo's `.archon/workflows/`, never in Fredis.

## Worktree isolation + base branch

- Runs execute in an **isolated git worktree** kept **outside any git tree**
  (`~/.archon/…`) — so nothing lands in the Fredis tree (which would wedge the
  vault-sync `git pull --ff-only`).
- Base-branch auto-detection needs `origin/HEAD` or `origin/main`. If a repo's
  default branch differs (e.g. `saulera-client-starter` is **`master`**), set
  `worktree.baseBranch: master` in that repo's `.archon/config.yaml`.

## Containment (the engine ignores Fredis's hooks)

The engine runs `permissionMode: bypassPermissions`, so **Fredis's `PreToolUse`
hooks protect nothing it does.** Containment is enforced by:

- **loopback bind only** (never all-interfaces) + **no platform adapters**
  (Slack / Telegram / Discord / GitHub-push all off),
- **workspace scoped to the target repo** (never Fredis, never the vault, never the
  engine clone) — confirm the workspace path before firing,
- **state + worktrees outside any git tree**,
- **draft-PR-only output** — never auto-merge, never push to a protected branch.
  `--i-confirm-run` is required before a run fires (it opens a PR on a real remote,
  on a shared Claude subscription).

## Firing internals (for debugging)

A run fires in two HTTP steps: create an **idle** conversation
(`POST /api/conversations {codebaseId}` — omit `message`, else it auto-dispatches a
chat turn) → `POST /api/workflows/{name}/run {conversationId, message}`. The fire
response carries `{accepted, status}` but **not** the runId; the CLI correlates it
via `GET /api/workflows/runs`. `conversationId` (orchestrator-internal) ≠ `id`
(`web-…` platform id) — run rows key on `conversationId`. *(HTTP-fire verified live
in WS1.4; the id/correlation detail is confirmed on the first live P4 run.)*
