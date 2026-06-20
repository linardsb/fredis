# AI Agent Workflow Playbook

_A prescriptive plan for improving any project that runs an AI workflow and builds personalised agents._

**Source.** Synthesised from the 20VC interview with Matan Grinberg (CEO/co-founder, Factory) — `docs/20vc_interview.txt`. Factory builds autonomous software-development agents ("droids") for large enterprises, so the interview is about enterprise dev agents. This playbook keeps only the **transferable architecture and operations layer** and reframes it as actions. The VC/fundraising/origin-story material is left out — it does not transfer.

**Running case studies.** The three products advertised in that same episode are used throughout as real-world examples — and the choice is instructive, because **all three are application-layer AI companies built on top of other people's foundation models**, which is exactly the layer Matan argues captures durable value:

- **Conversion** (`conversion.ai`) — AI-native B2B marketing-automation platform replacing Marketo/Pardot/HubSpot. "Conversion Agents" automate marketing-ops grunt work over a unified CRM+warehouse data model. ~$10M ARR, ~90% of customers ripping out a legacy tool; $28M Series A (Abstract Ventures, OpenAI angels). _Not to be confused with Jasper — `conversion.ai` was Jasper's original name in 2021, but Jasper moved to `jasper.ai`; a different company occupies the domain now._
- **Granola** (`granola.ai`) — AI "notepad" for back-to-back meetings. Captures device audio (no bot joins the call), transcribes on Deepgram + AssemblyAI, enhances notes with GPT-4o + Claude. Freemium → ~$14–35/user/mo. $125M Series C at a $1.5B valuation (Index, Kleiner Perkins). Its stated thesis: the value isn't the notes, it's making conversation knowledge available to _other_ systems and agents.
- **Superhuman** (`superhuman.com`) — premium AI email client ("save 4 hours a week") whose AI drafts replies "that sound like you". Acquired by Grammarly for ~$825M (2025); Grammarly then renamed itself **Superhuman** and bundled Mail + Grammarly + Coda + a proactive cross-app assistant (**Superhuman Go**, 800+ integrations) into one suite.

