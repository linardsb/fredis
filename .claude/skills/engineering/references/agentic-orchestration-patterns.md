# Agentic Orchestration Patterns

TL;DR — how agents are harnessed, orchestrated, remembered, and specialised. The runtime shape of an agentic product. Companion to `agentic-application-architecture.md` (backend shape) and `../../security-engineering/references/agent-guardrails.md` (defense layer).

## 1. Agent harness anatomy

A harness is the runtime scaffold around an LLM that makes it behave like an agent rather than a chatbot. Whether you build on Claude Code, the Anthropic Agent SDK, or roll your own, the same surfaces recur:

- **Tool mediation layer** — adapter between the model's tool-call output and real code. Validates tool args against schema, routes to the right implementation, catches exceptions, returns results in the model's expected shape.
- **Permission modes** — how much autonomy the harness grants. Canonical trio: `default` (ask on each significant action), `accept-edits` (auto-approve file edits but ask on shell / network), `bypass` (fully autonomous, for trusted automated flows). Pick the lowest mode that unblocks the work.
- **Hook system** — lifecycle callbacks: `SessionStart` (inject context), `PreToolUse` (validate / block / log), `PostToolUse` (observe / transform), `PreCompact` (persist critical state before compaction), `Stop` (final cleanup). Hooks execute deterministically around LLM turns.
- **Interrupt handling** — user or supervisor can preempt mid-turn. Harness must flush partial state and return cleanly. For long-running tool calls, the harness interposes a cancellation point.
- **Session state lifecycle** — conversation history, tool-call history, per-session scratchpad. Persisted so a process restart resumes the same conversation.
- **Prompt caching** — cache-control placement on system prompt + tool definitions + static context. 5-minute TTL is the hard economics: sleeps / polls under 5 min keep the cache warm; sleeps over 5 min burn a cache miss. The harness owns cache-control placement so callers don't think about it.
- **Context-window compaction** — automatic summarisation of older turns when the window fills. PreCompact hook runs first so load-bearing state gets persisted before the summary.

## 2. Four levels of agentic orchestration

Anthropic's "Building Effective Agents" taxonomy. Escalate reluctantly — higher levels trade predictability for capability, and every level adds a failure mode.

### L1 — Augmented LLM

Single call. The model has tools, structured output, retrieval. No iteration, no self-direction. One request → one response.

- **Shape**: `complete(messages, tools)` returns `(text, tool_calls)`; if tool calls happen, you run them and feed results back in one more call (≤2 turns). That's the ceiling at L1.
- **When**: the task is one reasoning step plus retrieval / computation. Summarise a document. Extract fields from a form. Classify into one of N buckets.
- **Economics**: cheapest, most predictable, easiest to eval. Every agentic product starts here.

### L2 — Workflow

Deterministic control flow; LLM only at nodes. Three canonical shapes:

- **Prompt chaining** — output of step 1 → input of step 2. Used when a big task decomposes into a fixed sequence (outline → draft → revise).
- **Routing** — a classifier LLM picks the next prompt template or downstream specialist. The graph is static; the edge chosen is dynamic.
- **Parallelisation** — fan out the same task over N inputs, aggregate. Embedding a batch, rating N candidates.

Control flow is code, not the model's choice. Graphs are small, debuggable, replayable. Most "should we build an agent" questions are actually L2 questions.

### L3 — Orchestrator-worker

Planner LLM decomposes a task into subtasks → specialist workers execute → aggregator assembles. Control flow is dynamic but bounded: the orchestrator generates a plan upfront, workers run it, no arbitrary loops.

- **Shape**: orchestrator prompt returns a structured plan (list of `(subtask, worker_type)`). Runtime dispatches each subtask to the named worker (sub-agent with a scoped tool allowlist). Aggregator prompt composes worker outputs into the final answer.
- **When**: the task is decomposable but the decomposition is content-dependent. Research a topic across N angles. Review a PR across security / perf / style.
- **Cost**: N worker calls + planner + aggregator. Token budget needs a ceiling enforced in code.

### L4 — Autonomous agent

