# Agent SDK Call Pattern

Canonical reference: `.claude/scripts/memory_flush.py` (function `_run_flush_inner`).

The Fredis shape for invoking the Claude Agent SDK from a background script.

## The four primitives

1. **`query(prompt, options)`** — returns an async iterator of messages.
2. **`ClaudeAgentOptions`** — configures the sub-session (cwd, tools, turn limit, resume, etc.).
3. **Async iteration over messages** — walk the stream, branch on message type.
4. **`ResultMessage.result` extraction** — the final completion signal; carries `subtype`, `total_cost_usd`, and (when present) the result text.

## Minimal working shape

```python
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

response_text = ""

async for message in query(
    prompt=my_prompt,
    options=ClaudeAgentOptions(
        cwd=str(PROJECT_ROOT),
        allowed_tools=[],
        max_turns=4,
    ),
):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                response_text += block.text
    elif isinstance(message, ResultMessage):
        # Terminal message. Log cost + subtype here.
        print(f"Completed: {message.subtype}")
        if message.total_cost_usd:
            print(f"Cost: ${message.total_cost_usd:.4f}")
```

## Invariants

- **Import inside the async function**, not at module top — keeps import cost off the hot path when the script early-exits (e.g. empty context file, dedup skip).
- **`AssistantMessage.content` is a list of blocks**, not a string. Iterate and filter by type (`TextBlock`, tool blocks, etc.) — don't assume text.
- **`ResultMessage` terminates the stream.** Use it to close out logging / state writes. Don't try to pull more after it arrives.
- **Accumulate text in a local string** as blocks stream in. The final `response_text` is what the caller returns / persists.
- **Wrap the whole `async for` in a `try/except`.** SDK errors surface here; swallow and log rather than raising, so a scheduled caller doesn't crash the outer process.

## `ClaudeAgentOptions` — what to pass

| Option | When to use |
|---|---|
| `cwd=str(PROJECT_ROOT)` | Always. Otherwise the sub-session runs in whatever dir spawned it. |
| `allowed_tools=[]` | When the sub-session should respond with text only (no tool calls). Pair with a prompt line: *"You have NO tools available — respond with plain text only."* |
| `max_turns=N` | Always cap. Prevents runaway cost if the model loops. `memory_flush` uses 4. |
| `setting_sources=["user","project"]` | Use when the sub-session **should** inherit hooks / `CLAUDE.md` / skills (heartbeat, reflection, chat). **Do NOT pass** for sub-sessions that must not re-trigger `SessionEnd` / `PreCompact` hooks on their own exit — that's the primary recursion firewall. `memory_flush` omits it deliberately. |
| `system_prompt` (append mode) | For sub-sessions with `setting_sources` that need an extra preamble on top of the inherited prompt (e.g., chat injects its advisor-mode note). |
| `resume=session_id` | To rehydrate a prior conversation. Chat uses this to map a Slack thread → persistent session. |

## Recursion firewall

Every Agent SDK caller in Fredis sets this at module top:

```python
os.environ.setdefault("CLAUDE_INVOKED_BY", "<caller-name>")
```

`PreCompact` / `SessionEnd` / `SessionStart` hooks read this env var and skip when it's set, so a sub-session's exit doesn't trigger another flush. `setdefault` preserves the first caller's label if two of these modules get imported in one process.

This is **defense in depth**. The primary firewall for `memory_flush` is omitting `setting_sources` (so hooks don't load at all for that sub-session). The env var catches the other three callers that do load hooks.

## Callers that follow this pattern

- `.claude/scripts/memory_flush.py` — pre-compact / session-end flush (no `setting_sources`)
- `.claude/scripts/memory_reflect.py` — daily reflection (inherits hooks)
- `.claude/scripts/heartbeat.py` — proactive check-in (inherits hooks)
- `.claude/chat/engine.py` — Slack chat session (inherits hooks, uses `resume`)
