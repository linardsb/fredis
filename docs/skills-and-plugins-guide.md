---
title: Fredis Skills + Plugins Guide
date: 2026-04-20
status: living document — reflects Phase 5.2 + 5.2.5 target state (20 Fredis skills + 7 Claude Code built-ins; agentic-backend references landed; plugin split deferred indefinitely — see Part 2 for trigger conditions)
audience: Linards
---

# Fredis Skills + Plugins Guide

Practical reference for how the Fredis skill stack works — what skills are, how to invoke them, what plugins are for, and when each matters. Short enough to read in one sitting, deep enough to come back to.

---

## TL;DR

- **Skills** are named capabilities Claude loads into its context when you trigger them. Each one encodes a specific framework, checklist, or workflow. Fredis has 20 of them post-Phase 5.2 (plus 7 Claude Code built-ins).
- **Plugins** are bundles of skills (and other capabilities) that load *conditionally*, not always. Useful when you have more skills than can cleanly fit in every session's context budget or mental model.
- **You invoke skills by natural language** ("price this for VTV", "run a Mom Test interview draft") or by slash command (`/loop`, `/schedule`). The model routes to the right skill based on the trigger phrases encoded in its description.
- **Plugins are deferred indefinitely** — Phase 5.3 is closed until a concrete trigger fires (skill count ≥ 30, publishing decision, or per-client repo isolation). Today every Fredis skill is always available, and the research showed the native plugin system doesn't support auto-activation-by-project-type without user-coded hook orchestration. See Part 2.

---

## Part 1 — Skills

### What a skill is

A skill is a named directory under `.claude/skills/<name>/` containing:

- **`SKILL.md`** — the skill's entry point. YAML frontmatter (`name` + `description`) + a markdown body.
- **`references/*.md`** (optional) — deep framework content that loads on demand.
- **`assets/*`** (optional) — templates, schemas, example files.
- **`scripts/*`** (optional) — executable helpers.

Claude Code auto-discovers every directory under `.claude/skills/` that has a valid `SKILL.md`. You don't install or register skills — they exist by being in the folder.

### The 3-level loading model (progressive disclosure)

Anthropic's official skill pattern layers content across three levels. Understanding this is the key to knowing what costs context and what doesn't:

| Level | Contents | When loaded | Budget |
|---|---|---|---|
| **1. Metadata** | `name` + `description` (YAML frontmatter) | **Always** in every session's system prompt | ~100 words per skill |
| **2. Body** | `SKILL.md` markdown body — routing table + primer + advisor block | **When the skill triggers** | ≤ 500 lines, ideally ≤ 300 |
| **3. Resources** | `references/*.md`, `scripts/*`, `assets/*` | **On demand** — only when Claude actively reads them | unbounded |

**Why this matters:** with 20 skills × ~80 tokens of description ≈ 1,600 tokens always loaded — ~1% of the 200k context window. Even with 50 skills you're at ~4,000 tokens always loaded. The body and references only cost tokens *when you invoke the skill*, so the cost per skill is capped at what fits in a Level-2 body.

### How to invoke a skill

There are three ways a skill gets loaded into context:

**1. Natural-language trigger.** The model reads your message and matches against each skill's description. If the description says "Use when user says 'Mom Test'", saying "run a Mom Test interview for VTV" routes to `idea-validation` (which contains `problem-validation.md`). You don't need to name the skill.

**2. Slash command.** Claude Code has built-in slash commands (`/loop`, `/schedule`, `/commit`, `/init`, etc.) that map to skills or commands. Type `/` in Claude Code to see the list.

**3. Explicit invocation.** If the model doesn't pick up on your trigger, you can name the skill directly: "use the `launch-governance` skill for this." This forces the router.

### Fredis's 20 skills — the map

Post-Phase 5.2 structure (see `.agent/plans/phase5-2-skill-consolidation.md` for the migration plan):

**Singular frameworks — kept standalone (7):**

| Skill | What it encodes |
|---|---|
| `ip-overhang-guard` | UK CDPA 1988 s.11(2) + Patents Act 1977 s.39 + clean-room rebuild playbook + Merkle letter template |
| `business-cycle-analyst` | Dalio debt cycles + Kondratieff waves + sector rotation + Chris-Lori voice rules |
| `robotics-engineer` | ROS2 architecture + ISO 10218/13482/15066 safety + motion planning (RRT*, MPC, PRM) — future-gated |
| `phase1-ready` | Fredis first-run onboarding from 103-question interview |
| `skill-creator` | Meta-skill for authoring other skills — the validator lives here |
| `obsidian-vault-structure` | Reference for the `Fredis/` vault layout |
| `ciso-advisor` | Strategic security leadership, compliance (SOC2/HIPAA/GDPR), board security reporting |

