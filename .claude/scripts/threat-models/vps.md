# Threat Model — VPS Host (Hetzner CX23)

Unlike the other pages in this directory, this one models the *host*
rather than a single Agent-SDK caller. The per-agent pages
(`heartbeat.md`, `chat.md`, `reflection.md`, `memory_flush.md`,
`memory_synthesis.md`) cover prompt-injection and in-process attack
surface; this page covers what the machine itself exposes to the public
internet. Follow the §7 checklist from
`.claude/skills/security-engineering/references/agent-guardrails.md`.

## Attack surface

**Public-facing:**

- **SSH (TCP/22)** — the only inbound port allowed by both the
  Hetzner Cloud Firewall and `ufw`. Key-only auth; `fail2ban` bans
  IPs after repeated failures.
- **Outbound WebSocket to Slack** (Socket Mode, `wss.slack.com:443`) —
  long-lived connection carrying DMs and @mentions into the chat
  engine. Treated as untrusted external input once it crosses into the
  main agent (see `chat.md` threat model for the sanitise pipe).
- **Outbound HTTPS** to Anthropic, Google, Asana, Monday, GitHub,
  Hetzner package mirrors. Initiated by the agents, never incoming.

**Not exposed:**

- **Postgres (5432)** — bound to `127.0.0.1:5432` in `docker-compose.yml`.
  Reached from Mac only via an SSH tunnel (`com.linards.ssh-tunnel.plist`).
- **Obsidian (8080)** — service commented out in `docker-compose.yml`
  by default. If re-enabled, binds to `127.0.0.1:8080` (LAN-only).
- **No HTTP webhook surface** — Phase 10 does not host any inbound
  HTTP listener. Slack is outbound-only; Gmail/Calendar/etc are
  polled. Phase 11+ would need to reopen this question if adding a
  web UI or webhook.

**Filesystem exposure (not public but worth naming):**

- `/root/claude-code-second-brain/.claude/scripts/.env` — mode 600,
  secrets for every integration.
- `/root/claude-code-second-brain/.claude/scripts/integrations/google_token.json`
  — mode 600, OAuth refresh token.
- `/root/.claude/.credentials.json` — mode 600, Claude Max OAuth
  credential (device-bound).
- `/root/claude-code-second-brain/Fredis/` — full memory vault
  (SOUL, USER, MEMORY, daily logs, drafts).

Any attacker with shell access becomes an attacker with all of the
above. There is no additional in-process sandbox beyond the
PreToolUse hook set.

## 1. Inputs

- SSH session (key-auth, gated by fail2ban + Hetzner firewall).
- Slack WebSocket messages (treated as untrusted — `chat.md` applies
  the 3-layer sanitize pipe on every inbound).
- API responses from Gmail / Calendar / Asana / Monday / Slack
  history / GitHub during heartbeat gather (pass through
  `sanitize.py` + Haiku guardrail before reaching the main agent).

**Trust boundary:** every external field arrives via Python and passes
through `sanitize.sanitize_external_text` + `wrap_external_data`
before it becomes prompt input. The host itself is *not* a trust
boundary for agent prompts — the in-process pipeline is.

## 2. Tools (host-level)

- `systemd` services run as `User=root` (see §Tech debt below).
- `docker` daemon runs as root; Postgres container runs as its
  image's `postgres` user.
- `claude` CLI / `uv run` inherit root.
- PreToolUse hooks (`block-secrets`, `block-dangerous-commands`,
  `block-template-residue`, `block-soul-edit`) apply to every Agent
  SDK sub-session via `setting_sources=["user","project"]`.

Blast radius if an agent is successfully jailbroken: anything root
can write. Mitigated at the hook layer (no outbound sends, no
SOUL edits, no writes outside the repo + vault sandbox).

## 3. Writes (to host state)

- Repo files (`Edit`/`Write` tool, gated by `block-template-residue`
  and `block-soul-edit`).
- Vault files under `Fredis/Memory/` (same gates).
- systemd journal (via `StandardOutput=journal`).
- Append-only run logs at `.claude/scripts/*_runs.log`.
- Postgres (chunks, sessions, chat history) via the app, not shell.
- `.claude/data/state/*.json` (per-machine state — heartbeat,
  reflection, guardrail).

No agent path writes to `/etc/`, `/root/.ssh/`, or systemd unit
files. A shell-level compromise would — which is why the guarded
surface is SSH, not the agents.

## 4. Memory reads

Agents on the VPS read the same vault files as on the Mac. The
Phase 5 injection-pipeline on memory reads (daily log bundle
`source:` header + `memory_reflect.py` abort on injection pattern)
applies the same way — see `reflection.md` and `memory_flush.md`.

Host-level reads of `.env` / `google_token.json` happen only via
the integration Python modules that need them; `block-secrets`
blocks any attempt to `Read`/`Cat` them from an agent tool call.

