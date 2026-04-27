# Fredis MCP server — operator guide

The Fredis MCP server (`fredis-mcp`) exposes the vault to non-Claude-Code AI clients (Claude Desktop, Cursor, Gemini, ChatGPT desktop) so they share the same persistent memory. **Transport is stdio**: each client spawns its own subprocess via `run_mcp_server.sh` for the duration of that session. No daemon, no port, no bearer token.

This is the **D2.5 = A (stdio, local-only)** branch of the OB1 integration plan. If you later open the server to remote clients (D2 = B), see `Phase 1B` in `.agent/plans/fredis-ob1-integration.md` — that variant uses HTTP+SSE with a bearer token and replaces this doc.

## What the server exposes

Eight tools — seven read, one write. Implementations live in `.claude/scripts/fredis_mcp_tools.py`.

| Tool | R/W | Purpose |
|---|---|---|
| `search_memory` | R | Hybrid / keyword / semantic search across the vault |
| `get_file` | R | Read a vault-relative path (denylist-checked) |
| `list_drafts` | R | List `Fredis/Memory/drafts/<status>/` |
| `list_recent_decisions` | R | MEMORY.md bullets + decision-shaped lines from daily logs |
| `get_soul_summary` | R | Returns `SOUL.md` (always allowed — the persona is the point) |
| `get_user_profile` | R | `USER.md` with secret-shaped tokens stripped |
| `index_status` | R | Same shape as `memory_index.py --stats` |
| `propose_draft` | W | **Only** write surface — lands in `drafts/active/<source>/` |

`propose_draft` validates `source` against a fixed allowlist (`chatgpt`, `cursor`, `gemini`, `claude-desktop`, `web-claude`). External AIs cannot smuggle paths through it — the source name becomes the on-disk directory.

## Quick start

1. **Enable the server.** In `.claude/scripts/.env`:
   ```
   FREDIS_MCP_ENABLED=1
   ```
   The server refuses to start with a one-line stderr message unless this is exactly `1`.

2. **(Optional but recommended)** confirm the denylist matches your sensitivity preferences. The variable is `FREDIS_MCP_DENYLIST` — a comma-separated list of vault-relative path prefixes. Trailing `/` matches a directory; no trailing `/` matches a single file. Denylisted paths are dropped from `search_memory` results and return `path not accessible` from `get_file` (same shape as a missing file — existence is not leaked). For the default value, see `.claude/scripts/.env.example`; do **not** copy it into responses, screenshots, or commits.