**Merged bundles (10):**

| Skill | Absorbs | Routing |
|---|---|---|
| `integrations` | direct-integrations + mcp-client | "check email", "show calendar", "check hubspot", "connect to MCP" |
| `executive-leadership` | ceo-advisor + founder-coach + solo-founder + scenario-war-room | "CEO advice", "board deck", "fundraising", "burnout", "war room", "what if X and Y" |
| `technical-leadership` | cto-advisor + startup-cto | "CTO advice", "technical strategy", "boring technology", "team scaling" |
| `org-design` | strategic-alignment + company-os | "OKRs", "silos", "EOS", "Scaling Up", "quarterly rocks" |
| `security-engineering` | senior-security + senior-secops + security-pen-testing + cloud-security + ai-security | "STRIDE", "SAST", "DAST", "CVE", "pen test", "IAM", "prompt injection" |
| `engineering` | senior-architect + senior-backend + senior-qa + tdd-guide | "ADR", "C4", "REST API", "DB query", "generate tests", "TDD" |
| `data-and-experimentation` | senior-data-scientist + statistical-analyst + experiment-designer | "A/B test", "hypothesis test", "sample size", "feature engineering", "MLflow" |
| `product-management` | product-strategist + product-discovery + product-manager-toolkit + product-manager | "OKRs", "roadmap", "OST", "assumption mapping", "RICE", "PRD" |
| `content-social` | linkedin-post + x-post + instagram-post | "LinkedIn post", "tweet", "thread", "Instagram carousel" |
| `content-artifacts` | pptx-generator + excalidraw-diagram + pdf + sop-creator | "slides", "deck", "diagram", "PDF", "runbook", "SOP" |

**Workflow-specialist bundles (3):**

| Skill | Absorbs | Routing |
|---|---|---|
| `idea-validation` | market-landscape-scan + problem-validation + minimum-lovable-product | "market scan", "validate idea", "Mom Test", "MVP", "MLP" |
| `product-shape` | pricing-shaper + positioning-sharpener + mvp-architect | "price this", "willingness to pay", "positioning", "build vs buy", "stack" |
| `launch-governance` | launch-wedge + metrics-gate + bet-review + decision-logger | "first 10 users", "Bullseye", "kill criteria", "monthly review", "continue or kill" |

### Voice-mode parameter (post-Phase 5.2)

Three merged skills accept a voice parameter that loads a persona reference instead of neutral SOUL voice:

- `executive-leadership` — "in solo-founder voice"
- `technical-leadership` — "in startup-cto voice"
- `product-management` — "in product-manager voice"

You can also invoke Chris-Lori voice across any relevant skill by saying "in Chris-Lori voice" — loads `_shared/chris-lori-voice.md`.

**Example:**
```
You: "Advise me on delegating the Email Hub first commit — in solo-founder voice"
→ routes to `executive-leadership`, loads `references/solo-founder.md` instead of neutral voice
```

Default is neutral SOUL voice (no parameter = no persona override).

### When do skills *not* trigger?

Sometimes the model should pick a skill but doesn't. Common reasons:

1. **Vague description.** If a skill's description is "helps with strategy stuff," it won't route — too broad.
2. **Trigger-phrase mismatch.** Description says "Use when user says 'Mom Test'", you say "run a customer interview." No match → no route.
3. **Collision with another skill.** Two skills list "product strategy" as triggers. Model fires one (not always the best one).

**Mitigation in Fredis:** every merged skill's description enumerates multiple trigger bundles to reduce both (1) and (2). Collisions from (3) are managed by the post-Phase-5.2 structure (no persona vs. function-role collision — personas are voice parameters, not separate skills).

### When to use which skill

Some decision heuristics by situation:

- **"I have a new product idea"** → `idea-validation` (scan → validate → MLP chain)
- **"I need to price a pilot"** → `product-shape` (pricing-shaper reference)
- **"I want to launch something"** → `launch-governance` (wedge → gate → review)
- **"Something's broken in production"** → `engineering` (architecture / backend / QA routing)
- **"Board deck next week"** → `executive-leadership` (CEO strategy reference)
- **"I need a LinkedIn post"** → `content-social` (LinkedIn reference)
- **"I need a diagram for a doc"** → `content-artifacts` (Excalidraw reference)
- **"Employer-IP check before I ship Email Hub"** → `ip-overhang-guard` (singular, always right call)
- **"What's the macro cycle doing?"** → `business-cycle-analyst`
- **"Design the agent architecture for a new product"** / **"agentic backend with VSA"** → `engineering` (loads `agentic-application-architecture.md` + `agentic-orchestration-patterns.md`)
- **"How do I defend this agent against prompt injection?"** / **"agent guardrails"** → `security-engineering` (loads `agent-guardrails.md`)
- **"I need an LLM-as-judge eval suite"** / **"regression evals for an agent"** → `data-and-experimentation` (loads `llm-evals.md`)

