---
title: Product Portfolio & Skill-Stack Plan
date: 2026-04-19
status: planning — Wave 1 authored 2026-04-19; Wave 2 product-shape + role-skills deferred; Wave 3 ship/govern + deep-engineering roles deferred; open questions §10 may still gate Archon wiring
context: post-Phase-9 product-building thesis + Archon integration + Fredis skill stack
---

# Product Portfolio & Skill-Stack Plan

Strategic plan captured from the 2026-04-19 conversation. Documents the reasoning,
decisions made, decisions deferred, and the sequenced build plan. **No skills have
been authored yet.** Execution is gated on the open questions at the end of this doc.

---

## 1. Context

- **Fredis state:** Phases 0–4 complete; Phases 5–8 largely built (skills, heartbeat, chat, guardrails all live). Phase 9 = deployment (`launchd` plists + VPS) is ~1 day of remaining work; the two new plists (`com.linards.fredis-heartbeat.plist`, `com.linards.fredis-reflect.plist`) are already uncommitted in the repo.
- **Linards's state:** pre-revenue, solo, Senior Email Dev at Dentsu/Merkle day-job, building AI-agentic consultancy in parallel. Active product lanes: Email Hub, VTV, UGOKI, GERBONI. Prospective: agri×AI, robotics.
- **Goal being planned here:** build a portfolio of products fast, using Fredis + Archon as the tooling spine. Not the "close one consulting lead" path — the "ship product bets" path.

---

## 2. The Original Question