**How to use this.** Each principle is _idea → why it matters → how to apply_, with **In the wild** notes showing how the case studies embody it. Treat the "Apply" bullets as a backlog, not prose. Where a principle has a specific consequence for a _personalised_ agent (one that holds a user's context, memory, and preferences), it is called out under **Personalisation**. The final section turns the whole thing into a self-assessment you run against each of your projects.

---

## 1. Treat models as a swappable, competitive layer — route per task

**Idea.** Roughly 80–90% of tasks don't need a frontier model; cheaper or open models do them faster and far cheaper. The remaining ~10–20% — planning and decision-making tokens — are where a frontier model earns its price. New models ship weekly, so no single provider stays "best" for long; value accrual is time-dependent. The bear case for any agent product is one provider running away from the rest.

**Why it matters.** Hard-wire one model and you inherit its pricing power, outages, and quirks — and you pay frontier rates for work an open model could do. Routing turns the model layer into a commodity you control instead of a vendor you depend on.

**Apply.**
- Put every model call behind a provider adapter so swapping is a config change, not a rewrite.
- Classify each task as **planning/decision** vs **implementation/retrieval**. Default to the cheap model; escalate to frontier only for the high-stakes reasoning steps.
- Track cost _per task class_, not just total spend — so you can see where the expensive tokens actually go.
- Re-benchmark routing whenever a notable model lands. Keep an eval set (see §9) so the swap is evidence-led.

**In the wild.** Granola already runs a _de facto_ routed stack — specialised, cheap models (Deepgram, AssemblyAI) for transcription, frontier models (GPT-4o, Claude) only for the summary/decision step. That split is the 80/20 rule made concrete. Superhuman goes further and never names its model to the user — the model is abstracted away entirely, the kind of provider-agnostic abstraction Matan champions, where the user never needs to know what is running under the hood.

**Personalisation.** Route on _user context_ too, not just task type: a quick "what's on my calendar" lookup is a cheap-model job; "help me decide between these two clients" is a frontier-model job. The user shouldn't know or care which model answered.

---

## 2. Measure outcomes, not intermediate metrics

**Idea.** Bloat comes from optimising intermediate metrics — features shipped, hours worked, tokens consumed. Matan's analogy: don't judge a basketball game by who sweated most; look at the scoreboard. "Token-maxing" (rewarding people for _using_ AI) is the same trap.

**Why it matters.** An agent that is _used a lot_ is not the same as an agent that _helps_. If your success metric is volume of output or usage, you'll ship a busy, expensive agent that moves no real needle.

**Apply.**
- Define the one or two **business/user outcomes** the agent exists to move (decision quality, time saved, a task actually completed) and measure those.
- Stop reporting "how much AI was used" as a success metric. Usage is a cost, not a result.
- Tie each agent action back to an outcome. If an action can't be traced to one, question why the agent does it.

**In the wild.** Superhuman's entire pitch — "save 4 hours every week" — is an _outcome_ metric (time returned to the user), not a usage or feature-count metric. Conversion sells against Marketo/HubSpot precisely because those incumbents bloated chasing intermediate metrics; the wedge is "fewer manual campaign builds, same results."

**Personalisation.** The outcome metric is "did this help _this user_?" — did the draft get sent, did the suggestion get acted on, did it save a step. Instrument acceptance/edit/discard of agent output as your real signal.

---

## 3. Build the factory, not just the agent — invest in agent DevX

**Idea.** Factory's name comes from the thesis that you stop building the product by hand and instead build the _factory_ that builds it — like a Tesla line of robotic arms that humans designed. The leverage is in the scaffolding around the agent: up-to-date documentation, sandboxes where the agent can _run_ its own output and iterate, CI/CD, linters, pre-commit hooks, clear standards. With human engineers this scaffolding pays off 1:1. With agents it pays off 10–100×, because every agent benefits at once.

**Why it matters.** The cheapest way to make agent output better is rarely a better prompt — it's giving the agent an environment that catches its mistakes and feeds them back automatically.

**Apply.**
- Give agents an **executable environment**: let them run their output, see the result, and iterate — don't make them generate blind.
- Maintain **machine-readable docs and standards** the agent reads at runtime, and keep them current (stale docs are worse than none).
- Wire **linters, formatters, pre-commit hooks, CI** so adherence to standards is enforced mechanically, not by review.
- Spend on the scaffolding _before_ scaling the number of agents — the payoff multiplies by agent count.

**In the wild.** Conversion's "unified data model" (CRM + Snowflake + BigQuery) is its factory — the agents are only as good as the clean, integrated substrate they act on. The product investment is in the assembly line, not in any single agent action.

**Personalisation.** The "factory" for a personalised agent is the **memory/context pipeline**: how user facts get captured, structured, retrieved, and kept fresh. Invest there first — it's the equivalent of the assembly line. (Granola's whole product is this pipeline for meetings.)

---

## 4. Design to minimise review — make output adhere to standards upstream

**Idea.** The first phase of any AI rollout is "look how much we can generate". The second is a senior person drowning in low-quality output that doesn't follow the standards. Review is the real bottleneck. The fix is upstream: make the agent produce production-ready output in the first place.

**Why it matters.** Review doesn't scale with generation. If a human must inspect everything, throughput is capped by that human — and the volume only grows.

**Apply.**
- Bake standards into the agent's context and guardrails so output _adheres by default_, instead of relying on a reviewer to catch drift.
- Use the mechanical gates from §3 (linters, tests, hooks) as the first reviewer — humans see only what passes.
- Reserve **human-in-the-loop review for high-stakes or irreversible actions**, not routine output. Match review depth to stakes.

**In the wild.** Superhuman Go acts proactively across apps but still surfaces drafts for the user to send — the irreversible step (sending) keeps a human gate, while low-stakes prep (scheduling suggestions, fetching data) runs without one. That is review depth matched to stakes.

**Personalisation.** For an advisor-style agent, the review gate is the user's approval before anything leaves the system (a draft, an email, a post). Keep that gate for outward-facing actions; remove it for internal/read actions where the cost of error is low.

---

## 5. Instrument cost from day one and pre-empt the "hangover"

**Idea.** Organisations move through three phases: **(1) panic** — "what's our AI strategy?"; **(2) token-maxing** — "adopt AI at all costs, measure usage"; **(3) the hangover** — looking at the bill and asking "what's the ROI?". One CIO found they were spending hundreds of thousands a month on people asking a frontier model for the weather. The contraction that follows is healthy — but only if you see it coming.

**Why it matters.** Cost discovered late forces a panicked clamp-down (blunt per-user limits) that kills good usage with the waste. Cost instrumented early lets you allocate consciously.

**Apply.**
- Instrument **spend per task class, per feature, and per user** from the start — before usage scales.
- Set **conscious budgets** where they matter, and differentiate: an important workflow gets a higher allowance than a casual one. Avoid one flat limit across everything ("painting with too wide a brush").
- Have an **ROI story before the bill arrives**: know which spend maps to which outcome (ties back to §2).
- Expect and plan for a usage contraction as you trim low-value calls — that's the system working, not failing.

