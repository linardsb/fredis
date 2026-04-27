## Fredis MCP server on the VPS — operator guide (Phase 1B)

This is the **D2 = B (remote)** variant of the Fredis MCP server: the same code that runs as a stdio subprocess on the Mac (see `docs/mcp-server.md`) is also hosted as a long-lived service on the VPS where Fredis already lives, reachable from Linards's other devices over Tailscale.

The Mac stdio MCP is **untouched** by this slice — it keeps working byte-for-byte as Phase 1.4 shipped it. This doc covers the additional VPS surface only.

## Architecture

```
[ phone / non-Mac AI client ]
            │   HTTPS via Tailscale MagicDNS
            ▼
[ tailscale serve on VPS ]   ← Tailscale-managed TLS, ACL gates the network
            │   forwards to loopback
            ▼
[ uvicorn on 127.0.0.1:4747 ]
            │   Starlette ASGI
            ▼
[ bearer middleware ]   ← rejects without Authorization header
            │
            ▼
[ FastMCP streamable-http app ]   ← same 8 tools as the Mac stdio server
            │
            ▼
[ same vault, same Postgres ]   ← git-synced + shared with the rest of Fredis
```

Three independent gates protect the read tools (`USER.md`, `retainers/`, `legal/`, `investors/` are denylisted in the same way as on the Mac):

1. **Tailscale ACL.** Only nodes Linards tags as allowed can reach `<vps-tailscale-name>` on HTTPS.
2. **Bearer.** Anyone who clears the ACL still needs the right Authorization header. Constant-time compare; the verdict is logged but the value never is.
3. **Loopback bind.** uvicorn listens on `127.0.0.1` only. Even if the ACL ever flipped open and Hetzner Cloud Firewall ever flipped open simultaneously, there's no listener on a public-facing interface to hit.

## What the server exposes

The same 8 tools as the Mac stdio server. See `docs/mcp-server.md` §What the server exposes for the table. The denylist enforcement, the `propose_draft` source allowlist, and the `get_user_profile` secret-stripping all run identically — the streamable-http transport is a network wrapper, not a new tool surface.

> **Source field is a label, not an authenticator.** `propose_draft(source=...)` accepts any value from the allowlist (`chatgpt`, `cursor`, `gemini`, `claude-desktop`, `web-claude`). With Mac stdio, only the locally-launched client wrote drafts so the source field was tamper-evident. With the remote transport, anyone holding the bearer credential can claim any source. Treat the on-disk source folder as a routing hint, not a provenance guarantee.

## Install runbook (one-time, run on the VPS)

These steps assume Fredis is already deployed on the VPS per `.claude/scripts/schedule/vps-bootstrap.md` (chat / heartbeat / reflect / vault-sync running, Tailscale up, `.claude/scripts/.env` populated).

### 1. Generate a fresh bearer credential on the VPS

Do **not** reuse anything from your Mac. Generate one specific to the VPS so a Mac compromise doesn't cross-contaminate.

```bash
ssh fredis-vps
openssl rand -base64 32
```

Copy the output — you'll paste it into `.env` next. Don't paste it into anything that might end up in chat history, screenshots, or commits.

### 2. Add the MCP env block to the VPS `.env`

```bash
ssh fredis-vps
nano /root/claude-code-second-brain/.claude/scripts/.env
```

Add (or edit) this block. Keep the values that aren't shown unchanged:

```
FREDIS_MCP_ENABLED=1
FREDIS_MCP_TRANSPORT=streamable-http
FREDIS_MCP_BIND=127.0.0.1
FREDIS_MCP_PORT=4747
FREDIS_MCP_AUTH_TOKEN=<paste the value from step 1>
FREDIS_MCP_DENYLIST=USER.md,retainers/,legal/,investors/
```

Save. Confirm permissions are still tight:

```bash
chmod 600 /root/claude-code-second-brain/.claude/scripts/.env
ls -l /root/claude-code-second-brain/.claude/scripts/.env
```

Mode should be `-rw-------`.

### 3. Install the systemd unit

```bash
cp /root/claude-code-second-brain/.claude/scripts/schedule/secondbrain-mcp-server.service \
   /etc/systemd/system/

systemctl daemon-reload
systemd-analyze verify /etc/systemd/system/secondbrain-mcp-server.service
systemctl enable --now secondbrain-mcp-server.service
systemctl status secondbrain-mcp-server.service --no-pager
```

Expected: `Active: active (running)`. The journal should show `starting fredis-mcp server (streamable-http transport on 127.0.0.1:4747)`.

If the service exits 1 with `refusing to start — FREDIS_MCP_TRANSPORT=streamable-http requires FREDIS_MCP_AUTH_TOKEN`, your `.env` doesn't have the credential on its own line — fix and `systemctl restart secondbrain-mcp-server`.

