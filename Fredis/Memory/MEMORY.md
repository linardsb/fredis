# MEMORY.md - Long-Term Memory

_Curated, important memories that persist across sessions. Daily logs capture everything; this file captures what matters._

## Key Decisions

_(Pre-revenue stage — formal locked-in decisions still to be made. Likely first entries will land as Email Hub commercial model, UK Ltd registration, and pricing per service line. See active TBDs in `USER.md → Service Lines`.)_

- **Credential rotation deliberately skipped (2026-04-18).** Six live tokens (Slack bot/app, Asana PAT, GitHub PAT, Monday.com, unknown hex credential) were exposed in chat during Phase 4 scoping. Linards explicitly accepted the risk. If any are later compromised, the forensic timeline is in the 2026-04-18 daily log.

- **.env access stays gated behind security hooks (2026-04-19).** Recommended `audit_env.py` companion for metadata-only reads as a future improvement (Cleanup D candidate). Direct `.env` reads remain blocked by `block-secrets.py` + `redact-secrets.py`.

- **PIV execution uses Option C — reconciliation doc + PRD as dual authority (2026-04-18).** Each `plan-feature` call must reference `.agent/plans/second-brain-prd.md` (including the Addendum — Context Deltas) and `.agent/plans/reconciliation.md`. The reconciliation doc lists known template residue per phase; plans should propose deletions where current code contradicts the PRD.

- **Strategic pivot: product-builder, not consultant-closer (2026-04-19).** Linards chose to build a portfolio of products using Fredis + Archon as tooling spine, rather than positioning as a consultant selling time. Three products selected: Email Hub (SaaS/MarTech), VTV (B2G public-transport optimisation for Riga), Cab App (B2C ride-hailing, shares VTV codebase). Sequencing: VTV ships first → Cab rides on VTV's distribution → Email Hub blocked until IP question resolved. Kill triggers agreed: Email Hub paused if no IP answer by month 2; Cab paused if VTV has no real conversations by month 4; VTV paused if no LOI/pilot by month 6. Full plan at `docs/product-portfolio-plan.md`. Execution gated on two open questions (see Open Watch Items).

- **Research/scraping stack: free trio, no paid subscriptions (2026-04-19).** Crawl4AI (self-hosted on Colima), Jina Reader (1M tokens/mo free), Exa (1k/mo free, semantic search). Built-in WebSearch/WebFetch covers ~85% of needs. Paid Firecrawl ($16-19/mo) only as fallback for Cloudflare-walled sites. Decision doc at `docs/research-stack-decision.md`.

- **No vault restructuring (2026-04-19).** Linards explicitly rejected workshop-template paths or entity/topic folders into `Fredis/`. Current flat MEMORY.md structure stays as-is.

- **Port-first, not build-first (2026-04-19).** Linards directive for skills: stop authoring de novo where an existing open-source skill fits. Port, add Fredis advisor-mode wrapper + attribution, only build de novo when no upstream match exists.

- **Phase renumber: Memory Loops = Phase 9, VPS Deploy = Phase 10 (2026-04-21).** Memory loops ship before deployment so VPS migrates a stable schema in one pass — no local-vs-VPS schema drift. `[impact: med, status: decided]`

- **4-loop memory architecture (2026-04-21).** Capture (memory_flush) → Consolidate (memory_reflect) → Dream (weekly synthesis) → Recall (auto-retrieval in chat + heartbeat). Recall is the highest-visible win — surfaces old decisions/drafts contextually. Synthesis drafts to `drafts/active/memory-synthesis/YYYY-Www.md` for human approval; never auto-writes to MEMORY.md. `[impact: high, status: decided]`

- **Fredis cut over to VPS runtime (2026-04-21).** All scheduled services now run on VPS via systemd: `secondbrain-chat`, `fredis-heartbeat.timer` (2h), `fredis-reflect.timer` (daily 08:00), `fredis-synthesis.timer` (Sun 08:00), `deps-audit.timer` (Mon 09:00), `fredis-vault-sync.timer` (2 min). Mac heartbeat + reflect plists unloaded. Code flow: Mac push → GitHub Action → `deploy.sh` on VPS (workflow `paths-ignore`s `Fredis/**` + `docs/**` + `**/*.md`). Memory search via SSH tunnel: local 5433 → remote 5432 (Mac's local Postgres owns 5432). `[impact: high, status: decided]`

- **Phase 10.5 single-repo vault sync (2026-04-21).** `Fredis/` tracked inside `linardsb/fredis` (not a separate vault repo). `vault-sync-repo.sh` uses mkdir-lock + subtree-only `git add -A Fredis/` + `commit --only -- Fredis/`, runs every 2 min on both sides. `concat-both` merge driver registered via `.gitattributes` for daily logs + drafts. WIP code outside `Fredis/` stays unstaged. `[impact: med, status: decided]`

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
- **HubSpot GBP currency not enabled on portal 144478060 (2026-04-23).** API rejects `deal_currency_code: "GBP"`; code falls back to portal default. Fix: HubSpot UI → Settings → Account Setup → Currency → Add GBP. After enabling, existing CLI code works as-is with `--currency GBP`. `[impact: low, status: pending]`
- **HubSpot default pipeline stages don't match plan spec (2026-04-23).** HubSpot Free caps at 1 deal pipeline → stuck with "Sales Pipeline" default. `overdue_invoices` heartbeat scan looks for a stage labelled `Invoice` — zero matches until stages renamed in HubSpot UI to `Inbound → Discovery → Proposal → Signed → Kickoff → Delivery → Invoice → Post-delivery`. Low-stakes until `HUBSPOT_SCANS_ENABLED=true`. `[impact: low, status: pending]`
- **HubSpot write-path cleanup pending (2026-04-23).** Step 9 of `.agent/plans/hubspot-slack-writes.md` bundles: revert `config.py` Monday shim, delete `integrations/monday_api.py` + `migrate_monday_to_hubspot.py`, Linards removes `MONDAY_*` from `.env`. Also defer-listed: CLI-level currency validation (~20 lines). `[impact: low, status: pending]`

---

_This file is curated from daily logs. During heartbeats, recent daily logs are reviewed and important items are promoted here._
