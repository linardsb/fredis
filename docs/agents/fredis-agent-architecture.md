# Fredis agent architecture — do we need a roster of role-agents?

**Status: DECISION NOTE / PLANNING.** No code in this document. It answers an architecture question and sets a direction; the build waits for an explicit go-ahead.

**Date:** 2026-06-30
**Origin:** a handwritten note (`img_0144.jpeg`) sketching `Fredis (brain) → Founder (me) → CTO · Sales · CEO · Marketing · PA = "OS"`, with the open question *"harness for each?"* — set against the Cole Medin / Archon "second brain as command centre" model (`10x_coding_workflow.txt`).
**Companions:**
- Engine / build side — `.agent/plans/fredis-archon-mission-control.md` (Archon as the execution harness; mission-control + studio surfaces; Saulera business-ops mapping in its Addendum 2).
- PRD gate — `docs/PRD/prd-as-project-start-condition.md` (the project-start condition; bullet 2 of the note).

---

## The question

The note draws an org chart: Fredis is the brain, the Founder sits below it, and five role-boxes hang off the Founder — **CTO, Sales, CEO, Marketing, PA** — bracketed together as an **"OS"**, with the scrawled worry *"harness for each?"*.

So: does Fredis need five (or more) distinct AI agents, each with its own harness, to run the business?

## The answer — no. Four of the five already exist; the gap is wiring, not capability

The role-boxes are not missing agents. **They already exist in the 24-skill stack**, each as both an execution point *and* an advisor persona (per the advisor-framing directive in `CLAUDE.md` §Skill Stack). The note is really about **orchestration and sequencing**, not new capabilities.

| Note box | Already covered by | Gap? |
|---|---|---|
| **CTO** | `technical-leadership` (cto-advisor + startup-cto) · `engineering` · `security-engineering` | — |
| **CEO** | `executive-leadership` (ceo-advisor + founder-coach + solo-founder + scenario-war-room) | — |
| **Marketing** | `content-social` (LinkedIn/X/IG) · `content-artifacts` (decks/carousels) · `product-management` (positioning/GTM) · `product-shape` (positioning-sharpener) | — |
| **PA** | `draft-reply` · `meeting-notes` · `client-log` · `integrations` (Gmail/Calendar/Slack/Drive) · `uk-latvia-context` | — |
| **Sales** | closest is `integrations` (HubSpot CRM) + `product-management` (GTM) — **no sales-advisor persona** | **real gap** (see below) |

**The "OS" in the note is the skill stack.** The Founder sits between Fredis-the-brain and the roles; Fredis is the dispatcher, and the roles are skills/personas it invokes. There is no separate "operating system" to build — it already runs.

## "Harness for each?" — no, one harness

This is the crux of the handwritten question. Split the work into two kinds:

