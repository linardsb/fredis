# Secret Rotation Runbooks

Rotation procedure for every secret in `.claude/scripts/.env.example` plus
supporting credentials that live outside `.env`. Run when a token leaks, on
a scheduled cadence (recommended: 90 days), or after a machine change.

**Never paste actual token values into this file.** All examples use
`<placeholders>`.

## General steps (applies to every secret)

1. **Generate new token** at the provider's dashboard (see per-secret URLs below).
2. **Update local `.env`** at `.claude/scripts/.env` with the new value.
3. **Update VPS `.env`** — copy the new value via SSH (`scp` or in-place edit).
4. **Restart dependent services** — see per-secret list.
5. **Verify** — see per-secret smoke test.
6. **Revoke old token** at the provider (don't leave it valid in parallel).

## Per-secret procedures

### `SLACK_BOT_TOKEN` — xoxb-…

1. Generate: https://api.slack.com/apps → pick the Fredis app → **OAuth &
   Permissions** → **Reinstall App** (triggers a token refresh).
2. Update `SLACK_BOT_TOKEN` in both `.env` files.
3. Restart services:
   - **Local** — kill + relaunch `run_chat.sh` (or `launchctl kickstart -k
     gui/$(id -u)/com.linards.fredis-chat`).
   - **VPS** — `systemctl restart secondbrain-chat.service`.
4. Verify: send a DM to the bot — expect a response.
5. Revoke old: Slack rotates the old token automatically on reinstall.

### `SLACK_APP_TOKEN` — xapp-…

1. Generate: Slack app settings → **Basic Information** → **App-Level
   Tokens** → regenerate.
2. Update `SLACK_APP_TOKEN` in both `.env` files.
3. Restart same services as `SLACK_BOT_TOKEN`.
4. Verify: chat engine logs should show `Slack adapter connected`.
5. Revoke old: click **Revoke** on the old token row.

### `ANTHROPIC_API_KEY` — sk-ant-…

Only set if overriding the Claude Code CLI credentials
(`~/.claude/.credentials.json`). Most local users skip this.

1. Generate: https://console.anthropic.com/settings/keys → **Create Key**.
2. Update `ANTHROPIC_API_KEY` in `.env` (or unset if reverting to
   CLI-credential mode).
3. Restart: heartbeat launchd job (`launchctl kickstart -k
   gui/$(id -u)/com.linards.fredis-heartbeat`) + chat service.
4. Verify: run `uv run python heartbeat.py --test`.
5. Revoke old: console → **Delete key**.

### `GITHUB_TOKEN` — ghp_… (or github_pat_…)

1. Generate: https://github.com/settings/tokens → **Generate new token**.
   Classic = `repo` + `read:user` scopes; fine-grained = read access to
   Fredis's watched repos + user.
2. Update `GITHUB_TOKEN` in both `.env` files.
3. Restart: heartbeat launchd + chat service (GitHub is used by the
   integrations module which is lazy-loaded).
4. Verify: `uv run python query.py github recent --hours 24`.
5. Revoke old: **Delete** the old token on the settings page.

### `ASANA_ACCESS_TOKEN` — 1/123456789:abc…

1. Generate: https://app.asana.com/0/developer-console → **New access
   token**.
2. Update `ASANA_ACCESS_TOKEN` in both `.env` files.
3. Restart: same as GitHub.
4. Verify: `uv run python query.py asana my-tasks --max 5`.
5. Revoke old: developer console → **Revoke**.

### `MONDAY_API_TOKEN` — JWT-shaped

1. Generate: Monday.com → avatar menu → **Admin** → **API** → **Generate
   new token**.
2. Update `MONDAY_API_TOKEN` in both `.env` files.
3. Restart: same as GitHub.
4. Verify: `uv run python query.py monday my-items --max 5`.
5. Revoke old: API page → previous token row → **Revoke**.

### Google OAuth (Gmail / Calendar / Drive / Docs / Sheets)

These share a single OAuth client (`google_credentials.json`) + refresh
token (`google_token.json`). Rotation scenarios:

**Refresh token only (expired / invalidated):**
1. Delete `google_token.json` at `.claude/scripts/integrations/`.
2. Re-run `cd .claude/scripts && uv run python setup_auth.py` — browser
   opens for OAuth consent.
3. Token auto-saved.
4. Restart heartbeat + chat service.
5. Verify: `uv run python query.py gmail list --max 3`.

**Full client-secret rotation (compromised `google_credentials.json`):**
1. Google Cloud Console → **APIs & Services** → **Credentials**.
2. Click the OAuth client → **Reset Secret**.
3. Download the new JSON → replace
   `.claude/scripts/integrations/google_credentials.json`.
4. Delete `google_token.json` → re-run `setup_auth.py`.
5. Restart + verify.
6. Revoke old: console → delete the prior OAuth client if creating a new
   one, or confirm the secret reset succeeded.

### `DATABASE_URL` — Postgres password

Only applies in VPS/Postgres mode.

1. Generate new password: `openssl rand -base64 32`.
2. Rotate on the DB:
   ```sql
   ALTER USER secondbrain WITH PASSWORD '<new-password>';
   ```
3. Update `DATABASE_URL` in the VPS `.env` (include the new password in
   the URL: `postgresql://secondbrain:<new-password>@localhost:5432/secondbrain`).
4. Restart `secondbrain-chat.service` (reads `.env` at startup).
5. Verify: `systemctl status secondbrain-chat.service` → running + no
   auth errors in `journalctl -u secondbrain-chat.service -n 30`.
6. Revoke old: the `ALTER USER` replaces the old password — nothing
   extra needed.

### SSH key (VPS access)

The key is used by `ssh-tunnel.plist` (local Postgres tunnel) and any
manual `ssh`.

1. Generate new key:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/secondbrain_new -C "secondbrain-rotated-YYYY-MM-DD"
   ```
2. Add the new public key to the VPS:
   ```bash
   ssh-copy-id -i ~/.ssh/secondbrain_new.pub <user>@<vps-host>
   ```
3. Update references:
   - `com.linards.ssh-tunnel.plist` — the `<KEY_PATH>` placeholder.
   - Any local `~/.ssh/config` host entry.
4. Reload the ssh-tunnel launchd:
   ```bash
   launchctl kickstart -k gui/$(id -u)/com.linards.ssh-tunnel
   ```
5. Verify: `nc -z localhost 5432 && echo TUNNEL_OK`.
6. Revoke old: SSH into VPS → edit `~/.ssh/authorized_keys` → remove the
   old public key line.

### SSH key (Fredis vault git remote)

Same shape as VPS key, but the public key lives on the git-remote host
(GitHub deploy key / internal git server / self-hosted remote).

1. Generate new key (see above, perhaps `~/.ssh/fredis_vault_new`).
2. Add public key to GitHub → **Settings** → **Deploy keys** (for the
   Fredis repo specifically) OR to the internal git server.
3. Update references in:
   - Local `~/.ssh/config`.
   - VPS `~/.ssh/config`.
4. Test: `git -C Fredis fetch`.
5. Revoke old: remove the old deploy key from GitHub / server.

## Summary table

| Secret | Rotate URL | Dependent services | Smoke test |
|--------|------------|--------------------|------------|
| `SLACK_BOT_TOKEN` | Slack app → OAuth & Permissions → Reinstall | chat service | DM the bot |
| `SLACK_APP_TOKEN` | Slack app → Basic Information → App-Level Tokens | chat service | `Slack adapter connected` log |
| `ANTHROPIC_API_KEY` | console.anthropic.com/settings/keys | heartbeat + chat | `heartbeat.py --test` |
| `GITHUB_TOKEN` | github.com/settings/tokens | heartbeat + chat | `query.py github recent` |
| `ASANA_ACCESS_TOKEN` | app.asana.com/0/developer-console | heartbeat + chat | `query.py asana my-tasks` |
| `MONDAY_API_TOKEN` | Monday admin → API | heartbeat + chat | `query.py monday my-items` |
| Google OAuth refresh token | Delete + re-run `setup_auth.py` | heartbeat + chat | `query.py gmail list` |
| Google OAuth client secret | Google Cloud Console → Credentials → Reset Secret | heartbeat + chat | after re-auth, `query.py gmail list` |
| Postgres password | `ALTER USER` on DB | chat service | `systemctl status secondbrain-chat` |
| SSH key (VPS) | `ssh-keygen` + `ssh-copy-id` | ssh-tunnel launchd | `nc -z localhost 5432` |
| SSH key (vault git) | `ssh-keygen` + add deploy key | vault-sync | `git -C Fredis fetch` |
