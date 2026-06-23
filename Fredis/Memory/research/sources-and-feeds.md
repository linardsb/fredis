# Sources & Feeds — canonical daily-pull config

Single source of truth for the free web sources + YouTube channels that feed the **daily brief**.
All free, no paid APIs. Lanes map to `Fredis/Memory/research/{lane}/`.

Built 2026-06-23. Keep this file in sync with `.claude/scripts/daily_brief.py` (the collector embeds the
same lane queries + channel IDs).

Legend: `RSS` = machine-readable feed · `API` = free, needs a free key · `browse` = no clean feed.

---

## Part A — Interest surfaces + keywords

The 8 content-engine lanes (= the 8 `MEMORY.md` research lanes) plus 5 more surfaces memory tracks.

| # | Surface | Keywords (search strings) |
|---|---------|---------------------------|
| 1 | AI / agentic eng | AI agents, agentic, LLM agents, Claude Code, MCP, multi-agent, agent orchestration, coding agents, AI evals, context engineering, harness/intent engineering, tool use, RAG, vertical AI for SMBs, local/on-device LLMs, agent reliability |
| 2 | AI in agriculture ★ | AI agriculture, agritech, precision agriculture, regenerative agriculture, farm robotics, crop AI, UK SFI, EU CAP, precision fermentation, alt-protein |
| 3 | AI robotics | humanoid robots, embodied AI, physical AI, robot learning, robotics foundation model, legged robots, cobot |
| 4 | Materials (mycelium/3DP) | mycelium, mushroom leather, biomaterials, biofabrication, mycelium packaging, additive manufacturing, 3D printing, concrete printing |
| 5 | Building business | building in public, solo founder, indie hacker, bootstrapped, one-person business, AI automation agency, micro-SaaS |
| 6 | Markets & macro | commodity supercycle, macro cycle, sector rotation, debt cycle, Fed policy, recession, Kondratieff, Dalio |
| 7 | Investing / compounding | compound interest, compounding, long-term investing, dividend growth, index funds, dollar cost averaging, financial independence, value investing, buy and hold |
| 8 | Policy & legislation | EU AI Act, UK AI regulation, AI governance, AI policy, EU tech regulation, consultations.gov.uk, tap.mk.gov.lv, EU Reg 1370/2007 |
| 9 | Investable watchlist | see `research/markets/watchlist-tickers.md` (9 ticker sub-lanes; ADA 100k position) |
| 10 | Product lanes | Email Hub (email dev, ESP, CMS, MarTech, MJML, Klaviyo, Ometria-watch); VTV (public transport optimisation, Rīgas Satiksme, transit, GTFS); Cab (ride-hailing, Bolt, two-sided marketplace) |
| 11 | Geographies | United Kingdom / East Grinstead · Latvia / Latvija / Rīga · Argentina |
| 12 | UK + LV admin | Companies House, HMRC, UK VAT threshold, SFI; Lursoft, VID, SIA, Saeima, cross-border UK–Latvia tax |
| 13 | X-follow signals | 27 handles in `USER.md` — pull their blogs/Substacks/YouTube, not raw X (Nitter is dead) |

---

## Part B — Free feeds per lane (operational)

Google News RSS turns any keyword string into a live UK-localised feed (verified working 2026-06-23):
`https://news.google.com/rss/search?q=QUERY&hl=en-GB&gl=GB&ceid=GB:en`

| Lane | Google News RSS query (URL-encoded) |
|------|-------------------------------------|
| AI / agentic eng | `%22agentic+AI%22+OR+%22AI+agents%22+OR+%22Claude+Code%22+OR+%22LLM+agents%22` |
| AI in agriculture | `%22precision+agriculture%22+OR+%22AI+agriculture%22+OR+%22farm+robotics%22+OR+agritech` |
| AI robotics | `%22humanoid+robot%22+OR+%22embodied+AI%22+OR+%22physical+AI%22+OR+%22robot+learning%22` |
| Materials | `mycelium+OR+%22mushroom+leather%22+OR+%22additive+manufacturing%22+OR+biofabrication` |
| Building business | `%22solo+founder%22+OR+%22indie+hacker%22+OR+bootstrapped+OR+%22AI+automation+agency%22` |
| Markets & macro | `%22commodity+supercycle%22+OR+%22sector+rotation%22+OR+%22Fed+policy%22+OR+%22debt+cycle%22` |
| Investing / compounding | `%22dividend+growth%22+OR+%22index+funds%22+OR+%22financial+independence%22+OR+%22value+investing%22` |
| Policy & legislation | `%22EU+AI+Act%22+OR+%22UK+AI+regulation%22+OR+%22AI+governance%22+OR+%22EU+tech+regulation%22` |
| Latvia | `Latvia+economy+OR+Latvia+transport+OR+Latvia+startup+OR+Latvia+AI` |

