# research/

Active research lanes. Each subfolder is a watchlist + capture area for one lane (markets, policy, ai, robotics, materials, agriculture). The `materials/` lane has sub-lanes `mycelium/` and `3d_printing/` (see MEMORY.md Research Lanes). Default sharing: see MEMORY.md M9.

---

## Papers Convention

The analyst agent (per MEMORY.md — not yet built) writes fetched papers into `{lane}/papers/`. One markdown file per paper; no raw PDFs (link to source URL instead — add a `_raw/` subfolder later if a specific lane needs offline PDFs).

**Filename:** `YYYY-MM-DD_<lowercase-hyphenated-slug>.md` — e.g., `2026-04-19_mycelium-acoustic-panels-rtu.md`. Date prefix gives free chronological sort and "this week's papers" globs.

**Frontmatter schema:**

```yaml
---
title: "Paper title"
authors: [Lastname, Lastname]
source: arXiv | PMC | SSRN | EUR-Lex | NBER | MDPI | ...
url: https://...
published: YYYY-MM-DD
fetched: YYYY-MM-DD
lane: ai | robotics | markets | policy | agriculture | materials | mycelium | 3d_printing
relevance_score: 1-5            # 5 = drop everything, 1 = archive-only
tie_in: active-project | service-line | personal-interest | frontier-only
tie_in_detail: "One sentence — why this paper matters to Linards specifically"
actionability: "What he could do within 2 weeks"  # optional, only when score >= 4
tags: [free-form]                # e.g., [lv-policy, tim-jackson, mycelium-packaging]
---
```

**Tie-in categories:**

| `tie_in` | Meaning | Active mappings |
|---|---|---|
| `active-project` | Direct ammo for what's shipping now | Email Hub, VTV, UGOKI, GERBONI, Cab |
| `service-line` | Validates / informs a service being prepped | AI-agentic for SMBs, Agri×AI, AI robotics |
| `personal-interest` | Latent curiosity / future move | Mycelium, 3D printing |
| `frontier-only` | Defensive positioning, no direct tie | Generic frontier AI with no SMB angle |

If the agent can't articulate a specific `tie_in_detail`, default to `tie_in: frontier-only` — don't force a tie.

**Body structure** (matches M8):

```markdown
## 5-bullet exec summary
- ...

## Key findings
- ...

## Why it matters (for Fredis lanes)
- ...  # expand on tie_in_detail
```

**Surfacing rules:** see `HEARTBEAT.md → Research Papers`.
