# Agentic Application Architecture

TL;DR — layout + discipline for building LLM-backed products that don't melt under load, audit, or team growth. Vertical-slice folders, typed layer separation, vendor isolation, composable graphs, colocated tests.

## 1. Vertical-slice layout per capability

One folder per capability — an agent, a tool, a connector, a domain concept. All code for that slice lives together: its models, schemas, persistence, service, errors, routes, and tests. A new engineer can delete the whole folder and know nothing else breaks except what's explicitly imported from it.

```
<capability>/
├── models.py          # SQLAlchemy / ORM models
├── schemas.py         # Pydantic V2 request / response shapes
├── persistence.py     # repository role — DB access only, no business logic
├── service.py         # business logic + structured logging + transactions
├── exceptions.py      # capability-scoped errors (subclass AppError)
├── routes.py          # thin HTTP adapter
└── tests/             # unit + integration tests colocated
```

Jimmy Bogard's VSA (vertical-slice architecture) is the canonical source. Contrast with layered-by-role layouts (`models/` / `services/` / `routes/` top-level) which force cross-folder jumps for a single feature. In an agentic product the slice = "what does this tool/agent do", and everything it needs sits next to it.

## 2. Typed layer separation

Inside each slice, three layers — never mix their responsibilities:

- **Persistence** (`persistence.py`) — DB reads / writes only. No business rules. No HTTP. No LLM calls. Returns ORM rows or raises `PersistenceError`.
- **Service** (`service.py`) — business logic. Orchestrates persistence calls, makes LLM / tool calls, enforces rules, emits structured logs. Raises typed errors. Never touches HTTP request / response objects.
- **Routes** (`routes.py`) — thin HTTP adapter. Parses request → calls service → maps result or typed error to HTTP status. One try/except block mapping `AppError` subclasses to status codes. No business logic.

### AppError hierarchy

```python
class AppError(Exception):
    """Root type — all app-level errors subclass this."""
    http_status: int = 500

class ValidationError(AppError):
    http_status = 400

class NotFoundError(AppError):
    http_status = 404

class AuthorisationError(AppError):
    http_status = 403

class ExternalServiceError(AppError):
    http_status = 502  # upstream LLM / connector failed
```

Route handler catches `AppError`, reads `http_status`, returns structured error body. No bare `Exception` catches — unknown errors propagate to the framework handler.

Sources: FastAPI + SQLAlchemy + Pydantic V2 official docs; standard layered-architecture canon.

## 3. LLM-provider adapter pattern

Never call the vendor SDK from service code directly. Wrap it in an internal interface:

```python
# llm/provider.py
class LLMProvider(Protocol):
    async def complete(self, messages: list[Message], tools: list[Tool] | None = None) -> Completion: ...
    async def complete_stream(self, messages: list[Message]) -> AsyncIterator[Chunk]: ...

class AnthropicProvider:
    """Anthropic-specific adapter. Handles caching, retries, rate limits."""
    ...
```

Service code sees `LLMProvider`, not `anthropic.Messages`. Three wins:
1. **Swappable** — testing can inject a fake; a second vendor can be added without touching business logic.
2. **Centralised concerns** — prompt-cache control, retry policy, rate-limit back-off, token accounting, observability hooks all live in one place.
3. **Prompt caching by default** — the adapter enforces cache-control placement on system prompts and tool definitions so every caller gets warm-cache economics without remembering.

## 4. Blueprint / node composition

Multi-step agentic flows compose from **typed nodes** arranged in a graph. Each node is a small, pure-ish unit (input type → output type) that does one thing — classify, retrieve, summarise, call a tool, branch on a condition.

LangGraph is the canonical reference for the pattern. The graph definition is data (a blueprint); the nodes are functions; the runtime walks the graph and passes state between nodes. Three properties that matter:

- **Typed state** — the shared state object is a Pydantic model, not a dict; node signatures are enforced by the type checker.
- **Conditional edges** — a router node inspects state and picks the next node. Deterministic when the decision is deterministic; LLM-routed only when the problem is genuinely open-ended.
- **Persisted checkpoints** — long-running flows snapshot state between nodes so a restart resumes cleanly.

For runtime orchestration and the decision of *when* to use a graph vs a simple loop, see `agentic-orchestration-patterns.md` §3 (the four levels).

## 5. Connector pattern — external integrations

All third-party integrations live under `connectors/<service>/` with a consistent adapter interface:

```
connectors/
├── __init__.py
├── slack/
│   ├── client.py       # authenticated API wrapper
│   ├── schemas.py      # Pydantic shapes for the service's payloads
│   ├── exceptions.py   # connector-scoped errors
│   └── tests/
├── github/
│   └── ...
└── calendar/
    └── ...
```