---

## Part 2 — Plugins

### What a plugin is

A plugin is a **bundle of skills + slash commands + agents** distributed as a package. Claude Code supports plugins natively via the `/plugin marketplace` command. You can install, enable, and disable plugins without editing any file.

The key property: **plugins load conditionally**. A plugin you haven't activated doesn't consume any context — its skills aren't visible to the model.

### Why plugins exist (the problem they solve)

Skills as directories work fine until you hit three problems:

1. **Skill sprawl.** Past ~30 skills, Level-1 descriptions start to clutter the system prompt and routing precision drops.
2. **Context mismatch.** When you're on a Slack DM drafting response, you don't need the full SAST/DAST security stack crowding the routing table. When you're debugging a backend API, you don't need LinkedIn-post style rules.
3. **Sharing / reuse.** A skill set built for Fredis might be useful on a friend's project. Without plugin packaging, you'd have to manually copy 20 directories.

Plugins solve all three by making skill sets modular and conditional.

### Phase 5.3 — deferred indefinitely (trigger-based)

Phase 5.2 landed 20 in-repo skills under `.claude/skills/`. The original idea was to split them into `fredis-core` + conditional plugins during Phase 5.3. **After verifying Claude Code's plugin system against the draft plan (2026-04-20), that split is deferred indefinitely — not timed.** Three constraints make the split less useful than the earlier framing assumed:

1. **No native conditional activation.** Plugins load all-or-nothing per scope (user / project / local). "Engineering plugin auto-activates in code repos" isn't a native feature — it would require user-coded `CwdChanged` hooks running `/plugin disable` + `/plugin enable` scripts. The native granularity is: install at user scope (always loaded) or project scope (loaded in that repo's `.claude/settings.json`), plus manual `/plugin enable/disable` mid-session.
2. **Plugins can't reference files outside themselves.** Plugins are copied to a cache at install time; a plugin referencing `../../_shared/lanes.md` breaks at runtime. Workarounds: symlinks preserved in the cache, duplicate-per-plugin, or monorepo + sparse-checkout. None are free.
3. **Plugin agents lose `hooks` / `mcpServers` / `permissionMode` frontmatter.** Security restriction. Any Fredis subagent needing those can't move to a plugin.

### When to reopen Phase 5.3

One of these triggers has to fire:

- **Skill count ≥ 30** with measurable system-prompt clutter or reproducible routing misfires.
- **Publishing decision** — you want to open-source or distribute Fredis's skill stack as a plugin marketplace (a business call — consultancy credibility, OSS release, monetisation — not an engineering one).
- **Per-client repo isolation** — you start maintaining client-specific skill sets in separate repos and want `/plugin install` over manual copying.

Until one fires, the split is infrastructure without a job: added maintenance (manifest files, shared-asset symlinks, plugin-agent restrictions, distribution story) without a problem it solves. 20 skills sits below the legibility threshold, Fredis is single-user, and the heartbeat runs outside the skill system entirely.

### If Phase 5.3 does reopen — one plausible structure

Illustrative only. The partition and plugin boundaries would need re-evaluation at reopen time against whichever trigger fired.

```
fredis-core (always loaded in every session):
├── ip-overhang-guard
├── business-cycle-analyst
├── executive-leadership
├── product-management
├── idea-validation
├── product-shape
├── launch-governance
├── integrations
├── phase1-ready
└── skill-creator
(~10 skills loaded baseline)

fredis-engineering (project-scope install in code repos):
├── engineering
├── security-engineering
├── ciso-advisor
└── data-and-experimentation

fredis-content (project-scope install when drafting / social):
├── content-social
└── content-artifacts

fredis-meta (project-scope install in the Fredis repo only):
├── obsidian-vault-structure
├── technical-leadership
├── org-design
└── robotics-engineer
```

**Key change from the pre-2026-04-20 draft:** "project-scope install" replaces "auto-activates" — activation is manual per-repo via that repo's `.claude/settings.json`, not automatic by file type or directory pattern. The auto-activation story would need `CwdChanged`-hook orchestration on top.

