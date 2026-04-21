# HEARTBEAT.md - Proactive Checklist

_This file defines what to check during heartbeat runs. Pre-loaded into the prompt by `heartbeat.py`._

## Active Window

- **Hours:** 05:00–20:00 Europe/London (sharpest 05:00–18:00)
- **Never nudge:** after 22:00 UK
- **Weekends:** same window — Linards typically works 6–8 h on weekends
- **Do not interrupt:** non-urgent items during identifiable family time
- **Protected window (no non-urgent nudges):** 05:00–08:30 weekdays — best-cognition Ship/Frontier hours; Dentsu eats 09:00–17:30 anyway

## Quick Checks (Every Heartbeat)

Data is pre-fetched via direct API integrations and included in the prompt context.

- [ ] Any urgent emails in the last 2 hours? (via Gmail API)
- [ ] Any calendar events in the next 4 hours? (via Calendar API)
- [ ] Any overdue tasks? (via Asana API — once integration ID lands; TBD)
- [ ] Any important Slack DMs / @mentions? (via Slack API — TBD)
- [ ] Any WhatsApp signal worth surfacing? (manual / future integration)
- [ ] **Gate-breach check** — `gate_loader.evaluate_gates` reads `Fredis/Memory/gates/*.yaml` and writes a breach draft to `drafts/active/launch-governance/metrics-gate/` when a pre-committed kill criterion fires. Surface breaches with Slack priority over everything else — a fired kill trigger means a lane decision is due.

## Custom Proactive Checks (per H3)

Each heartbeat, scan and surface only items that change Linards's next action:

- [ ] **Morning brief** (first heartbeat of the day): today's calendar, overdue tasks, draft inbox, AI news, government business news, AI agentic-coding innovation, market updates UK + LV, business news UK + LV. Three things on one screen, not 30
- [ ] **Meeting prep** 15 min before each calendar event: who, what, the open thread from last time
- [ ] **Overdue-task nudge** — only items assigned to Linards AND due ≤ 2 days
- [ ] **Market summary** — UK + LV + AR moves >3% in tracked tickers / commodities (see MEMORY.md research lanes for watchlist context)
- [ ] **Legislation updates** — UK + LV + EU + AR; only items with measurable business impact (new laws, opened consultations on `tap.mk.gov.lv` / `consultations.gov.uk`, EU AI Act implementation)
- [ ] **AI agent innovations / engineering news** — model releases, agentic-eng papers, framework updates
- [ ] **Material design / robotics / innovations** — flag major moves in tracked verticals, including mycelium / bio-materials and 3D printing / additive manufacturing
- [ ] **Business news Latvia + UK** — government support, sector shifts, competitor moves
- [ ] **End-of-day wrap** (final heartbeat ≤20:00): one-line "what closed today" + "what's open tomorrow". Nothing more

## Anomaly Detection

Flag anything unusual:
- [ ] Spike in unread email count (vs normal baseline)
- [ ] Cancelled or moved meetings that weren't expected
- [ ] Tasks overdue > 1 week (stale — suggest cleanup)
- [ ] No activity in usually active Slack/Discord channels
- [ ] Tracked commodity / ticker move >5% in a day
- [ ] New entry on `tap.mk.gov.lv` or `consultations.gov.uk` matching tracked policy domains

## Periodic Checks (Rotate Through)

### Project Status (1–2× daily)
- [ ] Any blocked tasks that need attention?
- [ ] Email Hub / VTV / UGOKI / GERBONI / Cab — anything stalled > 1 week?
- [ ] Any pull requests waiting for review (linardsb GitHub repos)?

### Pipeline / Sales (1× daily)
- [ ] Tim Jackson follow-up window check (10 business days after last touch — see MEMORY.md)
- [ ] Šlesers / Krištopans threads — any silence approaching unhealthy?
- [ ] Any inbound on Email Hub or VTV worth fast-tracking?

