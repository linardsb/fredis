# Threat Model — `memory_flush.py`

Spawned by `pre-compact-flush.py` (PreCompact) or `session-end-flush.py`
(SessionEnd). Reads the transcript excerpt written to a temp file and
asks Claude (SDK) to summarise what's worth saving into the daily log.
Advisor-mode invariants: minimal-by-construction (no writes via tools).

## 1. Inputs

- **Transcript excerpt** (`flush-context-*.md` temp file) — **untrusted**.
  The excerpt is captured by Claude Code during compaction and may contain
  raw tool_result blocks that echoed external data (email bodies, Slack
  messages, Asana descriptions, Monday items). Phase 5 re-applies
  injection re-check; Phase 6 uses the shared `scrub_secrets` helper.

**Trust boundary (Phase 5):** three-step pipeline before the transcript
reaches `query()`:
1. `scrub_secrets(context_content)` — shape-based token redaction.
2. `check_injection_patterns(context_content)` — if any hit → abort.
3. `wrap_external_data(..., source="transcript")` + `TRUST_BOUNDARY_INSTRUCTION`.

## 2. Tools

`allowed_tools = []` — this is the key constraint. The flush agent
**cannot call any tool at all**. It can only emit text; the CALLER
(the wrapper) decides what to do with that text (append to daily log).

This means the usual hook stack is largely moot for this agent: no
Edit, Write, Bash, etc. are ever attempted. The one remaining failure
mode is "the agent's text contains something bad" — addressed in §5.

**Invariant (recursion firewall):** `setting_sources` is NOT set on the
flush SDK call — see the inline comment at `memory_flush.py`. Omitting
it means this sub-session does not load `.claude/settings.json`, so its
own exit doesn't re-trigger `SessionEnd` or `PreCompact` hooks.
`CLAUDE_INVOKED_BY` is defense-in-depth; this omission is the primary
firewall.

## 3. Writes

- **Daily log** (via the caller's `append_to_daily_log` call, NOT the
  SDK agent). Section-routing determined by source (`pre-compact` →
  "Pre-Compaction Flush" under "Memory Maintenance"; `session-end` →
  "Session End Flush" under "Sessions").
- **State file** (`.claude/data/state/flush-state.json`) — tracks last
  flush timestamp + session id for dedup.
- On abort (Phase 5 injection detection): the temp context file is
  **preserved** so Linards can review the raw content; daily log gets
  `source=flush-aborted` warning.

## 4. Memory reads

- Transcript excerpt only. No MEMORY / USER / SOUL reads.

## 5. Outputs

- **Daily log append** — the caller writes the agent's text into the
  day's log. Content path: SDK text → `append_to_daily_log` →
  markdown-safe content.
  - `</external_data>` is escaped to `&lt;/external_data&gt;` on
    write — prevents a hostile transcript from injecting tag-structure
    via the flush output.
- **No Slack, no email, no tool calls.**

## 6. Failure mode

- **Injection in transcript (Phase 5):** abort. Context file
  preserved. Warning logged with `source=flush-aborted`.
- **Secret leak in transcript:** Phase 6 `scrub_secrets` replaces
  token-shaped strings with `[REDACTED:<kind>]` before the SDK ever
  sees the content.
- **Recursion risk:** absent. `setting_sources` omitted prevents
  SessionEnd/PreCompact hooks from re-firing.
- **Duplicate flush:** same-session dedup (<60s) via
  `flush-state.json`.
- **SDK exception:** caught; error logged to daily log with
  `section_name=section_name` (pre-compact / session-end routed).

Invariants preserved under all failure modes:
- `allowed_tools=[]` makes tool-based mischief impossible.
- No external send surface exists on this code path.
- Transcript content is always scrubbed + wrapped before SDK exposure.
