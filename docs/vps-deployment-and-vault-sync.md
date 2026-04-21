# VPS Deployment & Mirrored Vault Sync

_Reference doc — not a runbook. For the point-in-time deployment snapshot see `docs/phase10-deploy-progress.md`. For setup walkthrough see `.claude/scripts/schedule/vps-bootstrap.md`._

**Last revised:** 2026-04-21 after the Phase 10 + 10.5 cutover session.

---

## 1 · What this is

Fredis runs on a Hetzner CX23 VPS in Helsinki. The user's Mac is a dev environment (for code) and an Obsidian client (for the vault). All scheduled services — heartbeat, reflection, weekly synthesis, dependency audit, Slack chat — run exclusively on the VPS. The `Fredis/` vault folder (SOUL.md / USER.md / MEMORY.md / daily logs / drafts / research notes) is bidirectionally mirrored between Mac and VPS every 2 minutes via git, because Obsidian needs local files to work.

The final shape:

```
     Mac                                            VPS (46.62.175.147)
  ┌──────────────────────────┐                   ┌──────────────────────────┐
  │ Obsidian (reads vault)   │                   │ secondbrain-chat.service │
  │ Claude Code (dev)        │                   │ fredis-heartbeat.timer   │
  │ memory_search.py ────────┼── SSH tunnel ────▶│ fredis-reflect.timer     │
  │   (via localhost:5433)   │  (root Postgres   │ fredis-synthesis.timer   │
  │                          │   on 5432)        │ fredis-vault-sync.timer  │
  │ fredis-vault-sync plist  │                   │ deps-audit.timer         │
  │   (every 2 min)          │◀── git ────────▶  │ fredis-vault-sync timer  │
  └──────────┬───────────────┘                   └──────────┬───────────────┘
             │                                              ▲
             │                                              │ git pull --ff-only
             ▼                                              │
       ┌────────────────────┐       GH Action        ┌──────┴──────────┐
       │ git push origin ───┼────(deploy-vps.yml)───▶│ deploy.sh       │
       │   main             │      on push to main   │ selective       │
       └────────────────────┘      (paths-ignore     │ restart         │
                                    Fredis/ + docs/  └─────────────────┘
                                    + **/*.md)
```

---

## 2 · The three flows

### 2.1 · Code

- **Trigger:** `git push origin main` from the Mac.
- **Path:** GitHub → `deploy-vps.yml` → `appleboy/ssh-action` → `/root/claude-code-second-brain/.claude/scripts/deploy.sh` on VPS.
- **What deploy.sh does:**
  1. `flock /var/lock/fredis-deploy.lock` — only one deploy at a time.
  2. `git pull --ff-only origin main`.
  3. Diff the pulled range, and selectively:
     - `uv sync` if `pyproject.toml` or `uv.lock` changed.
     - Re-render every installed systemd unit from `.claude/scripts/schedule/*.{service,timer}` (substituting `__REPO_ROOT__`) and `daemon-reload` if any unit file changed.
     - `systemctl restart secondbrain-chat.service` if chat code changed.
- **What the workflow skips:** any commit whose changed paths match `Fredis/**`, `docs/**`, or `**/*.md`. This keeps the ~50/day vault auto-commits from triggering redeploys.
- **When the paths-ignore skips too aggressively:** trigger a deploy manually with `gh workflow run deploy-vps.yml -R linardsb/fredis` or `ssh fredis-vps "bash /root/claude-code-second-brain/.claude/scripts/deploy.sh"`.

### 2.2 · Vault

- **Trigger:** timer on each side every 2 minutes.
  - Mac: `com.linards.fredis-vault-sync` (launchd, `StartInterval=120`).
  - VPS: `fredis-vault-sync.timer` (systemd, `OnUnitInactiveSec=2min`).
- **Script:** both sides run `.claude/scripts/vault-sync-repo.sh`. It:
  1. `mkdir`-based atomic lock (cross-platform; macOS lacks `flock`). Reclaims lock if the owning PID is gone.
  2. `git add -A -- Fredis/` — subtree-scoped. Never stages anything outside `Fredis/`. WIP code on Mac stays unstaged.
  3. If anything staged, commits with the fredis-vault-sync identity. Message format: `vault: sync from $(hostname -s) @ $(date -u)`.
  4. Pulls with merge (concat-both handles daily logs). Identity passed explicitly so merge commits always have an author.
  5. If `@{upstream}..HEAD` is non-empty, pushes.