3. **Smoke-test by hand.** From the repo root:
   ```bash
   FREDIS_MCP_ENABLED=1 ./.claude/scripts/run_mcp_server.sh
   ```
   The process should block on stdin (it's waiting for a JSON-RPC handshake). `Ctrl-C` to exit. If it prints `refusing to start` and exits 1, your `.env` isn't being loaded — verify the file exists and `FREDIS_MCP_ENABLED=1` is on its own line.

4. **Wire your client(s).** See [§Client wiring](#client-wiring). Each client spawns its own subprocess; you don't need to "start" the server yourself.

## Logs

The server logs to a single file (created on first run):

```bash
tail -f .claude/data/logs/mcp-server.log
```

Each spawned subprocess (one per active client session) appends to the same file. Look for `starting fredis-mcp server (stdio transport)` to confirm a client connected.

There's no launchd `.out` / `.err` capture in this transport — the client's own logs (Claude Desktop's Developer pane, Cursor's MCP panel, etc.) capture stdio between the client and server.

## Client wiring

Each section below uses the absolute path to `run_mcp_server.sh`. Substitute your repo path — find it with `git -C "$(pwd)" rev-parse --show-toplevel` from anywhere inside this repo.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fredis": {
      "command": "/absolute/path/to/repo/.claude/scripts/run_mcp_server.sh",
      "args": []
    }
  }
}
```

Restart Claude Desktop. Open the **Settings → Developer** pane — `fredis` should appear under **Connected MCP servers** with the eight tools listed. If it shows an error, click `View logs` for that server.

### Cursor

Settings → MCP → **Add new MCP server** → `command` mode:

- Name: `fredis`
- Command: `/absolute/path/to/repo/.claude/scripts/run_mcp_server.sh`
- Args: (leave empty)

Cursor stores the config under `~/.cursor/mcp.json` and surfaces tool-call permission prompts inline. No token is required in stdio mode.

### Gemini CLI / Code Assist

Per the Gemini MCP docs — add to the Gemini settings (location varies by version, typically `~/.gemini/settings.json`):

```json
{
  "mcpServers": {
    "fredis": {
      "command": "/absolute/path/to/repo/.claude/scripts/run_mcp_server.sh",
      "args": []
    }
  }
}
```

Reload the CLI / IDE plug-in.

### ChatGPT desktop

If your ChatGPT desktop build supports MCP, the wiring matches the others (`command` → wrapper script, no args). If it doesn't, the fallback is a custom-GPT OpenAPI shim that re-exposes the same tool surface over HTTPS — that requires opening a network surface and a bearer token, which is **out of scope for this slice** (D2 = A). See `.agent/plans/fredis-ob1-integration.md` §Phase 1B if you want to take that route later.

## Manual integration test (run once per client)

For each client you wired up, do these two checks. If either fails, **stop, disable the client integration, and roll back per [§Rollback](#rollback)**. The first check is the highest-severity item in the parent plan's risk register.

1. **Read path — denylist enforcement.** Ask the AI:
   > What does Fredis know about Atis?

   Verify (a) the answer cites real vault content, (b) no `retainers/` or `legal/` paths appear in the response or the client's tool-call trace, (c) no hallucinated paths.

2. **Write path — `propose_draft`.** Ask the AI:
   > Save a draft titled "MCP integration test" with body "ping". Source: <client-name>.

   `<client-name>` must be one of `chatgpt`, `cursor`, `gemini`, `claude-desktop`, `web-claude`. Verify the file appears in `Fredis/Memory/drafts/active/<source>/<YYYY-MM-DD>_mcp-integration-test.md` with YAML frontmatter.

## Sensitivity gating

There's no auth token in stdio mode — anything with execute permission on `run_mcp_server.sh` and read permission on `.claude/scripts/.env` can spawn the server. Sensitivity comes from `FREDIS_MCP_DENYLIST`, which is enforced **after** the search engine returns results and **inside** every read tool.

To change which paths are accessible:

1. Edit `FREDIS_MCP_DENYLIST` in `.claude/scripts/.env`.
2. Restart any active client session (the next subprocess spawn picks up the new value via `python-dotenv`).

**Never paste the denylist into this doc, a commit message, or a screenshot.** It's not a secret in the cryptographic sense, but it's the map of "what's hidden", which is operationally sensitive.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Server exits with `refusing to start — FREDIS_MCP_ENABLED is not set to '1'` | Add `FREDIS_MCP_ENABLED=1` to `.claude/scripts/.env`. Double-check there's no inline comment or trailing whitespace on that line. |
| `ModuleNotFoundError: No module named 'mcp'` | Run `cd .claude/scripts && uv sync` to install the `mcp` package from `pyproject.toml`. |
| Client shows `fredis` server with zero tools | The subprocess died before completing the handshake. Tail `.claude/data/logs/mcp-server.log` and the client's own MCP log. Most common cause: `uv` not on the wrapper's `PATH` — `run_mcp_server.sh` exports `$HOME/.local/bin`; adjust if your `uv` lives elsewhere. |
| Denylisted path leaks into a tool response | **High severity.** Disable the affected client's `fredis` entry immediately, capture the offending response, and follow [§Rollback](#rollback). |
| Draft from `propose_draft` lands outside `drafts/active/<source>/` | Should be impossible — every path is rebuilt server-side from the validated `source` value. If it happens, treat it the same as a denylist leak: disable, capture, roll back. |
| `mcp` package missing only in some clients | Each client spawns its own subprocess with a fresh interpreter; verify `uv sync` ran for the same Python version `run_mcp_server.sh` resolves to. |

## Rollback

Stdio means there's no daemon to stop — disabling is per-client.

1. **Per client.** Remove the `fredis` entry from the client's MCP config and restart the client. Verify the tools no longer appear.
2. **Globally.** Set `FREDIS_MCP_ENABLED=0` in `.claude/scripts/.env`. Any client that still has a `fredis` entry will spawn the wrapper, the wrapper will exit 1, and the client will surface a connection error — harmless but noisy.
3. **Code-level.** No code rollback is needed in this slice; slices 1.1–1.3 stand on their own.

## Related

- Server entry point: `.claude/scripts/fredis_mcp_server.py`
- Tool implementations: `.claude/scripts/fredis_mcp_tools.py`
- Auth / denylist matcher: `.claude/scripts/fredis_mcp_auth.py`
- Wrapper script: `.claude/scripts/run_mcp_server.sh`
- Slice plan: `.agent/plans/ob1/04-phase-1.4-mcp-deploy.md`
- Parent plan: `.agent/plans/fredis-ob1-integration.md`
