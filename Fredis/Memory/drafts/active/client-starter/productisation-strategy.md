# Client Second-Brain — Productisation Strategy

*saulera internal. Drafted 2026-06-21. Derived from the Fredis build + the second-brain productisation analysis. Plain en-GB, hype-free.*

---

## TL;DR

saulera's own Fredis is the reference build for a service almost no competitor can credibly offer: **building a client their own AI second brain.** The opportunity is to deliver it *repeatably* — configure an instance per client instead of rebuilding — without destabilising Fredis (which is both the engine *and* saulera's #1 proof asset) and without pulling focus from Email Hub (the primary product bet). The route is **services-first**: each client engagement is a paid prototype; extract the reusable template from the first few.

---

## 1. The finding — saulera *is* the AI-native services direction

The generic "become an AI automation consultant" playbook describes, at low resolution, exactly what saulera already is at high resolution. Fredis is the reference build; the saulera site already sells this (8 industries, "first build, no fee", the agnostic promise). So a "second brain for clients" is **not a new idea — it's the existing positioning made into a repeatable delivery.** The work is productising the motion, not inventing it.

---

## 2. LLM-agnosticism — two different claims, keep them separate

| Claim | Status | Proof |
|---|---|---|
| What saulera **sells / builds for clients** is model-agnostic, incl. local | **True, architecturally real** | VTV swaps Anthropic / OpenAI / Ollama / Groq / OpenRouter via one env var + an OpenAI-compatible endpoint; Email Hub routes Claude/OpenAI via a provider abstraction |
| **Fredis itself** (its autonomous brain) is agnostic | **False — Claude-coupled by design** | Every loop (heartbeat, reflection, synthesis, chat) calls the Claude Agent SDK directly; no abstraction layer. The coupling is what buys the skills / hooks / advisor-mode safety model |

**Positioning line for a prospect:** *"The systems I build for you are agnostic — here's VTV running on five providers to prove it. Fredis, the system I run my own business on, is Claude-native because that's what makes its safety model work."* Don't conflate the two; conflating risks overclaiming, which by saulera's own trust-account logic is the fastest withdrawal you can make.

---

## 3. Two productisation shapes

- **Template / fork-per-client (SERVICES — now).** Each client gets their own deployment, their own keys. No multi-tenancy, no shared-system credential isolation. Claude-native works today. Right up to ~5 clients.
- **Multi-tenant SaaS ("Fredis Cloud" — later).** One platform, many tenants, OAuth, isolation, self-serve onboarding. ~3-month+ build. Only worth it when fork-maintenance starts to hurt.

**Recommendation:** template now; SaaS is the later graduation, not a parallel speculative track.

---

## 4. Architecture — engine vs config

The codebase is already **~70% engine/config separated**, which is why this is tractable:
- `config.py` derives every path from `PROJECT_ROOT` (relative, not hardcoded) — fork it anywhere and paths just work.
- `setup_workspace.py` already does master-env → per-target provisioning.
- The phase-1 onboarding pipeline already personalises the memory files from interview answers. **Fredis itself came from a template.**

| Layer | Contents | Per-client? |
|---|---|---|
| **Engine** (build once, shared) | runtime loops, hooks, the ~20 generic skills, vault structure | No |
| **Config** (per client) | the 5 memory files, `.env` (keys, MCP servers, ESP, CMS), channel routing, a small client-skill pack, vault content | Yes |
| **Provisioning kit** | onboarding interview → generate memory files → wire `.env` → deploy | runs once per client |

**The one rule that matters: clients track an upstream engine, they never fork it.** Engine = one shared remote; each client repo = config + overlay that *pulls* engine updates. Improve Fredis once → every client gets it on next pull. This requires splitting `.claude/skills/` into engine-core (upstream) + client-pack (local overlay).

**If/when a client demands non-Claude or local:** rebuild the agent loop on **Pydantic AI + LiteLLM** (the stack VTV/gerboni already use). What ports for free: skill *content*, memory architecture, integration logic, advisor-mode policy. What must be rebuilt: the agent loop, skills progressive-disclosure, and the hooks (→ application middleware).

---

## 5. The hard parts (ranked by risk)

1. **Per-tenant credential isolation** — *only* bites the SaaS shape; the template sidesteps it entirely (each client = own deployment, own keys).
2. **Skills progressive disclosure** without stuffing 24 skills into every prompt (context/cost).
3. **The safety model as app-level guards** — advisor-mode / soul / secret blocking are Claude-Code hooks today; on an agnostic stack they become middleware you own.
4. **Capability variance → eval harness per provider** — an *ongoing* tax, not a one-off. Target **"any high-end model that passes the eval suite"**, not literally any LLM.
5. **Multi-tenant substrate** (storage, OAuth, onboarding) — SaaS only; ~3 months on its own.

---

## 6. Sequencing — services as paid R&D

- saulera already builds bespoke, agnostic agents per client → **each engagement is a paid prototype of this product.**
- Build for clients → watch the common 80% across 3–5 builds → extract into the template (and later Fredis Cloud).
- The product becomes a **byproduct of revenue**, not a bet against it.
- **Guardrail:** Email Hub is ship-first (the primary product bet). The second-brain service competes for the same hours — time-box it; treat it as runway cash + portfolio proof, not a focus-shift. Discount the infomercial "window is closing" framing.

---

## 7. Status — what's built

- **This session:** the client intake instrument (`onboarding-interview.md`) — 172 questions, generalised from Fredis's own onboarding and stripped of personal answers, tier-tagged by client type (Tier 1 Core / Tier 2 Business depth / Tier 3 Deep personal).
- **The client-starter design** — engine vs config, upstream-tracking (this doc + the `client-starter/` seed).

---

## 8. Roadmap — remaining starter pieces

1. **Blank memory templates** — the 5 files (SOUL/USER/MEMORY/HABITS/HEARTBEAT) as fill-from-interview placeholders.
2. **Engine/skill split** — generic-core (upstream) vs personal client-pack (local).
3. **Per-client `.env` template.**
4. **Provisioning runbook** — interview → generate memory files → wire `.env` → deploy.
5. *(Later)* the agnostic engine (Pydantic AI + LiteLLM) — only when a client demands non-Claude / local.
6. *(Much later)* multi-tenant Fredis Cloud — only when fork-maintenance hurts.

---

## 9. Open decisions (for the agnostic future)

- **Supported-tier scope:** "any high-end model that passes the eval suite", not literally any model.
- **Provider model:** per-tenant fixed-at-onboarding (recommended) vs runtime hot-swap.