### Research Lanes (1× daily during morning brief)
- [ ] Scan primary sources per `Fredis/Memory/research/{markets,policy,ai,robotics,materials,agriculture}/` lanes
- [ ] 3–5 items max worth Linards's 5 minutes — depth picked by signal strength + 5-bullet summary

### Memory Maintenance (Daily)
- [ ] Review yesterday's daily log
- [ ] Extract anything worth promoting to MEMORY.md

## When to Notify

**Notify immediately (interrupt now):**
- Groundbreaking AI news (model release, agentic-eng breakthrough, regulation shift)
- Urgent business news in Latvia and UK affecting tracked lanes (transport, agri, MarTech, AI consulting)
- Urgent email from a G1 important contact (Tim Jackson, Matīs, Ana Laura Suárez)
- Calendar event starting < 2 h with no prep notes
- Overdue task tagged urgent / client-facing

**Batch for next interaction:**
- Non-urgent emails
- Tasks due > 48 h
- Interesting but not urgent information

**Stay silent (HEARTBEAT_OK):**
- Nothing new since last check
- Outside active hours (after 22:00 UK) unless truly urgent
- Inside the protected 05:00–08:30 weekday window unless truly urgent
- Everything is on track

## Draft Management (Every Heartbeat)

Data is pre-fetched: active drafts, platform posts/DMs, and sent mail are included in prompt context.

- [ ] Check `drafts/active/` for pending drafts
- [ ] For each active draft: check source platform for Linards's actual reply
- [ ] If he replied himself: move draft to `drafts/sent/` with the ACTUAL reply text (not the draft text)
- [ ] If draft > 24 h old with no reply: move to `drafts/expired/`
- [ ] Scan important emails (G1 + known client domains, see USER.md) without a reply — create draft reply
- [ ] Scan community DMs / Discord where last message isn't from him — create draft reply
- [ ] When drafting: search `drafts/sent/` via memory search for similar past responses (RAG voice-matching)
- [ ] Write all drafts in his voice (D8 sample is the canonical English reference; Latvian samples missing — flag if drafting in LV)

### Hard Block — Never Draft (per G3)
- Sender matches `noreply@`, `no-reply@`, `donotreply@`, `notifications-*@`, `mailer@`, `bounces@`
- Sender domain in: linkedin.com, github.com, notion.so, atlassian.com, intercom.io, hubspot.com, slack.com, calendly.com, zapier.com, substack.com, beehiiv.com, mailchimp.com, klaviyo.com
- Bank/payment: revolut.com, starling, monzo, stripe.com, paypal.com, shopify.com, any `@statements.*`
- Any email with a `List-Unsubscribe` header
- Subjects starting with: `[Receipt]`, `[Invoice]`, `Your order`, `Password reset`, `Verify your email`, `Login alert`, `New sign-in`, `Weekly digest`, `Your weekly`, `Monthly report`

### Cold-Outreach Patterns — Flag Only, Don't Draft
- First-time sender, body contains: "quick question", "hope this finds you well", "saw your recent", "loved your post", "15 minutes to explore", "are you the right person", "following up" (no prior thread)
- Any first-time email with an unrequested meeting link (Calendly, SavvyCal, Google Meet)
- "I help companies like yours…" / "I noticed you're using…" openers

### Draft Only If Linards Has Engaged ≥1 Reply on the Thread
- Anyone not in G1 important contacts — suggest a reply, don't pre-draft
- Threads with > 4 participants

### Draft Freely
- G1 important contacts (Tim, Matīs, Ana Laura)
- Known client domains (when F-section accounts land)
- Family / accountant / lawyer
- Any thread where he's already sent ≥1 reply

### Slack Draft Policy (G4)
- DMs + @mentions only. Skip channel activity he's not tagged in
- Client workspaces: draft aggressively
- Community workspaces: @mentions only, skip DMs
- Never draft for bots, @channel, or threads he hasn't already participated in

