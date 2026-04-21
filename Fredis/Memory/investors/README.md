# investors/

VC / angel / PE pipeline (CRM-style). Tracks relationships and pipeline state, not domain knowledge.

- `_pipeline.md` — master table (name · firm · stage · last contact · next action)
- `{investor}.md` — per-investor profile (warm/active relationships only — cold/speculative stays in the table)

Heartbeat scans `_pipeline.md` daily and surfaces any row where `next action due ≤ today` or any warm contact with > 10 business days since last touch.
