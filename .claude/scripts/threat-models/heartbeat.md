# Threat Model — `heartbeat.py`

Scheduled every 120 min (Europe/London, 05:00–20:00) via launchd / systemd.
Proactively gathers from six platforms, runs a guardrail pre-filter, and
yields a Slack alert. Advisor-mode invariants: never send, never edit SOUL,
never leave the sandbox.

## 1. Inputs

- **Gmail** (Python API) — read-only scopes (`gmail.readonly` +
  `gmail.compose`). Subject / snippet / sender metadata per thread.
- **Calendar** (Python API) — read-only (`calendar.readonly`).
- **Asana** (REST) — task titles / due dates / assignee / project.
- **Monday.com** (GraphQL, read-only token) — item names, status, updates.
- **Slack** (Bot + App tokens) — channel messages in the monitored channels
  from the last 2 hours.
- **GitHub** (PAT read-only) — commits / review-requests / mentions.
- **Guardrail state** (`.claude/data/state/guardrail-state.json`) — local
  file, previous verdict.
- **Heartbeat state** (`.claude/data/state/heartbeat-state.json`) — local
  file, previous snapshot for diffing.

**Trust boundary:** every external-platform field passes through
`sanitize.sanitize_external_text` + `wrap_external_data` before reaching
the main SDK prompt. The 4-layer pipe: regex pre-check → markdown escape
→ XML trust boundary → Haiku semantic-eval.

## 2. Tools

Main heartbeat agent: `allowed_tools = ["Read", "Write", "Edit", "Bash",
"Glob", "Grep", "Skill"]`.

Blast radius:
- `Read` / `Glob` / `Grep` — limited by `block-secrets` PreToolUse hook
  (no `.env`, no `id_rsa`, etc.).
- `Write` / `Edit` — gated by `block-dangerous-commands` (sandboxed to
  repo + Fredis/ dirs), `block-secrets` (exfil content check),
  `block-soul-edit` (SOUL.md protected), `block-template-residue`.
  Phase 1: matchers now cover `MultiEdit` + `NotebookEdit` too.
- `Bash` — `block-dangerous-commands` (destructive / outbound /
  financial / social patterns blocked); `validate_bash_command` hook
  attached in-process as additional defense.
- `Skill` — calls skill definitions under `.claude/skills/`. Skills
  inherit the parent's allowlist.

## 3. Writes

- **Daily log** (`Fredis/Memory/daily/YYYY-MM-DD.md`) — append-only;
  Phase 5 added `source:` provenance header so the reflection + flush
  consumers know which lines came from external data vs. Claude's
  reasoning.
- **Drafts** (`Fredis/Memory/drafts/active/`) — advisor-mode; Linards
  reviews + sends.
- **Gmail draft** (create only, never send) via `query.py gmail
  create-draft`.
- **State files** (`.claude/data/state/*.json`) — local, machine-specific,
  git-ignored.

Approval gate: advisor mode. No outbound messaging APIs, no
`drafts.send`, no Gmail send. Outbound mutations trip
`block-dangerous-commands`.

## 4. Memory reads

- `Fredis/Memory/HEARTBEAT.md` — local file (trusted, rule-set).
- `Fredis/Memory/USER.md` — local (trusted, user-authored).
- `Fredis/Memory/daily/YYYY-MM-DD.md` — contains
  external-data-sourced entries; provenance lines let the reader see
  origin.

Injection-pipeline on memory reads: **no** — heartbeat only reads its
own recent state. Daily log reads happen in `memory_reflect.py` +
`memory_flush.py`, which DO re-apply the pipeline (Phase 5).

## 5. Outputs

- **Slack DM** to Linards's bot — the one external surface, but
  delivered to a single private user. Phase 4 added
  `_neutralise_mentions` so broadcast triggers in Claude's response
  don't fire group notifications.
- **Daily log** — local file, not external.
- **PII reach:** Gmail subject+snippet, Asana/Monday task names,
  calendar event titles — none beyond what Linards already sees.

## 6. Failure mode

- **Prompt injection caught (Layer A regex or Layer B Haiku):**
  verdict=`fail` → heartbeat aborts entirely, Slack alert sent.
- **Haiku guardrail timeout / exception (Phase 2):** verdict=`error`
  → external data is stripped from the main agent prompt, Slack
  alert sent, heartbeat proceeds with local context only
  (drafts + habits + GitHub) so Linards still sees a heartbeat signal.
- **Tool blocked (hook exits 2):** the hook's stderr feedback is shown
  to Claude; Claude tries a different approach or gives up. No data
  leaks.
- **Unknown SDK exception:** caught at the top level, error logged to
  daily log + hook execution log; heartbeat exits non-zero (scheduler
  detects).

Invariants preserved under all failure modes:
- No email/Slack/social send without `--i-confirm-send` flag.
- No SOUL.md edit.
- No writes outside repo / Fredis/.
- No secret redaction bypass (layered `redact-secrets` hook on
  PostToolUse; shape-based scrub in Phase 6).

## Retrieval surface (Phase 9)

After guardrail verdict is known, `_extract_signals` pulls a short query
string per NEW item (email subject, task name, Slack first line) and
`_gather_relevant_memories` runs `search_hybrid(limit=3, min_score=0.5)`
per signal, dedupes by `chunk_id`, and caps the aggregate at 15 hits.
Results wrap as `<external_data source="memory_recall">` and inject as a
`## Relevant Memories` section alongside the other external-data
wraps — inside the same `TRUST_BOUNDARY_INSTRUCTION` fence.

**Verdict gate:** retrieval runs only on `pass` / `suspicious`. It is
skipped on `fail` (heartbeat aborts entirely) and `error` (external
data is stripped from the prompt — feeding retrieval without the
signals it was meant to contextualise would be misleading).

`db.touch_chunks(ids)` runs only after the main-agent run completes.
Aborted turns do not reinforce retrieval signal.

**Latency:** local FastEmbed + SQLite ≈ 200 ms p95 per query,
≤ 15 queries per heartbeat on the steady state — negligible next to
heartbeat run time (~5 s).

Fail-safe: per-signal search exception skips just that signal; import
failure of `memory_search` returns `("", [])` and the heartbeat runs
without the recall section.
