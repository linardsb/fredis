# TODO — Active execution roadmap

**Source of truth:** `.agent/plans/fredis-context-management-roadmap.md` — all phase detail, files touched, tests, verification steps live there. This file is the scannable status.

---

## Handoff — 2026-06-14 → for 2026-06-15 (infra / saulera / reflection state)

> Separate concern from the context-management roadmap below. This is the reconciled state of the infra audit, the saulera lead-detector rollout, the reflection/synthesis loop, and the uncommitted `memory_index` change — all verified **live** on 2026-06-14. Delete this block once the open items are cleared.

**Bottom line:** Fredis is fully deployed and healthy. Not blocked on Fredis — every open item is in Linards's hands.

### The one trigger you're waiting on
**Submit the saulera.com contact form** (the live lead test). The detector is built, deployed to the VPS, wired into the heartbeat, and flag-on — but has **never fired** (0 leads in 168h). It only triggers on a real email from `form@saulera.com` (subject "New enquiry"). After you submit, the next heartbeat tick (≤2h, during 05:00–20:00 UK) creates a HubSpot Review ticket + posts `[DRAFT] New saulera lead: <name>` to **#hubspot**.
- Verify: `cd .claude/scripts && uv run python query.py hubspot queue`
- NOTE: the old "create #saulera channel + invite bot" step is **stale/wrong** — leads route to #hubspot, no channel needed.

### Verified done (2026-06-14, live)
- Infra audit 4 gaps closed (commits `23f58a3`, `a34eb98`): lanes scan retired, VPS deploy chain restored, `pokable.ze` crontab + `ci-fallback` worktree removed.
- Saulera detector deployed + wired + flag-on (commit `0b82e4f`). Armed, never fired.
- Reflection loop healed: 06-13 + 06-14 08:00 runs succeeded; 21-day catch-up promoted to MEMORY.md; zero `dan_jailbreak` aborts since the fix.
- Weekly synthesis ran today (Sun 06-14), drafted **3 proposals** → `Fredis/Memory/drafts/active/memory-synthesis/2026-W24.md` — **review these**.
- GitHub PAT rate limit recovered (4902/5000).
- VPS deploy chain working: local `HEAD` = `origin/main` = VPS `HEAD` = `510013f`; deploy marker refreshed via 2-min vault-sync.

### Open — Linards's hands
- [ ] **Submit saulera form** (the trigger above).
- [ ] **Fix GitHub Actions billing** — `linardsb` account → Settings → Billing & plans. CI + Actions-deploy still dead (~3s, 0 steps = spending-limit). *Not urgent* — VPS self-deploy chain + local pre-push gate cover it.
- [ ] **Hand-check live `.env`** (Fredis is hook-blocked from it): stray `UBSPOT` typo + dead `ASANA_*` / `MONDAY_*` keys. Run the grep on your own machine, outside the hook.
- [ ] **Decide fate of the uncommitted `memory_index.py` change** — contextual-embedding prefix, coded + tested (9 pass, ruff/mypy clean), modified-but-unstaged. Committing only pays off after a full re-embed (`--rebuild` re-embeds the whole vault into the shared VPS Postgres over the tunnel) — a deliberate decision, not a quick commit.

### Open — Fredis/me can do on go-ahead
- [ ] Delete the stale `MONDAY_*` block from `master.env.example` (lines 69–72) — the only in-repo env residue, not hook-blocked.
- [ ] Commit + rebuild the `memory_index.py` change — if the decision above is "go".
- [ ] Surface the 3 synthesis proposals in `2026-W24.md`.

---

## Shipped

