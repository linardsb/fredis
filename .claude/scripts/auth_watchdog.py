#!/usr/bin/env python3
"""Auth watchdog — alert when Claude or Google credentials die.

Fredis's autonomous brain-calls run through the ``claude`` CLI (Claude Max
subscription token) and Google OAuth. Both have failed silently before — the
Claude "logged-in-but-401" jam recurred on 17 / 22 / 26 Jun 2026, and the
Google token was revoked twice — each time leaving Fredis "safe but blind"
until a human happened to notice. This probe runs hourly, makes one cheap real
call against each credential, and Slack-alerts on an auth failure (with the fix
steps) so an outage — including the ~yearly ``CLAUDE_CODE_OAUTH_TOKEN`` expiry —
surfaces in minutes, not days.

It alerts only on genuine *auth* failures (401 / invalid_grant), never on
transient timeouts or overload, so it doesn't cry wolf. It always exits 0 — a
watchdog must never page the scheduler it runs under.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Any

from config import STATE_DIR, now_local
from notifications import send_slack_notification
from shared import load_state, save_state

WATCHDOG_STATE_FILE = STATE_DIR / "auth-watchdog-state.json"

# While a credential stays down, re-alert at most once per this many hours: the
# channel isn't spammed every run, but a lingering outage still nags.
REALERT_AFTER_HOURS = 12

# Sonnet matches the model the heartbeat guardrail actually uses, so the probe
# fails only when a real brain-call would — minimising false alarms.
PROBE_MODEL = "sonnet"

_OK = "ok"
_DOWN = "auth_down"
_TRANSIENT = "transient"

_CLAUDE_FIX = (
    "Every Fredis brain-call will 401 and run blind. Most likely the "
    "CLAUDE_CODE_OAUTH_TOKEN expired (it lasts ~1 year). Fix: `ssh "
    "root@fredis-vps` then `claude setup-token`, store it in "
    ".claude/scripts/.env as CLAUDE_CODE_OAUTH_TOKEN, and verify with "
    "`uv run python heartbeat.py --test` (expect `Guardrail verdict: pass`)."
)
_GOOGLE_FIX = (
    "Gmail + Calendar reads will fail. The Google OAuth token was revoked or "
    "expired. Fix: `ssh root@fredis-vps`, `cd .claude/scripts`, `rm "
    "integrations/google_token.json`, then `OAUTHLIB_INSECURE_TRANSPORT=1 "
    "OAUTHLIB_RELAX_TOKEN_SCOPE=1 uv run python setup_auth.py --headless`."
)


def _probe_claude() -> tuple[str, str]:
    """Run one cheap ``claude -p`` call. Returns (status, detail)."""
    claude = shutil.which("claude") or os.path.expanduser("~/.local/bin/claude")
    try:
        proc = subprocess.run(
            [claude, "-p", "ping", "--model", PROBE_MODEL],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except FileNotFoundError:
        return _TRANSIENT, "claude CLI not found"
    except subprocess.TimeoutExpired:
        return _TRANSIENT, "probe timed out after 90s"

    output = f"{proc.stdout}\n{proc.stderr}".lower()
    auth_markers = ("401", "invalid authentication", "invalid bearer")
    if any(marker in output for marker in auth_markers):
        return _DOWN, "401 invalid authentication credentials"
    if proc.returncode != 0:
        lines = (proc.stderr or proc.stdout or "").strip().splitlines()
        return _TRANSIENT, f"exit {proc.returncode}: {lines[-1] if lines else 'no output'}"
    return _OK, ""


def _probe_google() -> tuple[str, str]:
    """Make one real, cheap Gmail call. Returns (status, detail)."""
    try:
        from integrations.gmail import get_unread_count

        get_unread_count()
    except Exception as exc:  # noqa: BLE001 - any failure means we couldn't read
        detail = (str(exc).splitlines() or [""])[0][:200]
        low = detail.lower()
        auth_markers = ("invalid_grant", "expired", "revoked", "refresh")
        if any(marker in low for marker in auth_markers):
            return _DOWN, detail
        return _TRANSIENT, detail
    return _OK, ""


def _evaluate(
    label: str, status: str, detail: str, fix: str, prev: dict[str, Any]
) -> dict[str, Any]:
    """Apply the alert / dedup rules for one credential, return its new state."""
    now = now_local()
    prev_status = prev.get("status", _OK)
    last_alert = prev.get("last_alert")
    new: dict[str, Any] = {
        "status": prev_status,
        "last_alert": last_alert,
        "detail": detail,
    }

    if status == _DOWN:
        if last_alert is None:
            due = True
        else:
            elapsed = now - datetime.fromisoformat(last_alert)
            due = elapsed > timedelta(hours=REALERT_AFTER_HOURS)
        if prev_status != _DOWN or due:
            send_slack_notification(f"Fredis {label} auth DOWN", f"{detail}\n\n{fix}")
            new["last_alert"] = now.isoformat()
        new["status"] = _DOWN
    elif status == _OK:
        if prev_status == _DOWN:
            send_slack_notification(
                f"Fredis {label} auth recovered",
                f"{label} is authenticating again.",
            )
            new["last_alert"] = None
        new["status"] = _OK
    # _TRANSIENT: leave the prior status/alert untouched — don't flap on a blip.
    return new


def main() -> None:
    state = load_state(WATCHDOG_STATE_FILE)
    claude_status, claude_detail = _probe_claude()
    google_status, google_detail = _probe_google()
    state["claude"] = _evaluate(
        "Claude", claude_status, claude_detail, _CLAUDE_FIX, state.get("claude", {})
    )
    state["google"] = _evaluate(
        "Google", google_status, google_detail, _GOOGLE_FIX, state.get("google", {})
    )
    state["last_run"] = now_local().isoformat()
    save_state(state, WATCHDOG_STATE_FILE)
    print(f"[{now_local()}] auth-watchdog: claude={claude_status} google={google_status}")


if __name__ == "__main__":
    main()