### How plugins get installed (the Claude Code mechanism)

Plugins live in a marketplace and install via slash command:

```
/plugin marketplace add <url-or-path>
/plugin install <plugin-name>
/plugin enable <plugin-name>
/plugin disable <plugin-name>
/plugin list
```

Example if Fredis published its own plugin:
```
/plugin marketplace add linardsb/fredis-product-skills
/plugin install fredis-engineering
/plugin enable fredis-engineering
```

From then on, the engineering bundle would be loaded in that scope (user / project / local). Activation granularity is per-scope only — **auto-activation by file type or directory pattern is not a native feature.** It can be emulated via `CwdChanged` hooks that call `/plugin enable` / `/plugin disable`, but that's user-coded orchestration, not built-in.

### When to use a plugin vs. a skill in `.claude/skills/`

| Situation | Use skill dir | Use plugin |
|---|---|---|
| Personal-only, single project | ✅ | ❌ |
| Shared across multiple repos / machines | ❌ | ✅ |
| Small skill set (< 15 total) | ✅ | ❌ |
| Large skill set with clear activation contexts | ❌ | ✅ |
| Rapid iteration, short feedback loop | ✅ | ❌ |
| Stable, version-gated, diffable | ❌ | ✅ |

**Fredis today** sits comfortably on the left column. The Phase 5.3 split is deferred indefinitely — see the trigger conditions earlier in Part 2. The right column starts mattering if skill count climbs past ~30 with measurable routing misfires, if you decide to publish the stack, or if you start maintaining per-client skill sets across repos.

### Plugin vs. skill vs. /slash command — when each applies

| Capability | What it is | Where it lives | How you invoke |
|---|---|---|---|
| **Skill** | Named capability encoded via SKILL.md | `.claude/skills/<name>/` or inside a plugin | Natural-language trigger |
| **Slash command** | Predefined prompt / command entry-point | `.claude/commands/<name>.md` or inside a plugin | `/<name>` |
| **Plugin** | Bundle of the above + hooks + agents | `/plugin marketplace` | `/plugin install <name>` |
| **MCP server** | External tool / data surface exposed via MCP protocol | Separate process / service | `mcp__<server>__<tool>` tool calls |

Fredis uses all four:
- **Skills** for advisor / role / workflow capabilities.
- **Slash commands** for workflows like `/session-init`, `/validation:*`, `/content-ideation:*`.
- **MCP servers** (jCodeMunch, jDocMunch, Pencil) for code/doc search and visual work.
- **Plugins** — not yet; Phase 5.3 deferred indefinitely until a trigger fires (see Part 2).

---

## Part 3 — Practical usage patterns

### Daily usage by lane

**Email Hub (pre-revenue, IP-gated):**
```
Linards: "check the IP status for Email Hub"
→ ip-overhang-guard (the singular skill — always right call for this lane)

Linards: "once IP is clear, scan competitors"
→ idea-validation → market-landscape-scan.md (with Email Hub lane pre-seeds)

Linards: "run a Mom Test on a CRM ops target"
→ idea-validation → problem-validation.md (Email Hub interview template)

Linards: "shape the MVP price"
→ product-shape → pricing-shaper.md (SaaS canvas)
```

**VTV (B2G, warm lead):**
```
Linards: "scan the EU transport optimisation market"
→ idea-validation → market-landscape-scan.md (VTV pre-seeds: Optibus, Trapeze, Remix, STEEP-P regulatory layer)

Linards: "draft a stack brief for VTV"
→ product-shape → mvp-architect.md (B2G optimisation canvas: FastAPI + PostGIS + OR-Tools)

Linards: "who are the first 10 users?"
→ launch-governance → launch-wedge.md (VTV lane starters: Šlesers, Atis, Juris, LPV contacts)

Linards: "set kill criteria for VTV"
→ launch-governance → metrics-gate.md (writes Fredis/Memory/gates/vtv.yaml; heartbeat watches deadline)
```

**Cab (B2C, sequenced after VTV):**
```
Linards: "sharpen Cab positioning"
→ product-shape → positioning-sharpener.md (forces escape from "Bolt replacement in Riga" weak starting position)

Linards: "Cab launch wedge"
→ launch-governance → launch-wedge.md (refuses until discovery fills outer-ring channels — Cab doesn't have warm network like VTV)
```

### Daily usage for Fredis-itself

```
Linards: "monthly bet review"
→ launch-governance → bet-review.md (loads Monday overdue, GitHub activity, gate YAML files; writes draft)

Linards: "what did we decide last month about Email Hub?"
→ launch-governance → decision-logger.md (DO_NOT_RESURFACE check, prior-review loading)

Linards: "draft a LinkedIn post on AI-agentic consultancy"
→ content-social → linkedin.md

Linards: "slide deck for Šlesers meeting"
→ content-artifacts → pptx.md
```

