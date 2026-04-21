# Threat Model — `memory_reflect.py`

Scheduled daily at 08:00 via launchd / systemd. Reads yesterday's daily
log and promotes important items to `MEMORY.md` using a focused Agent
SDK pass. Advisor-mode invariants: never send, never edit SOUL, never
leave sandbox.

## 1. Inputs

- **Daily log** (`Fredis/Memory/daily/YYYY-MM-DD.md`) — **untrusted**.
  The log is appended to by heartbeat with external-data-sourced content
  (email snippets, Slack messages, task titles). Phase 5 added `source:`
  provenance markers; Phase 5 also added an **injection re-check** on
  the aggregate log content before it reaches the reflection prompt.
- **MEMORY.md / USER.md / SOUL.md** (read-only here) — trusted
  long-term memory.

**Trust boundary (Phase 5):** `check_injection_patterns(log_context)`
runs before prompt-building. If any pattern match → reflection ABORTS
(no SDK call) and a warning is appended to today's daily log with
`source=reflection-aborted`. Otherwise the log is wrapped via
`wrap_external_data(..., source="daily_logs")` + `TRUST_BOUNDARY_INSTRUCTION`.

## 2. Tools

Main promotion pass: `allowed_tools = ["Read", "Edit", "Glob", "Grep",
"Bash"]`. Archive pass (second-phase): `allowed_tools = ["Read",
"Edit", "Write", "Glob"]`.

Blast radius:
- `Edit` — gated by `block-soul-edit` (SOUL.md write-protected),
  `block-template-residue`, `block-secrets`,
  `block-dangerous-commands`. Phase 1: matchers cover `MultiEdit` +
  `NotebookEdit`.
- `Write` — only enabled on archive pass; targets
  `Fredis/Memory/archive/YYYY-MM.md`.
- `Bash` — `block-dangerous-commands` + `validate_bash_command`.

## 3. Writes

- **MEMORY.md** (`Fredis/Memory/MEMORY.md`) — promotion target. No
  approval gate: this is the whole point of the pass. Invariants are
  enforced by hooks (block template residue, block secrets).
- **USER.md / SOUL.md** — prompt tells Claude to update `USER.md`
  only on repeated evidence and not to touch `SOUL.md` at all
  (standalone hook prevents it regardless).
- **Archive** (`Fredis/Memory/archive/YYYY-MM.md`) — overflow archive
  when MEMORY.md exceeds `MEMORY_LINE_LIMIT`. Wholesale cut/paste, not
  paraphrase.
- **Daily log** (today's file) — abort-warning provenance entries.

## 4. Memory reads

- Yesterday's daily log — untrusted, re-checked via injection pipeline
  (Phase 5). Wrapped in `<external_data>`.
- `MEMORY.md` / `USER.md` / `SOUL.md` — trusted (own-authored output of
  the previous reflection cycle + `phase1-ready` skill).

The archive pass reads `MEMORY.md` directly; it is the product of prior
reflections and is trusted by convention. If a past reflection
pre-Phase-5 promoted injection content to MEMORY.md, the archive pass
would cut/paste it to the archive file. This is an acceptance — the
archive pass is scope-limited to "wholesale cut/paste" and does not
interpret content.

## 5. Outputs

- **MEMORY.md mutation** — persists cross-session.
- **Daily log** — append only.
- **No external surface** — reflection does not post to Slack, does
  not send email.

## 6. Failure mode

- **Injection in daily log (Phase 5):** abort, record
  `state["result"] = "aborted_on_memory_injection"`, warn to today's
  daily log. No SDK call, no promotion, no MEMORY.md mutation.
- **Archive pass error:** caught, error logged to daily log, skipped.
- **SOUL.md edit attempt:** `block-soul-edit` exits 2 with feedback;
  Claude retries or gives up.
- **Template residue re-introduction:** `block-template-residue`
  blocks; Claude sees the stderr + picks an allowlist path or drops
  the edit.

Invariants preserved under all failure modes:
- No external send.
- No SOUL edit.
- Daily-log-sourced injection gets ratcheted OUT at reflection time
  (abort), preventing the memory-poisoning loop
  (`agent-guardrails.md` §6).
