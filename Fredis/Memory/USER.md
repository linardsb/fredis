# USER.md - About You

## Basic Info

- **Name:** Linards Bērziņš
- **Email:** linardsberzins@gmail.com
- **Timezone (primary):** Europe/London (UK)
- **Timezone (secondary):** Europe/Riga (always show alongside)
- **Location:** East Grinstead, UK (current); Riga, LV (secondary base, 1–2 trips/year)

## Professional Context

### Current Role
- Senior Email Developer at Dentsu (Merkle), 09:00–17:30 UK weekdays
- In parallel: building an AI-agentic consultancy that helps SMBs in East Grinstead, the wider UK, and Riga adopt agentic workflows
- Long-game positioning: 12 years of MarTech depth + current AI-agentic build = a defensible moat for delivering AI-assisted operations to real businesses, not generic AI consulting

### Key Projects
1. **Email Innovation Hub (Merkle/Dentsu)** — `/Users/Berzins/Desktop/merkle-email-hub` — agentic platform turning email developers into client-facing innovation partners; central engine for components, patterns, and AI-assisted workflows across ESPs/CMSs. SaaS or one-off-sale model TBD. **Note:** UK CDPA 1988 s.11(2) / Patents 1977 s.39 IP overhang — handle carefully (see MEMORY.md J5)
2. **VTV Riga Transport** — `/Users/Berzins/Desktop/VTV` — AI-agentic public-transport optimisation for Latvia. Inbound interest from Ainars Šlesers and Vilis Krištopans. Same codebase will base the Bolt-replacement Cab application planned with LV partners
3. **UGOKI** — https://github.com/linardsb/ugoki-iOS-Android-app — health & wellbeing iOS/Android app, MVP done. 2018 Tim Jackson (Walking Ventures) interest re-engaged via Email Hub cold note
4. **GERBONI** — https://github.com/linardsb/GERBONI — Latvian coat-of-arms t-shirt online shop; physical-product / aesthetic crossover

### Content Calendar
- **Cadence:** weekly
- **Channels active or planned:** LinkedIn, YouTube, X, Nate's Newsletter (https://natesnewsletter.substack.com/)
- **Topics he wants to write about:** AI and agriculture, AI agents, building business, mycelium / bio-materials, 3D printing / additive manufacturing

## Working Style

### Communication Preferences
- Length: balanced (ramps for higher stakes); formality: casual; emoji: never
- Voice: neutral; humor: avoid; direct disagreement preferred
- When telling him he's wrong: evidence first, then verdict
- Languages: **British English always** (authorise, organise, colour, realise, analyse, centre, -ise not -ize, -our not -or); Latvian when context calls for it. No US spelling in any output — Slack, Gmail, drafts, casual replies. Code identifiers stay as-is.
- Register: Slack = casual · drafts = professional · terminal = blunt
- Off-limits in public output: politics, current affairs, celebrities (private context tracking is fine — see SOUL.md)

### Schedule Patterns
- **Typical week:** East Grinstead, working from home for Dentsu 09:00–17:30. Wakes early; works on his business and research before/after the day job
- **Active hours:** 05:00–20:00 UK
- **Sharpest:** 05:00–18:00 (especially the 05:00–08:30 weekday window — protect it like the product)
- **Do not nudge:** after 22:00 UK
- **Weekends:** working too — typically 6–8 hours
- **UK ↔ Latvia travel:** 1–2 trips/year, ad-hoc
- **Recurring commitments:** none currently

### Team
- Solo. No employees, no co-founders. Atis (cousin) and Juris Ņefedovs are partners on the LV Cab project specifically — setup in progress, not formalised yet

## Integrations & Accounts

_Secrets and account IDs live in `.claude/scripts/.env`. This section documents shape and status only — never copy values here._

### Email
- Primary: linardsberzins@gmail.com
- Secondary accounts: none currently

### Calendar
- Google Calendar ID: configured in `.env` (`GOOGLE_CALENDAR_ID`)

### Task Management
- HubSpot Free: Private App token + hub ID configured in `.env` (`HUBSPOT_API_TOKEN`, `HUBSPOT_HUB_ID`). **Primary CRM + task layer** as of 2026-04-23. Schema bootstrapped with custom properties for urgent-alert contacts, engagement-type companies, service-line + source deals. Free-tier constraints: 1 deal pipeline max. Engineering work stays in GitHub Projects, not HubSpot. Asana fully removed 2026-04-24.

### Slack
- User ID: configured in `.env` (`SLACK_USER_ID`)
- Workspaces / channels: configured in `.env` (`SLACK_CHANNELS`). Bot + app tokens also in `.env`.

### Discord
- Not in use — will not be connected. Community channels live elsewhere.

### GitHub
- Username configured in `.env` (`GITHUB_USERNAME`); PAT in `.env` (`GITHUB_TOKEN`)
- Public profile is currently sparse (4 followers, old Ruby repos pinned) — flagged in MEMORY.md as a fix-in-90-days item
- Active repos: ugoki-iOS-Android-app, GERBONI
- Heartbeat reads push/PR events as the Ship-pillar signal (HABITS.md)

### Google Drive
- No client folder root set up yet — defer until first client project lands

### Other
- Linear · Notion · Bookkeeping (Xero/QuickBooks): not connecting; tooling choices unsettled (revisit post-first-client)
- Claude Code Max 20 subscription (active — primary build environment)
- **Advisor-model preference (2026-06-12):** never propose Fable as global advisor — "fable uses way more tokens than opus and is as good as opus." Default pairing is Sonnet/Opus main → Opus advisor; when Fable is main, recommend "No advisor" (Opus/Sonnet advisors are weaker than Fable, low value).

