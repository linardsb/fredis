---
name: data-and-experimentation
description: Data science + experimentation — ML modeling (XGBoost, Scikit-learn, SHAP, MLflow, causal inference via DiD), feature engineering, cross-validated AUC/PR evaluation, SQL / Pandas / NumPy (senior-data-scientist); hypothesis tests, effect sizes, confidence intervals, Bonferroni correction, sample-size calculation (statistical-analyst); A/B experiment design — testable hypothesis writing, sample-size estimation pre-launch, outcome interpretation with practical rigour (experiment-designer). Use when user says "A/B test", "experiment design", "sample size", "hypothesis test", "confidence interval", "effect size", "statistical significance", "XGBoost", "SHAP", "causal inference", "difference-in-differences", "MLflow", "feature engineering", "AUC-ROC", "Scikit-learn", "interpret results".
---

# data-and-experimentation

TL;DR — stats + experimentation + ML modeling. Three references: data-science (modeling depth), statistical-analysis (test rigour), experiment-design (pre-launch + interpretation). Invocations typically traverse: design (experiment-design) → size (statistical-analysis) → model or analyse outcome (data-science).

## Routing table

| Trigger | Reference |
|---|---|
| "XGBoost", "SHAP", "causal inference", "DiD", "feature engineering", "MLflow", "AUC-ROC / AUC-PR", "Scikit-learn", "classification", "regression" | `references/data-science.md` |
| "hypothesis test", "sample size" (calculation), "effect size", "confidence interval", "Bonferroni", "z-test", "t-test", "statistical significance" | `references/statistical-analysis.md` |
| "experiment design", "A/B test plan", "testable hypothesis", "pre-launch sizing", "interpret A/B results", "practical significance" | `references/experiment-design.md` |

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
| `references/*/scripts/` | Sample-size calculator, hypothesis tester, confidence interval scripts |

## Anti-patterns

- Reporting statistical significance without effect size + CI. A p-value without an effect size is information-free.
- Running the ML-modeling reference on a problem that's really an A/B test. Use `experiment-design.md` first — modeling over observational data when an experiment would answer it cleaner is backwards.
- LLM-eval / judge-based eval requests. Those are a future Phase 5.2.5 reference (`llm-evals.md`), not in this bundle yet.