## 5. Outputs

- **Slack DM** — the one user-visible external surface. Per-bot
  DM; `_neutralise_mentions` prevents `<!channel>` / `<@USER_ID>`
  broadcast triggers in the chat adapter (Phase 4).
- **Gmail drafts** — create-only, never send; `block-dangerous-commands`
  rejects any `drafts.send` shape.
- **Daily logs + drafts** (`Fredis/Memory/…`) — synced back to Mac via
  Phase 10.5 git-sync (pending); until then, stay on VPS.

No outbound posting APIs in any automated path (advisor mode).

## 6. Failure modes

- **Haiku guardrail timeout / exception** — heartbeat's guardrail
  has a 15s `asyncio.wait_for` (Phase 8 Phase 2); on timeout,
  verdict becomes `error`, external data is stripped from the
  main-agent prompt, Slack alert fires.
- **SSH brute-force** — fail2ban bans source IP after 3–5
  failed attempts for 10 min. Hetzner Cloud Firewall is the
  outer defence.
- **Compromised `.env`** — all tokens rotatable in ≤24 h per
  `.claude/scripts/schedule/rotation-runbooks.md` (90-day cadence,
  rotate immediately on suspected leak).
- **Docker daemon crash** — `secondbrain-postgres` has
  `restart: unless-stopped`; chat service has `Restart=always` and
  will reconnect.
- **Postgres data loss** — Hetzner snapshots (ON for the first 30
  days). Vault is in git (Phase 10.5), so the only non-recoverable
  loss would be chat session IDs — conversations start fresh on
  next message.
- **Unpatched kernel CVE** — `unattended-upgrades` auto-applies
  security channel; manual `apt full-upgrade` + reboot on kernel
  updates.

## Mitigations in force

| Layer | Control | Where |
|-------|---------|-------|
| Network | Hetzner Cloud Firewall — inbound TCP/22 only | B2 |
| Network | `ufw allow 22/tcp` + enable | B3 |
| Auth | SSH key-only; `fail2ban` sshd jail | B3 |
| OS | `unattended-upgrades` on security channel | B3 |
| Container | Postgres bound to `127.0.0.1` only; Obsidian commented out | `docker-compose.yml` |
| Filesystem | `.env` / `google_token.json` / `.credentials.json` mode 600 | B6 |
| Agent | 3-layer sanitize pipe (regex + markdown-escape + XML wrap) | `sanitize.py` |
| Agent | Haiku guardrail with 15s fail-closed timeout | `heartbeat.py` |
| Agent | PreToolUse hooks (secrets, dangerous, template, SOUL) on every SDK surface | `.claude/hooks/` |
| Data | Hetzner snapshots ON for first 30 days | B2 |

## Revisit triggers

Re-audit this threat model whenever any of the following changes:

- A new systemd service is added to `.claude/scripts/schedule/`.
- A new inbound port is opened in `ufw` or the Hetzner Cloud
  Firewall.
- The Docker Compose config exposes a new port (any `0.0.0.0:` bind
  is a red flag).
- A new integration is added to the heartbeat gather path
  (re-check the sanitize pipe coverage).
- A new PreToolUse hook is registered in `.claude/settings.json`.
- `User=root` changes (see Tech debt).
- Claude Code Agent SDK changes `allowed_tools` defaults.
- A new external surface is added (webhook, HTTP listener, MCP
  server exposed on a network port).
- A secret type rotates or is added to `.env`.

## Tech debt — `User=root`

Every systemd unit on the VPS (`secondbrain-chat`, `fredis-heartbeat`,
`fredis-reflect`, `vault-sync`, `deps-audit`) runs as `User=root`. This
matches the historical `secondbrain-chat.service` and is accepted for
Phase 10 as single-user tech debt, but it violates least-privilege.

A future hardening pass should:

1. Create a dedicated `fredis` user (+ group), no login shell needed.
2. Move the repo to `/home/fredis/claude-code-second-brain/`.
3. Move `~/.claude/.credentials.json` to `/home/fredis/.claude/`.
4. Update every unit's `User=`, `WorkingDirectory=`,
   `Environment=PATH=…`, and `Environment=CLAUDE_PROJECT_DIR=…`.
5. `chown -R fredis:fredis` on repo + Claude config dir.
6. Keep Docker running as root (daemon model); add `fredis` to the
   `docker` group so the user can `docker compose` without sudo.
7. Validate: `pytest` passes, heartbeat Slack alert fires, chat bot
   responds, `memory_reflect` edits `MEMORY.md` — all as `fredis`.

Tracked here until it lands.

## Out of scope for Phase 10

- TLS / reverse proxy / domain (no HTTP surface exists).
- Multi-region HA.
- Host IDS (falco, auditd-based monitoring).
- SELinux / AppArmor profiles for the agents.
- Log shipping / centralised SIEM.

Each would warrant reopening this page with an additional section.
