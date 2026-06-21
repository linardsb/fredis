# Client Second-Brain — saulera offering

How saulera turns its own Fredis build into a repeatable client product: give each client
their own second brain by **configuring an instance**, not rebuilding one from scratch.

## What's in this folder

- **`productisation-strategy.md`** — the full context: the strategic finding, the LLM-agnostic
  position, the two productisation shapes (template now / SaaS later), the engine-vs-config
  architecture, the hard parts, and the services-as-paid-R&D sequencing.
- **`onboarding-interview.md`** — the client intake instrument. 172 questions, tier-tagged
  (Tier 1 Core / Tier 2 Business depth / Tier 3 Deep personal). Run the relevant tier(s) per
  client type — SMB gets Tier 1; a founder gets all three.

## One-line

saulera already builds bespoke, model-agnostic agents per client — so **each engagement is a
paid prototype of "build your own second brain."** Extract the common 80% into a reusable
template after the first few clients; services fund and de-risk the product. Email Hub stays
the primary product bet.

## How this relates to the gitignored `client-starter/`

- **This folder (`business/client-second-brain/`)** = strategy + the blank intake template.
  No secrets — safe to track in git.
- **`client-starter/` (gitignored, separate)** = the runnable engine + per-client config
  (`.env`, keys, MCP servers, client vault). Gitignored because it holds secrets/client data.
  Not built yet — see the roadmap in `productisation-strategy.md`.

## Related saulera docs

- `../saulera-ai-native-agency-plan.md` — the 90-day services launch plan
- `../saulera-offer-one-pager.md` — the client offer + pricing