- [x] **Phase 0** — Per-channel tool / MCP / skill / model scoping (`7905b0b`, 2026-05-03)
- [x] **Phase A** — Token & turn-count surfacing + nudge (`44c8d82`, 2026-05-03)
- [x] **Phase 3** — Metric verification + patch + min-tier-gap guard (`a020ff5`, 2026-06-12) — verification refuted the input_tokens-only fix; shipped per-call AssistantMessage usage instead. 35-turn smoke + `[thread-nudge]` log check pending first live turns (observation window for Phase 4 starts now)
- [x] **Phase 3a** — Plugin-skills bloat measurement (2026-06-12) — closed, no action: VPS `enabledPlugins: null` (zero injection); worst case ~3.1k tokens < 5k threshold; `[scoping] skills=12` matches YAML (9 + 3 always-on)

---

## Pending — sequential

- [ ] **Phase 4** — `/consolidate` directive (~4h)
  - **Pre-gate:** Phase 3 shipped + ≥3 days observation + Linards green-light
  - 4.1 Directive parser (`save_directive.py`)
  - 4.2 Topic resolver (`engine.py`)
  - 4.3 Canon template + writer + schema migration (3 new columns) + skill files
  - 4.4 Slack response + nudge-timestamp consumption
  - 4.5 Stale-name flag (folds in former Phase C)
  - 4.6 Tests + docs

- [ ] **Phase 5** — Observation gate (≥3 days, no code)
  - Gates Phase 6. Skip Phase 6 entirely if "forgot to consolidate" rate is zero.

- [ ] **Phase 6** — `memory_reflect.py` background safety net (~½ day) — *conditional on Phase 5 outcome*
  - Extract canon writer to `canon_writer.py` if Phase 4 left it inline
  - Add `auto_consolidate_thresholded_threads()` pass

- [ ] **Phase 7** — OB1 naming sweep (~1h, deferrable)
  - Frontmatter rename + migrate existing canon files

---

## Background (parallel, not gating)

- [ ] **Phase 3-lite compliance observation** — 2 weeks
  - Sample one turn per channel per week. If >5% out-of-scope skill invocation attempts → escalate to Option Y (plugin-dir hard filter, ~2-3 days extra).

---

## OB1 backlog (idea pool — pull individually, not sequenced)

Tracked in `.agent/plans/fredis-ob1-integration.md` + `.agent/plans/ob1/*.md`. Skip indefinitely unless a specific trigger fires.

- [ ] OB1.1.6 — External-client wiring (Cursor / Claude Desktop / ChatGPT) — when you actually want Fredis context from a non-Claude-Code client
- [ ] OB1.2 — Typed frontmatter on new captures (~1 day)
- [ ] OB1.3 — Entity wiki (`memory_entities.py`, ~1-2 days)
- [ ] OB1.4 — Claudeception evaluator on drafts (~½ day)
- [ ] OB1.5 — Sensitivity tier upgrade (conditional on denylist leak)
- [ ] OB1.6 — Historical importers (conditional on archives)

