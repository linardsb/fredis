# The Team — build playbook (one prompt per context window)

**Purpose.** Detailed, **self-contained** prompts for the "Fredis + The Team" build (`fredis-agent-architecture.md`, Addendum 2026-06-30). Run **each in its own fresh context window** to avoid context rot.

**The anti-context-rot rule (from the loop-engineering source).** Each session: (1) **orients from durable docs**, not from prior chat; (2) does **one focused job**; (3) **writes a handoff file** so the next window resumes from state, not from a bloated transcript. Never carry a single window across two phases.

**Standing rules baked into every prompt.** Advisor mode (draft-only, never auto-send) · containment (Archon never touches the Fredis repo or vault; bind to loopback only) · local-first · Opus everywhere with a concurrency cap (default 3–5, overridable) · two HITL gates (post-brief PRD approval, post-implementation PR review) · **no build past a phase's scope without explicit go-ahead.**

**Single dispatch path (2026-06-30 update).** Chat is the *only* thing that fires a run — Fredis chat / Slack → `query.py workflow`. The cockpit board, the "Studio" tab, and the engine's own web UI are **read-only views over the same run state**, never independent dispatch surfaces. If a launch button is ever added to a visual surface, it POSTs through the *same* Fredis dispatch path — never a second direct-to-engine POST ("a button over the same dispatch, not its own brain"). Add a second trigger only when run volume actually forces it.

**One lane end-to-end first (2026-06-30 update).** Prove a single lane through the whole loop before widening — Archon is the only unbuilt piece and everything rides on it, so wire one seam at a time or you won't know which broke. **First lane = Email Hub** (`~/Desktop/merkle-email-hub`): issue → worktree → its own test/CI gate → **draft PR**. **Second lane = the client-site factory** (`~/Desktop/saulera-client-starter`), only after the first is green. This supersedes the archon plan's Addendum-2 Decision 1 ("both domains in parallel") and restores that plan body's original v1 target (Email Hub first).

**Repositories memory layer (2026-06-30 update).** The build sits on a repo-aware second-brain index — `Fredis/Memory/REPOSITORIES.md` (always-loaded) + `Fredis/Memory/repositories/<slug>.md` (per-repo, lazy-loaded), with reflection appending dispatch history over time. This is the lookup layer that lets chat resolve "fix issue N on Email Hub" → repo + workflow + worktree, and the **sink P4/P4b write dispatch history to**. It is the build of Addendum-2 Decision 3 / archon-plan §E, sourced from Cole Medin's "Archon as an arm of the second brain" workshop kit (`dynamous-community/workshops/archon-as-second-brain-arm`, private — Linards's gh account has access). **It works with or without Archon**, so it's stood up early (P0b) and independent of the engine spike. Adapt, don't copy: the workshop's `archon` skill folds into `integrations` + `query.py workflow` (24-skill cap — no 25th skill); the Default Dispatch Rule activates per-lane only once that lane is proven.

## Session map

| # | Session | cwd | Gated on | Handoff artifact |
|---|---|---|---|---|
| **P0** | Archon engine spike | Archon clone | — | `.agent/plans/the-team/p0-archon-spike-report.md` |
| **P0b** | Repositories memory layer | Fredis repo root | — (∥ P0) | `.agent/plans/the-team/repositories-system.md` |
| **P1** | Phase-1 plan + lean PRD | Fredis repo root | P0 | `phase1-PRD.md` + `.agent/plans/the-team/phase1-implementation.md` |
| **P2** | PRD-gate + `query.py workflow` | Fredis repo root | P1 approved | gate code + impl-plan update |
| **P3** | Cockpit skeleton | `~/Desktop/mission-control` | P0 | `mission-control/COCKPIT.md` |
| **P4** | First lane: Email Hub issue→PR | Fredis root (target = `merkle-email-hub`) | P2 + P3 | draft PR + dispatch-history entry |
| **P4b** | Second lane: client-site end-to-end | Fredis root (target = `saulera-client-starter`) | **P4 green** | draft PR + dispatch-history entry |
| **P5** | Phase-1→2 gate review | Fredis repo root | P4 (+ P4b) | `.agent/plans/the-team/phase1-gate-review.md` |
| **P6** | The Team: PA on Eve | new Eve repo | **P5 = go** | `.agent/plans/the-team/pa-agent.md` |
| **P7** | The Team: Sales agent | Eve repo | P6 + persona decided | `.agent/plans/the-team/sales-agent.md` |
| **P8** | The Team: Marketing agent | Eve repo | P6 | `.agent/plans/the-team/marketing-agent.md` |