- **Advisory / role work** — a CEO strategy call, a CTO architecture decision, marketing copy, a PA drafting a reply. This is a **skill/persona invocation in chat. It needs no harness at all.** Archon is irrelevant to it.
- **Build / delivery work** — client-site builds, Email Hub issue→PR, anything that produces a code artifact. This is the **only** work that needs the harness (Archon), pointed at the *target* repo, with the relevant role-skill injected per-node (Cole's progressive-disclosure pattern — load a skill only at the node that needs it).

```
                 FREDIS  (brain / second-brain / command centre)
                   │  dispatches
                   ▼
                FOUNDER (Linards)
                   │  invokes role as needed
      ┌────────────┼───────────────┬──────────────┬───────────┐
      ▼            ▼               ▼              ▼           ▼
    CTO          CEO           MARKETING        SALES         PA
 technical-   executive-    content-social/   (gap →       draft-reply/
 leadership   leadership    content-artifacts  fold in)    meeting-notes/
 +engineering +scenario-    +product-mgmt                   integrations
 +security    war-room                                       +uk-latvia
      └──────────────────────── the "OS" = the 24-skill stack ─────────────┘
                   │
                   │  only BUILD work crosses this line
                   ▼
                ARCHON  (one harness, per .agent/plans/fredis-archon-mission-control.md)
                points only at TARGET repos · worktree isolation · draft PR out
                NEVER Fredis or the vault
```

**Consequence:** you do not build five harnessed agents. **One engine (Archon, already planned)**, roles stay as skills, and most "agent" work never touches the harness. That collapses the note's per-role-harness worry — and it matches the containment rules already locked in the mission-control plan (Archon runs `bypassPermissions`, so it must never touch Fredis/the vault; point it only at other repos).

## What is genuinely new, then?

Not a roster of agents. The only genuinely new pieces are the three the note circles, and they are **all sequencing / wiring**:

1. **One harness** for build work — Archon. *Already specified* in `.agent/plans/fredis-archon-mission-control.md`. No new design needed here.
2. **A project-start condition** — every new project opens with a PRD before any build. *See* `docs/PRD/prd-as-project-start-condition.md`. This is the one piece the existing plan only half-covers (it names `archon-interactive-prd`); the PRD doc extends it.
3. **A control surface** — manage runs from chat (Slack via `query.py workflow`), the mission-control board, and Archon's web UI; **local-first, phone deferred** (VPS + Claude-auth fragility). *Already specified* in the plan. **Update (2026-06-30): single dispatch path — chat (`query.py workflow`) is the ONLY thing that *fires* a run; the board and the engine web UI are read-only views over the same run state, not independent dispatch surfaces (resolves the "surfaces" open question for Cole in the mission-control plan §G Q2). A launch button, if ever added, routes through the same chat/Fredis path — never a direct-to-engine POST.**

## The Sales gap — fold into a bundle, do not add a 25th skill

Sales is the one box with no advisor persona. The deal motion for Saulera is **founder-led consultative B2B**: 30-min scoping call → qualify → free build (1–2 concurrent) → paid sprint, on a pricing ladder. The pieces around it exist (HubSpot pipeline mechanics in `integrations`; pricing in `product-shape`'s pricing-shaper; GTM in `product-management`) — but nothing carries the *selling* voice: discovery, qualification, objection handling, follow-up cadence, close.

**Decision (per Linards, 2026-06-30): fold a `sales-advisor` persona into an existing bundle — no new top-level skill** (respects the 24-skill consolidation cap in `CLAUDE.md`).

- **Recommended home: `executive-leadership`.** For a solo operator, the deal motion *is* a founder/CEO function; it sits naturally beside solo-founder and ceo-advisor.
- **Alternative: `product-management`** if a GTM-flavoured home is preferred.
- **Mechanics stay where they are:** HubSpot pipeline in `integrations`, pricing in `product-shape`. The persona is the *judgement layer*, not the plumbing.

> Open sub-decision for Linards: confirm `executive-leadership` (recommended) vs `product-management` as the host bundle before the persona is written.

## How this lands in Saulera business operations

Saulera is run **solo** — the stack is one operator delivering at agency grade, and the binding constraint is **Linards's review attention, not compute** (per `MEMORY.md`). That shapes the architecture:

- **Advisory roles are chat-first and free.** Invoking the CEO/CTO/marketing voice costs nothing but a message — no harness, no orchestration, no review queue. Keep these light and on-demand.
- **Build roles are fire-and-forget through the one harness.** Client-site builds and Email Hub work go to Archon, run unattended in isolated worktrees, and come back as draft PRs. This is where the leverage is (Cole's "dispatch → walk the dog → come back to validated PRs").
- **HITL stays at two gates only** (post-brief, post-implementation) so the review bottleneck does not become the limiter. Do not run many HITL-heavy flows at once.
- **Every build starts with a PRD gate** (next doc) so Fredis's scarce review attention is spent on *intent* up front, not on rejecting half-built wrong things later.

So the "agent addition" worth making is **not** five role-agents — it is **Archon as the single execution engine for the build lanes, fronted by the existing skills-as-roles and gated by a PRD.** Everything else the note sketches already exists.

## Next concrete step (on go-ahead)

1. Confirm the Sales-persona host bundle (`executive-leadership` recommended).
2. Write the `sales-advisor` persona reference into that bundle (one reference file, advisor-mode like the rest).
3. Proceed with the PRD gate (`docs/PRD/prd-as-project-start-condition.md`) and the Archon spike (`.agent/plans/fredis-archon-mission-control.md` Phase 0).

No build until an explicit go-ahead.

---

## Addendum (2026-06-30) — research-driven evolution: the hybrid "Fredis + The Team" model

**Origin:** Linards asked how to add the specialised agents as *real* agents and manage them through a harness + agent-loop layer. Five research inputs were read:
- `docs/agents/agent_loopstxt.txt` — Cole Medin, "loop engineering": orchestrator/worker loops, `/loop` `/goal` `/routines`, the honest downsides (cost, reliability, context bloat), Archon as the deterministic answer.
- `github.com/coleam00/agent-control-plane` — Cole's loop dashboard: orchestrated vs Ralph modes, durable Neon-Postgres state, resume-gate HITL, per-run cost/token tracking, Pi provider-agnostic.
- `docs/agents/ Domain-Specific Agentstxt.txt` — Justin Shrader (Standard Agents): **composition over inheritance** — small domain-specific agents (own prompt, tools, loop, sandbox) coordinated in English, vs inflating one agent with 100 skills.
- `codewave.com/insights/domain-specific-agentic-ai-enterprises/` — enterprise micro-agent composition + governance + control plane + decision/execution separation + gradual autonomy.
- `github.com/vercel/eve` — filesystem-first agent framework (`tools/ skills/ channels[Slack]/ schedules[cron]/` + HITL); the substrate for building domain agents.

Four rounds of interactive Q&A (CLI) locked the decisions below. This addendum records them **and is deliberately honest about one tension the research surfaced.**

### What changed vs the conclusion in the body above

The body of this doc concluded *"no roster of agents — roles are skills, one harness, the bottleneck is review attention not compute."* **That reasoning is preserved and still holds** — it is exactly why the CEO role and the advisory voices stay chat skills. What the research adds is a *second pattern* (Shrader's domain-specific agents; Codewave's enterprise composition) that argues for *some* roles becoming real, isolated agents. The decision is to adopt that **partially and in phases**, not wholesale — so this addendum **extends, and does not delete,** the "no roster" reasoning.

### The honest tension (stated, not routed around)

The dominant practical justification for domain-specific agents is **cost** — small models 137× cheaper, 80%+ token efficiency (Shrader). Linards chose **Opus everywhere** (Q&A Round 2), which **removes the small-model argument**. Portability and horizontal scaling don't apply to a solo, draft-only operator. What survives as genuine new value: (a) tighter per-call context, (b) strict per-agent capability limits. **But both are partly already solved in Fredis** — progressive-disclosure skills (Fredis is *not* the "100 skills all loaded" anti-pattern Shrader describes) + `PreToolUse` guards + channel scoping. So, given Opus-everywhere, the net-new *internal-efficiency* value of the full four-agent expansion is **modest**. The value Linards is actually after — background drafts, one cockpit, a build harness — is largely real, but much of it is an **extension of what Fredis already has** (heartbeat/reflection loops + skills + the planned mission-control cockpit + the already-planned Archon harness), not necessarily a second framework and four new agents.

**Consequence for this plan:** phase it, prove value before building the weakly-justified parts, and apply the **lean-PRD / thinnest-MVP-that-proves-the-hypothesis** method Linards just adopted (`docs/PRD/prd-as-project-start-condition.md`) to this build itself. A big-bang 4-agent + 2-framework build would violate that exact principle.

### Decisions locked (Q&A, 2026-06-30)

| # | Decision | Choice |
|---|---|---|
| 1 | Architecture model | **Hybrid** — Fredis (coordinator/brain) + a few *real* domain agents; rest stay skills |
| 2 | Build harness | **Archon** for code/SDLC work (already specced in the mission-control plan) |
| 3 | Domain-agent substrate | **Eve (Vercel)**, branded **"The Team"** (PA / Marketing / Sales) |
| 4 | Roles that become real agents | CTO (Archon) · PA · Marketing · Sales (The Team). **CEO stays a chat skill** |
| 5 | Cockpit / UI | **Extend mission-control** into one desktop cockpit; **embed Archon's deep-debug**; concise Slack channel for phone |
| 6 | Send boundary | **Draft-only, Linards sends** — never-send boundary unchanged (incl. cold sales email; GDPR/PECR risk stays on a human) |
| 7 | Model / cost | **Opus everywhere** (see tension above) |
| 8 | PRD ownership | **Cockpit chat** — Fredis + The Team shape the lean PRD → HITL #1 approval → Archon builds (spec via `archon-interactive-prd`) |
| 9 | Concurrency | **Default 3–5, overridable** from the cockpit |
| 10 | State / hosting | **Local-first**; Archon SQLite + worktrees kept **outside the git tree** (containment) |
| 11 | Governance | **Per-agent least-privilege** + never-touch-Fredis/vault + decision (agent) / execution (human) separation |
| 12 | Cadence | **On-demand + scheduled drafts** to the review queue |
| 13 | First agent | **CTO / build agent on Archon** (Email Hub or throwaway) |

### Architecture — one brain, two engines, one cockpit, the PRD as the contract

```
  ┌──────────────────── ONE COCKPIT (extend mission-control) ─────────────────────┐
  │  chat with Fredis · "The Team" panel · Archon workflow panel + embedded debug  │
  │  + concise Slack channel for phone                                             │
  └────────────────────────────────────────────────────────────────────────────────┘
        ▲                                                              ▲
  THE TEAM (Eve, renamed)                                     ARCHON (build harness)
  PA · Marketing · Sales · research      ── lean PRD ──►       CTO / client-site / product
  research · shape brief · draft           (HITL #1:           worktree → draft PR
        │                                  you approve)         │
        └────────────── coordinated by FREDIS (brain) · all state in the vault ────┘
```

- **The two engines never couple directly.** They coordinate through **Fredis** and through the **PRD as the handoff contract** ("intent in → PR out"). Both are surfaced on one cockpit page; direct peer-to-peer API coupling is avoided (fragility).
- **The PRD is built in the cockpit** by Fredis + The Team (lean hypothesis PRD), approved by Linards, then handed to Archon for the build/spec. It lives in the vault (`drafts/active/` → finalised).

### UI naming — white-label rule (Linards's directive, 2026-06-30)

Every user-facing string in the cockpit shows **only Fredis / Saulera vocabulary**. The underlying frameworks are **never named in the UI** — not "Archon" (the build engine), not "Eve" (the agent framework), not the upstream mirror, nor any third-party name. Vocabulary map:

| Under the hood | UI label (Fredis/Saulera only) |
|---|---|
| build engine / workflow runs | the **Studio** tab (individual runs called "runs"/"builds") |
| domain-agent layer | **The Team** (agents: PA · Sales · Marketing) |
| the cockpit app | **Saulera Cockpit** |

**One honest caveat:** the embedded raw engine-debug view is the engine's *own* web UI and carries its name. To honour the rule, the cockpit's **primary** run views are built from the engine API (fully rebranded); the raw engine UI, if kept at all, sits behind a generic **"Engine debug (advanced)"** link — never a first-class surface. Enforced in the cockpit build (playbook **P3**).

### Note on Simplicity First (named, not routed around)

"The Team" agents are **Eve agents, not Claude Code skills** — so the literal 24-skill consolidation cap is **not breached**. But standing up a second framework + four agents **is a deliberate departure** from the repo's "consolidate, don't proliferate / Simplicity First" principle. Recorded as such; made on Linards's explicit direction; mitigated by the phasing below.

### Phased build plan

**Phase 1 — firm, strongly justified (the body of this doc already wanted it):**
1. **CTO / build agent on Archon** — **first lane = Email Hub** (issue→PR, its own test/CI gate), **then** the client-site factory (saulera-client-starter, guard.sh gate) as the second lane — one lane proven before the next (2026-06-30 update; supersedes the mission-control plan's Addendum-2 "both domains in parallel"): brief/issue → worktree → **draft PR**. → *verify:* one real task runs end-to-end on Email Hub first.
2. **Cockpit skeleton** — extend mission-control: chat pane + Archon workflow panel with embedded deep-debug. → *verify:* a run is launchable and watchable from the cockpit.
3. **PRD gate** — lean hypothesis PRD shaped in cockpit chat → HITL #1 → Archon (`docs/PRD/prd-as-project-start-condition.md`). → *verify:* no build starts without an approved PRD.
4. **Containment live** — local-first, state outside the git tree; Archon points only at the target repo; draft PRs only.
5. **Repositories memory layer** — `Fredis/Memory/REPOSITORIES.md` + `repositories/<slug>.md` + reflection/flush wiring (Decision 3 / mission-control plan §E; Cole's "Archon as an arm of the second brain" workshop kit). The lookup layer for single-dispatch ("issue N on Email Hub" → repo + workflow) and the dispatch-history sink. Works with/without Archon → stood up early (playbook **P0b**). *2026-06-30 update.*

**Phase 2+ — gated (build only if Phase 1 earns it):**
- **Gate to open Phase 2:** Phase 1 demonstrably reduced friction (brief→PR is faster/cleaner than today) **AND** the Opus-everywhere vs cost question is resolved (the small-model case for The Team is re-decided, or accepted as Opus-cost).
- Then: **The Team** on Eve — **PA first** (Shrader's prime domain example), then **Sales**, then **Marketing**; draft-only; on-demand + scheduled. The "The Team" rename + Slack-for-phone channel.
- **Cheaper alternative to re-weigh at the gate:** The Team as **Fredis-native SDK loops** (the Round-2 option) instead of a second framework — extends heartbeat/reflection rather than adopting Eve.

### Open questions carried to the Phase-1→2 gate

1. **Opus-everywhere vs the cost case for domain agents** — does The Team earn its keep without small models?
2. **Eve vs Fredis-native loops** for The Team — second framework, or extend what exists?
3. **Sales persona host bundle** — `executive-leadership` (recommended) vs `product-management` — still open from the body above; needed before the Sales agent.

### Companion: the Phase-1 build prompt

The exact, copy-pasteable planning prompt for Phase 1 lives at **`docs/agents/the-team-phase1-build-prompt.md`**. It produces a plan + lean PRD, **not** an execution trigger, and is gated on an explicit go-ahead.

No build until an explicit go-ahead.