Linards's initial wishlist proposed ~20 role-based skills: CEO, COO, CFO, market analyst, business analyst, business-cycle analyst, business strategist, technical architect, backend engineer, AI security engineer, systems-thinking architect, robotics engineer, data scientist, QA tester, security architect, product developer, plus marketing/branding/design/SEO for Fredis-the-product. Asked whether this is overengineering, and pointed to external catalogs:
- [awesome-skills.com](https://awesome-skills.com/)
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — 232+ skills
- [coleam00/Archon](https://github.com/coleam00/Archon) (the live repo; the original URL shared 404'd)
- Local clone of Cole Medin's workshops repo at `/Users/Berzins/Desktop/workshops`

---

## 3. The Core Strategic Call (why role-based skills fail)

**Skills aren't roles.** CEO, COO, Business Strategist, Business Analyst — implemented as skills they all collapse to the same prompt: "think strategically about trade-offs." Zero lift over Fredis's default reasoning.

A skill earns its slot only when it encodes one of:
- a **specific framework** the LLM won't spontaneously use (Van Westendorp pricing, Dalio's cycle lens, Mom Test)
- a **checklist** (pre-mortem, red-team, kill-criteria)
- a **workflow tied to the user's tools** (Monday.com stage → required artifact)

Cole Medin's `skill-creator` workshop endorses the same rule:
> "Concise is Key — Only add context Claude doesn't already have."
> "Progressive Disclosure — Metadata always in context, body when triggered, resources as needed."

Job titles are labels, not context. The frame is broken.

### External-catalog confirmation

Scanned the three references and the local workshops clone:
- **Workshops clone** (`claude-code-second-brain-skills/`): 7 skills, all content/brand (`brand-voice-generator`, `excalidraw-diagram`, `linkedin-post`, `pptx-generator`, `skill-creator`, `sop-creator`, `x-post`). Fredis already has equivalents. Nothing to pull.
- **`claude-skill-archon/`**: pedagogy about *how* skills work, not a source of new ones.
- **Other workshops** (archon-v2-alpha, claude-agent-sdk, hook-hackathon, mastery, deterministic-agentic-coding, hierarchical-rag, knowledge-graph, etc.): technical education. No business-strategy skills.
- **awesome-skills.com + alirezarezvani**: closest matches are *Solo Founder*, *Financial Analyst*, *SaaS Metrics Coach*, *Growth Marketer* in alirezarezvani's set — worth skimming for framework content, but still role-labelled.

**Net finding:** the commercial/strategic skill layer Linards wants does not exist upstream in any catalog. It will be a de novo build.

---

## 4. Refined Goal (reframe from "close leads" to "build products")

Linards's stated thesis: product builder, not consultant-closer. Wants fast ideation + MVP iteration for a portfolio of products, backed by Fredis + Archon.

### Push-back recorded (still holds)

"Portfolio of products" is the classic founder trap when applied pre-revenue-on-any-product. Five half-finished things, zero revenue, confident belief that the next idea will be the one. The people who actually run product portfolios (Andrew Wilkinson / Tiny, 37signals, Pieter Levels) ship *one to revenue first*, then add.

**Translation for this plan:** build the MVP machinery, but aim it at *one named product* until it's in paying hands. Then the same machinery accelerates product #2.

---

## 5. Products in Play

Linards picked **Email Hub + VTV/Cab**. Flagged during the conversation: "VTV/Cab" is actually two products sharing a codebase — not one. So the real list is three.

### Email Hub (Merkle)
- **Path:** productised email-dev tooling — SaaS or one-off-sale, TBD.
- **Market:** agencies, ESPs, CMSs.
- **Ship-first blocker:** **IP overhang.** MEMORY.md J5 flags CDPA 1988 s.11(2) / Patents Act 1977 s.39 (employer-ownership default). Until resolved (Merkle written carve-out, clean-room rebuild, or explicit assignment), every hour on Email Hub product skills is speculative.
- **Decision:** `ip-overhang-guard` becomes the *first* thing run on the Email Hub lane. No product-specific work until this lands.

### VTV (B2G — public-transport optimisation for Latvia)
- **Market:** Riga municipality + LV transport operators.
- **Warm lead:** real and recent — Šlesers (ex-Transport Minister) + Krištopans + LPV network.
- **Partners carry LV execution:** Atis Vīķis (cousin) + Juris Ņefedovs. Linards = technical lead + AI; not solo-load on relationships and regulatory.
- **Sales cycle:** 6–18 months realistic for B2G.
- **Ship-first candidate.**

### Cab (B2C — Bolt-replacement ride-hailing)
- **Shared codebase with VTV.**
- **Difficulties:** two-sided marketplace (drivers + riders), EU taxi/VHC directives + LV Road Traffic Law licensing, capital-intensive acquisition, Bolt has a decade head start.
- **Recommendation:** sequence *after* VTV. VTV gives you the operator network + government relationships; Cab rides on that distribution. Parallel push is only justified if there's a distinct Cab partner pulling that weight separately from the VTV push.

---

## 6. Sequencing — Now → First Product Shipped

Four phases. Roughly in order, some parallelism indicated.

### Phase A. Close out Fredis Phase 9 (1–2 evenings)
Commit the two uncommitted `launchd` plists. Test them. Doc-check `launchctl` commands. Fredis becomes fully deployed.

### Phase B. Build the product-lifecycle skill stack (2–3 weeks of evenings)
Full stack detailed in §7. Skills are product-agnostic workflows — they work across Email Hub, VTV, Cab, and anything future. Ordering inside this phase goes ideate-validate → product-shape → ship-and-govern, with `ip-overhang-guard` pulled forward to week 1 to unblock the Email Hub lane.

### Phase C. Install and wire Archon (~1–2 weeks)
See §8 for integration plan.

### Phase D. Run pipeline on product #1 (timeline product-dependent)
VTV first. Pipeline = Archon workflow orchestrating the skills end-to-end. Fix what breaks. This is where the skill set + Archon stack proves itself or doesn't.

---

## 7. The Skill Stack (10 skills)

All workflow-specialists, not title-specialists. Each encodes something the LLM won't spontaneously do. Product-agnostic bodies; invocation context differs per product.

### Week 1 — Ideate / Validate block

1. **`ip-overhang-guard`** — *promoted to skill #1.* Checklist + template letter to Merkle IP/legal + clean-room-rebuild triggers. Unblocks Email Hub before further investment. Narrow scope, ~1 day skill.
2. **`market-landscape-scan`** — structured competitor/pricing/gap/funding research given a lane (B2G transport, B2C ride-hailing, email dev tooling). Not vibes; not Claude's default research.
3. **`problem-validation`** — Mom Test interview design + synthesis. Kills bad ideas in a week, not a quarter.
4. **`minimum-lovable-product`** — forcing function that cuts feature list to the one thing proving core value. Anti-scope-creep.

### Week 2 — Product-shape block

5. **`pricing-shaper`** — Van Westendorp + anchor ladder + competitor teardown. Covers all three modes needed: B2G contract, B2C commission, SaaS/license.
6. **`positioning-sharpener`** — one-sentence positioning test per lane. Critical for Cab where "Bolt replacement in Riga" is a weak starting position.
7. **`mvp-architect`** — minimum-viable-stack blueprints per product type: B2G dashboard + optimisation engine, B2C mobile app + matching engine, MarTech SaaS integrations.

### Week 3 — Ship + govern block

8. **`launch-wedge`** — first-10-users channel pick. Forces a specific distribution hypothesis before code.
9. **`metrics-gate`** — defines kill criteria upfront: *if no X signal by Y date, shut down.* Protects against zombie-product drift.
10. **`bet-review`** — monthly portfolio review. With three bets active, kill triggers get teeth.

### Cross-cutting (slots anywhere)

- **`market-cycle-lens`** — Dalio cycles / sector rotation / supercycles in a Chris Lori voice. Applies to research, content, and product-timing decisions. Tied to Linards's stated stocks/commodities interest.

### What's explicitly deferred

Robotics engineer, backend engineer, technical architect, AI security engineer, data scientist, QA, systems-thinking architect, security architect — all defer until a product with paying users creates the need. Each is a real specialty; each is a solution hunting for a problem until then.

### What's already covered (do not duplicate)

Content / branding / SEO / design for Fredis-the-product is largely handled: `linkedin-post`, `x-post`, `yt-script`, `yt-shorts`, `instagram-post`, `pptx-generator`, `video-processor`, `sop-creator`, `excalidraw-diagram`, `skill-creator`, `content-ideation:*`. The gap was always strategic positioning upstream of content, not more content production.

---

## 8. Archon Integration Plan

### Sequencing rationale
Advisor initially argued "defer Archon 3–6 months." Revised once Phase 9 was clocked at ~1 day of work: Archon window is weeks, not quarters. Adoption *after* skills are built is correct — Archon is a workflow runner and needs workflows (= skills) to run. Empty scaffolding otherwise.

### Steps
1. Install Archon from `coleam00/Archon`; get dashboard running.
2. **Decide skill location** (open question in §10):
   - **(A)** `~/.claude/skills/` (personal, available everywhere, no versioning)
   - **(B)** standalone plugin repo `fredis-product-skills/` installed via `/plugin marketplace add linardsb/fredis-product-skills` (versioned, diffable, shareable — recommended)
   - **(C)** symlink/submodule per product project (fragile)
3. Wire Fredis memory: Archon workflows read `Fredis/Memory/` and write drafts to `Fredis/Memory/drafts/active/`. Same path as Fredis, or via MCP.
4. Write two parameterised test workflows:
   - `ideate-new-product(product_name, market)` → runs scan → validate → MLP skills in sequence.
   - `ship-mvp(product_name)` → runs architect → wedge → metrics-gate → code-gen → PR skills.

### Why parameterised workflows matter here
With three products sharing certain structural logic (research → validate → shape → ship), a single `ideate-new-product` workflow called with `{product: EmailHub}` vs `{product: VTV}` vs `{product: Cab}` beats duplicated per-product prompts. This is the concrete case *for* Archon in this portfolio — not against it.

---

## 9. Bet-Review Kill Triggers

`bet-review` gets sharper teeth with three active bets. Suggested triggers to build into the skill (for monthly review):

- **Email Hub:** if no IP answer from Merkle by end of month 2 → **paused**.
- **Cab:** if VTV isn't landing real B2G conversations by end of month 4 → **paused** (no distribution base).
- **VTV:** if no signed LOI or paid pilot discussion by end of month 6 → **pivot or pause**.

Three simultaneous zombie-products is the actual portfolio risk, not building too few skills.

---

## 10. Open Questions (gating execution)

Nothing gets built until these are answered.

1. **Email Hub IP status** — has this already been raised with Merkle's IP/legal, or is that ahead of you? If ahead, `ip-overhang-guard` runs this week and its first output is the letter.
2. **VTV vs Cab sequencing** — agree with VTV-first-then-Cab-on-VTV-distribution? If parallel push preferred, need the distinct Cab partner named.
3. **Skill location decision** (§8.2) — personal / plugin / symlink. Recommended: plugin. Locking this early prevents redoing it.
4. **First Archon workflow scope** — will the test run of the Archon pipeline target VTV (recommended) or something else?

---

## 11. Meta-Notes

### Tone and frame used throughout
Chris Lori-style: evidence first, then verdict. No hedging. Direct pushback where the plan was drifting (role-based skills rejected; "portfolio without first ship" flagged; "VTV/Cab" broken into VTV + Cab).

### What's NOT in this plan
- Content / social / design skills (already covered by existing Fredis skills).
- Financial / legal / operational infrastructure for running a business at scale (Ltd formation, accounting, insurance, client contracts) — out of scope until there's revenue to manage.
- Robotics / agri×AI / UGOKI / GERBONI specific work — parked until VTV or Email Hub produces real signal.

### Directive from Linards
"Don't draft anything yet." Nothing in `Fredis/` or `.claude/skills/` has been or will be modified until explicit go-ahead.

---

## 12. Sources

- [awesome-skills.com](https://awesome-skills.com/) — community skills directory (~50 categories surveyed)
- [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) — 232+ skills, 9 domains
- [coleam00/Archon](https://github.com/coleam00/Archon) — live Archon repo (YAML workflow engine for coding agents)
- [coleam00/remote-agentic-coding-system](https://github.com/coleam00/remote-agentic-coding-system) — Claude Code ↔ Slack/Telegram/GitHub bridge
- Cole Medin's workshops (proprietary, locally cloned at `/Users/Berzins/Desktop/workshops`) — 30+ workshop repos, content-skill library, Archon pedagogy
- Fredis memory files: `Fredis/Memory/SOUL.md`, `USER.md`, `MEMORY.md`, `HEARTBEAT.md`
- Fredis PRD: `.agent/plans/second-brain-prd.md` (Phase 9 deployment spec)

---

## 13. Wave 1 Authoring Log (2026-04-19)

Execute-pass of `.agent/plans/phase5-skill-stack.md`. See that plan for decisions, port
tables, and gating context. Decision file: `Fredis/Memory/daily/2026-04-19-phase5-port-decisions.md`.

**Ported from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) (MIT) — 25 skills:**

- C-level advisors (7): `ceo-advisor`, `cto-advisor`, `ciso-advisor`, `scenario-war-room`, `strategic-alignment`, `company-os`, `founder-coach`
- Engineering roles (10): `senior-architect`, `senior-backend`, `ai-security`, `senior-data-scientist`, `senior-qa`, `tdd-guide`, `senior-security`, `senior-secops`, `cloud-security`, `security-pen-testing`
- Statistics + experimentation (2): `statistical-analyst`, `experiment-designer`
- Product (3): `product-strategist`, `product-discovery`, `product-manager-toolkit`
- Personas (3): `startup-cto`, `solo-founder`, `product-manager`

**De novo (Fredis-authored) — 3 skills:**

- `ip-overhang-guard` — UK CDPA 1988 s.11(2) + Patents Act 1977 s.39 + clean-room playbook + Merkle-letter template.
- `business-cycle-analyst` — Dalio short + long debt cycles + Kondratieff waves + sector rotation + Chris-Lori voice.
- `robotics-engineer` — ROS2 architecture + ISO 10218 / 13482 / 15066 safety regimes + motion planning (RRT*, MPC, PRM, A*/D*).

**Deferred:**

- `playwright-pro` — upstream is a 60+ file plugin with MCP integrations and sub-skills; port strategy needs a Wave-2 call (vendor full tree vs. reference-only).
- Archon sub-agent port — per Phase 5.1 plan Amendment 4, deferred until post-Fredis-completion Archon install (Archon's sub-agents run inside Archon workflows natively).

**Validation results (2026-04-19):**

- `quick_validate.py`: 0 failures / 40 skill dirs
- `ruff check`: all checks passed
- `mypy --ignore-missing-imports`: 0 errors in 50 source files
- `pytest`: 282 passed (up from 249 baseline — no regressions)
- Strict frontmatter (Anthropic `name` + `description` only): 28 new skills clean; `skill-creator` retains pre-existing `license` field (allowed by validator).
- Injection-signal grep on ported content: no prompt-injection patterns; "System:" hits are legitimate template placeholders in threat-model / vuln-report outputs.

**Output-path scaffolding:** `Fredis/Memory/drafts/active/<skill>/.gitkeep` present for all 28 new skills.

**Not done in this pass (requires fresh Claude Code session):**

- Task 13 manual per-skill trigger-phrase dry-runs — trigger-phrase matching cannot be self-tested mid-session.
- Commit — gated on explicit ask per `MEMORY.md` `feedback_no_unprompted_commits.md`.