Full tool-use loop. Model plans, acts, observes, re-plans. Often paired with an evaluator-optimizer (second model critiques the first's output and loops until the critique passes). Highest leverage, highest variance.

- **When**: open-ended tasks where decomposition is itself the hard part. Long-horizon research. Debugging unfamiliar codebases. Multi-day tasks with no fixed script.
- **Protection**: hard turn caps, hard token caps, HITL gate on any state-mutating tool, tight eval harness. Without these, L4 is a way to lose money and trust simultaneously.

### Decision rule

Start at L1. Escalate only when evals (see `../../data-and-experimentation/references/llm-evals.md`) show the current level saturates. A successful L1 that covers 80% of cases beats a flashy L4 that covers 90% but fails unpredictably on the remaining 10%.

## 3. Memory patterns

An agentic product has at least three memory scopes — each with different lifetime, access control, and trust assumptions.

### Short-term / session memory

- Conversation history + tool-call history, live in process memory or a session store keyed by session ID.
- **Rolling window** — keep the last N turns verbatim.
- **Turn-capped compaction** — when N is hit, summarise the oldest turns into a compact description; keep the latest few turns verbatim. Most harnesses run this automatically.
- **Persistence** — on session end, write the full transcript (not just the summary) to durable storage so sessions resume cleanly and audit is intact.

### Long-term memory

- Survives sessions. Vector store (embeddings + ANN index) + keyword search (FTS / tsvector / BM25). Hybrid search combines the two.
- **Write policy** — what gets promoted from session to long-term? Explicit user ask ("remember this"), structured decisions, reusable lessons. Never raw transcripts.
- **Forgetting policy** — TTL on low-signal entries; relevance decay so old unused memories surface lower; a manual quarantine path for entries later judged wrong.
- **Provenance stamping** — every entry carries source + timestamp + author so downstream readers can verify. Critical for the injection-defense story in `../../security-engineering/references/agent-guardrails.md`.

### Cross-agent memory

- Shared store read by multiple agents. Three patterns:
  - **Blackboard** — shared workspace any agent can read / write. Simplest; weakest isolation.
  - **Typed message-passing** — agents communicate via a typed queue; each message is a structured record with sender + recipient + payload. Strong isolation; higher friction.
  - **Shared indexed store** — read-only shared knowledge base with a write-path gated by a trusted curator (human or constrained agent).
- **Trust boundary** — reads from cross-agent memory are external data from the reader's perspective. Apply the same injection defenses as any third-party input.

### Context-window management

- **Auto-compaction hooks** fire before the limit: summarise older turns, offload high-signal snapshots to a memory file on disk, persist the long tail of the conversation.
- **Memory-file offload** — some harnesses support a file that persists across compactions (`NOTES.md`, `MEMORY.md`). Treat it like a pre-session context injection: always present, costs tokens every turn, prune it.
- **Per-turn accounting** — log input / output / cache-read / cache-write tokens every turn; surface in traces. Compaction strategies are only tunable with numbers.

## 4. Specified sub-agents with specified skills

The right way to scale an agentic product is **more specialised agents**, not one giant agent with every tool attached.

### The skill model

A skill is a directory:

```
<skill-name>/
├── SKILL.md        # YAML frontmatter (name + description) + markdown body
├── references/     # deep content loaded on demand
├── assets/         # templates, schemas, fixtures
└── scripts/        # executables the skill invokes
```

Progressive disclosure across three levels:
- **Metadata** (`name` + `description`) — always in context; the router reads it to decide whether to load the skill.
- **Body** (`SKILL.md` markdown) — loaded when the skill triggers; routing table, primer, guardrails.
- **Resources** (`references/*`, `assets/*`, `scripts/*`) — loaded on demand by the body.

This keeps the always-on context budget small (one-line descriptions per skill) while making deep content available when relevant.

### Sub-agent spawning

- **`subagent_type` parameter** — on an Agent-tool surface the caller names the sub-agent role: `research`, `plan`, `execute`. Each type has a scoped system prompt + tool allowlist + (optional) skill subset.
- **Isolation** — each sub-agent gets its own context window and its own history. Parent sees only the summary the sub-agent returns.
- **Independent work rule** — spawn sub-agents in parallel when the work is independent; spawn sequentially when later work depends on earlier results.

### Capability manifests

Each skill's `description` field enumerates trigger phrases the router matches against — "user says X, Y, Z". Good manifests are enumerative rather than descriptive. Ambiguous triggers collide: two skills mentioning "strategy" both activate, and the router has to disambiguate. Prefer specific phrases ("OKR cascade", "threat model") over generic ones ("strategy", "security").

### A2A surfaces — MCP + plugins

- **MCP (Model Context Protocol)** — a standard way to expose tool + data surfaces to any MCP-speaking agent. An MCP server declares tools and resources; an MCP client (Claude Code, Agent SDK, or another MCP-compatible host) consumes them. Lets one agent's capabilities become another agent's tools without coupling.
- **Skill registries + plugins** — for larger products, skills can be packaged as plugins that load conditionally. Reduces the always-on context cost when only a subset is relevant for the current session.
- **Agent-to-Agent orchestration** — one agent host runs the conversation, spawns sub-agents, and mediates MCP tool calls on their behalf. Keeps one source of truth for permissions, logging, and session state.

## 5. Cross-links

- **Backend shape** — see `agentic-application-architecture.md` for the VSA layout, typed layers, and adapter pattern that host everything above.
- **Guardrails per level** — each orchestration level needs matching defenses; see `../../security-engineering/references/agent-guardrails.md`. L1 needs injection defense + HITL on state-mutating tools; L3 / L4 add per-sub-agent threat models + memory-provenance checks.
- **Eval-gated escalation** — move from L1 → L2 → L3 → L4 only when `../../data-and-experimentation/references/llm-evals.md` shows the current level's failure modes justify the jump. Escalating without evals is how teams build unreliable autonomous systems.

## 6. Anti-patterns

- **Starting at L4 without an L1 baseline.** You'll have no idea whether the autonomy is doing the work or the model is.
- **Sharing memory without trust boundaries.** An agent reads a poisoned long-term entry, summarises it into a new one, and the poison propagates. Stamp provenance; treat cross-agent reads as external data.
- **Sub-agents without scoped skill descriptions.** Router misfires. Two sub-agents both claim "analysis" triggers; the wrong one runs.
- **Orchestrator invoking workers sequentially that could run in parallel.** Latency adds up; token budgets get eaten by idle time. Fan out when the work is independent.
- **Cache-cold 300-second sleeps.** Cache TTL is 5 min. A 300 s sleep is the worst of both worlds — you pay the miss without amortising. Drop to 270 s (stay warm) or commit to 1200 s+ (buy a longer wait).
- **Ambiguous capability manifests.** "General analysis skill" collides with every other skill. Make descriptions specific and trigger-phrase-enumerative.
- **No turn / token cap at L4.** An autonomous loop with no ceiling is an unbounded bill. Always enforce in code.
