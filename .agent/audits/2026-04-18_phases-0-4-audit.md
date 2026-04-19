# Phases 0–4 Audit — 2026-04-18

Comprehensive audit + unit-test pass on bootstrap, memory layer, heartbeat, memory search, and integrations reconciliation.

> **Fix pass — 2026-04-19:** bugs #2–#10 resolved. Bug #1 verified already-resolved on re-run (mypy strict clean; the `# type: ignore[import-untyped]` comments that the audit recommends were already in place). See individual bug entries for per-fix notes.

## Test baseline

| Suite | Result |
|---|---|
| `pytest tests/` | **249 passed** in 9.4s (clean) |
| `ruff check .` | 0 errors |
| `mypy . --ignore-missing-imports` (strict) | **3 errors** — see Bug #1 |
| Phase 3 targeted (`test_db`, `test_embeddings`, `test_memory_index`, `test_memory_search`) | 20/20 pass |
| Phase 4 targeted (`test_github_api`, `test_monday_api`) | 17/17 pass |
| Live `memory_search.py "advisor mode" --mode keyword` | works, returns 3 hits |
| Live `memory_search.py "circle removal" --mode hybrid` | works, returns 3 hits incl. semantic match |
| Smoke imports: `heartbeat`, `onboard`, `interview_parser`, `db`, `memory_search`, `sanitize` | all clean |
| Sanitize injection-pattern check | flags `ignore all previous instructions` correctly |
| Config defaults (Phase 4) | `Europe/London / 05:00–20:00 / 120 min` loaded from `config.py` ✓ |
| **Integrative: `heartbeat.py --test`** | end-to-end pass in 57s, $0.17, guardrail=`pass`, all 6 integrations responded — **but** see Bug #10 (silent Slack `not_in_channel`) |