---

 ## [2026-06-21] AI-native company: filter skills → "AI employee" agents — REVISIT / DECISION PENDING

  **Goal:** run the business with ~4–6 role-based AI agents ("employees": technical, product,
  growth, finance/tax, strategy, data) rather than one Fredis. Q: can we filter the 24 skills
  onto those roles, and is it feasible?

  **Key finding — already ~70% built.** `.claude/config/channel-routing.yaml` (scoping ON since
  2026-06-20) already maps each Slack channel → {skill allowlist + tool palette + MCP servers +
  model tier + vault folder}. That IS the per-agent skill filter. Today's "employees" are
  channel-scoped facets of ONE Fredis identity, not separate agents.

  **The filter (24 skills → 6 roles):**
  - CTO/Engineering: engineering, technical-leadership, security-engineering, ciso-advisor
    (+robotics-engineer if it ships) → #email-hub / #vtv / #cab-app
  - Head of Product: product-management, product-shape, idea-validation → #product / #ideation
  - Growth/Marketing: content-social, content-artifacts (+launch-governance GTM, draft-reply)
  - CFO/Finance·Legal·Tax: uk-latvia-context, ip-overhang-guard, business-cycle-analyst
    (+client-log, launch-governance runway) → #legal / #finances (already scoped)
  - CEO/Chief-of-Staff (orchestrator): executive-leadership, org-design, launch-governance
    → #all-ai-agent
  - Head of Data/Research: data-and-experimentation (+idea-validation, built-in /deep-research)
  - Shared infra (NOT employees): integrations, draft-reply, meeting-notes,
    obsidian-vault-structure, _shared/
  - Meta: skill-creator (= "recruiter/L&D"), phase1-ready (one-time bootstrap)

  **Built vs to-build:**
  - Built: per-channel scope profiles; channels mapped to functions; advisor-mode (nothing
    auto-sends); per-skill draft folders + HubSpot "Fredis Review" queue (gated OFF:
    HUBSPOT_TICKETS_ENABLED=false); cross-agent memory patterns documented; constrained-SDK-call
    pattern proven (Haiku guardrail).
  - To build for true "employees": multi-agent identity (today one Fredis); an orchestrator for
    routing/handoffs/escalation; per-agent session keys (sessions key by channel:thread); hard
    skill gating (skills are soft prompt-rule today, not SDK-gated); turn the queue on.

  **Two models:**
  - Model A — "one Fredis, many hats" (channel=role): formalise the 6 roles in
    channel-routing.yaml. Mostly config; already running. Cheap, safe.
  - Model B — "real employees" (N agents + orchestrator): distinct identities/memory/inbox +
    CEO router. More capable; costs identity multiplexing, per-agent sessions, hard gates,
    N× heartbeat tokens.
  - Recommendation: start Model A; graduate a role to Model B only when it must run
    autonomously/in-parallel (e.g. Growth drafting daily, Finance watching runway).
    Summon-on-demand sub-agents ≫ always-on for cost.

  **Caveats:** valuable version = "AI staff DRAFT, Linards APPROVES" (advisor-mode), not an
  autonomous company. Tax agent = advisor only (uk-latvia-context is reference-only, flags when a
  human advisor is needed — never wire it to file). Roster white space: no dedicated Sales/BD,
  Customer Success, or HR/People bundle (partially covered by HubSpot+client-log+draft-reply /
  org-design+skill-creator).

  **Next actions (pick one):**
  1. Spec Model A as a concrete channel-routing.yaml proposal (6 role-channels w/ exact skill
     allowlists + tool palettes + model tiers).
  2. Design the Model B orchestrator (CEO/chief-of-staff agent that routes HubSpot tickets to
     employees + handles handoffs).
  3. Pressure-test / adjust the roster cut first.

  **Related:** prior turn — skill-improvement borrows from 5 external repos (DARE,
  ai-data-science-team, awesome-engineering-management, Awesome-finance-skills, DeepPaperNote);
  the research-rigour borrows would strengthen the Data/Research employee. See
  `.claude/config/channel-routing.yaml`; `engineering/references/agentic-orchestration-patterns.md`
  (L3 orchestrator-worker); CLAUDE.md §Advisor Mode + §Skill Stack.

  ---



## Workflow per phase

1. Re-read the relevant phase block in `.agent/plans/fredis-context-management-roadmap.md` to refresh context.
2. *(Optional)* Run `/be-planning <phase>` if more than a couple of days have passed since the roadmap was last revised — it re-pressure-tests assumptions against current code state. Not strictly required, since each phase already has step-by-step checklists in the roadmap.
3. Execute file-by-file in dependency order (schema → config → modules → engine → tests → docs).
4. Follow `## Operational playbook — every phase ship` in the roadmap (pre-flight tests → commit → push → auto-deploy → post-deploy verification).
5. Tick the box in this file once shipped. Append commit hash on the same line.

**Trigger phrase to start work:** `go Phase <N>` — I'll read the phase, run any read-only verification first, then propose the patch for confirmation before editing.