### Invoking voice modes

```
Linards: "advise on delegation — in solo-founder voice"
→ executive-leadership, loads references/solo-founder.md (voice override)

Linards: "architecture review — in startup-cto voice"
→ technical-leadership, loads references/startup-cto.md

Linards: "strategic call on VTV — in Chris-Lori voice"
→ any relevant skill + loads _shared/chris-lori-voice.md for tone rules
```

---

## Part 4 — When to add, when to merge

### When to add a new skill

Per the earned-slot test (from `docs/product-portfolio-plan.md` §3), a skill only belongs if it encodes **one of**:

1. A specific framework the LLM won't spontaneously use (e.g., Van Westendorp, Dalio cycles, CDPA s.11(2), Mom Test)
2. A checklist (pre-mortem, red-team, kill criteria)
3. A workflow tied to your tools (Monday.com stage → required artifact, Gmail draft → advisor review)

**Bad reasons to add a skill:**
- "It sounds like a useful role" (CEO, COO, CFO as title-skills)
- "Other skill catalogs have one" (without it encoding something specific)
- "I might need it someday"

**Good test:** write the SKILL.md body in one sitting. If you can't name the framework, checklist, or tool workflow in the first paragraph, the skill doesn't earn a slot.

### When to merge into an existing skill

You have a new framework and one of the existing 20 bundles is the natural home:

- **Same routing context** — would you invoke it alongside the bundle's existing references? → merge as new `references/<new-framework>.md` in that bundle.
- **Different routing context** — new triggers that don't collide with the existing bundle's descriptions? → probably a new skill.
- **Cross-cutting** (used by many bundles) — consider `.claude/skills/_shared/`.

**Example:**
- "I want to add a `blue-ocean-strategy` skill." → it's already a reference inside `idea-validation/references/market-landscape-scan.md`. Don't add a top-level skill; extend the existing reference.
- "I want to add a `gdpr-compliance` skill." → new context, specific framework, doesn't fit `security-engineering` or `ciso-advisor`. → new top-level skill.
- "I want an `agentic-application-architecture` skill." → same routing context as `engineering` (architectural shape sits next to the existing architecture + backend references). → extend `engineering` as a new reference, not a new top-level skill. This was the Phase 5.2.5 call.

### When to refactor the stack (split / plugin / restructure)

Signals that you're ready for the Phase 5.3 plugin split:

- You notice routing misfires — the model picks the wrong skill because descriptions are too similar.
- You find yourself opening Claude Code in different project types and not needing most of the stack.
- You want to share a skill set with a collaborator or publish one for the community.
- The `ls .claude/skills/` output is longer than your attention span.

---

## Part 5 — Where to find more

- **Phase 5.2 migration plan** — `.agent/plans/phase5-2-skill-consolidation.md` (file moves, per-merge spec, heartbeat wiring).
- **Phase 5.1 Wave 1 plan** — `.agent/plans/phase5-skill-stack.md` (original 28-skill port; binding authoring conventions).
- **Portfolio plan** — `docs/product-portfolio-plan.md` (strategic rationale for the skill stack, earned-slot test, three-lane context, open questions §10).
- **Skill-creator meta-skill** — `.claude/skills/skill-creator/SKILL.md` (authoring rules; frontmatter; progressive disclosure; `quick_validate.py`).
- **Anthropic's skill docs** — search for "Claude Code skills" in the Anthropic documentation for the canonical 3-level loading pattern and plugin marketplace API.

## Quick reference card

```
# See what skills are available in this session
(look at the system-reminder "available skills" list at session start)

# Invoke by natural language
"run a Mom Test interview for VTV"
"price Email Hub for a mid-market agency"
"set kill criteria for Cab — no VTV distribution by month 4"

# Invoke by slash command
/loop <interval> <prompt>
/schedule <cron> <prompt>
/commit

# Invoke voice mode on a merged skill
"advise on burnout — in solo-founder voice"

# Plugin commands (Phase 5.3+ only; not active yet)
/plugin marketplace add <url>
/plugin install <name>
/plugin enable <name>
/plugin list

# Check skill validity during authoring
cd .claude/skills/skill-creator/scripts
uv run python quick_validate.py ../../idea-validation/
```

---

Last updated: 2026-04-20. Reflects planned Phase 5.2 target state. Update when Phase 5.3 plugin split lands.
