# TODO — Active execution roadmap

**Source of truth:** `.agent/plans/fredis-context-management-roadmap.md` — all phase detail, files touched, tests, verification steps live there. This file is the scannable status.

---

## Shipped

- [x] **Phase 0** — Per-channel tool / MCP / skill / model scoping (`7905b0b`, 2026-05-03)
- [x] **Phase A** — Token & turn-count surfacing + nudge (`44c8d82`, 2026-05-03)

---

## Pending — sequential

- [ ] **Phase 3** — Metric verification + patch + min-tier-gap guard (~½ day) — **BLOCKS Phase 4**
  - 3.1 Verification (read-only, no code) — Agent SDK `Usage` semantics + production DB cross-check
  - 3.2 Patch `_extract_context_tokens` to use `input_tokens` only; add `NUDGE_MIN_TURNS_BETWEEN_TIERS = 3`; schema columns for soft/hard turn-count
  - 3.3 Tests
  - 3.4 Post-deploy verification on Saulera + smoke thread
  - 3.5 Docs in `.claude/scripts/CLAUDE.md`

- [ ] **Phase 3a** — Plugin-skills bloat measurement (~30 min, parallel with Phase 3)
  - Investigation; conditional doc updates only if plugins add >5k tokens/turn

- [ ] **Phase 4** — `/consolidate` directive (~4h)
  - **Pre-gate:** Phase 3 shipped + ≥3 days observation + Linards green-light
  - 4.1 Directive parser (`save_directive.py`)
  - 4.2 Topic resolver (`engine.py`)
  - 4.3 Canon template + writer + schema migration (3 new columns) + skill files
  - 4.4 Slack response + nudge-timestamp consumption
  - 4.5 Stale-name flag (folds in former Phase C)
  - 4.6 Tests + docs

- [ ] **Phase 5** — Observation gate (≥3 days, no code)
  - Gates Phase 6. Skip Phase 6 entirely if "forgot to consolidate" rate is zero.

- [ ] **Phase 6** — `memory_reflect.py` background safety net (~½ day) — *conditional on Phase 5 outcome*
  - Extract canon writer to `canon_writer.py` if Phase 4 left it inline
  - Add `auto_consolidate_thresholded_threads()` pass

- [ ] **Phase 7** — OB1 naming sweep (~1h, deferrable)
  - Frontmatter rename + migrate existing canon files

---

## Background (parallel, not gating)

- [ ] **Phase 3-lite compliance observation** — 2 weeks
  - Sample one turn per channel per week. If >5% out-of-scope skill invocation attempts → escalate to Option Y (plugin-dir hard filter, ~2-3 days extra).

---

## OB1 backlog (idea pool — pull individually, not sequenced)

Tracked in `.agent/plans/fredis-ob1-integration.md` + `.agent/plans/ob1/*.md`. Skip indefinitely unless a specific trigger fires.

- [ ] OB1.1.6 — External-client wiring (Cursor / Claude Desktop / ChatGPT) — when you actually want Fredis context from a non-Claude-Code client
- [ ] OB1.2 — Typed frontmatter on new captures (~1 day)
- [ ] OB1.3 — Entity wiki (`memory_entities.py`, ~1-2 days)
- [ ] OB1.4 — Claudeception evaluator on drafts (~½ day)
- [ ] OB1.5 — Sensitivity tier upgrade (conditional on denylist leak)
- [ ] OB1.6 — Historical importers (conditional on archives)

---

## Workflow per phase

1. Re-read the relevant phase block in `.agent/plans/fredis-context-management-roadmap.md` to refresh context.
2. *(Optional)* Run `/be-planning <phase>` if more than a couple of days have passed since the roadmap was last revised — it re-pressure-tests assumptions against current code state. Not strictly required, since each phase already has step-by-step checklists in the roadmap.
3. Execute file-by-file in dependency order (schema → config → modules → engine → tests → docs).
4. Follow `## Operational playbook — every phase ship` in the roadmap (pre-flight tests → commit → push → auto-deploy → post-deploy verification).
5. Tick the box in this file once shipped. Append commit hash on the same line.

**Trigger phrase to start work:** `go Phase <N>` — I'll read the phase, run any read-only verification first, then propose the patch for confirmation before editing.
