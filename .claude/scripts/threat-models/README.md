# Per-Agent Threat Models

One page per Agent-SDK caller. Each document answers the six-question
checklist from
`.claude/skills/security-engineering/references/agent-guardrails.md` §7 so a
future reviewer can diff a PR against a stated threat model.

## The six questions

1. **Inputs** — where does data come from, and what is the trust boundary
   between input and prompt?
2. **Tools** — which `allowed_tools` are enabled, and what can each tool do
   in this caller's blast radius?
3. **Writes** — what files / systems can the agent mutate? What is the
   approval gate?
4. **Memory reads** — what prior-context files does the agent read? Do
   those reads re-apply the injection pipeline (Phase 5)?
5. **Outputs** — what surfaces (Slack, daily log, drafts) does the agent's
   text reach? Which are external-visible?
6. **Failure mode** — what happens on prompt injection / Haiku timeout /
   unknown exception? Does the failure mode preserve the invariants (no
   send, no SOUL edit, no secret leak)?

## When to update

**Revisit a threat model whenever `allowed_tools` changes, when a new
integration is added to the gather path, or when a new hook is registered.**
Threat models go stale silently — a one-line edit to `heartbeat.py` that
adds a tool can invalidate the blast-radius answer below without anyone
noticing.

## Agents

- [heartbeat.md](heartbeat.md) — `heartbeat.py` (proactive 120-min Slack loop)
- [chat.md](chat.md) — `chat/engine.py` (Slack interactive session)
- [reflection.md](reflection.md) — `memory_reflect.py` (daily MEMORY.md promotion)
- [memory_flush.md](memory_flush.md) — `memory_flush.py` (PreCompact / SessionEnd flush)
- [memory_synthesis.md](memory_synthesis.md) — `memory_synthesis.py` (weekly MEMORY.md synthesis, advisor-mode drafts)
- [mcp.md](mcp.md) — MCP server audit + keep/remove decision (Phase 9.1)
