# Slack → Vault Memory Routing — Design Options

**Status:** Option A chosen 2026-04-21. Options B and C recorded here for future reference in case A turns out too rigid.

**Problem statement:** Slack conversations happen across multiple topical channels (e.g. `#ideation`, `#market-research`, `#marketing`). The current memory pipeline (chat → chat.db session → memory_flush → daily log → memory_reflect → MEMORY.md → weekly memory_synthesis) is channel-blind — everything lands in `Fredis/Memory/daily/YYYY-MM-DD.md` chronologically, regardless of which channel the conversation happened in. The vault's topical folders (`research/markets/`, `patterns/`, `competitors/`, etc.) only get written to by humans.

The question: how should channel context propagate into the topical structure of the vault?

---

## Option A — Static channel → folder map _(chosen)_

A small YAML config at `.claude/config/channel-routing.yaml` maps channel names / IDs to destination folders:

```yaml
channels:
  # Solo-founder topical channels
  ideation:        Fredis/Memory/ideation/
  market-research: Fredis/Memory/research/markets/
  marketing:       Fredis/Memory/marketing/
  product:         Fredis/Memory/product/
  legal:           Fredis/Memory/legal/

  # Explicitly route DMs into daily log (keep global chronology)
  dm:              Fredis/Memory/daily/

  # Catch-all for unmapped channels
  "*":             Fredis/Memory/daily/
```

On session end, `memory_flush.py` reads the Slack channel from the session metadata, resolves the destination folder, and appends a summary file there.

**Writes:** per-thread file, `<folder>/YYYY-MM-DD_<thread_ts>_<slug>.md`.

**Reads:** `memory_search.py` remains folder-agnostic (indexes all of `Fredis/Memory/`). Chat engine, when resuming a thread, boosts retrieval from the thread's channel folder first.

**Pros:**
- Predictable — the user controls routing explicitly.
- Easy to implement, easy to reason about.
- Works with existing memory_index.py (no schema change).

**Cons:**
- Rigid — off-topic chatter in `#marketing` still files under marketing.
- Every new channel needs a config edit (defaults to daily log if unmapped).
- Doesn't handle multi-topic conversations well (e.g. a discussion that bridges marketing and product).

---

## Option B — Channel as hint, Claude decides destination

Same YAML config, but the channel mapping is a **hint**, not a rule. At session end, Claude:

1. Reads the conversation transcript.
2. Considers the channel hint as default.
3. If the content is clearly off-topic relative to the channel (e.g. a genuine legal question in `#marketing`), routes to the more appropriate folder instead.
4. Writes the summary + records the chosen folder + reasoning in a short header block.

**Pros:**
- Cross-topic detours land in the right place.
- Channel config stays lightweight — Claude's judgment fills the gaps.
- Small config file stays evergreen because Claude handles edge cases.

**Cons:**
- Non-deterministic — you can't always predict where a conversation will land without opening it.
- Slight extra cost (another LLM call at session end to classify).
- Debugging: when you can't find a conversation, you have to check multiple folders OR rely on the routing decision header.

**When to upgrade from A to B:** when A starts producing enough "wrong folder" entries that you notice. Probably triggers around 10+ active channels or when topics start bleeding across channels.

**Implementation delta from A:**
- Add a classifier step to `memory_flush.py` that takes `(transcript, channel_hint, available_folders)` and returns `(chosen_folder, reasoning)`.
- Write `reasoning` into the file's YAML frontmatter so the routing trail is inspectable.
- Keep the channel config as `hints:` instead of `channels:`.

---

## Option C — Content tags, folders as views _(most Obsidian-native)_

Forget folder routing entirely. Every summary gets rich YAML frontmatter and lands in a single flat `Fredis/Memory/conversations/YYYY-MM-DD_<thread>.md`:

```yaml
---
channel: marketing
channel_id: C012ABCDEF
thread_ts: 1729532400.123456
participants: [linardsberzins, fredis]
topics: [pricing, positioning, go-to-market]
entities: [acme-co, launch-plan-q2]
outcomes: [decision, action-item]
---
```

Folder "views" live as Obsidian notes with Dataview queries:

```markdown
# Marketing view

\`\`\`dataview
TABLE thread_ts, topics, outcomes
FROM "Memory/conversations"
WHERE channel = "marketing" OR contains(topics, "marketing")
SORT file.ctime DESC
\`\`\`
```

**Pros:**
- A single conversation can surface under multiple topic views (via `topics` array).
- Zero information loss — the full conversation is in one place; views are queries.
- Channel rename doesn't break anything — frontmatter keeps channel_id for stable lookup.
- Extends naturally to other dimensions (entities, outcomes, people).

**Cons:**
- Requires Obsidian Dataview plugin + willingness to write query notes.
- Discovery is query-driven; if you forget the query, you lose the view.
- Longer summary files because frontmatter adds overhead.
- Search via `memory_search.py` still works but topic-folder boost is no longer meaningful (all conversations live in one folder).

**When to upgrade from A or B to C:** when you find yourself frequently wanting to view conversations by multiple cross-cutting dimensions (e.g. "show me every conversation about pricing across ALL channels"), or when channel renames start causing headaches.

**Implementation delta from A or B:**
- `memory_flush.py` writes ALL summaries to `Fredis/Memory/conversations/` with full frontmatter.
- A classifier extracts `topics`, `entities`, `outcomes` from the transcript (similar effort to B's folder classifier, but outputs tags instead of a folder).
- Pre-seed Obsidian with Dataview-based view notes at `Fredis/Memory/views/<topic>.md`.
- Channel-folder config still exists for the "route hint" but only informs search ranking, not file location.

---

## Hybrid path forward

The three options are compatible:

- Start with **A** (single config, per-channel folders, session-end summaries).
- If rigid routing bites, add **B**'s classifier step on top of A — folders still exist, but Claude gets override authority.
- If you find yourself wanting cross-cutting views, **C** is a parallel addition: dual-write summaries to both the channel folder (for easy browsing) and `conversations/` (with tags for Dataview views).

No option locks you out of the others. Don't over-engineer upfront.

---

## Decision rationale

A was chosen because:

1. **Simplicity** — single YAML config, no extra LLM calls in the write path.
2. **Predictability** — the user always knows where a conversation will land.
3. **Graceful degradation** — unmapped channels fall back to the existing daily-log path; worst case is we're exactly where we started.
4. **No Obsidian plugin dependency** — works with vanilla Obsidian.
5. **Fits the existing mental model** — the vault already has topical folders; this just connects Slack to them.

The "rigid routing" concern is real but low-severity for a solo user who controls which topics live in which channels. Revisit in 3–6 months.
