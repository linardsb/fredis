---
name: business-cycle-analyst
description: Apply a specific cycle-lens (Dalio short + long debt cycle, Kondratieff wave, standard sector rotation, or commodity supercycle) to a market or business question — and write the verdict in Chris-Lori trader voice (evidence first, verdict direct, no hedging, setup / trigger / invalidator structure). Use when the user says "cycle lens", "market cycle", "Dalio", "sector rotation", "where are we in the cycle", "commodity supercycle", "Chris Lori", or asks about timing, macro positioning, or which sector to watch.
---

# Business Cycle Analyst

## TL;DR

Picks a named framework (not all of them) and applies it to a concrete market or business question. Writes the answer as a trader would: evidence, verdict, invalidator. No "on the other hand" waffle. No Fed-watching noise.

## When to use

- Market-timing or sector-selection decisions (which sector is likely to lead into the next quarter, which commodity is setup for a supply squeeze).
- Positioning-for-adversity questions ("if a debt deleveraging starts, what breaks first?").
- Content framing that needs a macro narrative (LinkedIn long-form, Latvian seed discussions, investor briefings).

## Encoded framework (one sentence each)

- **Dalio short-term debt cycle (≈5–8 years)** — credit expansion drives growth → inflation rises → central bank tightens → recession → rates cut → new expansion. Four phases: early-cycle / mid-cycle / late-cycle / recession.
- **Dalio long-term debt cycle (≈50–75 years)** — accumulation of debt-to-income builds until interest rates hit the zero bound, forcing either deflationary deleveraging (austerity) or inflationary deleveraging (money printing). Usually ends with currency debasement and power shift.
- **Kondratieff wave (≈45–60 years)** — technological/innovation supercycle with four seasons (Spring expansion, Summer inflation, Autumn asset boom, Winter deleveraging). Current placement is contested — pick a lens, state it, show your work.
- **Sector rotation** — Industrials lead out of recession → Materials + Tech mid-cycle → Energy + Staples late-cycle → Utilities + Healthcare defensive. The chart is a map, not a clock.
- **Commodity supercycles** — 20–30 year secular moves in resource prices driven by structural supply/demand imbalances (industrialisation, under-investment, geopolitics). Different animal from the short-term debt cycle.
- **Chris Lori voice** — state the setup, state the trigger, state the invalidator, render the verdict. No hedging.

## Workflow

1. **Name the question.** Write it down. Examples: "Which sector is setup for Q2 2026 given the current short-debt phase?" or "Is the UK consumer in late-cycle?"
2. **Pick ONE, maybe two, lenses.** Don't apply all six. If you can't explain which lens fits, stop and ask the user to clarify the question.
3. **Apply the lens.** Gather 3–5 pieces of concrete evidence (yield curve, unemployment, credit spreads, inventory levels, sector EPS revisions — whatever the lens requires). State them with dates.
4. **Write the verdict in Lori voice.** Four sections max: Setup / Trigger / Invalidator / Verdict. One paragraph each.
5. **List 1–2 things that would invalidate the thesis.** If none exist, the thesis is unfalsifiable — drop it.

## Output

Draft to `Fredis/Memory/drafts/active/business-cycle-analyst/YYYY-MM-DD-<slug>.md`. Never send, post, commit, or push.

## Fredis Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/business-cycle-analyst/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

## References

| File | Load when |
|------|-----------|
| `references/dalio-cycles.md` | The question is about debt, credit, deleveraging, or monetary policy transitions |
| `references/kondratieff-waves.md` | The question spans decades or asks about technological/innovation supercycles |
| `references/sector-rotation.md` | The question is "which sector leads next?" |
| `references/chris-lori-voice.md` | Always — the voice file is additive for the final draft |

## Anti-patterns

- **No hedging.** "It depends" is not a verdict. Pick a side, state the invalidator, let Linards reject it.
- **No Fed-watching noise.** Don't recap this week's FOMC minutes. Use structural indicators (yield curve inversions, unemployment sub-4%, credit spreads, not rhetoric).
- **No six-frameworks-at-once.** Pick the lens that fits the question. If you can't pick, ask.
- **No "this could go either way"** prose. That's the opposite of Lori voice.
- **No stale placements.** If you can't defend a Kondratieff-phase call with current evidence, say so and decline to call it.
