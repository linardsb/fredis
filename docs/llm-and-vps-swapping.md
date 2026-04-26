# LLM & VPS Swapping

How to swap which AI talks to Fredis, and what would actually change on the VPS if you ever moved the autonomous brain off Claude.

> **Status (2026-04-26):** Pre-Phase-1. Fredis is single-front-end (Claude Code only) and single-back-end (Claude Agent SDK). The "easy swap" path described here lights up after OB1 Phase 1 ships the MCP server. The "hard swap" path is always a real refactor.

---

## TL;DR

Fredis has **two independent LLM layers** that should never be confused:

| Layer | What it does | Today | Easy to swap? |
|---|---|---|---|
| **Front-end clients** | Read vault, search memory, propose drafts | Claude Code only | After Phase 1 — yes, trivially |
| **Autonomous services** | Heartbeat, reflection, synthesis, Slack chat | Claude Agent SDK | No — full SDK rewrite |

You can multi-LLM the front (Cursor + Claude Desktop + ChatGPT etc., all hitting the same vault) without touching the back (heartbeat & co. keep running on Claude). Pretending these are the same layer leads to wrong scoping — "swap to Gemini" is two completely different projects depending on which layer.

---

## Layer 1: Front-end clients (the easy layer, post-Phase-1)

### What gets swapped

The AI tool you type into. Each client is a separate process with its own MCP config; they all talk to the same Fredis MCP server, see the same SOUL/USER/MEMORY/drafts.

### Architecture (after Phase 1)

```
Cursor          ─┐
Claude Code     ─┤
Claude Desktop  ─┼─→  fredis_mcp_server.py  ─→  vault + memory_search + drafts/active/
ChatGPT Desktop ─┤      (.claude/scripts/)
Gemini CLI      ─┘
```

The MCP server is a single Python process. Clients connect via either:
- **stdio** (D2.5 = A in the OB1 plan): each client spawns the server as a subprocess. No network, no token. Default for local-only use.
- **HTTP+SSE** (D2.5 = B): server binds `127.0.0.1:4747` with a bearer token. Required if any client is remote (e.g. via Tailscale to a VPS-hosted server, OB1 Phase 1B).

### How to add a client (after Phase 1.4 ships the wrapper script)

Each client has its own MCP-config location. Pattern is identical: name + command + (optional) bearer token.

**Claude Desktop / Code** — `~/.claude/mcp.json` (or per-project `.mcp.json`):
```json
{
  "mcpServers": {
    "fredis": {
      "command": "/Users/Berzins/Desktop/claude-code-second-brain/.claude/scripts/run_mcp_server.sh"
    }
  }
}
```

**Cursor** — `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "fredis": {
      "command": "/Users/Berzins/Desktop/claude-code-second-brain/.claude/scripts/run_mcp_server.sh"
    }
  }
}
```

**ChatGPT Desktop / Gemini / others** — same shape, different config path. Phase 1.4's `docs/mcp-server.md` will list the exact file per client.

### How to remove a client

Delete the `fredis` entry from that client's MCP config. Server keeps running for the others.

### How to switch *between* clients

Just open the other client. Same server, same data, different chat window.

### Per-client billing

| Client | Bills against |
|---|---|
| Claude Code / Claude Desktop | your Anthropic subscription (`~/.claude/.credentials.json`) |
| Cursor | Cursor's plan (pass-through to Anthropic / OpenAI / etc.) |
| ChatGPT Desktop | your OpenAI / ChatGPT Plus subscription |
| Gemini | Google Workspace / AI Studio billing |
| Local LLM (Ollama via MCP) | free, local compute |

Multi-front-end = multi-billing for *interactive* work. The autonomous Fredis services (Layer 2) stay on Claude billing regardless.

### What clients can / can't do via MCP

Per Phase 1.1 plan, the server exposes 8 tools. Read-only by default; one constrained write tool:

| Tool | Direction | Notes |
|---|---|---|
| `search_memory` | R | hybrid keyword + vector |
| `get_file` | R | denylist-checked |
| `list_drafts` | R | active drafts only |
| `list_recent_decisions` | R | parses MEMORY.md + recent daily logs |
| `get_soul_summary` | R | full SOUL.md (the persona is the point of plugging in) |
| `get_user_profile` | R | USER.md filtered for non-secrets |
| `propose_draft` | W | writes to `Fredis/Memory/drafts/active/<source>/...`, never elsewhere |
| `index_status` | R | `memory_index --stats` shape |

The write surface is intentionally tight: **clients can propose, only Linards can send.** Advisor mode is preserved across all clients.

---

## Layer 2: Autonomous services (the hard layer)

### What gets "swapped"

The autonomous Fredis processes that run on a schedule with no human in the loop:

| Service | Where | Schedule | Code |
|---|---|---|---|
| Heartbeat | VPS + Mac | every 120 min, 05:00–20:00 Europe/London | `.claude/scripts/heartbeat.py` |
| Reflection | VPS + Mac | daily 08:00 | `.claude/scripts/memory_reflect.py` |
| Synthesis | VPS + Mac | weekly | `.claude/scripts/memory_synthesis.py` |
| Slack chat | VPS only | always-on | `.claude/chat/main.py` (`secondbrain-chat.service`) |
| Memory flush | both | on session end / pre-compact | `.claude/scripts/memory_flush.py` |

