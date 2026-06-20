# MVP Architect

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Output a stack brief that names the minimum-viable stack per lane, a build-vs-buy grid, and a first-commit checklist (literal `git init` + `.env.example` + first file + first test + first deploy target).

## Frameworks applied (sources for follow-up authoring)

- **Eric Ries *Lean Startup* MVP** (2011) — build-measure-learn, smallest iteration that produces validated learning.
- **Henrik Kniberg MLP** (2016) — cross-ref with `idea-validation/minimum-lovable-product.md`.
- **Simon Wardley Mapping** (open source) — visibility + evolution axes; tells you what to build vs buy based on component maturity.
- **Simon Brown C4 model** — context / container / component / code levels; for diagrams (routes via `engineering/`).
- **Amy Hoy, Sales Safari** (Stacking the Bricks) — audience research pre-architecture (Email-Hub-specific gate).

## Three pre-built stack templates

### B2G optimisation (VTV)
- **Build:** route optimisation engine (OR-Tools or OptaPlanner), data-ingestion pipeline.
- **Buy:** mapping tiles (Mapbox / Maplibre), auth (Auth0 / Clerk), telemetry (Grafana + PostgreSQL / TimescaleDB).
- **Frontend:** Streamlit or Dash for ops dashboard; React for public-facing demo.
- **Backend:** FastAPI + PostGIS + OR-Tools.
- **Deploy:** single-region EU; compliance: GDPR + LV data-residency considerations.

### B2C ride-hailing (Cab)
- **Build:** matching engine, surge logic.
- **Buy:** maps (Mapbox), auth (Supabase), payments (Stripe / Adyen / LV-specific rails), messaging (FCM / APNs).
- **Frontend:** Flutter (cross-platform single codebase).
- **Backend:** FastAPI or Go + PostGIS + Redis for realtime.
- **Deploy:** EU region with local-LV scaling plan.

### MarTech SaaS (Email Hub)
- **Build:** the email-workflow logic — this is the whole product.
- **Buy:** Next.js frontend, Drizzle ORM + Postgres, Stripe, email-sending infra (Postmark / Resend / SES).
- **Deploy:** Vercel or similar.
- **IP resolved** — Email Hub is owned outright (2026-06-16); no IP gate applies.

## Structure (to be filled)

1. **Lane pre-load + stack-template selection** — load `_shared/lanes.md`.
2. **Email Hub IP** — resolved (owned outright, 2026-06-16); no IP gate applies.
3. **Sales Safari pre-gate (Email Hub)** — require `Fredis/Memory/research/email-hub/safari/` notes present.
4. **Build-vs-buy grid** — each component tagged with Wardley evolution stage (genesis / custom / product / commodity).
5. **First-commit checklist** — `git init`, `.env.example`, first file, first test spec, first deploy target.
6. **Kill criteria per lane** — "if no weeknight-slice demo by <date>, kill" → gate YAML.
7. **Atis £1k gate** — would Atis bet the stack choice is defensible?
8. **Hand-offs** — `engineering` for ADRs + C4 diagrams; `technical-leadership` (startup-cto voice) for the final brief read; `launch-governance/launch-wedge` for distribution.

## Ports / attribution

- No upstream port — de novo composite authored against primary-source canon (Ries, Kniberg, Wardley, Brown, Hoy).