**Native feeds (cleaner than Google News where they exist):**
- UK business — BBC Business `https://feeds.bbci.co.uk/news/business/rss.xml` `RSS`
- Latvia — LSM English `https://eng.lsm.lv/feeds/` `RSS`
- AI research — arXiv `https://rss.arxiv.org/rss/cs.AI+cs.CL+cs.LG+cs.MA` · cs.RO for robotics `RSS`
- AI/dev frontier — Hacker News `https://hnrss.org/frontpage?points=150` + keyword `https://hnrss.org/newest?q=agentic` `RSS`
- AI research pulse — Hugging Face Daily Papers `https://huggingface.co/api/daily_papers` `RSS`/API
- EU policy — EUR-Lex predefined RSS `https://eur-lex.europa.eu/content/help/search/predefined-rss.html` `RSS`
- UK policy — GOV.UK finder + `.atom` (e.g. `https://www.gov.uk/search/policy-papers-and-consultations.atom`) `RSS`
- Markets data — FRED `https://fred.stlouisfed.org/` `API` · Stooq EOD CSV (no key) · CoinGecko `https://www.coingecko.com/en/api` `API`
- Reddit workhorses — `r/LocalLLaMA`, `r/robotics`, `r/3Dprinting`, `r/SaaS` + `/.rss` `RSS`

---

## Part C — YouTube channels (transcripts → synthesis)

RSS of new uploads: `https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID`

| Channel | Handle | channel_id | Lane |
|---------|--------|-----------|------|
| IndyDevDan | @indydevdan | `UC_x36zCEGilGpB1m-V4gmjg` | AI / agentic eng |
| David Shapiro | @DaveShap | `UCvKRFNawVcuz4b9ihUTApCg` | AI / post-labour |
| Nate B Jones | @NateBJones | `UC0C-17n9iuUQPylguM1d-lQ` | AI strategy |
| AI Engineer | @aiDotEngineer | `UCLKPca3kwwd-B59HNr-_lvA` | AI / agentic eng |
| Matt Pocock | @mattpocockuk | `UCswG6FSbgZjbWtdf_hMLaow` | AI / dev tooling |
| YC Root Access | @ycrootaccess | `UCcefcZRL2oaA_uBNeo5UOWg` | Building business |
| Unsupervised Learning | @unsupervised-learning | `UCnCikd0s4i9KoDtaHPlK-JA` | AI + security |
| 20VC | @20VC | `UC9jkoB5oKe1eAGZ5zOW6iZA` | VC / founders |

Transcript fetch: `youtube-transcript-api` (Python). **Caveat:** the caption endpoint is IP-sensitive — works
from a residential IP (Linards's Mac); a datacenter IP (VPS) is often gated. Server-side needs a
residential-proxy / `pot`-token / fallback transcript service.

---

## Part D — Universal tricks

- Substack/WordPress/Ghost blog → append `/feed`.
- GOV.UK → any finder page + `.atom`.
- YouTube channel → `youtube.com/feeds/videos.xml?channel_id=UC...` (resolve `@handle`→`UC...` from the channel page HTML).
- Reddit → subreddit + `/.rss` or `/top/.rss?t=day`.
- Email-only newsletter (The Batch, Import AI) → `kill-the-newsletter.com` bridge.
- X accounts → no clean free native feed; use the author's blog/Substack/YouTube RSS, or Inoreader free tier.

---

## Part E — Daily-brief job

**Collector:** `.claude/scripts/daily_brief.py` — pulls all Part-B lane feeds + Part-C channel uploads
(+ recent transcripts), writes a raw bundle to `Fredis/Memory/drafts/active/daily-brief/YYYY-MM-DD_bundle.md`.

**Synthesis:** Claude reads the bundle and writes the brief (the heartbeat morning-brief pass, or
`claude -p "$(cat synthesis-prompt)" < bundle.md`). Synthesis prompt:

> You are Fredis writing Linards's morning brief for {date}. From the bundle below, produce:
> (1) "Three things that move today" — highest-signal items tied to his priorities (lead-gen, Email Hub,
> Frontier pillar). (2) "From your channels" — 3-4 video syntheses, 4 bullets + one "so what" each; **drop
> videos that don't match his lanes** (e.g. sports). (3) "Lane scan" — top web hit per lane, one line + so-what.
> (4) "Skipped" — transparency on what was dropped/stale/failed. Rules: British English, no emoji, neutral
> voice, blunt. One screen. Anchor every "so what" to Email Hub / VTV / Cab / lead-gen / his research lanes.

Run order, recency window, and per-lane caps live in the collector's constants.
