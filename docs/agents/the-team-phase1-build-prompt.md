# Phase-1 build prompt — Fredis harness + cockpit + PRD gate

**What this is.** The exact, copy-pasteable prompt to drive **Phase 1** of the "Fredis + The Team" architecture (`docs/agents/fredis-agent-architecture.md`, Addendum 2026-06-30). It produces an **implementation plan + a lean PRD** — it is **not** an execution trigger. It deliberately scopes to the strongly-justified slice (CTO/build agent on Archon + cockpit skeleton + PRD gate) and defers The Team (PA/Marketing/Sales on Eve) to a gated Phase 2.

**Why scoped this way.** Per the addendum's honest tension: with **Opus everywhere**, the cost case for a full domain-agent roster is weak, and much of the wanted value extends what Fredis already has. So Phase 1 proves the harness+cockpit reduce friction *before* the rest is built — applying Linards's own lean-PRD / thinnest-MVP method to this build itself.

**How to use it.** Paste the fenced block below into a Fredis / Claude Code session with `cwd` at the repo root. It will research, then produce the two artifacts, then stop for your review. No build code is written until you give an explicit go-ahead.

---

```
RUN FROM (cwd): ~/Desktop/claude-code-second-brain   (Fredis — home base)

You are Fredis, planning Phase 1 of the "Fredis + The Team" agent architecture.
Do NOT write build code or run any workflow. Produce a plan + a lean PRD, then stop for my approval.

CONTEXT — read these first, in order:
1. docs/agents/fredis-agent-architecture.md          (the architecture + the 2026-06-30 addendum with all locked decisions)
2. docs/PRD/prd-as-project-start-condition.md         (the two-stage PRD model — lean PRD gate → spec)
3. docs/PRD/prd-best-practices.md                     (how to write the lean PRD: intent, falsifiable hypothesis, PRD↔spec boundary)
4. .agent/plans/fredis-archon-mission-control.md      (the Archon engine spec: API, containment, mission-control cockpit, Phase 0/1)
5. .agent/plans/the-team/p0-archon-spike-report.md    (verified port/auth/repo from the P0 spike)
6. CLAUDE.md + Fredis/Memory/SOUL.md                  (advisor mode, never-send, containment guardrails)

PHASE-1 SCOPE (build nothing outside this):
A. CTO / build agent on Archon — prove the harness end-to-end ONE LANE AT A TIME (Archon is the only unbuilt
   piece; wire one seam first or you won't know which broke):
   - FIRST LANE = Email Hub (~/Desktop/merkle-email-hub): a real issue → enriched run input → worktree run →
     Email Hub's OWN test/typecheck/lint/CI gate (discover it from the repo — guard.sh is the client-site lane's
     gate, NOT Email Hub's) → draft PR. One small, low-blast-radius issue. Nothing auto-merges/sends.
   - SECOND LANE (only after the first is green) = the client-site factory (~/Desktop/saulera-client-starter;
     base/ + NEW-CLIENT.md + client/_TEMPLATE ready): brief → lean PRD → worktree → guard.sh PASS +
     git diff base/ empty → draft PR.
   These two lanes are SEQUENTIAL, not parallel (supersedes the archon plan's Addendum-2 "both domains in parallel").
B. Cockpit skeleton — extend the existing mission-control app into the one desktop UI ("Saulera Cockpit"):
   a chat pane to talk to Fredis + a "Studio" tab to launch/watch runs (raw engine detail behind a generic
   "Engine debug" link only). Served at http://localhost.
C. PRD gate — the lean hypothesis PRD is shaped conversationally in the cockpit (Fredis + idea-validation /
   launch-governance skills), I approve it (HITL #1), and ONLY THEN can a build run start.
D. Repositories memory layer — stand up Fredis/Memory/REPOSITORIES.md (always-loaded index) + repositories/<slug>.md
   per-repo pages + reflection/flush wiring (archon-plan §E / Decision 3; Cole's "Archon as an arm of the second brain"
   workshop kit). This is the lookup layer that lets chat resolve "issue N on Email Hub" → repo + workflow, and the
   sink the runs write dispatch history to. Works with/without Archon; the kit's archon skill folds into `integrations`
   (no 25th skill — 24-skill cap).

HARD CONSTRAINTS (non-negotiable):
- Advisor mode: draft-only. No auto-send on any channel; outward comms route to drafts/active/ + HubSpot review + [DRAFT] Slack.
- Containment: Archon runs only on the TARGET repo — NEVER the Fredis repo or the vault. Pin Archon to 127.0.0.1.
  Keep Archon's SQLite + worktrees OUTSIDE the git tree. Local-first (no cloud/VPS dependency in Phase 1).
- Model: Opus everywhere. Cost control = concurrency cap default 3–5, overridable from the cockpit.
- Single dispatch path: chat (Fredis / Slack → query.py workflow) is the ONLY thing that fires a run. The cockpit
  board, the "Studio" tab, and the engine web UI are read-only views over the same run state — never independent
  dispatch surfaces. A launch button, if ever added, routes through the same Fredis path, not a direct engine POST.
- Governance: per-agent least-privilege; decision (agent) is separated from execution (I approve sends/merges).
- Two HITL gates only: post-brief (the PRD approval) and post-implementation (the draft-PR review).
- UI naming (white-label): every user-facing string in the cockpit shows ONLY Fredis/Saulera vocabulary — never "Archon", "Eve", the upstream mirror, or any third-party framework name. Rename to: build engine → the "Studio" tab; domain agents → "The Team"; the app → "Saulera Cockpit". Rename wherever necessary; the one caveat (the raw engine-debug view carries the engine's own name) is handled in the cockpit prompt P3.
- DEFER to Phase 2 (do not design or build now): The Team (PA/Marketing/Sales on Eve), the "The Team" rename,
  the Slack-for-phone channel. Phase 2 is gated on Phase 1 proving value AND resolving the Opus/cost question.

DELIVERABLES (produce both, then stop):
1. A lean PRD for Phase 1 itself, written per docs/PRD/prd-best-practices.md — including a falsifiable hypothesis
   with an explicit RIGHT condition and WRONG condition (e.g. "right if Email Hub issue→draft-PR is meaningfully
   faster/cleaner than fixing the issue by hand within N runs; wrong if the cockpit/harness adds friction or the
   draft PRs need full rework").
   Save to: Fredis/Memory/drafts/active/the-team/phase1-PRD.md
2. An implementation plan broken into the smallest reversible steps, each with a concrete verify check, covering:
   - Archon Phase-0 spike reconcile (Bun build, :3090 vs :3000 port, localhost-fetch, CLAUDE_USE_GLOBAL_AUTH).
   - The cockpit changes needed in the mission-control repo (note: a Fredis session CANNOT edit mission-control —
     flag which steps must run in a separate session with cwd in ~/Desktop/mission-control).
   - The PRD-gate wiring (how the approved PRD becomes the Archon run input; extends archon-interactive-prd).
   - The repositories memory layer bootstrap (REPOSITORIES.md + per-repo pages + session-start-context.py inject +
     memory_reflect.py routing + memory_flush.py tagging), adapted to Fredis — the archon skill folds into
     integrations (24-skill cap). This is the dispatch index/pages the runs write to (see playbook P0b).
   - Containment checks that must be live before the first real run.
   Save to: .agent/plans/the-team/phase1-implementation.md

OUTPUT RULES:
- For anything you cannot verify from the repo (port, repo identity, auth behaviour), say "UNVERIFIED — confirm on spike",
  do not assert it.
- End with: (a) the single first reversible step, (b) what it proves, (c) the explicit go-ahead you need from me before any build.
```

---

## Notes for Linards

- **This prompt only plans.** The build itself waits for your explicit go-ahead (your standing rule).
- **Two repos, two sessions.** Cockpit edits happen in `~/Desktop/mission-control` (its own `.claude/`), not in a Fredis session — the prompt makes the planner flag this.
- **Phase 2 is intentionally absent.** The Team isn't in this prompt by design — it's gated. When Phase 1 is proven, a separate Phase-2 prompt stands up PA-on-Eve first.
- **Before running it,** decide the Sales-persona host bundle (`executive-leadership` vs `product-management`) — only matters once Phase 2 opens, so it's not blocking.
