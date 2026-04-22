# VPS Bootstrap Runbook (Hetzner CX23)

Single-source-of-truth runbook for deploying the Second Brain to a fresh Linux
VPS. Supersedes the earlier inline steps in `README.md` §VPS Deployment.

Target host: **Hetzner CX23** (2 vCPU / 4 GB / 40 GB, Ubuntu 24.04, Helsinki)
at €4.79/mo. Any €5–10/mo Linux host with Docker-capable Ubuntu 24.04+ works
with the same steps.

Every command below runs either from the Mac terminal (local) or inside
`ssh fredis-vps` (remote) — each section labels which. Each step has a
**Verify** line; stop and debug if a verification fails before moving on.

---

## B1 — Prerequisites

*Phase 9 commit status is NOT a blocker* (corrected 2026-04-21): VPS
Postgres starts empty, Phase 9's schema change is idempotent
(`ADD COLUMN IF NOT EXISTS`), and `memory_index.py --rebuild` reseeds.
Phase 9 can land on `main` on its own timeline.

What you do need:

- [ ] Hetzner account + payment method.
- [ ] SSH keypair generated locally (e.g. `~/.ssh/id_hetzner_vps`).
- [ ] Local `.env` and `integrations/google_token.json` populated on the
  Mac (you'll SCP these in B6).
- [ ] GitHub repo URL known (the project repo — NOT the vault, the vault is
  handled separately in Phase 10.5).

---

## B2 — Provision the CX23

Hetzner Console → **Add Server**:

| Field | Value |
|-------|-------|
| Location | Helsinki (HEL1) — closest EU option with low latency to London |
| Image | Ubuntu 24.04 |
| Type | CX23 (2 vCPU / 4 GB / 40 GB / €4.79/mo) |
| Networking | IPv4 + IPv6 enabled |
| SSH keys | Attach your local pubkey at create time (critical — enables passwordless root before any hardening) |
| Firewall | Create `fredis-prod-ssh-only` with inbound TCP/22 from `0.0.0.0/0, ::/0`; deny everything else inbound; outbound: all |
| Backups | **ON** (+20 % ≈ €0.96/mo) for the first 30 days, then reassess |
| Labels | `env=prod`, `role=fredis` |

Add a local SSH shortcut so you can type `ssh fredis-vps`:

```bash
cat >> ~/.ssh/config <<'EOF'

Host fredis-vps
  HostName <vps-ipv4>
  User root
  IdentityFile ~/.ssh/id_hetzner_vps
  IdentitiesOnly yes
EOF
chmod 600 ~/.ssh/config
```

**Verify:**

```bash
ssh fredis-vps uptime
```
Returns a load-average line within a few seconds.

---

## B3 — Harden the OS

Run on VPS (via `ssh fredis-vps`):

```bash
# Timezone + locale
timedatectl set-timezone Europe/London
locale-gen en_GB.UTF-8 && update-locale LANG=en_GB.UTF-8

# Firewall (defence in depth alongside Hetzner Cloud Firewall)
ufw allow 22/tcp
ufw --force enable
ufw status verbose

# Fail2ban — default sshd jail is sufficient for a personal box
apt update
apt install -y fail2ban unattended-upgrades
systemctl enable --now fail2ban
fail2ban-client status sshd

# Auto-apply security patches
dpkg-reconfigure -plow unattended-upgrades
systemctl enable --now unattended-upgrades.service

# Upgrade and reboot if a new kernel came in
apt full-upgrade -y
[ -f /var/run/reboot-required ] && reboot
```

**Verify:**

- `ufw status` lists `22/tcp ALLOW` and nothing else inbound.
- `fail2ban-client status sshd` shows the jail active.
- `systemctl is-enabled unattended-upgrades` returns `enabled`.

---

## B4 — Install dependencies

Run on VPS:

```bash
apt install -y docker.io docker-compose-v2 git build-essential

# uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.local/bin/env

# Claude CLI
curl -fsSL https://claude.ai/install.sh | bash
```

**Verify:**

```bash
docker --version        # 27+ or 29+
uv --version            # 0.11+
claude --version        # 2.x
git --version
```

---

## B5 — Clone the repo + `claude login`

Run on Mac (clone):

```bash
ssh fredis-vps "cd /root && git clone https://github.com/linardsb/<repo>.git claude-code-second-brain"
```

*Resolve the repo name against the actual GitHub URL before running — the
historical `linardsb/fredis.git` reference in the old README may be stale.*

Then `claude login` — **interactive, needs your Mac browser**:

```bash
ssh fredis-vps
```

Inside the VPS shell:

```bash
claude            # prints an OAuth URL — open on Mac, authorise, paste the code back
exit
```

**Verify:**

```bash
ssh fredis-vps "ls -la /root/.claude/.credentials.json && stat -c %a /root/.claude/.credentials.json"
```
File exists, mode `600`.

---

## B6 — Transfer secrets

Run on Mac:

```bash
scp .claude/scripts/.env \
    fredis-vps:/root/claude-code-second-brain/.claude/scripts/.env

scp .claude/scripts/integrations/google_token.json \
    fredis-vps:/root/claude-code-second-brain/.claude/scripts/integrations/google_token.json

ssh fredis-vps "chmod 600 \
  /root/claude-code-second-brain/.claude/scripts/.env \
  /root/claude-code-second-brain/.claude/scripts/integrations/google_token.json"
```

On VPS — uncomment `DATABASE_URL`:

```bash
ssh fredis-vps 'sed -i "s|^# DATABASE_URL=|DATABASE_URL=|" /root/claude-code-second-brain/.claude/scripts/.env && grep "^DATABASE_URL=" /root/claude-code-second-brain/.claude/scripts/.env'
```

**Verify:** the grep returns one line; `ls -l` on both files shows `-rw-------`.

---

## B6.5 — Rsync the vault (one-way, Mac → VPS)

Phase 10 workaround. The local `Fredis/` vault has no git remote set up,
so bidirectional git-sync is deferred to Phase 10.5. Rsync the vault
contents up once so heartbeat/reflection/memory-search have data to read.

Run on Mac:

```bash
rsync -av --delete \
  --exclude='.obsidian/workspace*.json' \
  --exclude='.trash/' \
  Fredis/ \
  fredis-vps:/root/claude-code-second-brain/Fredis/
```

**Verify:**

```bash
ssh fredis-vps "ls /root/claude-code-second-brain/Fredis/Memory/ | head && \
  wc -l /root/claude-code-second-brain/Fredis/Memory/SOUL.md"
```

Should list `SOUL.md`, `USER.md`, `MEMORY.md`, `daily/`, `drafts/` etc.

---

## B7 — Start Postgres (Obsidian stays off)

Run on VPS:

```bash
cd /root/claude-code-second-brain
TZ=Europe/London docker compose up postgres -d
sleep 20
docker compose ps postgres
docker exec secondbrain-postgres pg_isready -U secondbrain
```

**Verify:** `docker compose ps` column `STATUS` shows `healthy`.
`pg_isready` returns exit 0.

---

## B8 — Build the search index

Run on VPS:

```bash
cd /root/claude-code-second-brain/.claude/scripts
source ~/.local/bin/env
uv sync
uv run python memory_index.py --rebuild
```

First run downloads the FastEmbed ONNX model (~80 MB). Indexing a
typical vault takes 30–90 seconds.

**Verify:**

```bash
uv run python memory_search.py "heartbeat" --mode hybrid --limit 1
```
Returns at least one result.

---

## B9 — Install systemd units

Run on VPS:

```bash
REPO=/root/claude-code-second-brain

cp $REPO/.claude/scripts/schedule/secondbrain-chat.service /etc/systemd/system/
cp $REPO/.claude/scripts/schedule/{deps-audit,fredis-heartbeat,fredis-reflect,fredis-summary,vault-sync}.service /etc/systemd/system/
cp $REPO/.claude/scripts/schedule/{deps-audit,fredis-heartbeat,fredis-reflect,fredis-summary,vault-sync}.timer /etc/systemd/system/

# Substitute __REPO_ROOT__ in every unit file in one pass
sed -i "s|__REPO_ROOT__|$REPO|g" \
  /etc/systemd/system/{deps-audit,fredis-heartbeat,fredis-reflect,fredis-summary,vault-sync}.service \
  /etc/systemd/system/{deps-audit,fredis-heartbeat,fredis-reflect,fredis-summary,vault-sync}.timer

systemctl daemon-reload

# Enable everything EXCEPT vault-sync.timer.
# vault-sync.timer stays disabled until Phase 10.5 closes the git-remote gap —
# otherwise it fails every 2 min with "fatal: not a git repository".
systemctl enable --now secondbrain-chat.service
systemctl enable --now deps-audit.timer fredis-heartbeat.timer fredis-reflect.timer fredis-summary.timer
```

**Verify:**

```bash
systemctl list-timers | grep -E "fredis|deps"          # 4 timers (heartbeat, reflect, summary, deps-audit)
systemctl is-active secondbrain-chat                   # active
systemd-analyze verify /etc/systemd/system/{secondbrain-chat,deps-audit,fredis-heartbeat,fredis-reflect,fredis-summary,vault-sync}.{service,timer} 2>&1 | head
```

`systemd-analyze verify` should return no output (silent pass).

---

## B10 — Cutover (stop local plists to prevent split-brain)

Run on Mac:

```bash
launchctl unload ~/Library/LaunchAgents/com.linards.fredis-heartbeat.plist 2>/dev/null || true
launchctl unload ~/Library/LaunchAgents/com.linards.fredis-reflect.plist 2>/dev/null || true

# secondbrain-chat was running on Mac too — unload if so
launchctl unload ~/Library/LaunchAgents/com.linards.fredis-chat.plist 2>/dev/null || true

echo "Remaining local fredis agents (should be empty):"
launchctl list | grep com.linards.fredis || echo "  (none — good)"
```

**Smoke test — DM the Slack bot:**

Open a DM with the Second Brain bot in Slack, type `hello`.
Expected: reply within ~10 seconds, memory-aware, sourced from VPS
Postgres.

If no reply:

```bash
ssh fredis-vps "journalctl -u secondbrain-chat -n 50"
```

**Manual heartbeat trigger:**

```bash
ssh fredis-vps "systemctl start fredis-heartbeat.service"
sleep 90
ssh fredis-vps "journalctl -u fredis-heartbeat.service -n 40"
```

**Manual reflection trigger** (does an Edit on `MEMORY.md` — exercises the
`block-soul-edit` hook path and confirms the Agent SDK write channel):

```bash
ssh fredis-vps "systemctl start fredis-reflect.service"
sleep 60
ssh fredis-vps "journalctl -u fredis-reflect.service -n 40"
```

**Verify:** no tracebacks in the journal. Slack DM works. Any heartbeat
alert that needed to fire has fired.

---

## B11 — Local SSH tunnel (so local memory search hits VPS Postgres)

Run on Mac:

```bash
cp .claude/scripts/schedule/com.linards.ssh-tunnel.plist \
   ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist

sed -i '' \
  -e "s|__HOME__|$HOME|g" \
  -e "s|__REPO_ROOT__|$(git rev-parse --show-toplevel)|g" \
  -e "s|__KEY_PATH__|$HOME/.ssh/id_hetzner_vps|g" \
  -e "s|__VPS_USER__|root|g" \
  -e "s|__VPS_HOST__|<vps-ipv4>|g" \
  ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist

mkdir -p .claude/data/logs
launchctl load ~/Library/LaunchAgents/com.linards.ssh-tunnel.plist
sleep 3
nc -z localhost 5432 && echo TUNNEL_OK
```

Add `DATABASE_URL` to local `.env` so local searches hit VPS Postgres:

```bash
PASS=$(ssh fredis-vps "grep '^POSTGRES_PASSWORD=' /root/claude-code-second-brain/.claude/scripts/.env | cut -d= -f2")
echo "DATABASE_URL=postgresql://secondbrain:${PASS}@localhost:5432/secondbrain" >> .claude/scripts/.env
```

**Verify:**

```bash
cd .claude/scripts
uv run python memory_search.py "Phase 8" --mode hybrid --limit 3
```
Results returned. Confirm they come from VPS by temporarily unloading the
tunnel (`launchctl unload …ssh-tunnel.plist`) → query should fail →
reload to restore.

---

## B12 — Validate, log, done

Run on VPS:

```bash
cd /root/claude-code-second-brain/.claude/scripts
uv run pytest tests/
```
Expect ≥471 passing, 0 failing (Phase 8 baseline; Phase 9 adds more).

Append a Phase 10 entry to today's daily log (either on Mac, via rsync on
next cycle, or on VPS directly). Add a Phase 10 stub to
`CLAUDE.md` §Completed Phases.

