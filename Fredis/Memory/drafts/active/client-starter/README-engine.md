# client-starter

Reusable template for standing up a saulera client's second brain — so each engagement
**configures an instance** instead of rebuilding one from scratch.

Lives **gitignored inside the saulera repo**: it's a separate delivery engine, not part of
the marketing site, and shouldn't enter the site's git history.

## What's here now

- `.agent/plans/onboarding-interview.md` — the client intake. 172 questions, tier-tagged
  (Tier 1 Core / Tier 2 Business depth / Tier 3 Deep personal), generalised from the original
  Fredis onboarding and stripped of any one person's answers. Run the relevant tier(s) per
  client type (SMB → Tier 1; founder/agency → Tier 1+2; full brain → all three).

## The design — engine vs config

- **Engine (shared, build once):** runtime loops (heartbeat, reflection, synthesis), hooks,
  the generic skill set, vault structure. Clients track this from upstream — they never fork it.
- **Config (per client):** the filled-in interview → their memory files; their `.env` (their
  keys, MCP servers, ESP, CMS); their channel routing; a small client-specific skill pack;
  their own vault content.

This split is what lets an engine improvement reach every client on a pull, instead of being
re-patched in N forks.

## Still to seed (not built yet)

- Blank `Fredis/Memory/` templates (the 5 memory files as fill-from-interview placeholders)
- The `.claude/` engine + the generic-skill subset (split from the personal-skill pack)
- A per-client `.env` template
- A provisioning runbook: interview → generate memory files → wire `.env` → deploy

Strategy + full context: `business/client-second-brain/productisation-strategy.md`.
Working engine to copy from: the `claude-code-second-brain` repo.
