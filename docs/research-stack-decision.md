# Research Stack for Fredis Analyst/Researcher/Innovator Skills

**Date:** 2026-04-19
**Status:** Exploration — not yet committed
**Context:** Deciding which web scraping / research APIs to wire into Fredis skills that will support research and innovation decision-making.

---

## Problem

Fredis needs a research layer that can back analyst, researcher, and innovator skills. The layer must:

- Pull clean text from arbitrary web pages (static + JS-rendered)
- Support semantic/conceptual discovery (innovator skill — finding non-obvious connections)
- Return source URLs for citation (decisions will be made on this output)
- Stay cheap — ideally free
- Not add operational weight beyond what Fredis already carries

Ruled out upfront:
- Browser-automation-as-default (Playwright/Bright Data) — overkill, heavy
- Perplexity MCP — returns answers, not raw sources; bad for analyst work

---

## The Decision Space

### MCP vs Skill

Web scraping needs a runtime (HTTP client, headless browser, auth, retries). A skill alone is markdown + instructions — it can describe *how* to scrape but still needs a runtime to do it. **MCP wins for the execution layer.** A skill wraps *when and how* to invoke the MCP (same pattern as `direct-integrations`).

### Paid hosted vs self-host vs built-in

Three tiers considered:

| Tier | Example | Cost | Capability |
|---|---|---|---|
| Built-in (Anthropic subscription) | `WebSearch`, `WebFetch` | $0 | ~85% of what's needed |
| Self-hosted OSS | Firecrawl, Crawl4AI | Infra only | Full feature set; maintenance cost |
| Hosted API | Firecrawl, Tavily, Exa | $0-83/mo | Best-in-class; vendor lock |

Built-in `WebSearch` + `WebFetch` cover mainstream content well but have two real gaps:
1. **JS-heavy sites** — WebFetch struggles with SPAs; Firecrawl/Crawl4AI don't
2. **Semantic discovery** — built-in is keyword-only; Exa's embedding search is uniquely useful for innovator work

---

## Options Considered

### Firecrawl (hosted or self-host)
- Best pure extractor — cleanest markdown, handles JS, schema-based structured extraction
- **Hosted:** $16/mo Hobby (3k credits) or $19 Starter (3k) / $83 Standard (100k)
- **Self-host:** AGPL-3.0, Docker Compose, ~2-3GB RAM, loses "Fire-engine" (anti-bot layer) in self-hosted mode
- **Gap:** search is weaker than dedicated search APIs; no semantic search

### Tavily (hosted)
- Agent-optimized search + extract + crawl in one server
- **Free:** 1,000 credits/mo (1-2 per query depending on depth)
- **Paid:** $27-30/mo for ~10k credits
- **Best for:** fresh/time-sensitive queries, quick agent loops
- **Gap:** extraction depth less than Firecrawl

### Exa (hosted)
- Embedding-based semantic search — `findSimilar(url)` is the killer feature for innovator work
- **Free:** 1,000 searches/mo
- **Weakness:** bad at time-sensitive content (24% on FreshQA benchmark)

### Crawl4AI (self-host, open source)
- Drop-in Firecrawl replacement, LLM-optimized markdown
- **Has official MCP server** — easy swap from Firecrawl MCP
- Runs in Docker/Colima — same footprint as Firecrawl Simple
- **Cost:** $0 ongoing; infra only

### Jina Reader (hosted, free)
- `https://r.jina.ai/<url>` → clean markdown. No auth needed for basic use
- 1M tokens/mo free with API key
- **Best for:** default "read this page" in skill flows; fastest setup of anything reviewed

### Discarded

- **Playwright / Bright Data MCPs** — capable but heavy; only needed if local extraction consistently fails
- **Brave Search API** — keyword only; removed free tier
- **Apify** — platform overhead, pay-per-actor
- **fetch-mcp / fetcher-mcp** — too minimal for decision-grade research
- **SerpAPI** — tight free tier, keyword only

---

## Heartbeat Considerations

Fredis heartbeat fires every 120 min during active hours (~8 runs/day). If heartbeat does 5 research searches/run = **1,200/mo** — blows through any free tier meant for skills.