**Post-deploy verification checklist:**

- [ ] `systemctl list-timers | grep -E "fredis|deps"` → 3 timers listed
- [ ] `systemctl is-active secondbrain-chat` → `active`
- [ ] Slack bot replies to `hello` in a DM
- [ ] `systemctl start fredis-heartbeat.service` → journal shows clean exit
- [ ] `systemctl start fredis-reflect.service` → journal shows clean exit, `MEMORY.md` updated
- [ ] Local `memory_search.py` returns results from VPS Postgres (via tunnel)
- [ ] `ufw status` shows only 22/tcp
- [ ] `ss -tlnp` shows only sshd on a public interface (all other listeners on 127.0.0.1)
- [ ] `.env` and `google_token.json` on VPS are mode 600
- [ ] `launchctl list | grep com.linards.fredis` is empty on Mac (split-brain prevented)

---

## Rollback

If anything in B10 goes wrong, get the Mac back online quickly:

```bash
# 1. Stop VPS services
ssh fredis-vps "systemctl stop secondbrain-chat fredis-heartbeat.timer fredis-reflect.timer vault-sync.timer 2>/dev/null || true"

# 2. Bring local agents back
launchctl load ~/Library/LaunchAgents/com.linards.fredis-heartbeat.plist
launchctl load ~/Library/LaunchAgents/com.linards.fredis-reflect.plist
launchctl load ~/Library/LaunchAgents/com.linards.fredis-chat.plist 2>/dev/null || true

# 3. Unset DATABASE_URL locally → memory search falls back to SQLite
sed -i '' '/^DATABASE_URL=/d' .claude/scripts/.env
```