### Discord Draft Policy (G5)
- Draft when addressed or in a thread he's engaged in
- Flag (don't draft) unanswered expertise-channel questions ≥ 2 h old — he'll write the reply himself

### Approval Flow (G8)
- Slack preview with approve/edit buttons for routine
- Inline draft file + explicit approval for high-stakes / long drafts
- Auto-send only on plain acknowledgements at ≥ 95% confidence
- Never auto-send: apologies, pushback, first contact

### Draft File Format
Files go in `Fredis/Memory/drafts/active/`:
- Filename: `YYYY-MM-DD_<type>_<slugified-name>.md`
- YAML frontmatter: type, source_id, recipient, subject, context, created, status, **service** (per K8 — `service: bookkeeping` / `service: ai-build` / etc.)
- Body: `## Original Message` + `## Draft Reply`

## Habits Tracking (Every Heartbeat)

The habits tracker lives at `Fredis/Memory/HABITS.md`. Pillars: Ship · Frontier · Read · Ground (Body + Near).

- [ ] Read HABITS.md for today's checklist state
- [ ] If first run of day (today's date doesn't match the "Today" header): archive yesterday to History, reset today's checklist
- [ ] Suggest specific actions for unchecked pillars using calendar / tasks / email context
- [ ] **Late-day nudge: OFF** (per I7). Don't ping at 18:00 about unchecked pillars
- [ ] Frontier 18:00 self-report fallback (per HABITS.md) is allowed — single ask, not a nudge cycle
- [ ] If Linards reports completing a pillar (via chat/conversation): check it off with description
- [ ] Auto-detection: only check off a pillar if it meets the criteria in HABITS.md (Ship via Gmail-to-client + Asana + Drive shares; Frontier via build-repo activity + daily-log keyword; Ground both halves; Read self-report only)
- [ ] When in doubt, do NOT auto-check — let Linards report it himself

## Research Pulls (Morning Brief)

- [ ] Daily headline pull from sources mapped in MEMORY.md research lanes — yes (per M4)
- [ ] 3–5 items worth 5 minutes; depth picked by signal strength + 5-bullet exec summary (per M8)
- [ ] Default share-status: frontier lanes (AI, robotics, materials) public-shareable; competitive-edge lanes (policy, markets, agriculture) private (per M9)

## Research Papers

Analyst-agent write-target: `Fredis/Memory/research/{lane}/papers/` — one `.md` per paper. Schema + tie-in categories + filename convention in `Fredis/Memory/research/README.md → Papers Convention`.

### Daily surfacing (morning brief)

- [ ] Pick top 3 papers across all lanes where `relevance_score >= 4` AND `tie_in` in `{active-project, service-line}`
- [ ] Surface each as one-line headline from `tie_in_detail`, not the paper title
- [ ] If no paper clears the bar, stay silent on papers — no forced picks

### Weekly digest (Mondays)

- [ ] At first heartbeat on Monday in the active window, generate `Fredis/Memory/research/weekly_digest_YYYY-WNN.md`
- [ ] Top 5 papers cross-lane ranked by `relevance_score`, tiebreak by tie-in priority (active-project > service-line > personal-interest > frontier-only)
- [ ] One `### {Lane name}` header per lane that has picks; omit lanes with zero picks
- [ ] Link back to each paper's `.md` file

### Interruption rule (immediate Slack nudge)

- [ ] ONLY `relevance_score: 5` AND `tie_in: active-project` triggers an immediate nudge — no other combination
- [ ] Everything else waits for morning brief or weekly digest

### Archive behaviour

- [ ] Papers with `tie_in: frontier-only` OR `relevance_score <= 3` stay in `papers/` searchable via memory-search but never surfaced proactively
- [ ] If agent can't articulate a Linards-specific `tie_in_detail`, default to `tie_in: frontier-only` — don't force a tie

## Notification Channels

- Slack DM
- macOS native
- WhatsApp

## Check Tracking

Last checks are tracked in `state/heartbeat-state.json`. Don't repeat a check if it was done < 30 minutes ago.

---

_Update this file to add or remove checks as needs change. When integration IDs (F1–F13) land, replace TBD references with actual workspace / channel / project IDs in USER.md and tighten the corresponding checks above._
