---
name: engineering
description: Hands-on engineering — system design, ADRs, C4 / PlantUML / Mermaid diagrams, microservices-vs-monolith, dependency analysis, scalability planning (senior-architect); REST / GraphQL API design, PostgreSQL optimisation, auth flows, Node.js/Express/Fastify patterns, DB migrations, load testing (senior-backend); Jest + React Testing Library + Playwright + MSW test generation, coverage analysis, E2E scaffolding (senior-qa); red-green-refactor TDD across Jest / Pytest / JUnit / Vitest / Mocha with fixture + mock generation (tdd-guide). Use when user says "design architecture", "ADR", "C4", "microservices vs monolith", "choose a database", "scalability", "REST API", "GraphQL", "optimise queries", "authentication flow", "Node.js patterns", "generate tests", "test coverage", "scaffold E2E", "Playwright", "Jest", "TDD", "red-green-refactor", "write unit tests".
---

# engineering

TL;DR — hands-on engineering from system design to test generation. Four references: architecture, backend, QA, TDD. Cross-reference each other — an ADR from `architecture.md` often needs tests from `tdd.md` or `qa-testing.md`.

## Routing table

| Trigger | Reference |
|---|---|
| "design architecture", "ADR", "C4", "microservices vs monolith", "dependency analysis", "choose a database", "scalability", "system design review" | `references/architecture.md` |
| "REST API", "GraphQL", "optimise queries", "auth flow", "Node.js", "Express", "Fastify", "DB migration", "load test", "backend security hardening" | `references/backend-systems.md` |
| "generate tests", "unit tests", "test coverage", "scaffold E2E", "Playwright", "Jest", "React Testing Library", "MSW", "test fixtures" | `references/qa-testing.md` |
| "TDD", "red-green-refactor", "Pytest", "JUnit", "Vitest", "Mocha", "test mocks", "write a test first" | `references/tdd.md` |

## Shared assets

- `_shared/lanes.md` — lane-specific stack templates live in `product-shape/mvp-architect.md` but engineering decisions reference them back.
- `_shared/draft-path-convention.md`

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/engineering/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

For engineering in particular: never run state-mutating DB operations, never execute migrations live, never deploy. Draft the migration SQL + ADR — Linards runs it.

## References

| File | Load when |
|---|---|
| `references/architecture.md` | System design, ADRs, diagram generation, dependency analysis |
| `references/backend-systems.md` | API / DB / auth implementation |
| `references/qa-testing.md` | React/Next.js test generation, coverage analysis, E2E |
| `references/tdd.md` | TDD discipline across frameworks + mock / fixture generation |
| `references/*/scripts/` | Test generator, fixture generator, tech-debt analyzer, etc. |

## Anti-patterns

- `senior-architect`-style abstract diagrams for a one-person pre-revenue product. Keep the first ADR to "decisions I'd regret flipping" — pick the DB, pick the framework, pick the deploy target. More ADRs when a second person joins.
- Running the QA skill without a concrete test target. This skill generates tests *for* existing components; asking it to design a test strategy before code exists is the wrong direction — use `architecture.md` first.
- Generating tests that mock the module under test. Tests must exercise real behaviour; mock at trust boundaries only.
