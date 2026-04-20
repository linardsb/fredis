# LLM Evals

TL;DR — evals are first-class: fixture-driven, judge-based, regression-guarded. An agent without an eval harness is an agent whose quality is assumed, not measured.

## 1. Eval-as-code

Evals live alongside the agent or tool they test, version-controlled in the same repo. One eval file per capability:

```
<capability>/
├── service.py
├── tests/            # unit + integration tests
└── evals/
    ├── fixtures.yaml         # input / expected pairs
    ├── judge_prompts.md      # rubrics for LLM-as-judge scoring
    ├── eval_runner.py        # loads fixtures, runs, scores, reports
    └── runs/                 # historical run outputs (gitignored or stored elsewhere)
```

Treating evals as code — reviewed, versioned, PR-gated — is the difference between "we have evals" and "we learn from evals". If an eval can't be traced to a commit, it can't be trusted as a regression gate.

## 2. Judge-based evaluation (LLM-as-judge)

Most agent outputs aren't one-to-one matchable against a fixed string. LLM-as-judge closes the gap:

- **Judge prompt** — explicit rubric: "Score this output 1–5 on `factual_accuracy`, `follows_instructions`, `cited_sources`. Return JSON `{score, reasoning}`."
- **Rubric dimensions** — 2–5 per eval. Broad dimensions (helpfulness) aren't actionable; narrow dimensions (cites at least one source from the provided corpus) are.
- **Calibration** — hand-score a small gold set (50–200 examples); check that the judge's scores correlate with the human labels. Recalibrate whenever the judge model or judge prompt changes.
- **Judge model isolation** — the judge should NOT be the same model family as the agent under test. Same-family judges over-agree with their own outputs (the G-Eval paper documents this bias directly). Use a smaller or different-family model as judge.

## 3. Fixture-driven evals

Input / expected pairs stored in YAML or JSONL, next to the agent code:

```yaml
# evals/fixtures.yaml
- id: research_001
  input:
    query: "Summarise the key architectural decisions in <scenario>"
    corpus: "fixtures/corpus_001.md"
  expected:
    must_mention: ["vertical slice", "adapter pattern"]
    must_cite: ["corpus_001.md#section-3"]
    rubric_scores:
      factual_accuracy: { min: 4 }
      cited_sources: { min: 4 }
```

Fixtures are the unit currency of evals. They're versionable, reviewable, diffable. When a regression shows up, you add the failing case as a new fixture — the next run re-verifies the fix didn't break.

Classes of fixtures worth maintaining:
- **Happy path** — representative common inputs.
- **Edge cases** — short / long / empty / malformed inputs.
- **Known regressions** — every historical bug becomes a permanent fixture.
- **Adversarial** — prompt-injection attempts; see `../../security-engineering/references/agent-guardrails.md`.

## 4. Regression evals per agent or tool

Every PR that touches agent code, prompt files, or tool definitions runs the eval suite in CI. Merge-blocking rules:

- Aggregate score must not drop below the prior run's aggregate by more than a calibrated threshold (e.g. 2%).
- No individual regression fixture may go from pass to fail.
- New fixtures added in the PR must pass.

Reporting format — a short markdown comment on the PR:

```
Eval run 4f2a9c (llm-opus-4-7, judge=haiku-4-5)
Aggregate: 4.12 (↓0.03 from main)
Dimensions: factual_accuracy 4.3, cited_sources 3.9, follows_instructions 4.1
Regression fixtures: 47/47 pass
Full report: evals/runs/4f2a9c.md
```

One table, one delta vs. main, a link to the full run. Enough signal to merge-or-block without drowning the reviewer.

## 5. Online vs offline evals

Two regimes, both necessary:

### Offline — deterministic development loop

- Run locally or in CI.
- Fixed fixtures + deterministic seeds (temperature 0, fixed random state where the agent uses one).
- Fast feedback — a full suite should finish in a few minutes, not an hour.
- Used during iteration; treat as the primary gate for "is this change worth merging".

### Online — production-trace sampling

- Sample 1–5% of real production runs.
- Score them with the same judge prompts offline uses.
- Catches real-user-distribution drift that synthetic fixtures miss.
- Feeds back into the fixture pool: any low-scoring online sample becomes a candidate new regression fixture.

Online evals don't gate production (latency-sensitive), but they gate the decision to escalate orchestration level (see `../../engineering/references/agentic-orchestration-patterns.md` §2).

## 6. Failure-mode taxonomies

Aggregate scores hide the shape of the failures. Taxonomise so fixes are targeted:

- **Hallucination** — claim not supported by the provided corpus.
- **Tool misuse** — wrong tool chosen, or the right tool called with wrong args.
- **Policy violation** — output breaks a hard rule (advisor-mode breach, secret leaked, sent content that shouldn't have been sent).
- **Cost overrun** — ran over the token budget or turn cap.
- **Latency overrun** — exceeded the P95 latency target.
- **Judge disagreement** — judge flagged low confidence; flag for human review.

Tag every failed fixture with one of these in the run report. Ship each fix with a named taxonomy entry so the trend across runs is legible.

## 7. Cross-links

- **Backend shape** — `../../engineering/references/agentic-application-architecture.md` for the VSA layout that puts `evals/` next to the capability it tests.
- **Orchestration escalation** — `../../engineering/references/agentic-orchestration-patterns.md` §2; evals are the gate for moving L1 → L2 → L3 → L4.
- **Guardrail regression** — `../../security-engineering/references/agent-guardrails.md`; the injection-defense suite is itself a fixture set — run it on every prompt or tool change.

## 8. Anti-patterns

- **Evals written after the agent ships.** The eval suite drives design; writing it last means the agent was built without a target. Start with 10 fixtures before writing the first prompt.
- **Judge and agent from the same model family.** Self-agreement bias inflates scores. Different family, often smaller model.
- **No human-labeled calibration set.** A judge that's never been compared to human labels is an opinion, not a measurement.
- **Aggregate-score-only reporting.** Regressions hide in dimensions. Publish per-dimension scores.
- **Fixtures frozen in time.** The fixture set should grow; every production failure becomes a fixture. A static fixture set means the agent is only measured against yesterday's problems.
- **Skipping the merge gate.** Evals that don't block merges are nice-to-have, not load-bearing. Make them block.