> P1 is the planning prompt already at `docs/agents/the-team-phase1-build-prompt.md` — reproduced below for completeness. P6–P8 are **gated**: do not open them until P5 returns a go. **P4 (Email Hub) runs before P4b (client-site) — one lane proven before the next, never in parallel.**

---

## P0 — Archon engine spike (cwd = `~/Desktop/cloned_repos/archon/Archon`)

```
RUN FROM (cwd): ~/Desktop/cloned_repos/archon/Archon

You are running a zero-integration spike to prove the Archon engine works locally. Touch NOTHING outside the Archon clone.

CLONE: ~/Desktop/cloned_repos/archon/Archon — the canonical github.com/coleam00/Archon, branch dev, fresh (last commit 2026-06-27). IGNORE the sibling ~/Desktop/cloned_repos/archon/remote-coding-agent (an older mirror, 2026-04-08).

READ FIRST (Fredis docs by absolute path — you are NOT in the Fredis repo):
- ~/Desktop/claude-code-second-brain/.agent/plans/fredis-archon-mission-control.md  (sections: "Verified Archon API facts", "Phase 0 — spike", "Risks & gotchas")

DO, each with a verify check:
0. git pull on the Archon clone (already canonical); decide dev vs main for the spike.  → verify: HEAD is current; note the branch used.
1. Install Bun; build Archon from this clone.            → verify: server starts; GET /api/workflows returns JSON.
2. Reconcile the port (the plan says :3090; STUDIO-PLAN said :3000).  → verify: note the ACTUAL port.
3. Configure Claude auth with CLAUDE_USE_GLOBAL_AUTH=true (avoids the CLAUDE_CODE_OAUTH_TOKEN-shadows-credentials gotcha).
   → verify: archon-assist runs end-to-end on a THROWAWAY repo; a worktree + result appear.
4. Serve a one-line page over http://localhost and fetch the Archon API from it.  → verify: JSON returns in the browser (proves the cross-origin overlay path).
5. Confirm the draft-PR path exists (every lane's output is a draft PR): `gh auth status` + `gh pr create --help` show --draft.  → verify: gh is authenticated; note the gh account.

CONTAINMENT: bind Archon to loopback only — never all interfaces. Keep Archon's SQLite + worktrees OUTSIDE any git tree. The smoke test runs on a THROWAWAY repo only — never Email Hub, saulera-client-starter, Fredis, or the vault.

OUTPUT → write ~/Desktop/claude-code-second-brain/.agent/plans/the-team/p0-archon-spike-report.md (absolute — it must land in Fredis) with: actual port, auth method that worked, the localhost-fetch result, the repo identity (coleam00/Archon vs the local clone), and any blocker. Mark anything unverified as UNVERIFIED. Then STOP — do not start Phase 1.
```

---

## P0b — Repositories memory layer (cwd = Fredis repo root) — runs ∥ P0, independent of the engine

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base)

You are installing the repo-aware second-brain memory layer: REPOSITORIES.md (always-loaded index) + repositories/<slug>.md (per-repo pages) + reflection/flush wiring. This is the build of Addendum-2 Decision 3 / archon-plan §E, from Cole Medin's "Archon as an arm of the second brain" workshop kit. It works WITH OR WITHOUT Archon, so it is independent of the P0 engine spike and can run in parallel. Build the addressing/memory layer ONLY — no Archon dispatch code here.