**Solution: RSS feeds for heartbeat, APIs for skills.**

RSS is strictly better than search for recurring signal scans:
- Deterministic — subscribe once, new items surface
- Free, no rate limits
- Cacheable → fits existing state-diff pattern (same as email/task diffing)
- ~10 lines of `feedparser` code

Starter feed list:
- ArXiv cs.AI, cs.LG
- Anthropic news, OpenAI blog, DeepMind blog
- Stratechery (free posts)
- FT markets, Bloomberg Opinion
- UK gov.uk policy feeds
- Hacker News front_page
- Google Alerts → RSS for custom keywords

Pair with built-in `WebFetch` for follow-up reads. Cost: $0.

---

## Self-host Infra Options

### VPS vs Mac-only

Fredis VPS currently runs: Postgres/pgvector, vault git-sync, scheduled heartbeat, Slack chat bot, memory indexing.

If Mac is awake 10-12h/day (active hours = 15h → 3-5h gap):
- Heartbeat misses 3-5 cycles/day — acceptable given advisor-mode (nothing urgent waits)
- Slack bot offline when Mac closed — fine if mostly at desk
- Postgres → SQLite fallback (already supported)
- Vault git-sync works on launchd

**Conclusion: Mac-only is viable given usage pattern.** Firecrawl/Crawl4AI can run on Colima.

### If keeping VPS — cheapest options (April 2026)

| Provider | Plan | $/mo | Specs |
|---|---|---|---|
| **Hetzner CX22** | 2 vCPU / 4GB / 40GB | ~$5 | Winner |
| **Contabo Cloud VPS 10** | 3 vCPU / 8GB / 75GB | $4.50 | Slower CPU, lower reliability |
| **OVH VPS Starter** | 1 vCPU / 2GB / 20GB | ~$4 | Fine for current stack |
| DigitalOcean Basic | 1 vCPU / 1GB / 25GB | $6 | 1GB too tight once Firecrawl/Crawl4AI added |

### Colima resource sizing

If self-hosting on Mac via Colima:
```bash
colima stop
colima start --cpu 4 --memory 6 --disk 30
```
Firecrawl wants ~2GB, Playwright service up to 4GB. Default Colima (2 CPU / 2GB) insufficient.

---

## Recommended Stack

**$0/mo, more capable than Firecrawl-alone because it adds semantic search:**

| Layer | Tool | Why |
|---|---|---|
| Primary extractor (self-host) | **Crawl4AI (Colima)** | Firecrawl equivalent, free, official MCP server |
| Zero-setup extractor (hosted) | **Jina Reader** | `r.jina.ai/<url>`, no auth for basic, free tier generous. Default for one-off reads. |
| Semantic search | **Exa free tier** | 1k/mo. `findSimilar()` unique; essential for innovator skill. |
| Fresh / keyword search | **Built-in `WebSearch`** | Already in Anthropic subscription. Covers Exa's FreshQA weakness. |
| Heartbeat signal scan | **RSS (feedparser)** | Deterministic, state-diffable, zero cost. |
| Fallback for anti-bot walls | Hosted Firecrawl $19 only if needed | Monthly-toggle based on actual failure rate |

### Skill → Tool Mapping

- **Analyst** — Crawl4AI (schema extraction) + built-in WebSearch (fresh results)
- **Researcher** — Jina Reader (fast extract) + Exa (semantic breadth) + built-in WebSearch (recent)
- **Innovator** — Exa `findSimilar` (cross-domain) + Jina Reader (follow-up extraction)

---

## Open Questions (defer until implementation)

1. Does the innovator skill actually need Exa, or is built-in WebSearch good enough? → answer empirically after a few weeks of use
2. Run Crawl4AI on VPS or Colima? → depends on VPS retention decision
3. Add hosted Firecrawl fallback? → only if local Crawl4AI hits anti-bot walls in practice

---

## Decisions Deferred

- Whether to keep the VPS or go Mac-only
- Whether to commit to Crawl4AI self-host vs. start with Jina Reader + Exa alone (lighter footprint)
- Final skill specs for analyst / researcher / innovator

No code written or services subscribed to. This doc captures the reasoning to resume from.
