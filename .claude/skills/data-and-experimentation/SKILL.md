---
name: data-and-experimentation
description: Data science + experimentation — ML modeling (XGBoost, SHAP, MLflow, causal inference / DiD), feature engineering, AUC / PR evaluation, SQL / Pandas / NumPy (senior-data-scientist); hypothesis tests, effect sizes, CIs, Bonferroni, sample-size (statistical-analyst); A/B experiment design + pre-launch sizing + outcome interpretation (experiment-designer); LLM eval harness — judge-based with rubric calibration, fixture-driven regression, online vs offline, failure-mode taxonomies (llm-evals). Use when user says "A/B test", "experiment design", "sample size", "hypothesis test", "confidence interval", "effect size", "statistical significance", "XGBoost", "SHAP", "causal inference", "difference-in-differences", "MLflow", "AUC-ROC", "Scikit-learn", "interpret results", "LLM eval", "judge-based eval", "agent regression test", "eval harness", "LLM-as-judge", "G-Eval", "fixture-driven eval", "eval-as-code".
---

# data-and-experimentation

TL;DR — stats + experimentation + ML modeling. Three references: data-science (modeling depth), statistical-analysis (test rigour), experiment-design (pre-launch + interpretation). Invocations typically traverse: design (experiment-design) → size (statistical-analysis) → model or analyse outcome (data-science).

## Routing table

| Trigger | Reference |
|---|---|
| "XGBoost", "SHAP", "causal inference", "DiD", "feature engineering", "MLflow", "AUC-ROC / AUC-PR", "Scikit-learn", "classification", "regression" | `references/data-science.md` |
| "hypothesis test", "sample size" (calculation), "effect size", "confidence interval", "Bonferroni", "z-test", "t-test", "statistical significance" | `references/statistical-analysis.md` |
| "experiment design", "A/B test plan", "testable hypothesis", "pre-launch sizing", "interpret A/B results", "practical significance" | `references/experiment-design.md` |
| "LLM eval", "judge-based eval", "LLM-as-judge", "agent regression test", "eval harness", "G-Eval", "fixture-driven eval", "eval-as-code", "failure-mode taxonomy" | `references/llm-evals.md` |

## Shared assets

- `_shared/draft-path-convention.md`
- `_shared/atis-test.md` — optional but encouraged on experiment-conclusion drafts ("would Atis bet £1k on this read?" is a useful sanity gate on effect-size claims).

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/data-and-experimentation/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

## References

| File | Load when |
|---|---|
| `references/data-science.md` | ML modeling, causal inference, feature pipelines, model evaluation |
| `references/statistical-analysis.md` | Hypothesis tests, sample-size calculators, confidence intervals |
| `references/experiment-design.md` | A/B experiment planning and outcome interpretation |
| `references/llm-evals.md` | Judge-based evals, fixture-driven regression suites, online vs offline regimes, failure-mode taxonomies for LLM-backed products |
| `references/*/scripts/` | Sample-size calculator, hypothesis tester, confidence interval scripts |

## Anti-patterns

- Reporting statistical significance without effect size + CI. A p-value without an effect size is information-free.
- Running the ML-modeling reference on a problem that's really an A/B test. Use `experiment-design.md` first — modeling over observational data when an experiment would answer it cleaner is backwards.
- Treating LLM evals like A/B tests. A/B frameworks assume independent samples and stable distributions; LLM behaviour drifts with prompt, tooling, and model changes — use `llm-evals.md` for fixture-driven regression instead.