Contract per connector:
- Stateless client factory — takes credentials at construction, no global singletons.
- Typed method signatures — callers pass / receive Pydantic models, not raw JSON.
- Connector-specific errors subclass `ExternalServiceError` so they map to 502 uniformly.
- Tests colocated — one fixture file replaying captured HTTP responses.

Agents reference connectors by an allowlisted capability set, never by direct import from service code paths that shouldn't own the integration.

## 6. Structured logging convention

Event names follow `domain.action_state`:

```python
log.info("llm.complete_start", model=model, prompt_cache_id=cache_id, token_budget=budget)
log.info("llm.complete_success", duration_ms=duration, input_tokens=in_tok, output_tokens=out_tok)
log.warning("llm.complete_rate_limited", retry_in_seconds=delay)
log.error("llm.complete_failed", error_class=type(exc).__name__)
```

Three parts, separated by dots:
- **domain** — subsystem (`llm`, `persistence`, `connector.slack`, `agent.research`).
- **action** — verb (`complete`, `fetch`, `write`, `retry`).
- **state** — `start` / `success` / `failed` / `skipped` / specific failure mode.

Use `structlog` with a JSON renderer in production, console renderer in dev. Field names follow OpenTelemetry semantic conventions where they exist (`http.method`, `db.statement`, etc.). Request-scoped correlation IDs get injected via context-var so every log line from one request shares an ID.

## 7. Observability hooks

Beyond structured logs, three surfaces:
- **Traces** — OpenTelemetry spans around service-method calls and LLM completions. Span attributes carry model, token counts, cache-hit rate, tool names invoked.
- **Metrics** — counters for `llm.completions.total`, `agent.runs.total`, histograms for `llm.latency_ms`, `agent.turn_count`. Exported via Prometheus or OTLP.
- **Correlation** — one correlation ID per top-level request flows through all downstream LLM calls, tool invocations, and DB writes. Enables tracing one user turn across sub-agents.

Put trace / metric initialisation in `observability/` — never inline in service code. Service code calls typed helpers (`observe_llm_call(...)`), not the OTel API directly.

## 8. Feature lifecycle

Build order for a new capability — one file at a time, each commit runnable:

1. `schemas.py` — Pydantic request / response shapes. No business logic.
2. `models.py` — DB model if the feature persists state.
3. `persistence.py` — repository methods + their tests.
4. `service.py` — business logic + its tests (mock the LLM adapter, not the service).
5. `exceptions.py` — typed errors as they become needed.
6. `routes.py` — HTTP surface + route tests that exercise the stack.
7. DB migration — Alembic revision for the new model.
8. Registration — wire the route into the app router, the service into DI.

This order means every commit after step 3 compiles and tests pass on its own — no "stub everything first" anti-pattern.

## 9. Per-module Claude guidance

Every significant module carries a local `CLAUDE.md` — short, module-scoped notes that an editor would want in context when touching files under that directory:

```
<capability>/CLAUDE.md      # invariants, gotchas, links to related slices
connectors/<service>/CLAUDE.md   # auth model, rate-limit behaviour
llm/CLAUDE.md               # adapter contract, cache-control conventions
```

Keep them ≤40 lines. They describe invariants and cross-cutting concerns, not what the code does (well-named code already shows that). The top-level `CLAUDE.md` stays the big-picture orientation; module-level files handle the local detail.

## 10. Cross-links

- **Runtime behaviour** — this file describes the backend shape. For the agent-harness / orchestration levels / memory patterns that shape hosts, see `agentic-orchestration-patterns.md`.
- **Guardrails** — every LLM call and tool invocation needs the layered defenses in `../../security-engineering/references/agent-guardrails.md` (injection, HITL, destructive-command guard, memory provenance).
- **Evals** — before escalating a capability from L1 (single call) to L2 / L3 / L4 (multi-step, orchestrator, autonomous), prove the current level works via `../../data-and-experimentation/references/llm-evals.md`.

## 11. Anti-patterns

- **Business logic in routes.** Routes parse / validate / call service / map error. Nothing else. If you find yourself writing an `if` on domain state in a route handler, that's service code.
- **Persistence with side effects beyond the DB.** Repositories don't send notifications, don't enqueue background jobs, don't call HTTP. They read and write rows. Side effects belong in services, which also give transactions a clean fit.
- **Agent code importing the vendor SDK directly.** Every `import anthropic` outside the adapter is a regression — it centralises nothing, hides token cost, and breaks the swap-out invariant.
- **Skipping the eval harness.** "It worked when I tried it" is not an eval. No capability ships to a user without a regression eval (see `llm-evals.md`).
- **Shared state across slices.** Slices talk via typed events / queues / service interfaces, never by reading each other's tables or importing each other's models. The cost of the indirection is worth the isolation.
- **Global singletons for connectors.** Pass clients as dependencies. Global state wrecks testing and forbids multi-tenant work later.