SOURCE KIT (private repo — Linards's gh account has access). Pull the raw templates:
  gh api repos/dynamous-community/workshops/contents/archon-as-second-brain-arm  → README.md, REPOSITORIES.md (index template), repositories/*.md (7 example pages), .claude/skills/archon/ (skill — for CONTENT MINING ONLY; see CAP rule).
Read repos via:  gh api repos/dynamous-community/workshops/contents/archon-as-second-brain-arm/<path> --jq .content | base64 -d

FREDIS SHAPE (already known — verify, don't re-discover from scratch):
- memory root: Fredis/Memory/  · identity: SOUL.md, USER.md, MEMORY.md
- SessionStart hook: .claude/hooks/session-start-context.py  · reflection: .claude/scripts/memory_reflect.py  · flush: .claude/scripts/memory_flush.py (called by pre-compact-flush.py + session-end-flush.py)

BUILD (each with a verify):
1. Fredis/Memory/REPOSITORIES.md — the index. One row per repo: local path · GitHub URL · default branch · visibility · Archon-target? (Y/N) · per-repo page link. Seed list (CONFIRM with me first): Fredis, saulera, saulera-client-starter, merkle-email-hub, VTV, Cab, mission-control, GERBONI. Flag Fredis + the vault "NEVER an Archon target — command center."   → verify: table renders; every local path resolves on disk.
2. Fredis/Memory/repositories/<slug>.md — one page per ACTIVELY-worked repo (start with merkle-email-hub + saulera-client-starter; others only past the 3+-daily-log-mention threshold). Frontmatter: title · type: entity · category: repository · github · visibility · default_branch · local_path · archon_enabled · tags · related · created · updated. Body: ## Identity · ## Archon Configuration · ## Workflow Preferences · ## Dispatch History (seed "(YYYY-MM-DD) Page created.") · ## Recent Activity · ## Related.   → verify: YAML parses on every page; [[wiki-links]] resolve.
3. SessionStart injection — in .claude/hooks/session-start-context.py, inject REPOSITORIES.md into the additional-context blob right AFTER the MEMORY.md injection. Mind the char cap (Fredis already loads SOUL+USER+MEMORY + 3 daily logs — bump it if needed).   → verify: pipe a synthetic startup event to the hook; output contains a "## Repositories" section.
4. Reflection routing — add the workshop's "Repository / codebase activity" routing rule to memory_reflect.py's prompt (route Archon dispatches / PRs / commits / repo-scoped lessons into the right page's ## Dispatch History / ## Recent Activity / ## Workflow Preferences; recognise repos by path prefix, "ran archon on …", or github.com/<org>/<repo>; 3+-mention threshold before auto-creating a page) AND add REPOSITORIES.md to the reflection prompt context.   → verify: a dry run (memory_reflect.py --test) routes a seeded dispatch line to the right page.
5. Flush tagging — add a "Repository / codebase activity" bullet to memory_flush.py's output format so dispatches get tagged by repo name (e.g. "merkle-email-hub: …") for reflection to route next morning.   → verify: a flush captures a tagged repo line.
6. Default Dispatch Rule — author it in REPOSITORIES.md (Archon is the default coding dispatch for any repo in the Active Pages table even when "Archon" is unsaid; signal phrases fix/implement/build/ship/review-PR; SKIP for typos/one-liners/planning/read-only). GATE IT: a repo enters the Active Pages table ONLY once its lane is proven (P4 = Email Hub, P4b = client-site) — until then Active Pages is empty / non-Archon only. Mirror a one-line summary into CLAUDE.md §Advisor Mode — NOT SOUL.md (hook-blocked; append a SOUL suggestion to today's daily log instead).   → verify: the rule is present; no repo is "active" until its lane is green.

CAP / CONTAINMENT (Fredis locked decisions — do NOT breach):
- NO 25th top-level skill. The kit's .claude/skills/archon/ is for CONTENT MINING ONLY — fold its dispatch knowledge into the existing `integrations` skill + the planned `query.py workflow` (P2). The repo is at 24 skills.
- Advisor mode holds: the Default Dispatch Rule still yields draft PRs only; nothing auto-sends/merges.
- Fredis + the vault are NEVER Archon targets (marked in the index).

7. Validate (workshop Step 8): YAML parses on every page; wiki-links resolve; SessionStart injects ## Repositories; for any archon_enabled:true page, listed custom workflows match actual <repo>/.archon/workflows/*.yaml (none yet → mark UNVERIFIED until P0/P4).

OUTPUT → write .agent/plans/the-team/repositories-system.md (what was installed, the confirmed repo list, the cap + gating adaptations, how to test it). Then STOP.
```

---

## P1 — Phase-1 plan + lean PRD (cwd = Fredis repo root)

> This is the planning prompt from `docs/agents/the-team-phase1-build-prompt.md`. Run it verbatim in a fresh window. It reads the architecture + PRD docs + the P0 spike report, then produces a lean PRD (`Fredis/Memory/drafts/active/the-team/phase1-PRD.md`) and an implementation plan (`.agent/plans/the-team/phase1-implementation.md`), then STOPS for your approval. See that file for the full block. **The first lane it plans for is Email Hub issue→PR (client-site follows as P4b) — that standalone doc has been updated to match. Phase 1 also stands up the repositories memory layer (P0b) — the dispatch index/pages the runs write to.**

---

## P2 — PRD-gate + `query.py workflow` (cwd = Fredis repo root)

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base)

You are wiring the PRD gate and the workflow CLI in the Fredis repo ONLY. Do not edit mission-control or the vault internals beyond defined draft paths. This `query.py workflow` CLI is THE single dispatch path — every surface (chat, Slack, the cockpit board) fires runs through it; nothing POSTs the engine directly.

READ FIRST:
- .agent/plans/the-team/phase1-implementation.md   (the approved plan — do exactly its PRD-gate + CLI steps, no more)
- docs/PRD/prd-as-project-start-condition.md         (two-stage model; extend archon-interactive-prd, don't re-propose)
- docs/PRD/prd-best-practices.md                     (the lean-PRD shape the gate must enforce)
- .claude/scripts/query.py                           (the CLI to extend) + .claude/scripts/CLAUDE.md

BUILD (smallest reversible steps, each with a verify):
1. A `query.py workflow` subcommand: list / run / approve / status.   → verify: `query.py workflow list` returns the engine's workflows.
2. The gate: an approved lean PRD (from drafts/active/the-team/) becomes the run INPUT (the $ARGUMENTS message) to an Archon run; nothing runs without an approved PRD.   → verify: attempting a run with no approved PRD is refused.
3. Guidance folded into the existing `integrations` skill — including the dispatch knowledge mined from the repositories kit's `.claude/skills/archon/` (workflow names, worktree isolation, base-branch rules). NO new top-level skill — the 24-skill cap means the `archon` skill is ABSORBED here, not installed standalone.   → verify: `integrations` covers "run workflow X on repo Y" without a 25th skill.

CONTAINMENT: draft-only; the gate never sends. OUTPUT → update phase1-implementation.md with what shipped + how to test it. Then STOP.
```

---

## P3 — Cockpit skeleton (cwd = ~/Desktop/mission-control — SEPARATE repo/session)

```
RUN FROM (cwd): ~/Desktop/mission-control   (its own repo — NOT a Fredis session)

You are extending the mission-control app into the single "Saulera Cockpit". This is mission-control's OWN repo — a Fredis session cannot do this; you are in a session with cwd here.

READ FIRST (in this repo):
- HANDOFF.md, app.js, board.data.js, scripts/discovery.workflow.js   (how the board renders today)
- (reference, read-only) ~/Desktop/claude-code-second-brain/.agent/plans/fredis-archon-mission-control.md  ("UI topology = option 1", the Archon API facts) and ~/Desktop/claude-code-second-brain/docs/agents/fredis-agent-architecture.md (the cockpit decision + naming rule)

NAMING (white-label — HARD RULE): every user-facing string, label, nav item, title, tab, and copy shows ONLY Fredis/Saulera vocabulary. NEVER surface "Archon", "Eve", the upstream mirror, or any third-party framework name on any primary surface. Rename wherever necessary:
  - build engine / workflow runs  → the "Studio" tab (individual runs called "runs"/"builds")
  - domain-agent layer            → "The Team"  (individual agents: "PA", "Sales", "Marketing")
  - the app itself                → "Saulera Cockpit"

BUILD (served over http://localhost; static file:// keeps working as a degraded fallback):
1. A chat pane to talk to Fredis (wire to the Fredis chat entrypoint). **This chat pane is the cockpit's ONLY dispatch surface — runs are fired here, through the Fredis `query.py workflow` path, and nowhere else.**   → verify: a message round-trips; a "run the … workflow" message fires a run via the Fredis path (not a direct engine POST).
2. PRESERVE the existing cross-repo TODO board (window.BOARD in board.data.js — per-repo phases from the /mission sync scan) as a **read-only view**. This is the backlog you work from (e.g. the live merkle-email-hub Phase 50/51/54 phases).   → verify: the board still renders all existing-project phases.
3. The "Studio" tab is a **read-only overlay** over run state: subscribe to the engine API (SSE `/api/stream/__dashboard__` or poll `/api/dashboard/runs`) and render OUR OWN run views (status, nodes, logs) so no engine branding leaks; the next /mission sync scan promotes the item.   → verify: a run fired from the chat pane shows live in the Studio tab with Saulera labels only.
4. **`@delegate` from the board is DEFERRED (single-dispatch rule).** Do NOT wire a board click to a direct engine POST. If a one-click launch is wanted later (only when run volume forces it), it must POST through the *same* Fredis dispatch path the chat pane uses — "a button over the same dispatch, not its own brain." Record this decision in COCKPIT.md.
5. Deep-debug: keep raw engine detail behind a generic "Engine debug (advanced)" link/iframe, NOT a primary surface (it's the engine's OWN web UI and carries its name). For zero engine branding, build the detail view from the API instead of embedding — note the trade-off in COCKPIT.md.   → verify: primary surfaces show no third-party names.

DO NOT build any of The Team UI yet (Phase 2). OUTPUT → write COCKPIT.md (at the mission-control repo root) describing what exists, the naming map applied, and how to run it locally. Then STOP.
```

---

## P4 — first lane: Email Hub issue→PR end-to-end (cwd = Fredis; target = `~/Desktop/merkle-email-hub`)

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base; build TARGET is ~/Desktop/merkle-email-hub)

You are proving the build harness end-to-end on the FIRST lane: a real issue→PR run on Email Hub — the cleanest "issue in, draft PR out" loop (dispatch → worktree → the repo's OWN test/CI gate → draft PR). Run orchestration from Fredis; the build TARGET is ~/Desktop/merkle-email-hub. Pick ONE small, low-blast-radius issue — an existing scoped issue if one fits, otherwise author a throwaway test issue; do NOT assume a backlog exists.

READ FIRST:
- .agent/plans/the-team/phase1-implementation.md, .agent/plans/the-team/p0-archon-spike-report.md
- Fredis/Memory/drafts/active/the-team/phase1-PRD.md   (the approved PRD — its hypothesis is what this run tests)
- .agent/plans/fredis-archon-mission-control.md ("Verified Archon workflow facts": archon-fix-github-issue; run input = $ARGUMENTS; NO repo param → point the workspace at the target repo)
- IN THE TARGET REPO: merkle-email-hub's README + package.json + any CI config — to DISCOVER its real test / typecheck / lint / build commands. Do NOT invent gate commands.

SETUP (once):
0. Mold archon-fix-github-issue for Email Hub: its hard gate is Email Hub's OWN validation suite (the commands you discovered above), wired as bash: validation node(s) that MUST pass before the PR node. (guard.sh + `git diff base/` are the CLIENT-SITE lane's gates — they belong to P4b, NOT here.)   → verify: the workflow list (workspace pointed at merkle-email-hub) shows the molded fix-issue workflow.

RUN THE PIPELINE (target = merkle-email-hub):
1. Enrich the chosen issue into the run input (Cole: "the issue is the contract") → I approve (HITL #1).
2. Fire the run FROM CHAT via the single dispatch path (`query.py workflow run …` with the issue as input).   → verify: a worktree run appears in the Studio tab (read-only overlay).
3. Run completes → Email Hub's test/CI gate PASSES (validated in a separate session) → DRAFT PR only; nothing merges, nothing sends.   → verify: a draft PR against merkle-email-hub; worktree was outside the git tree; HITL #2 (you review).

CONTAINMENT CHECK before the run: Archon points only at merkle-email-hub (never Fredis/vault); loopback-bound; worktrees outside the git tree; concurrency cap respected. Draft-PR-only is the safety net — the target is the real-business primary-income repo, so the worst case must be an ignorable draft PR, not a broken product.

OUTPUT (updates the repositories layer from P0b) → (a) append a dispatch-history entry to Fredis/Memory/repositories/email-hub.md (date · issue · workflow · PR link · outcome); (b) record the test/CI gate commands you discovered in that page's ## Workflow Preferences so later runs don't rediscover them; (c) now this lane is proven, move merkle-email-hub into the Active Pages table in REPOSITORIES.md so the Default Dispatch Rule applies to it. Then STOP and report whether issue→draft-PR via the harness was cleaner/faster than fixing the issue by hand.
```

---

## P4b — second lane: client site end-to-end (cwd = Fredis; target = `~/Desktop/saulera-client-starter`) — GATED on P4 green

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base; build TARGET is ~/Desktop/saulera-client-starter)

Only start once P4 (Email Hub) is green. You are pointing the SAME proven engine at the SECOND lane: building a REAL client website on saulera-client-starter — the templated re-skin with hard deterministic gates. Run orchestration from Fredis; the build TARGET is ~/Desktop/saulera-client-starter.

READ FIRST:
- .agent/plans/the-team/phase1-implementation.md, .agent/plans/the-team/p0-archon-spike-report.md, the P4 dispatch-history entry
- Fredis/Memory/drafts/active/the-team/phase1-PRD.md   (the approved PRD)
- saulera-client-starter/NEW-CLIENT.md (the build runbook), base/guard.sh, client/_TEMPLATE (the pack to clone)
- .agent/plans/fredis-archon-mission-control.md (the new-client-site.yaml sketch under "Path B")

SETUP (once):
0. Author saulera-client-starter/.archon/workflows/new-client-site.yaml from NEW-CLIENT.md (copy the Path-B sketch): scaffold → fill-pack → pack-gate (approval) → build-pages → guard (bash: guard.sh PASS) → base-clean (bash: git diff base/ EMPTY) → open-pr (gh pr create --draft).   → verify: the workflow list (pointed at saulera-client-starter) shows new-client-site.

RUN THE PIPELINE (target = saulera-client-starter):
1. Shape a small real client brief → lean PRD (per docs/PRD/prd-best-practices.md) → I approve (HITL #1 = the pack-gate).
2. Fire the run FROM CHAT via the single dispatch path (`query.py workflow run new-client-site` with the brief/PRD as input).   → verify: a worktree run appears in the Studio tab (read-only overlay).
3. Run completes → guard.sh PASS + git diff base/ EMPTY → DRAFT PR only; nothing merges, nothing sends.   → verify: a draft PR with a new client/<slug>/ pack; base/ untouched; HITL #2 (you review).

CONTAINMENT CHECK before the run: Archon points only at saulera-client-starter (never Fredis/vault); loopback-bound; worktrees outside the git tree; concurrency cap respected.

OUTPUT (updates the repositories layer from P0b) → (a) append a dispatch-history entry to Fredis/Memory/repositories/saulera-client-starter.md (date · client · workflow · PR link · outcome); (b) record its gate (guard.sh + git diff base/) in ## Workflow Preferences; (c) move saulera-client-starter into the Active Pages table in REPOSITORIES.md. Then STOP and report whether brief→site was cleaner/faster than the manual NEW-CLIENT.md run.
```

---

## P5 — Phase-1→2 gate review (cwd = Fredis repo root)

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base)

You are deciding whether to open Phase 2 (The Team on Eve). Be adversarial — default to "not yet" unless the evidence is clear.

READ FIRST:
- docs/agents/fredis-agent-architecture.md  ("The honest tension", "Open questions carried to the Phase-1→2 gate")
- The P4 (Email Hub) dispatch-history entry, the P4b (client-site) entry if it ran, + the phase1-PRD hypothesis (right/wrong conditions)

ANSWER, with evidence from the P4 / P4b runs (not opinion):
1. Did the harness+cockpit make issue→PR (and brief→site, if P4b ran) meaningfully cleaner/faster than by hand? (the PRD's RIGHT condition) — or did either of the WRONG conditions trip?
2. The Opus-everywhere vs cost question: does a domain-agent roster earn its keep WITHOUT small models? If not, is the answer "accept Opus cost", "revisit small models", or "skip separate agents"?
3. Eve vs Fredis-native SDK loops for The Team — second framework, or extend heartbeat/reflection (the cheaper Round-2 option)?

OUTPUT → write .agent/plans/the-team/phase1-gate-review.md with a clear GO / NO-GO for Phase 2, the substrate decision (Eve vs native), and — if NO-GO — what would change the answer. Then STOP. Do not open P6 without an explicit go-ahead.
```

---

## P6 — The Team: PA on Eve (cwd = new Eve repo) — GATED on P5 = go

```
RUN FROM (cwd): ~/Desktop/the-team   (the NEW Eve repo — create it here if absent: sibling of Fredis, OUTSIDE the Fredis git tree)

You are standing up the FIRST domain agent — the PA — on Eve, branded "The Team". Only proceed if phase1-gate-review.md says GO and the substrate decision is Eve (if it says native loops, ignore this prompt and build the PA as a Fredis SDK loop instead).

READ FIRST (Fredis docs by absolute path — you are NOT in the Fredis repo):
- ~/Desktop/claude-code-second-brain/.agent/plans/the-team/phase1-gate-review.md  (the go + substrate decision)
- ~/Desktop/claude-code-second-brain/docs/agents/fredis-agent-architecture.md  (the decisions table; governance = per-agent least-privilege)
- Eve docs (github.com/vercel/eve): tools/ skills/ channels/ schedules/ + HITL

BUILD the PA agent (inbox / calendar / admin triage):
1. Scaffold Eve; brand the layer "The Team"; PA gets ONLY the tools/paths it needs (read mail/calendar; draft; NO send, NO code, NO Fredis-repo or vault write except the defined draft path).   → verify: capability audit shows least-privilege.
2. Cadence: on-demand (from the cockpit/Slack) + a scheduled pass that writes drafts to the review queue (drafts/active/ + HubSpot Review ticket + [DRAFT] Slack).   → verify: a scheduled run produces a draft, sends nothing.
3. Surface it in the cockpit's "The Team" panel as a **read-only view** (invoke/coordinate via Fredis — the single dispatch path; shared vault artifacts; no direct Eve↔Archon coupling, no second dispatch brain).

CONTAINMENT: draft-only; sandboxed; decision (agent) separated from execution (you send). OUTPUT → write ~/Desktop/claude-code-second-brain/.agent/plans/the-team/pa-agent.md (what it does, its tool allow-list, how to run it). Then STOP.
```

---

## P7 — The Team: Sales agent (cwd = Eve repo) — GATED on P6 + sales-persona bundle decided

```
RUN FROM (cwd): ~/Desktop/the-team   (the Eve repo from P6)

Stand up the Sales agent on Eve. PREREQUISITE: the sales-advisor persona host bundle is decided (executive-leadership recommended vs product-management) — if not, stop and ask first.

READ FIRST: ~/Desktop/claude-code-second-brain/.agent/plans/the-team/pa-agent.md (the pattern to copy), ~/Desktop/claude-code-second-brain/docs/agents/fredis-agent-architecture.md (Sales gap section).

BUILD: scoping-call follow-ups + HubSpot pipeline nudges, DRAFT-ONLY (cold email is GDPR/PECR-regulated and never auto-sends). Least-privilege: HubSpot read + draft; no send; no code.   → verify: a follow-up draft + a suggested pipeline move land in the review queue, nothing sends.
OUTPUT → ~/Desktop/claude-code-second-brain/.agent/plans/the-team/sales-agent.md. Then STOP.
```

---

## P8 — The Team: Marketing agent (cwd = Eve repo) — GATED on P6

```
RUN FROM (cwd): ~/Desktop/the-team   (the Eve repo from P6)

Stand up the Marketing agent on Eve.

READ FIRST: ~/Desktop/claude-code-second-brain/.agent/plans/the-team/pa-agent.md, the content-social + content-artifacts skills.

BUILD: scheduled content drafting/repurposing (LinkedIn/X/IG) to the review queue, DRAFT-ONLY. Least-privilege: no send, no code. Lowest-risk Team agent (pure drafts) — good for shaking out the cron+HITL loop.   → verify: a scheduled pass drafts a post to drafts/active/, sends nothing.
OUTPUT → ~/Desktop/claude-code-second-brain/.agent/plans/the-team/marketing-agent.md. Then STOP.
```

---

## Notes

- **Where to run each (cwd):** P0 → `~/Desktop/cloned_repos/archon/Archon` · P0b / P1 / P2 / P4 / P4b / P5 → `~/Desktop/claude-code-second-brain` (Fredis — home base; P4 target = `merkle-email-hub`, P4b target = `saulera-client-starter`) · P3 → `~/Desktop/mission-control` · P6 / P7 / P8 → `~/Desktop/the-team` (new Eve repo). Each prompt states its RUN FROM at the top.
- **Order:** (P0 ∥ P0b) → P1 → (P2 ∥ P3) → **P4 (Email Hub, first lane) → P4b (client-site, second lane)** → P5 → [gate] → P6 → (P7 ∥ P8). P0b (repositories memory layer) is Fredis-side and independent of the engine, so it runs alongside the P0 spike. One lane proven before the next — **P4 and P4b are sequential, NOT parallel.** P2 and P3 are independent (different repos) and can run in parallel windows; P7/P8 likewise after P6.
- **Every prompt ends with STOP** — they plan/build one slice and report, honouring the wait-for-go-ahead rule.
- **Cross-repo reminder:** P3 (cockpit) and P6–P8 (Eve) are *other* repos — run them in sessions with the right cwd; a Fredis session cannot edit them.
