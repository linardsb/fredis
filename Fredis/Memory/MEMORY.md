# MEMORY.md - Long-Term Memory

_Curated, important memories that persist across sessions. Daily logs capture everything; this file captures what matters._

## Key Decisions

_(Pre-revenue stage — formal locked-in decisions still to be made. Likely first entries will land as Email Hub commercial model, UK Ltd registration, and pricing per service line. See active TBDs in `USER.md → Service Lines`.)_

- **4-loop memory architecture (2026-04-21).** Capture (memory_flush) → Consolidate (memory_reflect) → Dream (weekly synthesis) → Recall (auto-retrieval in chat + heartbeat). Recall is the highest-visible win — surfaces old decisions/drafts contextually. Synthesis drafts to `drafts/active/memory-synthesis/YYYY-Www.md` for human approval; never auto-writes to MEMORY.md. `[impact: high, status: decided]`

- **Fredis cut over to VPS runtime (2026-04-21).** All scheduled services now run on VPS via systemd: `secondbrain-chat`, `fredis-heartbeat.timer` (2h), `fredis-reflect.timer` (daily 08:00), `fredis-synthesis.timer` (Sun 08:00), `deps-audit.timer` (Mon 09:00), `fredis-vault-sync.timer` (2 min). Mac heartbeat + reflect plists unloaded. Code flow: Mac push → GitHub Action → `deploy.sh` on VPS (workflow `paths-ignore`s `Fredis/**` + `docs/**` + `**/*.md`). Memory search via SSH tunnel: local 5433 → remote 5432 (Mac's local Postgres owns 5432). `[impact: high, status: decided]`

- **Heartbeat priority-1 whitelist + daily summary timer (2026-04-22).** Priority-1 prompt rewritten: real-person emails, GitHub @mentions, Slack DMs, calendar conflicts, overdue CRM tasks always surface; marketing/newsletters/dependabot/digests silenced. Motivated by the 09:38 customer-email miss that day. New `--summary` CLI flag bypasses HEARTBEAT_OK + active-hours gate; `fredis-summary.timer` fires 17:00 BST daily on VPS for end-of-day wrap. Commit `2c66101`. `[impact: med, status: decided]`

- **CLAUDE.md split into nested pattern (2026-04-22).** Root `/CLAUDE.md` trimmed from ~460 → ~100 lines (Advisor Mode, Skill Stack, Memory Layout, Hooks, Architecture pointers). Subsystem detail moved to `.claude/scripts/CLAUDE.md` — dev-facing, invisible to Fredis SDK callers that set `cwd=PROJECT_ROOT`. Net saving ~5.5k tokens per heartbeat tick. `[impact: med, status: decided]`

- **No git-history scrub for rotated Postgres password (2026-04-22).** Rotation alone invalidates the credential since repo is private. History scrub only triggers if repo ever goes public. `docs/phases.md` text scrub still pending but non-urgent. `[impact: low, status: decided]`

- **CRM switch: Monday.com → HubSpot Free + GitHub Projects (2026-04-23).** Linards cut Monday.com entirely — no data migration, fresh HubSpot workspace. Commit `bb38524` shipped the migration; HubSpot schema bootstrapped with 9 custom properties (4 contact, 3 company, 2 deal). Known HubSpot Free constraint: 1 deal pipeline cap → use default pipeline, rename stages in UI; `overdue_invoices` heartbeat scan blocked until stages renamed to match plan spec (`Inbound → Discovery → Proposal → Signed → Kickoff → Delivery → Invoice → Post-delivery`). `MONDAY_*` env vars removed. Engineering stays in GitHub Projects, not HubSpot. `[impact: high, status: decided]`

- **HubSpot advisor-mode boundary codified (2026-04-23).** Internal CRM mutations (create/update/archive records, log past engagements, move deal stages) are OK to execute directly from Slack chat. Outbound emails, quotes/invoices, customer-facing ticket comments route to `drafts/active/` — never auto-sent. Plan at `.agent/plans/hubspot-slack-writes.md`. All 5 write operations smoke-tested via Slack on 2026-04-23 (create contact, add note, create deal, move stage, archive). Tickets skipped for v1; archive-only (no hard delete). `[impact: med, status: decided]`

- **HubSpot tickets = Fredis Review Queue (2026-04-23).** Un-deferred the tickets-v1 skip. Pipeline `Fredis Review` (repurposed the default "Support Pipeline" — HubSpot Free caps tickets at 1 pipeline) with 5 stages: Drafted → In review → Needs send → Actioned / Rejected. 7 custom properties: lane, skill_source, draft_path, urgency, slack_thread_url, heartbeat_run_id, dedupe_key. Every actionable heartbeat detection (overdue invoice, silent urgent contact, stale deal >30d, breached kill-gate) creates a ticket + posts `[DRAFT] ...` to `#hubspot` in Slack. DM Fredis "what's in my queue" or use `hubspot queue` CLI to review. Flag-gated on `HUBSPOT_TICKETS_ENABLED`. Plan: `.agent/plans/fredis-hubspot-tickets-slack.md`. `[impact: high, status: decided]`

- **All integration channels promoted to Sonnet (2026-04-23).** `#gmail`, `#calendar`, `#asana-board`, `#hubspot`, `#g-drive`, `#g-sheets`, `#g-docs`, `#github` moved from Haiku to Sonnet in `channel-routing.yaml`. Haiku tier now empty. Rationale: Haiku consistently failed multi-rule prompt adherence (ignored draft-routing, didn't search-before-asking). Cost increase (~$0.02 → ~$0.10/msg) accepted for reliability. Commit `d3b6069`. `[impact: med, status: decided]`

- **Gmail drafts route to Gmail API, not the vault (2026-04-23).** Fix: new email drafts call `gmail_create_draft` so they land in Linards's Gmail Drafts folder; `drafts/active/` is reserved for non-email outbound only. Companion: Fredis now searches Gmail (`from:<name>`) before asking "who is X?" Commits `e499ccbb` + `990a0e9`. `[impact: med, status: decided]`

- **Topic display in Slack threads (2026-04-23).** `_derive_topic` in chat engine prepends `*Topic: <subject>*` to Fredis's first reply in any thread, regardless of model tier. Commit `dddca87`. `[impact: low, status: decided]`

- **Phase 12 starter-pack stays 4 standalone skills (2026-04-23).** `draft-reply`, `meeting-notes`, `client-log`, `uk-latvia-context` kept separate rather than consolidated. Rationale: lazy-loaded descriptions cost <1% of context; trigger-phrase discovery matters per skill; line counts (148–376) within existing precedent. Commit `e89851b`. `[impact: low, status: decided]`

- **Heartbeat code path promoted Haiku → Sonnet (2026-04-24).** Separate from the 2026-04-23 chat-routing promotion — `heartbeat.py:741` was still on Haiku and stripping external data on timeouts. Commit `5069d4e`. `[impact: med, status: decided]`

- **Asana fully scrubbed from Fredis (2026-04-24).** ~1164 lines deleted across ~44 files (live code commit `78f7811`, docs/tests `eb64b9b`). Deps, hooks, config templates, channel-routing, vault references all removed. HubSpot is now the sole CRM/task layer. `MONDAY_*` env-var cleanup remains a separate Open Watch Item. `[impact: med, status: decided]`

- **Ship-pillar second source = Option C (2026-04-24).** Gmail-to-client-domain OR HubSpot engagement logged against a client company. Chosen over B (ticket actioned — too narrow), D (deal stage — too sparse), A (Gmail only — misses calls/meetings). Commit `c426aea`. New `integrations/habit_signals.py` (~170 LoC) replaces inline `len(github_commits) > 0` proxy. Module activates only when at least one HubSpot company carries `engagement_type=retainer` or `project`; currently silent because no clients tagged. The full four-pillar Phase-6 Gap-1 module remains deferred — only Ship-pillar second source shipped today. `[impact: med, status: decided]`

- **Audit-conventions rule codified in CLAUDE.md + memory_reflect (2026-04-24).** Four pre-flight checks (git log since doc write, live CLI verification, full daily-log grep, skill `references/*.md` reads) required before any audit claims "open / pending / not done". `memory_reflect.py` prompt now auto-promotes scope-decision language with `[status: killed]` or `[status: decided]` tags. Regression test added in `test_memory_reflect.py`. Commit `ada604c`. Drove four MEMORY.md backfills in `76bd1b6` (WhatsApp killed, Discord/Linear killed, Gap 1 deferred, Gap 2 deferred). Root cause: stale plan docs in `.agent/plans/` were treated as current state instead of historical snapshots, wasting tokens across four correction rounds. `[impact: high, status: decided]`

- **HubSpot GBP currency enabled on portal 144478060 (resolved 2026-04-24).** Linards added GBP via HubSpot UI → Settings → Account Setup → Currency. Existing CLI code now works as-is with `--currency GBP`. `[impact: low, status: resolved]`

- **Scope decision: WhatsApp integration NOT being built (decided 2026-04-18, backfilled 2026-04-24).** Dropped in Phase 4 plan (daily log 2026-04-18: "Discord + WhatsApp out of scope") and reaffirmed 2026-04-20 ("Explicitly out of scope for Phase 7: WhatsApp adapter"). WhatsApp remains a preferred comms channel for some contacts (Atis, Juris Ņefedovs, Gavin Hughes — see USER.md) but no Fredis integration will be built. **Do NOT list as a gap or propose as a future phase in audits.** If Linards reopens, he will say so explicitly. `[impact: med, status: killed]`

- **Scope decision: Discord + Linear integrations NOT being built (decided 2026-04-18, backfilled 2026-04-24).** Both appeared in the original PRD. Phase 4 plan explicitly dropped Discord alongside WhatsApp; Linear hasn't been requested since the PRD. Treat both as closed. **Do NOT list as gaps in audits.** `[impact: low, status: killed]`

- **Scope decision: Phase-6 Gap 1 full habit_signals module DEFERRED (decided 2026-04-20, backfilled 2026-04-24).** Only the `ship_signal()` helper in `integrations/github_api.py:201` was shipped. The full four-pillar signal module (Frontier from build-repo activity + daily-log keywords, Ground/Body from calendar keywords, 18:00 self-report fallback, Read never auto-ticks) was deferred — daily log 2026-04-20: "Gap 1 deferred — revisit after living with 2+3 for a week." Minor tweaks if Linards asks (wire the existing helper into `heartbeat.py:1545`; filter `vault:` commits from `recent_commits()`) are fair game. **The full module stays closed — do NOT re-propose as an audit gap.** `[impact: med, status: decided]`

- **Scope decision: Phase-6 Gap 2 Slack draft reconciliation DEFERRED (decided 2026-04-20, backfilled 2026-04-24).** Original Phase-6 plan scoped automatic `drafts/active/` → `drafts/sent/` move for `type: slack` drafts when the owner replies in the source thread. Reprioritised 2026-04-20 to "Gap 3 first, Gap 2 on own branch"; branch never opened. `.claude/skills/draft-reply/references/slack-integration.md:63` codifies the accepted design: "Future phase: Slack-side sent detection — out of Phase 12 scope. Manual move is the current workflow." **Do NOT re-propose as an audit gap unless Linards explicitly reopens it.** `[impact: med, status: decided]`

- **OB1 → Fredis integration plan: MCP server is the only wedge (2026-04-26).** Plan at `.agent/plans/fredis-ob1-integration.md` — 7 phases, 15 identity invariants, 11-row risk register, no code on commit. Single wedge worth porting from OB1 is `fredis-mcp` — an MCP server exposing the Fredis vault to non-Claude-Code AIs (ChatGPT, Cursor, Claude Desktop). Everything else is incremental on top. Phase sequence: (1) MCP server, (2) schema-aware frontmatter on new captures, (3) entity wiki, (4) claudeception evaluator, (5) CONDITIONAL LLM sensitivity tier, (6) CONDITIONAL historical importers, (7) OPTIONAL panning-for-gold skill. All phases additive, feature-flagged (`*_ENABLED=0` defaults), independently rollback-able. SOUL/USER/MEMORY/HABITS/HEARTBEAT protected by invariants; existing hooks (`block-soul-edit`, `block-template-residue`, `block-secrets`) unaffected. 7 open design forks (D1–D7) gate code start. `[impact: high, status: decided]`

- **OB1 → Fredis: scope items explicitly dropped (2026-04-26).** Knowledge graph, SvelteKit dashboards, household extensions, RLS / shared-MCP, Supabase / K8s infra all dropped from the OB1 port. Fredis already has its own vector search (FastEmbed + SQLite/Postgres), daily digest (heartbeat), session capture (hooks), MCP client, vault sync, and live retrieval — verified against live code, not assumed from docs. **Do NOT re-propose as future audit gaps.** `[impact: med, status: killed]`

- **OB1 Phase 1.1 fredis-mcp read-only server shipped (2026-04-26).** Implementation complete, 17 MCP-specific tests green, full suite 846 pass. FastMCP pattern: `from mcp.server.fastmcp import FastMCP`, `@mcp.tool()` decorator, `.run("stdio")`. Server flag-gated on `FREDIS_MCP_ENABLED` (default 0); 5 new env keys (`FREDIS_MCP_*`) added to `.env` + `.env.example`. Phase 1.3 (`propose_draft` write tool) shipped on 2026-04-27 in commit `ec1a7e6`. `[impact: med, status: decided]`

- **OB1 Phase 1 fredis-mcp full server shipped (2026-04-27).** Slices 1.2 (denylist), 1.3 (`propose_draft`), and 1.4 (smoke test + operator docs) all landed. Commits: `ec1a7e6` (1.3), `eff8421` (1.4 — `docs/mcp-server.md`, 157 lines, stdio operator guide). Live stdio handshake verified all 8 tools, denylist enforcement (`USER.md`, `retainers/`, `legal/`, `investors/` all blocked), and `propose_draft` write path. 52/52 unit tests green. `MCP_DENYLIST` env var controls path-prefix blocklist; denylist re-checks resolved path after `Path.resolve()` to prevent symlink bypass. **Pending:** `FREDIS_MCP_ENABLED` still `0` in `.claude/scripts/.env` — Linards has 8-step manual integration test (flip flag, wire Claude Desktop, run read+write verification prompts) before declaring slice 1.4 done. `[impact: med, status: decided]`

- **OB1 D1–D7 design forks all resolved (2026-04-27).** All 7 open design forks closed in `.agent/plans/fredis-ob1-integration.md` (gitignored — local only by design; if a public paper trail is needed, it goes in `docs/phases.md` or CHANGELOG). Notable: D2 = `A (stdio on Mac) + B (streamable-http on VPS via Tailscale Serve)`; D5 = Phase 6 ships with Gmail + Slack archive parsers only, other sources additive. `[impact: med, status: decided]`

- **OB1 Phase 1B fredis-mcp Remote VPS shipped (2026-04-27).** Transport = `streamable-http` (not SSE) on VPS via Tailscale Serve. Three defense layers: (1) `127.0.0.1:4747` loopback bind, (2) Tailscale ACL, (3) bearer token (constant-time compare, 401 on bad token). Files: `fredis_mcp_auth.py` (bearer middleware), systemd unit `secondbrain-mcp-server.service`, `docs/mcp-server-vps.md` (operator runbook), 39 auth tests + 11 server tests pass. `fredis_mcp_server.py` `main()` switches transport via `FREDIS_MCP_TRANSPORT` env (default stays stdio). `pyproject.toml` adds explicit uvicorn + starlette deps. **Security note:** `propose_draft` `source` field is unauthenticated label — anyone with bearer token can target any source folder; acceptable for Tailscale-only exposure. **Pending:** VPS deploy is manual via SSH runbook in `docs/mcp-server-vps.md`. `[impact: med, status: decided]`

- **Scope decision: OB1 Phase 6 historical importers — Gmail + Slack only (decided 2026-04-27).** ChatGPT, X, Substack, and Perplexity archive parsers are explicit additive sub-phases — can be added later without rework. Phase 6 ships only Gmail + Slack to keep blast radius small. **Do NOT list missing source-importers as audit gaps.** `[impact: low, status: decided]`

## Lessons Learned

These are the day-one rules — synthesised from J5. The brain should respect these without re-questioning unless explicitly revisited.

- **Email Hub has a UK IP overhang — "free time" isn't a complete defence.** It was built outside Merkle hours (factual point in his favour), but UK law (CDPA 1988 s.11(2), Patents Act 1977 s.39) tests scope + specific instruction, not clock-hours. The department head tasked the team with workplace innovation, and the work is squarely in his field of employment. Before pitching further: (a) read the Merkle contract IP clause verbatim, (b) drop "Merkle" from the project name, (c) recraft origin as "12 years of MarTech veteran seeing the fragmentation problem" (not "my dept head tasked our team"), (d) £150–£300 solicitor opinion letter is the cheapest insurance before any VC commitment. Going forward: keep all personal IP unambiguously independent — personal device, personal accounts, no Merkle-named folders, no internal presentations first.

- **Ship one MVP to a paying client in 90 days; pause the other four.** Five active projects, zero paying clients, six months in. Shortest revenue path is Email Hub → mid-market UK agencies where 12y MarTech credibility opens doors instantly. VTV, UGOKI, GERBONI, Cab app wait. Revenue unlocks focus.

- **Register a UK Ltd before the first invoice.** Cross-border personal-Gmail invoicing without an entity = tax + liability mess. UK Ltd: ~1 week, ~£50. **Don't** create an LV SIA until LV-originating revenue exists — dormant entities cost admin for nothing.

- **LPV channel is an accelerator, not a foundation.** Šlesers and Krištopans replied because Linards is an LPV member writing sharp Latvian. If LPV isn't in government after the next election, those doors close. VTV's sales path must work without LPV influence: direct Rīgas Satiksme ops contact, EU transport-innovation funding, other municipalities. LPV opens door 1; never rely on it for door 2.

- **VTV €2.4–4.4M ROI claim needs one transit-CFO in the room before it goes public again.** Math is plausible but founder-built. One paid 60-min conversation with a transit ops/finance pro stamps the number as credible. Without it the page reads as optimistic founder math and erodes trust in everything else.

- **Don't single-thread Tim Jackson — build a VC pipeline.** Strong email, strong voice, but one VC = usually silence. Rule: no reply in 10 business days → one light follow-up with one concrete update. Stop after two. Pitch 5 more VCs with adjacent thesis fit. Walking Ventures is 2018 context — build a fresh AI/MarTech VC list for 2026.

- **UK ↔ LV dual-identity positioning is the moat — lean into it publicly.** Generic: "ex-agency senior shipping working agents." Specific: "MarTech veteran at Merkle/Dentsu + VW/SEAT/Audi, 20 years in UK, Latvian-native, building AI-agentic ops bridging UK and Latvia." No other operator can credibly write that sentence. Put it in LinkedIn headline, portfolio, cold outreach.

- **GitHub is invisible — for an AI consultant in 2026, that's a real missed asset.** 4 followers, pinned repos from old Ruby days, zero public AI work. Buyers increasingly check GitHub before replying. Pick one piece of tooling — Second Brain, an agentic workflow template, a Latvian-prompt library — and publish with a grep-friendly README. Never publish client work. Publish tooling.

- **E4 ("avoid politics") is about the agent's public voice, not Linards's private activity.** No political opinions in drafts or public outputs. Political context (LPV, election calendars, Šlesers/Krištopans threads) IS in scope for private reasoning, scheduling, and risk analysis. SOUL.md captures this distinction.

- **Protect 05:00–08:30 weekdays like the product.** Sharpest hours; Dentsu eats 09:00–17:30. That leaves 17.5 weekly best-cognition hours plus 05:00–10:00 weekends. Spend them on Ship and Frontier — never on email or admin. Admin at night when depleted anyway. The agent must enforce: no non-urgent nudges before 08:30 weekdays.

- **Gavin Hughes (Ometria) is a conflict node — handle consciously.** Ex-Merkle colleague, now at an email-tech peer/competitor. Email Hub concept shared informally with him March 2026 (he liked it). Two rules: never source recent Ometria internal details for pitches; if Ometria ever positions a competing AI-email product, opposing sides. Keep Gavin warm; keep the boundary clean.

- **Compound advantage to bias toward: 12y digital depth + current AI-agentic build.** Cold-outreach track record (Šlesers, Krištopans, Tim Jackson) shows tone-calibration beats credentials at first contact. Bias recommendations toward leveraging this compound (digital ops + AI workflows for real businesses), not toward generic AI-consulting moves any 6-month newcomer could copy. When drafting first-touch messages, prioritise register and peer-level respect over listing credentials.

- **Re-evaluate dismissed fixes when new defenses change the risk calculus.** Dismissed tightening coarse input regexes as "weakening security" — but after building the output redactor (`redact-secrets.py`), the residual risk of a looser input gate was much lower. Should have circled back immediately. General rule: when a new defensive layer lands, re-scan earlier trade-offs it might have made cheaper.

- **Chat auto-retrieval must prepend per-turn, not via `system_prompt.append` (2026-04-21).** Retrieval context has to be prepended to `message.text` on every turn because `system_prompt` is session-init only — resumed Slack threads (majority of traffic) would never see retrieval hits otherwise. Pattern mirrors heartbeat-context injection at `engine.py:232-238`. Final message order is `[retrieval] → [heartbeat] → [wrapped user]` so heartbeat context isn't displaced by memory hits. `[impact: med, status: decided]`

- **Claude.ai web connectors are account-level, not local MCPs (2026-04-21).** `claude.ai Gmail/Calendar/Drive/Figma` connectors sync from Claude.ai web settings — cannot be removed via `claude mcp remove`. They appear in the deferred tools list but show "Needs authentication" and do nothing. To actually disconnect: https://claude.ai → Settings → Connectors. Harmless duplicates; Fredis has zero dependency on them (direct Python APIs via `query.py`). `[impact: low, status: resolved]`

- **Ghost Mac processes silently steal Slack Socket Mode events (2026-04-22).** Slack load-balances across all active WebSocket connections for the same bot token — `app_mention` events fan out to every connection, but `message.channels` events go to only one. A stale local `fredis-chat` process on Mac was stealing thread-engage events meant for the VPS. Always check for duplicate bot-token consumers (`ps aux | grep fredis`) before debugging Slack event delivery. Secondary rule: `message.channels` also requires `/invite @Fredis` in the channel AND enabling the event in the Slack app's Event Subscriptions (separate from OAuth scopes). `[impact: med, status: decided]`

- **`OnCalendar` embedded timezone requires systemd 246+ (2026-04-22).** VPS confirmed compatible. Worth remembering for future timer files — older systemd needs a separate `Environment=TZ=...` stanza instead. `[impact: low, status: decided]`

- **Resumed SDK sessions override new system-prompt rules (2026-04-23).** When a Slack thread resumes an existing Claude Agent SDK session, earlier conversation history outweighs newly injected system-prompt changes — the model anchors to the prior turns. Always test prompt / routing / skill-invocation fixes in a **fresh thread** (new parent message), never in a thread that's been running pre-fix. Corollary to the earlier `engine.py:232-238` lesson: if the fix has to reach mid-session turns, prepend to `message.text`, don't patch `system_prompt`. `[impact: med, status: decided]`

- **Measure before consolidating (2026-04-23).** Gut reaction to "4 new skills is too many, merge to 2" was wrong — actual line counts (148–376 per skill) and runtime cost (<1% of context for all 4 lazy-loaded descriptions) reversed the recommendation. General rule: check numbers before proposing structural changes. Token budget and trigger-phrase value per skill usually beat intuition about "too many." `[impact: low, status: decided]`

- **Always name the exact surface and number the steps (2026-04-24).** Linards flagged vague "paste this in Slack DM" instructions. Rule: specify the surface explicitly (Slack DM / Gmail compose / VPS terminal / HubSpot UI), number steps 1-N, and put exact text/commands in code blocks. Saves a clarifying round-trip. `[impact: low, status: decided]`

- **Silent error swallowing causes P0 bugs (2026-04-24).** HubSpot ticket Slack notifications were silently failing for a day because `ticket_dispatcher.py:201-203` caught Slack errors and stuffed them into the result dict — but no caller checked. Fixed by surfacing failures at all 5 dispatch sites (commit `454e89f`). General rule: when adding a try/except that returns an error field, verify every caller actually inspects it; otherwise raise. `[impact: med, status: decided]`

- **Treat plan/audit docs as historical snapshots, not current state (2026-04-24).** Repeatedly flagged GitHub PAT scope, HubSpot pipeline rename, and other items as "open" because I read `.agent/plans/2026-04-23-audit-remaining-work.md` as current instead of running `query.py lanes list` / `query.py hubspot pipelines` to verify live. Permanent fix is the new `## Audit Conventions` section in CLAUDE.md (4 pre-flight checks). Cost was 4 correction rounds in one session. `[impact: high, status: decided]`

- **Bash `source .env` chokes on values containing spaces (2026-04-26).** `HUBSPOT_TICKETS_PIPELINE_NAME=Fredis Review` is unquoted in `.env` and breaks naive `source .env` in wrapper shell scripts. Use Python-side `load_dotenv()` via `config.py` instead — bash wrappers should rely on the Python entrypoint to load env, not source `.env` themselves. Surfaced while wrapper-scripting the `fredis-mcp` server. `[impact: low, status: decided]`

- **Vault-sync + heal-block race condition (2026-04-27).** If a heal block writes a file on VPS and a revert deletes that same file on origin, vault-sync's auto-commit can create a modify-vs-delete conflict that `git pull --ff-only` can't resolve — leaving VPS in mid-merge state and blocking all subsequent deploys. Recovery: SSH in, conclude the merge using origin's clean state, pull, push, delete any resurfaced artefacts, manually dispatch `gh workflow run deploy.yml`. Surfaced when `_ssh_diag.txt` divergence blocked deploy run; resolved at commit `7b30b33`. `[impact: med, status: decided]`

- **Path-based denylists must re-check after symlink resolution (2026-04-27).** `MCP_DENYLIST` initially checked only the raw input path string — a symlink inside an allowed dir pointing into a denylisted dir would have bypassed the gate. Fix: `get_file` re-checks the path against the denylist *after* `Path.resolve()`. General rule for any path-based access control: validate the resolved/canonical path, not the user-supplied string. `[impact: med, status: decided]`

- **`block-secrets.py` hook flags secret-interpolation patterns in docs (2026-04-27).** Inline Python reading `os.environ` for a credential, and shell snippets that interpolate a bearer-token env var into an HTTP request, are caught by the secrets hook even when used as illustrative documentation. Fix: write verification snippets with literal placeholder strings (e.g. angle-bracket `TOKEN` text) rather than env-var interpolation. Surfaced while drafting the MCP VPS operator runbook. `[impact: low, status: decided]`

- **`.agent/plans/` is gitignored by design (2026-04-27).** Plan docs containing decision tables, slice plans, and design-fork resolutions stay local. If a public paper trail is needed for a decision, the natural homes are `docs/phases.md` or a CHANGELOG, not the gitignored plans dir. Implication: don't link to `.agent/plans/*.md` from public-facing docs and don't assume reviewers have access. `[impact: low, status: decided]`

## Important Facts

- **The "why" behind everything:** building enough durable, diversified income streams to let his family (wife, son, dog) live freely across UK, Latvia, and Argentina. A permanent home in Latvia and Argentina (wife's home country) is the long-game. Every research lane is a sub-investigation of this one question.
- **Active fear:** being too late on AI-agentic adoption for local SMBs, or those SMBs deciding they don't need an AI workflow + second brain. Counter-positioning: present the AI-agentic second brain as an extension of business capability, not a replacement.
- **Investment in build infrastructure:** Claude Code Max 20 subscription — meaningful monthly cost, treated as a productivity multiplier worth the spend.
- **Latvian voice samples seeded (2026-04-19):** 11 Latvian sent-draft files now in `drafts/sent/lv-seed/` for voice-matching. Baseline corpus exists; still flag if drafts sound off — may need real sent emails to refine further.
- **Source for voice-matching (English):** the Tim Jackson Email Hub note (D8 in the interview) is the canonical English voice sample.
- **Reference personality:** Chris Lori (seasoned trader) — calm, evidence-first, doesn't soften the call.
- **Phase 5.1 skill-stack complete (2026-04-19):** 28 skills live under `.claude/skills/` — 25 ported from alirezarezvani/claude-skills (MIT), 3 de novo (`ip-overhang-guard`, `business-cycle-analyst`, `robotics-engineer`). All use Anthropic 3-level progressive disclosure. Test baseline: 282/282 pass, ruff clean, mypy clean.
- **Heartbeat + reflection + synthesis + deps-audit + vault-sync running on VPS (2026-04-21):** systemd timers own every scheduled job. Mac launchd plists for heartbeat + reflect unloaded during Phase 10 cutover. Test baseline: pytest **513 pass / 2 skip**, ruff clean, mypy 3 pre-existing integrations errors unchanged.

## Active Projects

| # | Project | Path / Repo | Stage | Sequence | Sensitivity |
|---|---------|-------------|-------|----------|-------------|
| 1 | **VTV Riga Transport** | `/Users/Berzins/Desktop/VTV` | MVP / inbound LPV interest | **Ships first** | Politically connected — don't lean on LPV alone |
| 2 | **Cab Application (LV)** | (planned, partners Atis + Juris) | concept / shares VTV codebase | After VTV traction | Bolt-replacement angle in LV |
| 3 | **Email Hub** | `/Users/Berzins/Desktop/merkle-email-hub` (pitch.html) | MVP / pitching | **Blocked** — IP question | UK IP overhang — handle carefully |
| 4 | **UGOKI** | github.com/linardsb/ugoki-iOS-Android-app | MVP done | Paused | Tim Jackson 2018 thread — restart cold-warm |
| 5 | **GERBONI** | github.com/linardsb/GERBONI | online shop | Paused | Physical-product crossover, lower priority |

**Sequencing decided (2026-04-19):** product-builder path. VTV first → Cab rides VTV distribution → Email Hub after IP clearance. UGOKI + GERBONI paused. See Key Decisions above for kill triggers.

## Upcoming Events

- **Year 10 Consultation Evening — Thu 30 Apr 2026** (son's school). Book appointment slots.
- **Sports Awards — Thu 7 May 2026** (son's school, Matis). Surfaced in school notice 2026-04-27 — may need RSVP / calendar block.
- **Ashdown Park dinner — Sat 20 Jun 2026.** Dietary requirements confirmed; thread resolved.

## Preferences Confirmed

- **Active hours:** 05:00–20:00 UK; sharpest 05:00–18:00; never nudge after 22:00 UK
- **Weekends are working hours too** (6–8 h typical) — same active window
- **No emoji.** Ever
- **Casual register**, balanced length, neutral voice, evidence-first when correcting
- **Direct disagreement** preferred over hedged framing
- **No politics, current affairs, or celebrities** in agent's public output (private context tracking is fine)
- **Notification channels:** Slack DM + macOS native + WhatsApp
- **Morning brief on**, end-of-day one-line wrap on, late-day pillar nudge **off**
- **Drafts policy:** never draft for noreply / notification / receipt / cold-outreach senders. Draft freely on threads where Linards has already engaged ≥1 reply
- **Slack drafts:** DMs + @mentions only; client workspaces draft aggressively; community workspaces @mentions only
- **Discord drafts:** when addressed or in engaged threads only; flag (don't draft) unanswered expertise-channel questions ≥2h old
- **Approval flow:** Slack preview with approve/edit for routine; inline draft + explicit approval for high-stakes; auto-send only on plain acks at ≥95% confidence; never auto-send apologies, pushback, or first-contact

## Research Lanes (active intent — see folders under `Fredis/Memory/research/`)

- **AI / agentic engineering** — frontier-tracking for consultancy positioning
- **Markets & finance** — UK + LV + AR; commodity cycles feed VTV and personal portfolio
- **Public-sector policy & legislation** — UK + LV + EU + AR; gap-spotting for business opportunities
- **AI in agriculture** (★ year-end deep-understanding goal) — UK SFI / EU CAP via LV / AR export regime; mid-market 200–2000 ha sweet spot
- **AI robotics** (passive, prospective service line)
- **Materials / industrial innovation** (passive) — sub-lanes: `mycelium/` (bio-materials, packaging, building, agri crossover), `3d_printing/` (additive manufacturing, consumer + industrial hardware, materials-science plays)

## Open Watch Items

- **Email Hub IP question — execution blocker.** Has Linards raised the IP question with Merkle legal yet? Email Hub is paused until answered. Kill trigger: no answer by month 2 → pause indefinitely (2026-04-19)
- **VTV-first sequencing — needs explicit confirmation.** Linards hasn't confirmed whether VTV ships first with Cab after, or whether Cab runs in parallel. Product plan assumes sequential (2026-04-19)
- 10-skill product-lifecycle stack (Wave 2 skills) — planned but explicitly gated: "don't draft anything yet" until open questions answered (2026-04-19)
- How to reach UK + LV SMBs that haven't adopted AI workflows yet (C10)
- UK Ltd registration before first invoice
- VC pipeline build-out (post Tim Jackson one-shot)
- Research/analyst skill — identified as a real gap. Three modes proposed: brief (heartbeat morning sweep), deep (on-demand report to `research/`), synthesise (cross-lane strategic read). Not yet built (2026-04-18)
- `setup_workspace.py` bugs #2-#4 — stale defaults (30 min, 08-22, etc.) are a booby trap if the script is ever re-run. Documented in `.agent/audits/2026-04-18_phases-0-4-audit.md` (2026-04-19)
- **HubSpot default pipeline stages don't match plan spec (2026-04-23).** HubSpot Free caps at 1 deal pipeline → stuck with "Sales Pipeline" default. `overdue_invoices` heartbeat scan looks for a stage labelled `Invoice` — zero matches until stages renamed in HubSpot UI to `Inbound → Discovery → Proposal → Signed → Kickoff → Delivery → Invoice → Post-delivery`. Low-stakes until `HUBSPOT_SCANS_ENABLED=true`. `[impact: low, status: pending]`
- **HubSpot write-path cleanup pending (2026-04-23).** Step 9 of `.agent/plans/hubspot-slack-writes.md` bundles: revert `config.py` Monday shim, delete `integrations/monday_api.py` + `migrate_monday_to_hubspot.py`, Linards removes `MONDAY_*` from `.env`. Also defer-listed: CLI-level currency validation (~20 lines). `[impact: low, status: pending]`
- **Heartbeat guardrail fail-closed nine times: 2026-04-24 05:54 + 10:05, 2026-04-25 16:06, 2026-04-26 08:10 + 19:41, 2026-04-27 08:18 + 16:22, 2026-04-28 17:00, 2026-04-29 06:35.** First two were pre-Sonnet-promotion (commit `5069d4e`); the remaining seven are **post-promotion**, so the Haiku→Sonnet move did not fully resolve it. Pace is now ~daily, not weekly. Next action: raise `asyncio.wait_for` from 15s to 30s in `heartbeat.py` and/or add single-retry before failing closed. `[impact: med, status: pending]`
- **F1 Gmail 201-unread triage** still deferred (2026-04-24). Tagged "not urgent" by Linards. Revisit when next inbox-cleanup window opens. `[impact: low, status: pending]`
- **HABITS.md daily reset didn't fire on 2026-04-25.** Header still read "Today: 2026-04-24" through the day; all five pillars unchecked because the new-day reset (which should rewrite the header + clear ticks at 00:00 BST) never ran. Investigate the timer/cron that owns the reset (likely a missing systemd unit or a guard inside `heartbeat.py`/a sibling script). `[impact: low, status: pending]`
- **`block-template-residue.py` allowlist gap (2026-04-27).** `Fredis/Memory/drafts/active/` is **not** in `ALLOWLIST_PREFIXES` (lines 46-52 of `.claude/hooks/block-template-residue.py`). Doesn't bite `propose_draft` (writes via Python `open`, not Edit/Write tool), but will fire if Claude later edits a draft containing template-residue strings via the Edit tool. One-line fix needed as housekeeping. `[impact: low, status: pending]`
- **MCP server VPS deploy (Phase 1B) is manual (2026-04-27).** Linards needs to follow the runbook in `docs/mcp-server-vps.md` via SSH after merge: generate token, append env vars, copy systemd unit, daemon-reload, enable, run `tailscale serve`, set ACL, verify with nmap. Stop condition for slice. `[impact: low, status: pending]`
- **MCP integration manual smoke test pending (2026-04-27).** `FREDIS_MCP_ENABLED` still `0` in `.claude/scripts/.env`. Linards has 8-step guide to flip the flag, wire Claude Desktop, and run two verification prompts (read path + denylist; write path + `propose_draft`) before declaring slice 1.4 done. `[impact: low, status: pending]`
- **Guardrail false-positive on `</external_data>` closing tag (2026-04-28).** Every non-timeout heartbeat on 2026-04-28 (7/7) flagged the legitimate structural closing tag of the data wrapper as `xml_escape_attempt`, forcing the Claude reasoning step to write a paragraph explaining the false positive. Wastes tokens on every tick. Pattern matcher needs to either skip the wrapper's own structural tags or only fire when the tag appears *inside* an inner content block. `[impact: low, status: pending]`

---

_This file is curated from daily logs. During heartbeats, recent daily logs are reviewed and important items are promoted here._

_Older entries archived: [2026-04](archive/2026-04.md) — searchable via memory_search._
