# Bet Review

> Phase 5.2 skeleton — structural framework + source list. Deep framework bodies to be filled in a follow-up authoring pass.

## Purpose

Monthly (or on-demand) portfolio review. Per lane: evidence + verdict + next action. Written in Chris-Lori rhythm (setup / trigger / invalidator / verdict). Flags zombies (continue × 3 months with no new evidence) and forces focus decisions when solo-founder load is saturated.

## Frameworks applied (sources for follow-up authoring)

- **Annie Duke, *Thinking in Bets*** (2018) — separate decision quality from outcome quality.
- **Charlie Munger inversion** — "how would I kill this bet if I were trying to?"
- **Eric Ries pivot-or-persevere** (*Lean Startup*, 2011) — explicit binary at each review cycle.
- **Chief-of-staff cadence + stale-decision surfacing** (ported from `c-level-advisor/chief-of-staff/`).
- **CPO invest/maintain/kill voice** (ported from `c-level-advisor/cpo-advisor/`).
- **Org-health monthly scored template** (ported from `c-level-advisor/org-health-diagnostic/`).

## Pre-run data ingestion

`bet-review` is data-heavy. Before writing a verdict, call `query.py` to gather per-lane state:

- `asana overdue` + `asana due-soon --days 30` — task evidence per lane.
- `monday overdue` + `monday my-items` — Monday-tracked work.
- `github recent --hours 720` — commits per lane repo.
- `gmail search "lane-keyword"` — threads touched this month.
- Read `Fredis/Memory/gates/*.yaml` — gate status per lane.
- Read `Fredis/Memory/drafts/sent/` — prior `bet-review` outputs for drift detection.

(Dedicated `scripts/gather_month.py` helper planned — deferred to follow-up authoring pass.)

## Per-bet verdict schema

```markdown
### Lane: <email-hub / vtv / cab>

**Setup:** (3 sentences — what's been happening)
**Trigger:** (what would move this from continue → ship)
**Invalidator:** (what kills this bet)
**Verdict:** (continue / pivot / pause — one line)

**Evidence (this month):**
- ...

**Biggest risk:**
- ...

**Flip evidence that would change the verdict:**
- ...

**Gate breaches this month:**
- ... (from gates YAML + heartbeat drafts)

**Sunk-cost flag:** yes/no (and why)

**Drift flag:** yes/no — "continue" X months running without new evidence
```

## Solo-founder enforcement rule

If two lanes = "continue" + the third lane's gate breached → force a focus decision. Fredis refuses to emit three parallel "continue" verdicts when a breached gate exists.

## Monthly cadence (future — not wired yet)

Planned: new launchd plist `com.linards.bet-review.monthly.plist` — first of each month, posts drafting prompt + Slack DM. Does NOT auto-review; prompts Linards to run the skill. Deferred to follow-up authoring pass.

## Structure (to be filled)

1. **Gather month data** — integrations via `query.py` (see above).
2. **Load prior reviews** — via `memory_search.py --path-prefix drafts/sent/bet-review`.
3. **Detect drift** — "continue" × 3 months without new evidence → zombie flag.
4. **Per-lane verdict** — schema above, Chris-Lori voice.
5. **Portfolio-level Munger inversion** — "how would I kill all three bets?"
6. **Solo-founder saturation check** — enforce focus rule.
7. **Atis £1k gate** — would Atis bet £1k on each "continue" verdict?
8. **Decision-logger pass** — anything worth retiring from the active-decisions list (DO_NOT_RESURFACE).

## Ports / attribution

- chief-of-staff / cpo-advisor / org-health-diagnostic: MIT, ported from `alirezarezvani/claude-skills/c-level-advisor/`.
- Thinking-in-Bets + Munger + Ries pivot-or-persevere composition: de novo.
