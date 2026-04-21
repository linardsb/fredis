# Threat Model — `memory_synthesis.py`

Scheduled weekly (Sun 08:00 Europe/London) via launchd / systemd. Reads
MEMORY.md as a whole against the last 7 days of daily logs, drafts
contradiction / resolution / kill-trigger / merge proposals, and writes
them to `Fredis/Memory/drafts/active/memory-synthesis/<ISO-week>.md`.
Advisor-mode: never mutates MEMORY.md, never sends, never edits SOUL.

## 1. Inputs

- **MEMORY.md** — own-authored long-term memory, trusted by convention.
- **Daily logs** (`Fredis/Memory/daily/YYYY-MM-DD.md`, last 7 days) —
  **untrusted**. Daily logs are appended to by the heartbeat with
  external-data-sourced entries (email snippets, Slack messages, Monday
  items). Phase 5 provenance markers tag each entry with a `source:`
  blockquote header.

**Trust boundary:** `check_injection_patterns(log_bundle)` runs before
prompt assembly. On any match → synthesis aborts, no SDK call, warning
appended to today's daily log with `source=synthesis-aborted`. Otherwise
the bundle is wrapped via `wrap_external_data(..., source="daily_logs")`
+ `TRUST_BOUNDARY_INSTRUCTION`.

## 2. Tools

`allowed_tools = ["Read", "Glob"]`. No Edit, no Write, no Bash — the SDK
cannot mutate any file. Blast radius:

- `Read` — gated by `block-secrets` (no `.env`, no credentials).
- `Glob` — read-only discovery.

The draft file under `Fredis/Memory/drafts/active/memory-synthesis/` is
written by the caller (`_run_synthesis_inner`) from `response_text`, NOT
by a Write tool call. This is a deliberate narrowing of the SDK's blast
radius: even a perfect prompt-injection that coerced the model cannot
write outside the assistant's text output.

`permission_mode="default"` (not `acceptEdits`) — any tool call the SDK
attempts that required approval would silently fail, reinforcing the
above.

## 3. Writes

- **Draft file** (`Fredis/Memory/drafts/active/memory-synthesis/<slug>.md`)
  — caller-written. Advisor-mode: Linards reviews and hand-merges.
- **State file** (`.claude/data/state/synthesis-state.json`) — local,
  per-machine.
- **Daily log** — append-only `Synthesis pass` entry.

Approval gate: advisor mode. MEMORY.md itself is read-only from this
caller. The draft file is a proposal, not an applied change.

## 4. Memory reads

- MEMORY.md — trusted (own-authored).
- Daily logs — untrusted, re-checked via injection pipeline (same policy
  as reflection). Wrapped in `<external_data source="daily_logs">`.

## 5. Outputs

- **Draft file** under `drafts/active/memory-synthesis/` — local only.
- **Daily log** — local.
- **No external surface.** No Slack send, no email, no web POST.

## 6. Failure mode

- **Injection in daily-log bundle:** abort, record `state["result"] =
  "aborted_on_memory_injection"`, warn to today's daily log. No SDK call,
  no draft file, MEMORY.md untouched.
- **SDK error:** caught, error logged to daily log, returns None. No
  partial draft written.
- **Empty SYNTHESIS_OK response:** state records `proposals_count = 0`,
  daily log gets `SYNTHESIS_OK`, no draft file written.
- **Lock timeout (concurrent run):** second invocation bails fast, no
  SDK call.

Invariants preserved under all failure modes:
- No external send.
- No SOUL edit (standalone hook + no Edit tool).
- No MEMORY.md mutation (caller-controlled write path, only under
  `drafts/active/memory-synthesis/`).
- Daily-log injection is ratcheted OUT at synthesis time (abort),
  preventing the memory-poisoning loop
  (`agent-guardrails.md` §6), same as reflection.