All of these use **Claude Agent SDK** (`claude_agent_sdk`). They construct `ClaudeAgentOptions`, invoke `query()`/`query_with_tools()`, and stream Claude responses with tool-use loops. Authentication inherits from `~/.claude/.credentials.json`.

### Why swapping is hard

The Agent SDK is **Anthropic-specific**. There is no LangChain-style abstraction layer in the codebase — every agent loop is written directly against the Anthropic SDK shape:

- `ClaudeAgentOptions(...)`, `query(prompt=..., options=...)`
- Tool definitions with `name` / `description` / `input_schema`
- Streaming partial responses, handling `tool_use` and `tool_result` blocks
- `setting_sources=["user","project"]` to inherit hooks (block-soul-edit, block-secrets)
- `resume=session_id` for persistent chat threads

Migrating to OpenAI / Gemini / Bedrock means rewriting all of that against a different SDK shape. Tool-use semantics differ, streaming differs, session resumption differs.

### What a swap would actually touch

If you ever do this (probably never — but documented):

| File | What changes |
|---|---|
| `.claude/scripts/heartbeat.py` | Replace `query(prompt, options)` with the new SDK's equivalent. Re-implement the guardrail prompt-injection check (currently uses Haiku via Agent SDK). |
| `.claude/scripts/memory_reflect.py` | Same. The reflection prompt currently expects Claude's tool-use loop for `Edit` on MEMORY.md. |
| `.claude/scripts/memory_synthesis.py` | Same. Heavy use of `Edit` tool to write proposal drafts. |
| `.claude/chat/engine.py` | Largest file. Implements 25-turn conversation buffer, $2 budget cap per session, Slack thread → session ID mapping. Provider-specific session-resume APIs. |
| `.claude/scripts/config.py` | New env vars for the alternate provider's auth. |
| `.claude/scripts/.env` + `.env.example` | New keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, etc.). |
| `.claude/hooks/block-secrets.py`, `block-soul-edit.py` | Hooks fire from Claude Agent SDK's hook plumbing. Other SDKs may not support hooks at all — would need application-level enforcement instead. |
| `.claude/skills/*/SKILL.md` | Skills are a Claude-Code-specific concept. On other providers they'd need to become regular system prompts or tool-use templates. |

The skills + hooks coupling is the deepest. Fredis's safety model (advisor mode, soul protection, secret blocking) is enforced at the Claude-Code-harness layer. Swapping providers means re-implementing the safety model in application code.

### When to actually swap Layer 2

Reasonable triggers:
- Anthropic prices Claude out of feasible long-running-agent use
- A different provider ships materially better long-context or tool-use accuracy for the agentic-loop workload
- Vendor lock-in becomes a contract / sovereignty issue

Until one of those fires: don't. Layer 2 works, the SDK is stable, the safety model is integrated. Keep the back end on Claude and use the front-end MCP layer (cheap, easy) to bring other LLMs into your daily flow.

---

## Common scenarios

### "I want to use Cursor for coding while Fredis stays Claude-powered"

After Phase 1.4: configure Cursor's `~/.cursor/mcp.json` to point at `run_mcp_server.sh`. Cursor reads the vault, proposes drafts back to `drafts/active/cursor/`, the heartbeat keeps running on Claude as before. **Done — no Layer 2 changes.**

### "I want ChatGPT Desktop to brainstorm with my Fredis context"

Same as above with ChatGPT's MCP config path. **Done — no Layer 2 changes.**

### "Anthropic raised prices, I want heartbeat to use Gemini"

Real Layer 2 swap. Plan:
1. Build a thin provider-adapter abstraction (the codebase doesn't currently have one — that's the first refactor).
2. Port `heartbeat.py` first (lowest-risk, easiest to roll back per-machine).
3. Verify guardrail still catches prompt-injection (you'll need a Gemini-equivalent for the Haiku semantic check).
4. Port `memory_reflect.py` and `memory_synthesis.py`.
5. Port `chat/engine.py` last — most complex (session resume, budget tracking).
6. Migrate hooks: rebuild `block-secrets.py` / `block-soul-edit.py` semantics as application-level guards (Gemini SDK doesn't have an equivalent harness).

Estimate: weeks, not days. Plan it as a project, not a config flip.

### "I want both: VPS keeps Claude, but laptop tries Gemini for some tasks"

Trivial — that's just Layer 1 with an extra client. Add Gemini CLI to the MCP config list. The VPS services don't know or care which clients are connected.

---

## Pointer file

This doc is the canonical reference for "how do I change which LLM Fredis uses." If you're about to make either layer's change, read this first.

- Front-end client config snippets per tool: see Phase 1.4 plan (`.agent/plans/ob1/04-phase-1.4-mcp-deploy.md`) once shipped.
- Layer 2 SDK code lives in `.claude/scripts/` and `.claude/chat/`. Each agent loop is documented inline with its own threat model under `.claude/scripts/threat-models/`.
- Cost / billing rotation context: `.claude/scripts/schedule/rotation-runbooks.md`.