- **Merge conflicts on daily logs** — resolved automatically by the `concat-both` merge driver. Mapped in root `.gitattributes`:
  ```
  Fredis/Memory/daily/*.md         merge=concat-both
  Fredis/Memory/drafts/active/**   merge=concat-both
  Fredis/Memory/drafts/sent/**     merge=concat-both
  ```
  Driver script: `.claude/scripts/git-merge-concat`. Takes remote as base, appends local lines not already present, dedupes. Git registers the driver per-machine via `git config merge.concat-both.driver "bash .../.claude/scripts/git-merge-concat %O %A %B"`.
- **Log:** `.claude/scripts/vault_sync_runs.log` on each side. Sample verdict line: `[2026-04-21T14:28:37Z] vault-sync: committed vault changes`.

### 2.3 · Memory search

- **Source of truth:** markdown files in `Fredis/Memory/` (shared between sides).
- **Search index:** VPS Postgres + pgvector container (`secondbrain-postgres`, image `pgvector/pgvector:pg17`, bound to `127.0.0.1:5432`). Rebuilt from the files by `memory_index.py` — incremental by default.
- **Mac access:** SSH tunnel forwards **local 5433** → VPS `localhost:5432`. (Local port had to be 5433, not 5432, because the Mac runs its own local Postgres on 5432 — without the port change the tunnel silently routes to the local DB, which doesn't have the `secondbrain` role.)
- **Tunnel plist:** `~/Library/LaunchAgents/com.linards.ssh-tunnel.plist`. Template at `.claude/scripts/schedule/com.linards.ssh-tunnel.plist` with `__KEY_PATH__` etc. placeholders.
- **DATABASE_URL on Mac:** `postgresql://secondbrain:changeme@localhost:5433/secondbrain` in `.claude/scripts/.env`.
- **Query:** `cd .claude/scripts && uv run python memory_search.py "..." --mode hybrid --limit 5`.
- **If tunnel is down** (`nc -z localhost 5433` fails): the SSH key is passphrase-protected, so `ssh-add ~/.ssh/id_hetzner_vps` then `launchctl kickstart -k gui/$(id -u)/com.linards.ssh-tunnel`.

---

## 3 · Infrastructure inventory

### 3.1 · VPS

| Attribute | Value |
|---|---|
| Provider / size | Hetzner Cloud CX23 |
| Location | Helsinki |
| IP | `46.62.175.147` |
| OS | Ubuntu 24.04 |
| Repo path | `/root/claude-code-second-brain` |
| Firewall | Hetzner Cloud Firewall `fredis-prod-ssh-only` — tcp/22 inbound, all outbound |
| Host firewall | UFW, 22/tcp only |
| Abuse defense | fail2ban sshd jail |
| Patching | `unattended-upgrades` daily timer |
| Timezone | Europe/London |
| Backups | Hetzner snapshots, daily, 7-day retention (€0.96/mo) |
| SSH alias from Mac | `ssh fredis-vps` (loads `~/.ssh/id_hetzner_vps` from Keychain) |

Installed tools: Docker 29.1.3 + Compose 2.40.3, `uv` 0.11.7, Claude Code CLI 2.1.116, git 2.43.0, build-essential.

Git identity on VPS (set during Phase 10.5 cutover — merge commits need an author):
```
user.name  = fredis-vps
user.email = fredis-vps@fredis.local
```

### 3.2 · Repos

- **Code + vault:** `github.com/linardsb/fredis` — private. Single repo hosts both application code and the `Fredis/` vault tree. Path filter on the deploy workflow separates them.
- **No second vault repo.** The Phase 10.5 doc originally suggested `linardsb/fredis-vault` but that was rejected in favor of single-repo simplicity (vault commit noise is contained by `paths-ignore`, privacy is non-issue given the repo is private).

### 3.3 · Keys

| Key | Purpose | Location |
|---|---|---|
| `~/.ssh/id_hetzner_vps` | Mac ↔ VPS SSH (interactive, `ssh fredis-vps`, tunnel) | Mac only |
| `~/.ssh/id_github_deploy` | GitHub Action → VPS (appleboy/ssh-action) | private key on Mac; public key in VPS `/root/.ssh/authorized_keys` |
| `/root/.netrc` on VPS | Classic GitHub PAT for `git clone`, `git push` | VPS only (from `.env GITHUB_TOKEN`) |

GitHub Actions secrets (at https://github.com/linardsb/fredis/settings/secrets/actions):
- `VPS_HOST = 46.62.175.147`
- `VPS_SSH_KEY` = content of `~/.ssh/id_github_deploy`

### 3.4 · Database

- Container: `secondbrain-postgres` (`pgvector/pgvector:pg17`). Healthcheck passing.
- Port bind: `127.0.0.1:5432` — never public.
- Credentials: role `secondbrain`, password `changeme` (low-risk because bind is localhost-only).
- Docker Compose file: `docker-compose.yml` at repo root.

---

## 4 · What runs where

### 4.1 · VPS services

| Unit | Schedule | Purpose |
|---|---|---|
| `secondbrain-chat.service` | Always on, `Restart=always` | Slack Socket Mode chat interface |
| `fredis-heartbeat.timer` | Every 2h, 05:00–20:00 London | Proactive gather-reason-draft loop |
| `fredis-reflect.timer` | Daily 08:00 | Promotes yesterday's log items to MEMORY.md |
| `fredis-synthesis.timer` | Sunday 08:00 | Weekly memory synthesis draft |
| `deps-audit.timer` | Monday 09:00 | `pip-audit` + `safety check` |
| `fredis-vault-sync.timer` | Every 2 min | Bidirectional vault sync |

All timers are installed, enabled, and running as of 2026-04-21.

Unit templates live at `.claude/scripts/schedule/*.{service,timer}` with `__REPO_ROOT__` placeholders. `deploy.sh` re-renders them into `/etc/systemd/system/` on every deploy, substituting the path. Only units already installed on the host get re-rendered — new template files are ignored until manually installed.

### 4.2 · Mac launchd agents

| Plist | Schedule | Purpose |
|---|---|---|
| `com.linards.fredis-vault-sync.plist` | Every 120s | Mac-side vault sync |
| `com.linards.ssh-tunnel.plist` | RunAtLoad + KeepAlive | Postgres SSH tunnel on 5433 → 5432 |
| `com.linards.fredis-heartbeat.plist` | *unloaded* | Deprecated — VPS runs heartbeat now |
| `com.linards.fredis-reflect.plist` | *unloaded* | Deprecated — VPS runs reflection now |
| `com.linards.fredis-chat.plist` | *present* | Legacy Mac chat runner — not loaded; VPS is primary |

Verify Mac state: `launchctl list | grep com.linards`.

---

## 5 · File reference

### 5.1 · Vault-sync layer

| File | Role |
|---|---|
| `.claude/scripts/vault-sync-repo.sh` | The actual sync script. Single-repo safe (stages only `Fredis/`). Mkdir-based atomic lock. Identity passed into pull-merge. |
| `.claude/scripts/git-merge-concat` | Custom merge driver. Takes remote as base, appends local lines not in remote, dedupes. Uses `grep -qFx --` to handle lines starting with `-`. |
| `.gitattributes` (root) | Maps daily logs + drafts to `merge=concat-both`. Forces LF line endings across `Fredis/**`. |
| `.claude/scripts/schedule/vault-sync.service` | Systemd unit template. Not actively used — replaced by `fredis-vault-sync.service` installed directly on VPS. |
| `.claude/scripts/schedule/com.linards.fredis-vault-sync.plist` | launchd template with `__REPO_ROOT__` + `__HOME__` placeholders. |
| `.claude/scripts/vault_sync_runs.log` | Per-run verdicts on each side. |

### 5.2 · Deploy layer

| File | Role |
|---|---|
| `.github/workflows/deploy-vps.yml` | Workflow. Triggers on push to `main` except for `paths-ignore: [Fredis/**, docs/**, **/*.md]`. |
| `.claude/scripts/deploy.sh` | Runs on VPS. `flock`-guarded. Selective restart based on diff. |
| `.claude/scripts/schedule/*.{service,timer}` | Source-of-truth for VPS systemd units. `deploy.sh` re-renders these into `/etc/systemd/system/` with `__REPO_ROOT__` substituted. |

### 5.3 · Chat / memory / heartbeat (unchanged from before Phase 10)

| File | Role |
|---|---|
| `.claude/chat/*.py` | Slack Socket Mode chat engine |
| `.claude/scripts/heartbeat.py` | Proactive check pipeline |
| `.claude/scripts/memory_reflect.py` | Daily reflection |
| `.claude/scripts/memory_synthesis.py` | Weekly synthesis |
| `.claude/scripts/memory_index.py` / `memory_search.py` | Hybrid search over `Fredis/Memory/` |
| `.claude/scripts/db.py` | SQLite + Postgres backends |

### 5.4 · `.gitignore` inside `Fredis/`

Top-level `/Fredis` line was removed in Phase 10.5. Scoped excludes added:
```
Fredis/.obsidian/workspace.json
Fredis/.obsidian/workspace-mobile.json
Fredis/.trash/
Fredis/**/.DS_Store
Fredis/**/*.lock
```

---

## 6 · How to make changes

### 6.1 · Code change

1. Edit on Mac.
2. Commit and push to `main`.
3. GitHub Action runs `deploy.sh` on VPS.
4. Watch: `gh run watch` (or check https://github.com/linardsb/fredis/actions).
5. If the workflow skipped (all changed paths fall under `Fredis/**`, `docs/**`, or `**/*.md`), trigger manually: `gh workflow run deploy-vps.yml -R linardsb/fredis`.

### 6.2 · Vault change from Mac

Edit in Obsidian. Within 2 minutes:
1. Mac's `fredis-vault-sync` timer stages + commits + pushes.
2. VPS's `fredis-vault-sync` timer pulls the commit.

No manual action. The workflow does not redeploy (paths-ignored).

### 6.3 · Vault change from VPS

A heartbeat / reflect / synthesis run writes to the vault. Within 2 minutes:
1. VPS's `fredis-vault-sync` timer stages + commits + pushes.
2. Mac's `fredis-vault-sync` timer pulls the commit.
3. Obsidian auto-reloads the changed file.

### 6.4 · Systemd unit change

Update the template at `.claude/scripts/schedule/<unit>.service|.timer` → commit → push. On next deploy (or `gh workflow run deploy-vps.yml`), `deploy.sh` detects the changed unit file and re-renders into `/etc/systemd/system/` + `daemon-reload`.

**Note:** the deploy script only re-renders units already installed on the host. To install a brand-new unit:
```bash
ssh fredis-vps "cd /root/claude-code-second-brain && sed 's|__REPO_ROOT__|/root/claude-code-second-brain|g' .claude/scripts/schedule/new-unit.service > /etc/systemd/system/new-unit.service && systemctl daemon-reload && systemctl enable --now new-unit.service"
```

### 6.5 · Secret rotation

Follow `.claude/scripts/schedule/rotation-runbooks.md`. Update `.env` on both Mac and VPS (SCP the file):
```bash
scp .claude/scripts/.env fredis-vps:/root/claude-code-second-brain/.claude/scripts/.env
ssh fredis-vps "chmod 600 /root/claude-code-second-brain/.claude/scripts/.env && systemctl restart secondbrain-chat.service"
```

---

## 7 · Operational runbook

### 7.1 · Health checks

```bash
# All VPS services + timers
ssh fredis-vps "systemctl is-active secondbrain-chat fredis-heartbeat.timer fredis-reflect.timer fredis-synthesis.timer fredis-vault-sync.timer deps-audit.timer; echo ---; systemctl list-timers --no-pager | grep -E 'fredis|deps'"

# Vault sync log (most recent verdicts)
ssh fredis-vps "tail -20 /root/claude-code-second-brain/.claude/scripts/vault_sync_runs.log"
tail -20 .claude/scripts/vault_sync_runs.log

# Postgres + memory DB
ssh fredis-vps "docker compose -f /root/claude-code-second-brain/docker-compose.yml ps"

# Mac tunnel
nc -z localhost 5433 && echo TUNNEL_OK

# End-to-end memory search
cd .claude/scripts && uv run python memory_search.py "any query" --mode hybrid --limit 3
```

### 7.2 · Common problems

**Symptom: `git pull --ff-only` fails in `deploy.sh` with "Not possible to fast-forward".**

Both sides diverged. Usually caused by vault-sync on VPS producing local commits that haven't pushed yet, while Mac independently pushed to origin.

Fix: SSH to VPS, run `git pull --no-rebase --no-edit origin main` followed by `git push origin main`. After the merge pushes, subsequent deploys resume working. If the failure persists, check `vault_sync_runs.log` on both sides for push failures.

**Symptom: `vault-sync-repo.sh` logs "pull failed — manual resolution likely needed".**

Usually merge conflict that `concat-both` couldn't resolve, or auth failure.

Manual resolution path: `ssh fredis-vps "cd /root/claude-code-second-brain && git status"`. If the tree shows a dirty merge state, resolve conflicts, `git add`, `git commit`, `git push`. If nothing staged but the pull refused, rerun `git pull --no-rebase --no-edit origin main`.

**Symptom: Slack bot doesn't respond.**
```bash
ssh fredis-vps "systemctl status secondbrain-chat --no-pager -l | head -20"
ssh fredis-vps "journalctl -u secondbrain-chat -n 50 --no-pager"
```
Common causes: `.credentials.json` missing (re-run `claude login` on VPS), Postgres down (`docker compose ps`), Slack token expired (rotate per `rotation-runbooks.md`).

**Symptom: Heartbeat guardrail fails-closed repeatedly.**
- Check for Haiku API rate limiting / outages.
- Expected behavior per Phase 8: external data stripped, Slack alert fires anyway with metadata only, no injection risk.
- Look at `journalctl -u fredis-heartbeat.service` for the Haiku error detail.

**Symptom: `memory_search.py` returns `role "secondbrain" does not exist`.**
- Tunnel is connecting to Mac's local Postgres instead of VPS's. Check `lsof -iTCP:5432 -sTCP:LISTEN` — if something listens on 5432, the tunnel (which tries to bind 5432 locally in older setups) silently falls through.
- Current setup forwards local 5433 → remote 5432 specifically to avoid this.

**Symptom: `redact-secrets` hook fires on `linardsb` in git push output.**
- Known false positive — the GitHub username triggers the `secret_patterns.py` entropy rules. Cosmetic only; commits + pushes still succeed.
- To silence: tune `secret_patterns.py` to require additional context around short usernames (tech-debt, not fixed yet).

### 7.3 · Rollback procedures

**Full rollback from VPS-only runtime to Mac-only** (if VPS services misbehave):
```bash
# Stop VPS services
ssh fredis-vps "systemctl stop secondbrain-chat fredis-heartbeat.timer fredis-reflect.timer fredis-synthesis.timer fredis-vault-sync.timer"

# Resume Mac plists
launchctl load ~/Library/LaunchAgents/com.linards.fredis-heartbeat.plist
launchctl load ~/Library/LaunchAgents/com.linards.fredis-reflect.plist
```
Also comment out `DATABASE_URL` in `.claude/scripts/.env` so memory search falls back to local SQLite. The Mac SQLite DB was never deleted — just unused while the tunnel pointed at VPS Postgres.

**Restore vault from VPS backup (first 1–2 weeks):**

`ssh fredis-vps "ls /root/claude-code-second-brain/Fredis.pre-phase10-5-backup/"` confirms the backup exists. It captures vault state at 2026-04-21 15:24 just before the Fredis/ directory was renamed away so git pull could materialize the tracked copy. Prune once you're confident the new setup is stable.

**Revert a bad code deploy:**

Identify the last good commit with `git log --oneline -10`. Then point the VPS at it with `git fetch origin` followed by the force-reset to that sha, then re-run `deploy.sh`. The full sequence needs the hard-reset flag — documented in `.claude/scripts/schedule/vps-bootstrap.md` §Rollback where it can safely sit in a runbook.

---

## 8 · Decision log (Phase 10 + 10.5)

### Single repo vs two repos for the vault

Original Phase 10.5 plan (see `docs/phase10-deploy-progress.md` §6) called for a separate private repo `linardsb/fredis-vault` for the vault. Rejected in the cutover session because:

1. **Privacy** — non-issue if the code repo is also private.
2. **Commit noise** — real concern (vault produces ~50 auto-commits/day). Solved by `paths-ignore` on the workflow instead of repo separation.
3. **git-sync ergonomics** — the original plan used `simonthum/git-sync` which commits everything dirty. That's catastrophic for a mixed code-and-vault repo because WIP code would auto-commit to `main`. Solved by writing a new `vault-sync-repo.sh` that only stages the `Fredis/` subtree.
4. **Operator overhead** — one repo to manage instead of two.

Trade-off accepted: `git log` history is interleaved with ~50/day vault commits. Mitigation: filter by path when reviewing (`git log -- .claude/` for code only).

### Port 5433 for the Mac SSH tunnel

The Mac runs its own local PostgreSQL on 5432 (a historical dev install). When the SSH tunnel tried to bind `-L 5432:localhost:5432`, the `nc -z localhost 5432` test succeeded but the connection resolved to the local Postgres, not the VPS one — because SSH tunnel's local bind fails silently in some configurations when the port is taken. The symptom was `role "secondbrain" does not exist` on the first `memory_search.py` call.

Fix: bump the local forward port to 5433. Updated in both the installed plist and the template at `.claude/scripts/schedule/com.linards.ssh-tunnel.plist`.

### `flock` replaced by `mkdir` lock

The first cut of `vault-sync-repo.sh` used `flock` for the single-run lock. `flock` is Linux-only — macOS's `/bin/bash` doesn't ship it. Switched to an atomic `mkdir /tmp/fredis-vault-sync.lock.d` with PID tracking and stale-pid reclaim. Works identically on both sides.

### Global git identity required on VPS

Vault-sync's `git pull --no-rebase --no-edit` creates a merge commit when the histories diverge. Merge commits need an author. The first version of `vault-sync-repo.sh` set identity only on the `git commit` call via `-c user.name / -c user.email`, so `pull` fell back to the global git config — which on the VPS was unset (`root@ubuntu-4gb-hel1-1.(none)`). Result: pull failed, VPS accumulated local commits that couldn't push.

Fix applied twice:
1. Set a global identity on the VPS: `git config --global user.name fredis-vps && git config --global user.email fredis-vps@fredis.local`.
2. Patched `vault-sync-repo.sh` to pass `-c user.name / -c user.email` directly on the `git pull` invocation, so it works regardless of host git config.

### `git-merge-concat` grep hardening

The concat-both driver uses `grep -qFx "$line" file` to check for duplicate lines. `grep` interprets arguments starting with `-` as options — and lots of daily-log lines start with `-` (markdown bullets). Fix: add `--` separator: `grep -qFx -- "$line" file`. Also replaced `echo` with `printf` to handle special characters robustly.

Before this fix, the driver crashed on any merge where the diff included bullets, and git silently fell back to the `ort` strategy. The `ort` fallback happens to work for simple appends but can break on non-trivial divergence — worth having `concat-both` actually execute.

---

## 9 · Deferred / known issues

- **`Fredis.pre-phase10-5-backup/` on VPS** — backup copy of the vault from before tracking it in git. Prune after 1–2 weeks of confidence.
- **Guardrail Haiku timeout** — fired fail-closed on the first post-cutover heartbeat. Expected Phase 8 behavior. Monitor the next few cycles to confirm it's not systemic.
- **`notify-send` missing on VPS** — cosmetic log line on each heartbeat. Slack is the real channel; no action required unless you want to `apt install libnotify-bin`.
- **`secret_patterns.py` false positive on `linardsb`** — cosmetic, blocks Read output but not tool execution. Fix: add entropy + context-anchor rules to the shape patterns.
- **Non-root VPS service user** — all systemd units run as `User=root`. Tech debt noted in `.claude/scripts/threat-models/vps.md`. Low priority given the firewall-restricted surface.
- **VPS kernel 6.8.0-110 pending reboot** — not urgent; do during a quiet window.

---

## 10 · Session-level stats (2026-04-21 cutover)

17 task items, 8 commits on `main`:

| SHA (short) | Type | Summary |
|---|---|---|
| `c097e46` | feat | Phase 10.5 scaffolding — workflow paths-ignore, vault-sync-repo.sh, .gitattributes, .gitignore edits |
| `7cf238d` | feat | First vault content commit (113 files) |
| `9f2d6f1`, `f7cb0f2` | vault | Mac-side auto-commits from vault-sync |
| `3f22eeb`, `4cceb78` | vault | VPS-side auto-commits from vault-sync |
| `b326aa7` | fix | Cross-platform lock + commit arg order |
| `980735d` | vault | Mac auto-commit |
| `c0c3f37` | docs | CLAUDE.md Phase 10 stub + tunnel port 5433 template |
| `0287bc1` | merge | VPS merge of divergent histories |
| `54910bd` | fix | Merge identity into pull + grep driver hardening |

Both sides converged at `54910bd`. Bidirectional sync verified: Mac → VPS (imac commits landed on VPS), VPS → Mac (ubuntu-4gb-hel1-1 commits landed on Mac), divergence resolved automatically on the next cycle after the identity fix.
