# Phase-1 → Phase-2 Gate Review (P5)

**Date:** 2026-07-01
**Decides:** whether to open **Phase 2 — The Team on Eve** (PA / Marketing / Sales domain agents).
**Stance:** adversarial — default to *not yet* unless the evidence is clear (per playbook P5).
**Inputs read this session:** `docs/agents/fredis-agent-architecture.md` (gate condition + the three carried questions + the "honest tension"); `Fredis/Memory/repositories/merkle-email-hub.md` Dispatch History (the P4 run-set, verbatim); `Fredis/Memory/drafts/active/the-team/phase1-PRD.md` (the pre-registered hypothesis). P4b (client-site) has **no dispatch history** — it did not run.

---

## Verdict: **NO-GO** (hold — not a kill)

Do **not** open Phase 2. This is a *hold at not-yet-proven*, not a teardown: the Phase-1 harness is validated for one narrow class of work (keep it — see §Keep), and the exit criteria to revisit are concrete (§What would change this).

The NO-GO is **not my opinion applied to the runs — it is the PRD's own pre-registered decision rule applied to the runs.** The switch-test outcome lands in the hypothesis's explicitly-named *ambiguous middle*, whose rule is "hold, don't expand." Phase 2 sits **two gates** beyond what the evidence authorises: the P4 run-set never cleared the "clear RIGHT" bar that (a) opens even **P4b**, let alone (b) Phase 2.

### Why it rests on the pre-registered rule, not hindsight

`phase1-PRD.md:29`, verbatim: *"Ambiguous middle = not-yet-proven → hold, don't expand. (E.g. passes the gate but neutral on attention, or 1 clean run + 2 mediocre.) Neither open Phase 2 nor P4b nor widen the cockpit — run more, or reassess. **Only a clear RIGHT opens P4b; any WRONG stops the build.**"*

The P4 run-set is precisely "1 clean real win + 1 gate-green-but-inert" — the named ambiguous case. So P4b never opening is **the protocol working as designed**, not an oversight to backfill.

---

## Evidence — the N=3 mapped to the verbatim RIGHT / WRONG conditions

**RIGHT if** (`phase1-PRD.md:27`, three conjuncts, **all** required): each of 3 issues yields a draft PR passing `make lint types test` with **≤1 fixup**, **AND** Linards judges dispatch→review **lower-attention** than in-session, **AND** he **chooses to dispatch** #2/#3.

**WRONG if any one of** (`:28`): harness **adds** attention net across the 3; PRs **routinely need full rework** (≳50% on ≥2 of 3); **any containment breach** (writes to Fredis/vault, or auto-send/merge/push).

| # | Issue (class) | PR | Gate ≤1 fixup? | Lower-attention? | Chose to dispatch next? |
|---|---|---|---|---|---|
| 1 | #302 test-only (harness proof) | #303 | ✓ 0 fixup, merged | n/a (not a real build task) | — |
| 2 | #308 · 50.6.4 constantize (**mechanical/refactor**) | #310 | ✓ 0 fixup, merged | **Yes** — review was a pre-scoped 5-field env check | — |
| 3 | #307 · 51.3 tool-call cap (**logic-wiring / runtime-model**) | #309 | ✓ 1 fixup | **No** — gate-green but *functionally inert*; catching it took reverse-engineering the execution model | **No** — diagnosis concluded "re-plan in-session, NOT re-dispatch" |

**Conjunct 1 (gate ≤1 fixup): 3/3 MET.** The harness itself is sound — hardened over the run-set to structural gate-before-PR (`denied_tools:[Bash]` on every AI node but the two PR pushers; informed-retry `fix→gate2`; graceful gate-fail). As an *engineering deliverable*, P1–P4 succeeded.