### 4. Front it with Tailscale Serve

This is the step that makes the loopback service reachable from your other Tailscale nodes — and adds Tailscale-managed TLS so clients see `https://`.

```bash
tailscale serve --bg --https=443 http://127.0.0.1:4747
tailscale serve status
```

`tailscale serve status` should list `https://<vps-tailscale-name>/` proxying to `http://127.0.0.1:4747`.

If `tailscale serve` rejects the command with "HTTPS not enabled", enable it once in the Tailscale admin (https://login.tailscale.com/admin/dns → **HTTPS Certificates** → **Enable HTTPS**) then re-run.

### 5. Restrict Tailscale ACL to your nodes

In the Tailscale admin (https://login.tailscale.com/admin/acls), the ACL should only allow Linards's tagged nodes to hit the VPS on TCP/443. A minimal pattern (adjust tag names to match your tailnet):

```jsonc
{
  "acls": [
    // ... existing rules ...
    {
      "action": "accept",
      "src": ["tag:linards-personal"],
      "dst": ["tag:fredis-vps:443"]
    }
  ],
  "tagOwners": {
    "tag:linards-personal": ["autogroup:owner"],
    "tag:fredis-vps":       ["autogroup:owner"]
  }
}
```

Tag the VPS node with `tag:fredis-vps` and your Mac / phone with `tag:linards-personal`. Save the ACL — Tailscale enforces it within seconds.

### 6. Verify the port is closed from outside Tailscale

This is the safety gate. Until this passes, do **not** consider the install complete.

From a non-Tailscale-connected machine (your phone on cellular, or another machine that isn't on the tailnet):

```bash
nmap -p 4747 <vps-public-ipv4>
nmap -p 443  <vps-public-ipv4>
```

Both ports must show `closed` or `filtered`. Port 4747 is closed because uvicorn binds to loopback only. Port 443 is closed because Hetzner Cloud Firewall (`fredis-prod-ssh-only`) drops it; only Tailscale's WireGuard tunnel (UDP/41641) carries the HTTPS traffic. If either shows `open`, **stop**, disable the unit (`systemctl disable --now secondbrain-mcp-server`), and root-cause before retrying.

### 7. Verify from a Tailscale-connected client

From your Mac (Tailscale connected), run two HTTP probes against `https://<vps-tailscale-name>/mcp` (substitute your actual tailnet host name):

- **Without an Authorization header** — expect HTTP 401. The body is `{"error": "unauthorized"}`; the response includes `WWW-Authenticate: Bearer realm="fredis-mcp"`. Use any HTTP client (browser dev tools, Insomnia, Postman). The point of this probe is to confirm bearer auth is enforced.
- **With `Authorization: Bearer <your-credential>`** — expect HTTP 200 (or whatever the streamable-http app returns at its root). Read the credential from the VPS `.env` directly (`ssh fredis-vps "grep FREDIS_MCP_AUTH_TOKEN /root/claude-code-second-brain/.claude/scripts/.env"`), pass it through your local clipboard, and paste into the client tool — never echo it through your shell history.

Then wire a real MCP client (see [§Client wiring](#client-wiring)) and run the same denylist + propose_draft sanity checks as on the Mac (`docs/mcp-server.md` §Manual integration test).

## Client wiring

Each client gets the HTTPS URL and the bearer credential. Substitute `<vps-tailscale-name>` (e.g. `fredis-vps.tail0abc.ts.net`) and `<TOKEN>` (paste from `/root/claude-code-second-brain/.claude/scripts/.env`'s `FREDIS_MCP_AUTH_TOKEN` value).

> **Never paste the credential into this doc, a commit, a screenshot, or chat history.** Read it from the VPS `.env` when you need it.

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fredis-vps": {
      "url": "https://<vps-tailscale-name>/mcp",
      "headers": {
        "Authorization": "Bearer <TOKEN>"
      }
    }
  }
}
```

Restart Claude Desktop. Settings → Developer should list `fredis-vps` with the 8 tools.

You can keep both `fredis` (Mac stdio) and `fredis-vps` (remote) configured at the same time — they share the same vault, so they return the same answers; pick whichever the client connects to first.

### Cursor

Settings → MCP → **Add new MCP server** → `url` mode:

- Name: `fredis-vps`
- URL: `https://<vps-tailscale-name>/mcp`
- Headers: `Authorization: Bearer <TOKEN>`

Cursor stores the credential in its secrets store, not the JSON config.

### Gemini CLI / Code Assist

In `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "fredis-vps": {
      "url": "https://<vps-tailscale-name>/mcp",
      "headers": {
        "Authorization": "Bearer <TOKEN>"
      }
    }
  }
}
```

### Phone / mobile MCP clients

Same pattern — provide the HTTPS URL and the bearer header. The client must be Tailscale-connected. If the client doesn't speak `streamable-http`, fall back to the Mac stdio surface (Phase 1B doesn't add SSE; if a specific client requires it, that's a small follow-on slice).

## Logs

```bash
ssh fredis-vps
journalctl -u secondbrain-mcp-server -f
```

Per-request auth verdicts log as `auth: ok|missing|invalid|malformed`. The credential value never appears.

The server also writes its own log at `.claude/data/logs/mcp-server.log` (file-handler, not the journal). Tail it from inside the repo on the VPS.

## Credential rotation

Rotation cadence is **monthly** for the VPS credential (vs event-driven for the Mac stdio token, which has no network surface).

Procedure: see `.claude/scripts/schedule/rotation-runbooks.md` → §`FREDIS_MCP_AUTH_TOKEN`. Steps in brief:

1. Generate a new value on the VPS (`openssl rand -base64 32`).
2. Update `FREDIS_MCP_AUTH_TOKEN` in `/root/claude-code-second-brain/.claude/scripts/.env`.
3. `systemctl restart secondbrain-mcp-server`.
4. Update each client's stored value (Claude Desktop config / Cursor secrets / Gemini settings).
5. Verify: a probe with the old value returns 401; a probe with the new value returns 200.

The Mac stdio token (if you have one set for some reason) is independent — rotating the VPS value does not affect it.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `systemctl status` shows `Active: failed` immediately after `enable --now` | `journalctl -u secondbrain-mcp-server -n 50` — most common cause is missing `FREDIS_MCP_AUTH_TOKEN`. The error line names the missing variable. |
| Service running but Tailscale clients get connection refused | `tailscale serve status` on the VPS — if the entry is missing, re-run step 4. If it's there but the URL still fails, `systemctl restart tailscaled`. |
| `nmap` from outside Tailscale shows port 443 open | Check the Hetzner Cloud Firewall — only TCP/22 should be allowed. If 443 is allowed, remove that rule. Tailscale uses UDP/41641, not TCP/443, so the public 443 should never be open. |
| Tailscale auth-key expired (`tailscale status` shows logged out) | Re-auth: `tailscale up --auth-key=<new-key>` (rotate the key in the Tailscale admin first). Until re-auth, the MCP service keeps running on loopback but is unreachable. |
| Vault-sync hasn't run recently → MCP returns stale results | The MCP server reads the same vault that vault-sync pulls. Check `systemctl list-timers \| grep vault-sync` — the timer should fire every 2 min. If it's stopped, `systemctl start vault-sync.service` to catch up. |
| Bearer logged as `invalid` for a known-good client | Whitespace or quoting in the client config. Check the client config file with `cat -A` — no `\r`, no surrounding quotes inside the header value. |
| Client times out on first request | The streamable-http handshake takes 1–2 s on a fresh process. Set the client's MCP timeout to ≥10 s. |
| `journalctl` shows `port 4747 already in use` | Something else (probably an old test instance) is on 4747. `ss -tlnp \| grep 4747` to find it; kill it, then `systemctl restart secondbrain-mcp-server`. |

## Rollback

The Mac stdio MCP keeps working through any of these — rollback is VPS-side only.

1. Stop and disable the service:
   ```bash
   ssh fredis-vps
   systemctl disable --now secondbrain-mcp-server.service
   ```
2. Remove the unit file:
   ```bash
   rm /etc/systemd/system/secondbrain-mcp-server.service
   systemctl daemon-reload
   ```
3. Tear down the Tailscale Serve mapping:
   ```bash
   tailscale serve --https=443 off
   ```
4. (Optional) clear the env block — set `FREDIS_MCP_TRANSPORT=` and `FREDIS_MCP_AUTH_TOKEN=` in the VPS `.env`.

No code revert needed. The transport switch is opt-in; with `FREDIS_MCP_TRANSPORT` empty the stdio path runs (and on the VPS, with no client driving it, that's a no-op).

## Related

- Mac stdio operator guide: `docs/mcp-server.md`
- Server entry point: `.claude/scripts/fredis_mcp_server.py`
- Bearer middleware: `.claude/scripts/fredis_mcp_auth.py` (`bearer_auth_app`)
- Systemd unit: `.claude/scripts/schedule/secondbrain-mcp-server.service`
- Rotation runbook: `.claude/scripts/schedule/rotation-runbooks.md` → §`FREDIS_MCP_AUTH_TOKEN`
- Slice plan: `.agent/plans/ob1/05-phase-1B-mcp-remote-vps.md`
- Parent plan: `.agent/plans/fredis-ob1-integration.md` (D2 = A on Mac + B on VPS, recorded 2026-04-27)