## Proactivity Preferences

### Things You'd Appreciate (Unsolicited)
- Morning brief (today's calendar, overdue tasks, draft inbox, AI news, gov-business news, AI agentic-coding innovation, market updates UK + LV, business news UK + LV)
- Meeting prep 15 min before
- Overdue-task nudges
- Market summary
- Legislation updates (UK + LV + EU + AR — see MEMORY.md research lanes)
- AI agent innovations / AI engineering news
- Material design news, robotics, innovations (including mycelium / bio-materials and 3D printing / additive manufacturing)
- Business news in Latvia and UK
- End-of-day wrap: one-line "what closed today" + "what's open tomorrow"

### Things That Would Be Annoying
- Repeated reminders for the same item
- Emoji-heavy updates
- Interruptions during deep work
- Non-urgent during family time

### Decision-Making Patterns
- Direct pushback preferred over deferential framing
- For technical reviews: 2–3 alternatives to compare
- Higher stakes (client work, financial) → opinion dial 4 of 5
- Off-limits in agent's public voice: politics, current affairs, celebrities

## Service Lines

_Operational map of what Linards sells / could sell. Mostly TBD until early clients land — keep this section live._

- **Active selling right now:** none formally — pre-revenue. Generating leads and potential clients is the K7 high-touch priority
- **Service lines on the menu (in development):**
  - AI-agentic builds for SMBs (Email Hub-style productisation)
  - Custom web + native apps (e.g., VTV transport tech, Cab application)
  - SaaS products (Email Hub potential SaaS path)
  - Marketing / bookkeeping / accounting / sales support (bundled, secondary)
  - Agriculture × AI (prospective service line — UK SFI / EU CAP via LV / Argentine export regimes — see MEMORY.md M11)
  - AI robotics (passive prospect — see MEMORY.md M10)
- **Pricing model per line:** open — thinking in progress (asked 2026-04-18, no decision yet). Revisit once first paid engagement lands; that anchor usually sets the shape
- **Deal-flow stages (HubSpot):** inbound → discovery call → proposal → signed → kickoff → delivery → invoice → post-delivery. Stages need renaming in HubSpot UI to match (default "Sales Pipeline" still in place as of 2026-04-23).
- **Lead sources by line:** none flowing yet — historical: 2018 Tim Jackson (Walking Ventures) for UGOKI; 2026 Ainars Šlesers + Vilis Krištopans (VTV) cold outreach successes
- **High-touch priority for urgent alerts:** generating leads and potential clients
- **Drafts tagged by service line in frontmatter:** yes — e.g., `service: bookkeeping`, `service: ai-build` (RAG filtering enabler)

## Geography & Dual Operations

- **Bridge angle (UK ↔ LV):** personal and family. Atis (cousin) and Juris Ņefedovs (Atis's cousin) anchor the LV side
- **Argentina:** wife's home country; long-term family base alongside Latvia. Real in-country access for the agri-tech lane
- **Latvian language register:** uses Latvian for direct LV outreach (e.g., LPV-context emails to Šlesers / Krištopans). Will need to seed `drafts/sent/` with 3–5 sent Latvian emails so the brain can voice-match — currently absent
- **Local network (East Grinstead):** not yet gathered (asked 2026-04-18). Candidates to plug in when ready: chamber of commerce, BNI, local WhatsApp groups, business directories
- **Local network (Riga):** not yet gathered (asked 2026-04-18). Candidates: LIAA, Altum, relevant accelerators
- **Cross-border compliance:** flag everything crucial for early business development. UK MTD/VAT, LV VID, EU intrastat — to be personalised when integrations land. Currently broad: alert on all government policy moves that impact UK or LV businesses
- **Working currencies:** GBP (UK), EUR (LV), ARS (AR). Needs a quick GBP↔EUR↔ARS converter surfaced in the heartbeat / chat (build later — small utility, cache daily FX rate)

## Key Contacts

_Source: C8 (service providers / network), G1 (urgent contacts), W1 (whose opinion matters)._

### Urgent / Important — alert immediately on inbound
- **Tim Jackson** — `tim@walking.vc` — Walking Ventures (General Partner & CEO Coach). 2018 UGOKI interest, 2026 Email Hub cold re-engagement
- **Matīs** — `opbagles@gmail.com`
- **Ana Laura Suárez** — `analaura.suarez@gmail.com`

### Network / Service Providers
- **Atis** — cousin, LV. Partner on Cab (setup in progress, not formalised). Features, product dev, marketing. WhatsApp; responds quickly
- **Juris Ņefedovs** — business advisor, LV. Potential investor in Cab application. Business dev, funding, distribution. WhatsApp; responds quickly
- **Gavin Hughes** — former Merkle colleague, now Principal Creative Developer at Ometria. WhatsApp. **Conflict node** — Ometria is an email-tech peer/competitor; Email Hub concept shared informally with him in March (see MEMORY.md J5)
- **Cole Medin** — AI expert, Dynamous community
- **Daniel Miessler** — AI expert (research / signal source)
- **IndyDevDan** — AI expert (research / signal source)
- **Vilis Krištopans** — LPV co-founder, former LV Transport Minister, businessman. Facebook DM; replies seldom. Potential VTV / Riga public-transport contact
- **Ainars Šlesers** — LPV co-founder, former LV Transport Minister, businessman. Facebook DM; replies seldom. Same VTV angle as Krištopans

## Notes

_(Add things learned over time here.)_

---

_This file grows as I learn more about Linards. I update it when I learn new preferences, patterns, or context._
