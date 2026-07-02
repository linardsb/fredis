# PRD as a project-start condition

**Status: DECISION NOTE / PLANNING.** Sets how a PRD gates every new project. No code here. Build waits for an explicit go-ahead.

**Date:** 2026-06-30
**Origin:** bullet 2 of the handwritten note (`img_0144.jpeg`) — *"add [Claude] Code's create-prd to Fredis as a project-start condition"* — grounded in the material in this folder:
- `PRD_workshop_transcript.txt` — Rasmus Widing (8-yr PM) + Cole Medin workshop on PRDs as intent.
- `slack-threads-prd.html` — the worked example of a good lean PRD (Slack Threaded Messages, reconstructed).
- `.claude/commands/create-prd.md` — the PRD slash-command Fredis already ships.

**Companions:** `docs/agents/fredis-agent-architecture.md` (the role-agent question) · `.agent/plans/fredis-archon-mission-control.md` (the Archon harness this PRD feeds).

---

## The principle (from the workshop)

> "A PRD defines a problem, and our hypothesis about solving that problem, in a form a team can challenge before building and judge after shipping." — if it has no falsifiable hypothesis, "it isn't really a PRD. It's just an opinion, your own bias, or your agent's bias sitting in a template."

A PRD is **intent, not solution.** The heart of it is a **hypothesis with a separate right condition and a separate wrong condition** — most PRDs say what success looks like; few say what failure looks like. Engineering decisions (data model, API, sync, indexing) are *not* in the PRD — they live in the **spec**. The worked example states this cleanly: *"The PRD says we will not break old clients. The spec says how."*

## The catch — `create-prd.md` is actually a spec template

Fredis's existing `.claude/commands/create-prd.md` is a 15-section document covering Executive Summary, **Core Architecture**, **Technology Stack**, **API Specification**, **Implementation Phases**. That is the "solution sitting in a template" the workshop warns against — it is a **spec**, not the intent-PRD the note is asking to gate projects with.

## The resolution — two stages, not two competing templates

**Decision (per Linards, 2026-06-30): two stages.** Use both documents; rewrite neither. Reposition, don't replace.

```
  LEAN HYPOTHESIS PRD          THINNEST MVP            SPEC                 ARCHON BUILD
  (intent gate)        ──►     that proves      ──►    (the "how")    ──►   (worktree →
  = PROJECT-START              the hypothesis          = existing           draft PR)
    CONDITION                  right/wrong             create-prd.md
                                                       repositioned
  ▲ problem + falsifiable      ▲ build only what       ▲ architecture,      ▲ only after the
    hypothesis + non-goals       proves the bet;         stack, API,          hypothesis has
    + success metrics            defer the rest          phases               survived
```

1. **Lean hypothesis PRD = the project-start condition.** Short, opinionated, about the bet — not the build. This is the gate the note asks for: no project opens without it.
2. **Existing `create-prd.md` = the spec, repositioned.** It runs *after* the hypothesis survives, which is exactly where the workshop puts it: *"the full spec, the one you build the real thing from, comes after your hypothesis has landed."* No rewrite — just relabel it as the spec stage and stop treating it as the front gate.

This dissolves the conflict (both documents earn their place) and is surgical (nothing is deleted).

## The lean PRD shape (the gate's contents)

Modelled on `slack-threads-prd.html` — the concrete "good PRD" in this folder:

| Section | What it captures |
|---|---|
| **Problem statement** | The real, observed problem (with evidence, not assertion). |
| **Why now** | What changed that makes this worth doing today. |
| **Hypothesis** | *We believe [change] will cause [cohort] to [behaviour], resulting in [measurable outcome]. Right if [condition]. **Wrong if [condition].]*** — both conditions mandatory. |
| **Target user** | Primary, secondary, and explicitly **not** the target. |
| **Non-goals** | Out of scope for v1, to kill scope creep. |
| **Risks & assumptions** | Each risk → the assumption it rests on → how it's de-risked. |
| **Open questions** | Resolved during build, flagged here. |
| **Success metrics** | Target · cohort · window, including a **guardrail** metric. |
| **Experiments / discovery plan** | The cheapest tests that prove the hypothesis before full commit. |

Everything else — data model, API, mobile sync, indexing — is **deliberately not in the PRD**; it is named as belonging to the spec.

## Fredis already does most of this

The lean-PRD method is largely native to the skill stack — the gate composes existing skills rather than adding capability:

- **`idea-validation`** — Mom Test problem interviews, MLP scoping, **explicit kill criteria** and the Atis-£1k smoke test. This is the problem + non-goals + falsifiability discipline.
- **`launch-governance`** — falsifiable hypothesis, AARRR metrics gate, pre-mortem, kill triggers (`Fredis/Memory/gates/*.yaml`, read by the heartbeat). This is the right/wrong-condition + success-metrics + guardrail machinery.
- **`product-shape`** — MVP architecture, pricing, positioning. This is the thinnest-MVP and the spec-adjacent shaping.

So the gate is mostly **sequencing what exists**, not building new skills.

## Wiring it to Archon (the project-start condition, mechanically)

- **The lean PRD is the input artifact to every Archon run.** Cole's model: every workflow has a defined input (issue / ticket / plan.md) and a defined output (a draft PR). The lean PRD is that input for new-project work; the issue is the input for brownfield fixes.
- **Extend `archon-interactive-prd`, don't re-propose it.** The mission-control plan's Addendum 2 already names `archon-interactive-prd` (a guided 5-phase PRD with approval gates) as "half of 'shape the brief' ships." The lean-PRD gate **shapes that workflow's output** toward the hypothesis-first structure above — it is an extension, not a new workflow. (Audit Conventions: this was checked against the existing plan before writing.)
- **HITL gate #1 sits on the PRD.** Fredis drafts the lean PRD (sourcing from `meetings/`, `retainers/`, idea-validation), Linards approves it, *then* the build fires. This is the first of the two HITL gates a solo operator can afford (the second is post-implementation).
- **Source / sink.** Draft PRDs land in `Fredis/Memory/drafts/active/` per advisor mode; a matching HubSpot Review ticket + `[DRAFT]` Slack notice make it reviewable; nothing auto-builds.

## The create-prd slash command — what to change

Per the two-stage decision, the existing `.claude/commands/create-prd.md` is **kept as the spec template** and **not rewritten now**. If a dedicated lean-PRD command is wanted later, it would be a separate, thin command that "asks the right questions" (the workshop's framing of a good create-prd: *"it doesn't create the perfect template, it's designed around asking you the right questions"*) — deferred until the gate is exercised in practice.

## Next concrete step (on go-ahead)

1. Author the lean-PRD gate as a declared structure (the table above doubles as the spec) sourced from `idea-validation` + `launch-governance`.
2. Wire it as the input artifact + HITL gate #1 to the Archon `new-client-site` / brownfield runs (extends `archon-interactive-prd`).
3. Leave `create-prd.md` in place as the post-hypothesis spec stage.

No build until an explicit go-ahead.