Rollback is safe because:

- Local `.env` is restored by step 3 (the backed-out line was the only change).
- Local plists were only unloaded, never deleted — reload restores them.
- Chat sessions resume from local `chat.db` when the local chat bot restarts.
- VPS state is preserved; retry after diagnosing.

---

## Troubleshooting

### `claude login` token expired on VPS

Symptom: `secondbrain-chat` restart-loops; journal shows `401 Unauthorized`
from Anthropic API.

Fix:

```bash
ssh fredis-vps
claude                           # complete OAuth again
systemctl restart secondbrain-chat
```

### `docker compose up postgres` fails with `port 5432 in use`

Something else on the VPS is already bound to 5432 (another Postgres
install, leftover container).

```bash
ss -tlnp | grep 5432             # find the culprit
systemctl stop postgresql 2>/dev/null || true
apt purge -y postgresql postgresql-*      # if native install
docker ps -a | grep postgres
docker rm -f <leftover-container>
docker compose up postgres -d
```

### Postgres healthcheck hangs — `pgdata` volume permission mismatch

After a host reboot or `docker compose down -v`, the pgdata volume can
own-mismatch (root vs postgres user inside the container).

```bash
docker compose down
docker volume rm claude-code-second-brain_pgdata
docker compose up postgres -d
sleep 20
docker compose ps postgres
cd .claude/scripts && uv run python memory_index.py --rebuild      # reseed
```

### Heartbeat journal shows `Operation not permitted`

Either the `.env` file is wrong mode or the Claude credentials expired.
Check `stat -c %a` on both; should be `600`.

### `launchctl unload` on Mac fails with "no such file"

You never installed those plists on this Mac. Safe to ignore — the
command block uses `|| true` for that reason.

---

## After deploy — what still needs attention

See the parent plan's **Phase 10.5** section for the vault-sync
follow-up (bidirectional git-sync for `Fredis/`). Until that's closed:

- Vault changes written by heartbeat/reflection on the VPS stay on the VPS.
- Vault edits on Mac don't reach the VPS unless you re-run the B6.5 rsync.
- Keep notes where you make them, rsync manually when needed.

Priority: medium. Close within 1–2 weeks of the Phase 10 cutover.