**In the wild.** Granola is the cautionary tale in motion: analysts note its margins are squeezed because every meeting hits expensive frontier models as the user base grows. The §1 routing move — frontier only for the summary, cheap models for the bulk — is precisely the lever that defuses this hangover.

---

## 6. Optimise the agent-to-agent surface: clean data, integrations, docs — prune bloat

**Idea.** When agents (not humans) are the consumers of your output, UI and design stop mattering and **data structures, integrations, and documentation** start mattering a lot. Without careful standards this surface bloats fast — gratuitous comments, dead context, sprawl — which degrades every downstream agent.

**Why it matters.** Agents read context literally and pay (in tokens and accuracy) for every bit of noise. Bloat in the shared surface is a tax on every agent that touches it. As Matan puts it: when agents are the buyers, the value of a clean API and a good context store goes _up_.

**Apply.**
- Invest in **clean schemas, well-defined integration points, and current docs** — the things agents actually consume.
- **Aggressively prune** anything an agent doesn't need: gratuitous comments, stale notes, redundant context.
- Enforce **context hygiene** with explicit standards, the way you'd enforce code style.

**In the wild.** This principle is Granola's _entire strategy_, stated almost word-for-word: "the value isn't the notes, it's making the knowledge locked inside conversations accessible to other systems — if an agent can pull context from every meeting, it makes better decisions." Granola is building the context substrate for agents. Superhuman Go's 800+ integrations are the other half of the surface — the connectors that let an agent reach across tools.

**Personalisation.** This is your memory store. Keep one fact per record, keep it structured, link related facts, and prune what's wrong or stale — a bloated memory makes a personalised agent _worse_, not more personal.

---

## 7. Build security in — code and action volume is outpacing safety

**Idea.** The amount of AI-generated code (and AI-taken action) is growing exponentially; security effort is not keeping pace. Matan expects significant incidents in the next couple of years, and notes the most adversarial behaviour hasn't even shown up yet.

**Why it matters.** A personalised agent has access to someone's life — messages, files, calendar, credentials. The blast radius of a compromised or manipulated agent is large and personal.

**Apply.**
- **Least-privilege tool access**: give each agent only the integrations and scopes it needs.
- **Human-in-the-loop gates** for destructive or outward-facing actions (sending, deleting, posting, paying).
- **Prompt-injection defence** on any content the agent ingests from outside (emails, web pages, documents can carry instructions).
- **Secret hygiene**: scanning, rotation, never inlining credentials into prompts or logs.
- Treat security as a first-class workstream that scales _with_ generation volume, not an afterthought.

**In the wild.** Every case study sits on highly sensitive data — Superhuman on the inbox, Granola on private meeting audio, Conversion on the CRM. Each is a large personal/commercial blast radius, and injection risk is real: an email Superhuman ingests, or a meeting transcript Granola summarises, is untrusted content that can carry instructions. Sensitive surface is the price of being useful — which is exactly why the gate belongs upstream.

---

## 8. Give agents end-to-end outcome ownership, and run an "agent ops" loop

**Idea.** The valuable role shifts from "do one narrow task" to a **GM-style owner of an end-to-end outcome**. Alongside it a new function emerges — **agent operations**: continuously creating and maintaining agents, finding the inefficient seams in a workflow, and "agentifying" them. A function that isn't proactively doing this is a bad sign.

**Why it matters.** Agents scoped to a single narrow step create handoff seams and orphaned work. Agents scoped to an outcome (with the human owning that outcome) close the loop. And agents are never "done" — they need an explicit maintenance loop or they rot.

**Apply.**
- Scope agents around **outcomes** ("keep the inbox triaged", "surface decisions that need me") rather than isolated micro-tasks.
- Assign clear ownership: a human owns the outcome the agent supports, end-to-end.
- Run a recurring **agent-ops review**: which steps are still manual and worth automating, which agents are underperforming, what's drifted. Make improving the agents someone's explicit job.

**In the wild.** Conversion's agents own the marketing-ops _outcome_ (campaigns shipped, leads routed), not isolated copy snippets — the full-stack-marketer idea productised. Superhuman Go is pitched as proactive ownership across apps (drafting, scheduling, fetching) rather than a single feature. And Granola's arc — meeting notetaker → enterprise AI app — is an agent-ops expansion: the same captured context, pointed at a bigger outcome.