**CLI entry points NOT exercised in this audit:** `memory_index.py` (full re-index from cold), `memory_reflect.py` (yesterday's-log promotion), `memory_flush.py`, `setup_workspace.py` (any flag), `onboard.py` TUI, `chat/main.py` Socket Mode listener. Static analysis only for those.

## Bugs

Severity legend: **HIGH** = breaks documented behaviour or silently corrupts user setup; **MED** = visible drift between docs and code; **LOW** = housekeeping.

---

### #1 — Mypy strict run violates the "0 errors" baseline   **HIGH**

**Where:** `.claude/scripts/integrations/{monday_api,github_api,asana_api}.py`

**Repro:**
```bash
cd .claude/scripts && rm -rf .mypy_cache && uv run --with mypy mypy . --ignore-missing-imports
```
Yields:
```
integrations/monday_api.py:34: error: Library stubs not installed for "requests"  [import-untyped]
integrations/github_api.py:30: error: Library stubs not installed for "requests"  [import-untyped]
integrations/asana_api.py:487: error: Library stubs not installed for "requests"  [import-untyped]
Found 3 errors in 3 files (checked 49 source files)
```

`CLAUDE.md` → Pre-Commit Workflow promises "0 mypy errors expected". Phase 4 introduced `requests` imports in three integration modules without adding `types-requests` to the dev extras or appending `# type: ignore[import-untyped]`. `--ignore-missing-imports` does **not** silence `import-untyped` for installed-but-unstubbed packages — only fully-missing modules.

**Cache twist:** with the stale `.mypy_cache` from a prior run, mypy reports the *same* lines as `Unused "type: ignore" comment [unused-ignore]` instead — equally a baseline failure but easy to misread because the lines no longer contain a `# type: ignore`. Cache-state-dependent diagnostics make this harder to debug.

**Fix:** add `types-requests>=2.31` to the dev extra in `pyproject.toml`, OR append `# type: ignore[import-untyped]` to the three `import requests` lines. Pre-commit guidance should also tell developers to wipe `.mypy_cache` when behaviour looks weird.

---

### #2 — `setup_workspace.py` ENV_FILES mapping is missing all Phase 4 vars   **HIGH**

**Where:** `setup_workspace.py:31-51`

The `ENV_FILES[".claude/scripts/.env"]` dict propagates a hard-coded subset of master-env keys into the per-script `.env`. Phase 4 added five env vars (`MONDAY_API_TOKEN`, `MONDAY_USER_ID`, `MONDAY_BOARD_IDS`, `GITHUB_TOKEN`, `GITHUB_USERNAME`) — they appear in `master.env.example`, in `.claude/scripts/.env.example`, and in `config.py`, but the propagator silently drops them.

The same dict is also missing several pre-Phase-4 settings present in `.env.example`: `SLACK_APP_TOKEN`, `SLACK_OWNER_USER_ID`, `SLACK_NOTIFICATION_CHANNEL`, `SLACK_MONITORED_CHANNELS`, `REFLECTION_HOUR`, `DRAFT_EXPIRY_HOURS`, `EXPIRED_DRAFT_RETENTION_DAYS`. (The `DATABASE_URL → SB_DATABASE_URL` mapping is correct — master.env namespaces sibling-repo Postgres URLs by prefix, e.g. `CE_DATABASE_URL`, `OA_DATABASE_URL`.) A user running `setup_workspace.py --env master.env` on a fresh box gets a per-script `.env` missing Monday, GitHub, Slack chat creds, and reflection scheduling — heartbeat will look broken.

**Fix:** add the missing keys to `ENV_FILES`. Better long-term: pull the var list from a single source of truth (e.g. read `.env.example` and forward any key whose name appears in `master.env`) so the two files can't drift again.

---

### #3 — `setup_workspace.py` heartbeat defaults still on the pre-Phase-4 schedule   **HIGH**

**Where:** `setup_workspace.py:56-61`

```python
DEFAULTS = {
    "HEARTBEAT_INTERVAL_MINUTES": "30",
    "HEARTBEAT_ACTIVE_HOURS_START": "08:00",
    "HEARTBEAT_ACTIVE_HOURS_END": "22:00",
    "HEARTBEAT_TIMEZONE": "America/Chicago",
}
```

`config.py:161-164` and `.claude/scripts/.env.example:21-24` both ship the Phase 4 defaults: `120 / 05:00 / 20:00 / Europe/London`. If a master env doesn't set these (the common case), `setup_workspace.py` writes the old values into `.claude/scripts/.env`. **Confirmed:** `config.py:12,15` calls `load_dotenv(...)` before any `os.getenv` lookup, so the per-script `.env` value wins — the bogus 30/Central defaults will override `config.py`'s Phase 4 fallbacks at runtime. Heartbeat will fire every 30 minutes from 08:00–22:00 Central instead of every 120 minutes from 05:00–20:00 London.

**Fix:** sync `DEFAULTS` with `config.py`. Better: drop `DEFAULTS` entirely and let `config.py`'s `os.getenv(..., default)` handle fall-through; only write a key into the per-script `.env` if it's actually present in master.

---

### #4 — `setup_workspace.py --generate-template` would overwrite the good `master.env.example`   **HIGH**

**Where:** `setup_workspace.py:134-178`

`generate_master_template()` rebuilds `master.env.example` from a hard-coded `sections` list that contains only nine vars (`OWNER_NAME`, `SB_DATABASE_URL`, `ASANA_*`, `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `SLACK_OWNER_USER_ID`, `GOOGLE_CALENDAR_ID`). Anyone running `python setup_workspace.py --generate-template` on this repo will replace the comprehensive 113-line `master.env.example` — which currently documents shared keys (OPENAI/ANTHROPIC/GITHUB), Content Engine, Video Processor, Obsidian Agent, Phase 4 Monday + GitHub, Reflection, etc. — with a stripped-down 9-var version.

**Fix:** rebuild the `sections` list to mirror what's actually in `master.env.example` today, OR delete the `--generate-template` code path and stop pretending the file is generated.

---

### #5 — README is stale on Phase 4 status   **MED**

**Where:** `README.md:338`

> "Monday.com + GitHub subcommands land in Phase 4 tasks 6–7."

Phase 4 is shipped. `query.py` already exposes `monday {boards,board,my-items,overdue,search}` (lines 613–618) and `github {recent,review-requests,mentions,ship}` (lines 621–623). The README's CLI command catalogue (lines 280–335) lists Gmail, Calendar, Asana, Slack, Sheets, Docs, Drive — but **no Monday or GitHub command examples**. CLAUDE.md has them; README does not.

**Fix:** delete line 338, copy the Monday + GitHub command block from `CLAUDE.md` into the README.

---

### #6 — CLAUDE.md mis-states Slack `send` status   **MED**

**Where:** `CLAUDE.md` direct-integrations CLI section.

> "Slack (read-only; `send` intentionally omitted — Task 9 will add it behind --i-confirm-send)"

`query.py:347-358` already implements `slack send` gated by `--i-confirm-send`, with the documented advisor-mode refusal message when the flag is missing. The doc claims it doesn't exist yet.

**Fix:** rewrite that line to: "Slack (`send` available behind `--i-confirm-send`; advisor-mode refuses otherwise)."

---

### #7 — CLAUDE.md test-count baseline is stale   **LOW**

**Where:** `CLAUDE.md` → Pre-Commit Workflow.

Says "113 tests passing expected". Current count: **249**. Not a bug per se, but the line gives a false ceiling for "is the suite intact?" checks.

**Fix:** rephrase as a floor: "≥249 tests passing as of 2026-04-18". Or stop pinning the number and rely on the green-bar contract.

---

### #8 — `check_for_important_messages` ID heuristic relies on Slack's lowercase-channel-names convention   **LOW**

**Where:** `.claude/scripts/integrations/slack_api.py:242`

```python
if ch_name.startswith(("C", "D", "G")):
    ch_id: str | None = ch_name
```

Treats any name starting with capital `C`/`D`/`G` as a Slack ID. Slack enforces lowercase channel names, so this is correct **today**. If Slack ever relaxes that rule, or if a user puts a literal raw channel display string in `SLACK_MONITORED_CHANNELS`, the heuristic silently mis-classifies.

**Fix (optional hardening):** use `re.fullmatch(r"[CDG][A-Z0-9]{8,}", ch_name)` instead. The diff for this file is also currently uncommitted — fold this in before committing.

---

### #9 — Top-level diagram-generation scripts are orphans   **LOW**

**Where:** `build_v2.py`, `generate_diagram.py` (repo root)

Two ~20 KB scripts at the repo root (~498 KB Excalidraw output). Not imported by anything else, no docs, no tests, not referenced in `setup_workspace.py`. They look like one-off architecture-diagram tooling.

**Fix:** move under `tools/` or `.agent/`, or delete if the diagram is no longer maintained. Right now they pollute the repo's top-level surface area and confuse the bootstrap mental model ("is this build_v2 part of Phase 0?").

---

### #10 — Heartbeat silently swallows Slack `not_in_channel`   **MED**

**Where:** `.claude/scripts/integrations/slack_api.py:109` (`get_recent_messages`) and `:226` (`check_for_important_messages`).

Reproduced live during the `heartbeat.py --test` run:
```
Error fetching messages: The request to the Slack API failed. (url: https://slack.com/api/conversations.history)
The server responded with: {'ok': False, 'error': 'not_in_channel'}
[2026-04-18 22:04:59.699664+01:00] Slack: 0 important messages
```

When the bot isn't a member of a channel listed in `SLACK_MONITORED_CHANNELS`, `get_recent_messages` prints the error to stderr and returns `[]`. The outer loop swallows that and `Slack: 0 important messages` is logged identically to the genuine quiet-channel case. Operator can't distinguish between "no important messages" and "Fredis is blind to that channel because the bot was never invited" — and the latter persists silently across every heartbeat.

**Fix:** detect the `not_in_channel` SlackApiError specifically and either (a) raise a one-time `Slack monitoring degraded: bot not in #X — invite with /invite @Second Brain` warning that surfaces on the heartbeat alert path, or (b) skip the channel and emit a `data["errors"]["slack_<channel>"]` entry so the alert surface gets it. (a) is more useful — silent degradation in a monitoring pipeline is worse than a chatty one.

---

## What was checked and is healthy

- Phase 0: hooks (`pre-compact-flush`, `session-end-flush`, `session-start-context`, `redact-secrets`, `block-secrets`, `block-dangerous-commands`) all import and the redact hook actively scrubbed PII from this session's tool output.
- Phase 1: `interview_parser.parse_interview` parses the 27-section / 103-question interview and reports 88 answered. `phase1-ready` skill (SKILL.md + runbook.md + drafting_hook.py) is intact, allowlist covers all five memory files plus folder READMEs and PRD addendum.
- Phase 2: heartbeat orchestration loads cleanly. All four SDK callers (`heartbeat`, `memory_flush`, `memory_reflect`, `chat/engine`) set `CLAUDE_INVOKED_BY` at module top; both flush hooks honour it. Sanitize layer's pattern catalogue + markdown escaper + XML wrapper all verified by 60+ unit tests.
- Phase 3: SQLite memory DB reachable, hybrid + keyword search both return relevant hits live. FastEmbed batch=256 + path-prefix filtering tested. Chat module imports clean and `engine.py` correctly stamps the invocation marker.
- Phase 4: integration registry includes Monday + GitHub with correct `required_config`. No remaining Circle.so references in project source. Heartbeat formatters for Monday + GitHub wrap output in `<external_data>` (verified by `test_format_*_wraps_in_external_data_tag`). Advisor-mode boundary holds for automated paths — `chat_postMessage` in `slack_api` is only reached via:
  1. Heartbeat → `notifications.send_slack_notification` → owner-channel only.
  2. Chat module replies in user-initiated threads (allowed by design).
  3. CLI `slack send` gated by `--i-confirm-send`.
