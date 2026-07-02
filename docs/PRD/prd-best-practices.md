# PRD best practices — how to write the lean hypothesis PRD

**Status: REFERENCE.** The "how" behind the project-start gate in `prd-as-project-start-condition.md`. Use this when shaping any PRD in the cockpit.

**Origin:** distilled from the workshop in this folder — `PRD_workshop_transcript.txt` (Rasmus Widing, ~8 yrs PM, ~200 PRDs written; with Cole Medin) — and the worked example `slack-threads-prd.html`.
**Companions:** `prd-as-project-start-condition.md` (the two-stage gate) · `docs/agents/the-team-phase1-build-prompt.md` (consumes this).

---

## What a PRD is

> A PRD "defines a problem, and our hypothesis about solving that problem, in a form a team — or your AI — can challenge before building and judge after shipping." If it carries no falsifiable hypothesis, "it isn't really a PRD. It's just an opinion, your own bias, or your agent's bias sitting in a template."

A modern PRD is **short, opinionated, and about the bet — not the solution.** The worked Slack example has **no solutions section anywhere**. That's not a gap; it's the discipline.

## Three different jobs — never squash them

| Document | Answers | Holds |
|---|---|---|
| **PRD** | *what* problem + *why* | the problem + the intent + the falsifiable hypothesis |
| **Spec** | *how* | the engineering decisions (data model, API, architecture) |
| **Roadmap** | *when* | the sequencing |

"Almost all of the confusion in this space comes from squashing them together." You may keep them in one file — as long as every reader can tell the sections apart. In Fredis's two-stage model: the **lean PRD is the gate**; the existing `.claude/commands/create-prd.md` is the **spec**, and it runs only *after* the hypothesis survives.

## The five marks of a good PRD

Rasmus: "most PRDs miss at least one or two of these, including my own."

1. **Problem grounded in evidence** — real numbers and real customer conversations, not opinion/vibes/bias. The Slack example names them: ">100 msgs/day — ~7% of channels but >60% of attention", mute/leave rates, QBR themes. *Not* "the user wants this."
2. **A hypothesis with a separate RIGHT condition and a separate WRONG condition.** "A wrong condition is the single most skipped line in any PRD." See the template below — it is the heart of the document.
3. **Success metrics shaped as outcomes, not engagement.** Something you'd be willing to be judged on, tied to the behaviour you're changing — "people staying and posting", not "the threads button got clicked X times".
4. **An explicit non-goals section.** "Writing down what you're deliberately not doing is how you stop building from quietly sprawling." (Slack: no multi-level threading, no retroactive threading, not replacing channels.)
5. **Open questions, honestly stated.** "A good PRD is honest about what it still doesn't know" — and those questions are what discovery/experiments go and answer.

## The switch test (don't forget it)

Solving a real pain is only the first 10% — people already cope today, even clumsily. The real question a PRD must answer is **not** "does this solve the problem?" but **"does it solve it so much better than what they do today that they'll actually switch?"** If that isn't a clear yes, they won't choose you, "no matter how clean and technically excellent you build it." *Solving the problem is table stakes; solving it better than today is the product.* (This is the JTBD-switch lens — see the `idea-validation` skill.)

## The hypothesis template (the heart of the PRD)

Fill this in. It doesn't always look exactly like this, but it forces you to pin down what matters:

```
We believe that  [the change we're making]
will cause        [these specific users]
to                [this specific behaviour / mechanism — not just the end result]
resulting in      [an outcome we actually care about].

We'll know we're RIGHT if  [a leading signal]  within  [a timeframe].
We'll know we're WRONG if   [a counter-signal appears, OR a guardrail metric moves the wrong way].
```

It forces you to name: the actual change · who specifically it's for · the behaviour and mechanism (not just the hoped-for result) · a timeframe (so you don't over-invest) · and **failure defined as something other than "it didn't work."**

**Cautionary tale — Klarna.** Their unspoken hypothesis was "AI can take over most of our customer service and save a fortune." There was **no wrong condition** — no pre-agreed line like "we'll know we've pushed too far if CSAT drops past X." So when quality slipped, nothing caught it; the reversal came ~18 months later as a public CEO admission. "A wrong condition isn't pessimism — it's the contract that lets you switch back cheaply instead of slowly, expensively, and embarrassingly."

## The sticky-note rule — after the PRD

> Build the **thinnest slice that most easily and quickly tests the hypothesis**, then measure.

If it holds → keep going (you may even throw the slice away and build it properly). If it fails → throw it away completely and move to the next hypothesis. "That's the whole difference between a PRD that drives discovery and a PRD that pretends discovery already happened." Anything not in service of proving the hypothesis is deferred.

## Problem vs solution-in-disguise

A problem statement names the observed problem **without baking in a fix or an unproven cause**:

| Statement | Verdict |
|---|---|
| "New customers who place one order rarely come back within their first month." | ✅ Problem |
| "Add a one-tap *reorder your last meal* button to the home screen." | ❌ Solution |
| "Customers need a quicker way to get back to meals they've ordered before." | ⚠️ Solution in disguise — "quicker way to get back" has already picked *reorder shortcut*. |
| "Customers abandon their cart **because checkout has too many steps**." | ⚠️ Solution in disguise — the cause is unproven; "fewer steps" is smuggled in as fact. |

The pattern: everything after "because…" is usually an untested solution/hypothesis wearing a problem's clothes.

## Match the rigour to the risk (especially solo)

- **Greenfield** — dominant risk is "does anyone even want this?" → lean on fake-doors, user interviews.
- **Brownfield** (where most work lives) — dominant risk is "will this break/annoy existing users and make them leave?" → lean on A/B tests + data you already have.
- **Over-planning is a risk game.** If shipping the wrong feature could make a big enterprise customer leave, 9 months of planning is worth it (Slack). **If it's just you building something new, an hour on one page is enough.** Don't out-plan the stakes.

## Three altitudes — PRD work is *intent* engineering

1. **Prompt engineering** — optimise the wording.
2. **Context engineering** — optimise what the model knows, and when.
3. **Intent engineering** — optimise for actual business impact: *getting the right thing built in the first place.* This is where the PRD lives, and where most of the leverage is.

## Ready-to-use lean PRD skeleton

Matches the worked example. Keep it to ~one page for solo work.

```
# <Title> — PRD

## Problem statement      (evidence: real numbers / customer quotes — no solution)
## Why now                (what changed that makes this worth doing today)
## Hypothesis             (the template above — RIGHT and WRONG conditions both filled in)
## Target user            (primary · secondary · explicitly NOT the target)
## Non-goals              (out of scope for v1 — kills scope creep)
## Risks & assumptions    (each risk → the assumption it rests on → how we de-risk it)
## Open questions         (what we still don't know — drives the experiments)
## Success metrics        (outcome-shaped · target · cohort · window · a guardrail metric)
## Experiments            (the thinnest slice that proves/refutes the hypothesis)
# NOT here: data model, API, architecture, sequencing — those live in the spec / roadmap.
```