**Personalisation.** The agent-ops loop _is_ how a personalised agent gets more personal over time — periodic reflection on what worked, what the user corrected, and what to encode into memory or behaviour.

---

## 9. Design for model churn — keep everything portable and eval-driven

**Idea.** Model releases will stop being discrete events ("GPT-3 → 3.5 → 4") and become continuous — models that quietly, constantly improve. Engineers already can't track every release, and shouldn't have to.

**Why it matters.** If your agent is coupled to one model's specific quirks, every improvement elsewhere is a migration you can't take. Portability lets you ride the curve instead of fighting it.

**Apply.**
- Keep prompts and architecture **portable** — avoid depending on undocumented quirks of one model.
- Maintain an **automated eval set** so you can qualify a new/cheaper/faster model quickly and adopt it with evidence, not vibes (this is what makes §1 routing safe to change).
- Re-evaluate the cost/quality/speed trade-off on a cadence, not just at crises.

**In the wild.** Superhuman and Granola both abstract the model away from the user, so swapping in a better/cheaper one is an internal change with no user-facing churn. That abstraction _is_ the portability — and it only stays safe if you have evals to qualify the swap.

---

## The through-line

The neat irony of the three ads: **all three are application-layer AI companies running on other people's models**, advertised in an episode arguing that durable value accrues to the model-agnostic application layer — not the models. Conversion abstracts models for marketing ops, Granola for meeting context, Superhuman for communication. Each is a live proof point for Matan's thesis — and each is exposed to his central risks: one model running away from the pack (kills the agnostic advantage), or the frontier-spend hangover (Granola's margin squeeze) catching up. Build on the app-layer side of that line, and route/abstract so neither risk owns you.

## Priority order

If you can only do three things first:

1. **§1 routing + §5 cost instrumentation** — stop overpaying and get visibility before usage scales. (Granola's margin problem is what you're avoiding.)
2. **§3 agent DevX / the factory** — the highest-leverage investment; everything downstream gets better.
3. **§7 security** — because a personalised agent's blast radius is your whole digital life.

Everything else (§2 outcomes, §4 review, §6 context hygiene, §8 ownership, §9 portability) compounds on top of those three.

---

## Applying this to your projects

Run this as a scorecard against each project — `merkle-email-hub`, `VTV`, `claude-code-second-brain` (Fredis), `AI/GERBONI`:

1. **Score each project 1–5 on the nine principles.** Be honest about where it's a 2.
2. **Find the two lowest scores per project.** Those are the cheapest wins.
3. **Check the priority order first.** If §1 (routing), §5 (cost visibility), or §7 (security) is weak, start there regardless of the other scores — they cap everything else.
4. **Write one concrete action per weak principle**, not a goal. "Put model calls behind an adapter and route transcription to a cheap model" beats "improve cost efficiency".
5. **Re-score next month.** Treat the scorecard itself as the §8 agent-ops loop.

A useful prior, not a verdict: a personalised-advisor project like Fredis tends to be strong already on §4 (human-in-the-loop gates), §6 (a structured memory store), and §7 (least-privilege + injection hooks), and weakest on §1 (per-task model routing) and §5 (per-task cost instrumentation) — the same gap Granola has. Email- and contract-shaped projects (`merkle-email-hub`, `VTV`) will live or die on §7 (untrusted inbound content = injection surface) and §6 (clean extraction schemas). But score them yourself before acting — that's the point of step 1.

**Next step (on your go-ahead):** I can read each repo and produce a filled-in scorecard with concrete per-project actions — a tailored pass rather than this generic loop.

---

_Sources for the case studies: [Conversion $28M Series A](https://theaiinsider.tech/2025/08/05/ai-marketing-startup-conversion-raises-28m-series-a-to-challenge-legacy-automation-tools/) · [Jasper naming history](https://research.contrary.com/company/jasper) · [Granola $125M / $1.5B](https://techcrunch.com/2026/03/25/granola-raises-125m-hits-1-5b-valuation-as-it-expands-from-meeting-notetaker-to-enterprise-ai-app/) · [Granola pricing](https://www.granola.ai/blog/ai-meeting-notes-pricing-granola-costs-less-alternatives) · [Grammarly acquires Superhuman](https://www.aol.com/news/exclusive-grammarly-acquires-email-startup-110833051.html) · [Grammarly rebrands to Superhuman](https://www.business-standard.com/technology/tech-news/grammarly-rebrand-superhuman-new-ai-tools-plans-price-125103000847_1.html)._