**Conjunct 2 (lower-attention): SPLIT → not met across the set.** True for mechanical work; **false** for logic-wiring — #309 passed the gate while the change never fired on the live path (`_ToolCallCounter.record_tool_call()` has zero production call sites; `BaseAgentService` is single-shot). The gate structurally cannot see "never called on the live path." That is the class where you'd *most* want leverage, and it's the class the harness gave a false-green on.

**Conjunct 3 (chose to dispatch next): failed for the follow-up.** The recorded decision on 51.3 was *hand-fix in-session, do not re-dispatch* (the cap's real site is an unstated threat-model call — a human design decision, not a dispatchable brief).

**Is it a clean WRONG?** No. No "routine full rework on ≥2 of 3" (only one real PR was unmergeable, and via a *plan* defect, not rework). **Zero containment breaches** — engine shut down post-review, every output a draft PR, nothing auto-merged (the merges were Linards's explicit instruction, his hands). The safety guardrail (`:63`) **held** in full.

→ Neither clear RIGHT nor WRONG ⇒ **ambiguous middle ⇒ hold, don't expand.**

### One caveat the hypothesis measured around

"Gate-green" is a **narrower** claim than "mergeable." The harness gate (`make lint types test`) structurally omits the review-time gates — network **pip-audit** + **Trivy** container scan — so both green PRs were still CI-red on pre-existing dependency vulns and needed a separate fix (#306) before merge. The PRD anticipated this (`:51`: full `make ci` / GitHub CI "is the review-time gate, not the harness signal"), so it is **not** a WRONG — but it does mean even the RIGHT-side wins clear a lower bar than "shippable," which softens the RIGHT side rather than strengthening it.

---

## The three gate questions (mapped 1:1 to the prompt)

### Q1 — Friction: did issue→PR (and brief→site) beat by-hand, or did a WRONG condition trip?

**Answered in full in §Evidence above** — in one line: **neither a clean RIGHT nor a clean WRONG.** Across the N=3 the RIGHT condition's three conjuncts split (gate ≤1 fixup met 3/3; *lower-attention* and *chose-to-dispatch-next* failed for the logic-wiring class), and no WRONG condition cleanly tripped (no routine full rework; zero containment breaches). That is the PRD's pre-registered **ambiguous middle → hold, don't expand.** And **brief→site (P4b) never ran**, so half the RIGHT surface is untested.

### Q2 — Opus-everywhere vs cost: does the roster earn its keep without small models? → **Skip separate agents (defer the roster)**

**Direct answer: no — the roster does not earn its keep on the evidence.** Walking your three named resolutions explicitly:

- **Not "revisit small models."** That option only helps if the roster were *valuable but too expensive* — i.e. model price is the blocker. It isn't. The architecture doc's own "honest tension" (`:120-124`) puts the 4-agent expansion's net-new value at "modest" *regardless* of price, and the P4 switch-test reinforced it: the one demonstrated win (mechanical/refactor dispatch) is exactly the class where an in-session Claude is *already* cheap and fast. Cheaper models cannot rescue a roster whose problem is thin value, not cost.
- **Not "accept Opus cost" — not on current evidence.** This is a legitimate resolution (the gate defines "resolved" to *include* it, `:188`) *if* you judge the qualitative value is there. The runs don't show it: dispatch earned its keep on cheap-anyway mechanical work and *misled* on the logic-wiring work where leverage would actually matter (51.3 gate-green-but-inert). Paying the Opus bill to industrialise the cheap case is weak justification for a second framework plus three agents.
- **→ Resolution: "skip separate agents" — defer the roster.** It is not cost-blocked, it is value-unproven; so the disciplined move is to extend what already exists (heartbeat/reflection + skills + the validated harness) and reopen the roster only if a concrete task-class shows a domain agent beating a skill+harness. This is a recommendation on a call that is ultimately yours to ratify — but the evidence points one way, and it dovetails with the substrate answer below.

**Note — model routing is your pending decision, and it does not gate this verdict.** The NO-GO rests on **Q1** (friction sitting in the PRD's pre-registered *ambiguous middle*); even if you later choose "accept Opus cost," that alone would not open Phase 2, because a *clear RIGHT* on friction is a separate, still-unmet precondition. So you can settle model routing on your own timeline — it neither blocks this gate nor is unblocked by it.

### Q3 — Eve vs Fredis-native loops (the substrate decision) → **Fredis-native**

**Substrate: Fredis-native SDK loops, not Eve.** Nothing in the P4 run-set demonstrated a need for a second agent framework. What was proven is that a **contained Archon build-harness** works for a narrow task class — a *harness* result, not an *agent-roster* result. Adopting Eve adds a whole framework to carry three draft-only personas for a solo operator whose bottleneck is his own review attention (per memory: Saulera is run solo; the constraint is review, not compute). Simplicity First + the "modest net-new value" finding both point the same way: **extend the existing heartbeat/reflection loops + skills, defer Eve until a concrete need names itself.**

### Additional carried question (architecture doc, *not* in the gate prompt) — Sales-persona host bundle

**Moot until Phase 2 opens; recommendation stands as `executive-leadership`** (the architecture doc's own lean). Sales is closer to founder/deal motion than to product-discovery, and executive-leadership already absorbs the CEO/founder-coach/war-room personas. No evidence from P4 bears on this — it is a Phase-2 packaging call, parked with the rest of Phase 2.

---

## Keep (this is not a backdoor GO)

Retain the **one** validated Phase-1 capability: the Archon build-harness for **mechanical/refactor Email Hub dispatch**, advisor-mode, draft-PR-only. Keeping a proven Phase-1 capability is **not** a Phase-2 approval — it is banking the part of Phase 1 that cleared its bar and stopping there. Continue to dispatch mechanical Email Hub issues where they're a clean win; hand-fix logic-wiring in-session.

---

## What would change this answer (NO-GO exit criteria)

Ranked by how much each moves the verdict:

1. **A clear RIGHT on more P4 runs — the durable driver.** Run more Email Hub issues, weighted toward **logic-wiring / runtime-model** tasks (the class that failed), and clear *all three* RIGHT conjuncts: gate ≤1 fixup **AND** Linards judges lower-attention **AND** he chooses to dispatch the next rather than hand-fix. By the PRD's own rule this is what opens **P4b** in the first place.
2. **Then P4b (client-site brief→site) — the currently-blank second domain.** It has never run — correctly, because the clear-RIGHT that gates it never came. A clean P4b win is the offsetting second-domain data point we entirely lack today. (Note: P4b alone would **not** flip this to GO — it removes a *reason we can't reach GO*, it is not itself a *reason to GO*.)
3. **A concrete task-class or portability need a *domain agent* does materially better than a Fredis skill + the Archon harness.** Absent one, the cost and substrate calls (Q2/Q3) keep pointing at "extend Fredis-native," and the roster stays weakly justified.
4. **An explicit Q2 override from you** — a deliberate "accept Opus-cost because the qualitative value is worth it," backed by a value case the current runs don't show. (This overrides the recommendation; it is *not* "revisit small models," which doesn't address the thin-value finding.)

---

## Honesty caveats

- **"Meaningfully faster/cleaner than by hand" for 50.6.4 is a judgement, not a measured baseline** — no stopwatch was run on hand-fixing the same issue. That only strengthens "not yet."
- **N of *real* build tasks = 2**, not 3 (#302 and the #304 fires were test-only / harness-validation). The RIGHT condition asks for 3 real issues; the sample of representative work is thinner than the headline "3/3 gate-green" suggests.
- The harness's genuine, bankable success is **infrastructural** (contained, hardened, structurally gate-before-PR). That is real and worth keeping — it is just not the same claim as "demonstrably reduced Linards's review friction across the board," which is what the Phase-2 gate requires.

---

**STOP.** P5 ends here. Do not open P6 (or P4b, or Phase 2) without an explicit go-ahead from Linards.
