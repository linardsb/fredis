"""HTTP client for the Archon build-harness engine (loopback only).

`query.py workflow` is Fredis's SINGLE dispatch path into the engine — every
surface (chat, Slack, cockpit) fires runs through the CLI, never by POSTing the
engine directly. This module is the ONLY place in Fredis that speaks HTTP to it.

Containment note: the engine runs `permissionMode: bypassPermissions`, so
Fredis's `PreToolUse` hooks do NOT protect what it does. Containment is
workspace-scoping + loopback bind + state-outside-tree + draft-PR-only, enforced
at boot (WS1) and by each target codebase's `default_cwd` — never by this client.

API shape verified against the engine's OpenAPI routes
(`packages/server/src/routes/api.ts`) and the WS1.4 live HTTP-fire recorded in
`.agent/plans/the-team/phase1-implementation.md`.
"""

from __future__ import annotations

from typing import Any

import requests

from config import ARCHON_BASE_URL, ARCHON_HTTP_TIMEOUT


class ArchonUnreachableError(RuntimeError):
    """The engine did not answer on the loopback seam (not booted / wrong port)."""


class ArchonError(RuntimeError):
    """The engine answered with a non-2xx status."""


def _url(path: str) -> str:
    return f"{ARCHON_BASE_URL.rstrip('/')}{path}"


def _request(method: str, path: str, *, json: dict[str, Any] | None = None) -> Any:
    """Single HTTP entrypoint. Raises ArchonUnreachableError on connection failure and
    ArchonError on a non-2xx response, so callers never see a raw requests error."""
    try:
        resp = requests.request(
            method, _url(path), json=json, timeout=ARCHON_HTTP_TIMEOUT
        )
    except requests.exceptions.RequestException as exc:
        raise ArchonUnreachableError(
            f"Archon engine unreachable at {ARCHON_BASE_URL} "
            f"({exc.__class__.__name__}). Boot it (WS1, cwd = the Archon clone, "
            f"loopback-only) or set ARCHON_BASE_URL."
        ) from exc
    if resp.status_code >= 400:
        raise ArchonError(
            f"{method} {path} -> HTTP {resp.status_code}: {resp.text[:300]}"
        )
    if not resp.content:
        return None
    try:
        return resp.json()
    except ValueError:
        return resp.text


# --- reads -----------------------------------------------------------------


def list_workflows() -> Any:
    """GET /api/workflows — the engine's available workflows."""
    return _request("GET", "/api/workflows")


def list_runs() -> list[dict[str, Any]]:
    """GET /api/workflows/runs — every run row (used to correlate a fired run)."""
    data = _request("GET", "/api/workflows/runs")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        runs = data.get("runs", [])
        return runs if isinstance(runs, list) else []
    return []


def get_run(run_id: str) -> Any:
    """GET /api/workflows/runs/{runId} — one run's node/status state."""
    return _request("GET", f"/api/workflows/runs/{run_id}")


def list_codebases() -> list[dict[str, Any]]:
    """GET /api/codebases — registered target repos."""
    data = _request("GET", "/api/codebases")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        cbs = data.get("codebases", [])
        return cbs if isinstance(cbs, list) else []
    return []


def resolve_codebase_id(repo: str) -> str:
    """Resolve a repo slug/name to a registered codebase id.

    Only READS existing codebases — registration (`POST /api/codebases` with
    `default_cwd` = the target repo) is a real-lane, engine-side action (WS5/WS6).
    """
    codebases = list_codebases()
    for c in codebases:
        if repo in (c.get("id"), c.get("name"), c.get("slug")):
            return str(c["id"])
    known = ", ".join(str(c.get("name") or c.get("id")) for c in codebases) or "(none)"
    raise ArchonError(
        f"No registered codebase matches '{repo}'. Registered: {known}. "
        f"Register the target with POST /api/codebases (default_cwd = the repo) first."
    )


# --- fire: 2-step (idle conversation -> run) -------------------------------


def create_conversation(codebase_id: str) -> dict[str, Any]:
    """POST /api/conversations — create an IDLE conversation.

    Omit `message` (the strict body accepts only {codebaseId?, message?}); passing
    a message auto-dispatches a chat turn instead of leaving the conversation idle
    for a workflow fire. Returns {conversationId, id, dispatched?}.

    UNVERIFIED (confirm on first live run — see impl-plan WS1.4 #4): `conversationId`
    is the orchestrator-internal id that run rows key on; `id` is the `web-…`
    platform id the cockpit uses. Both the run body and run correlation use
    `conversationId`, NOT `id`.
    """
    body: dict[str, Any] = {"codebaseId": codebase_id} if codebase_id else {}
    result = _request("POST", "/api/conversations", json=body)
    return result if isinstance(result, dict) else {}


def run_workflow(name: str, conversation_id: str, message: str) -> dict[str, Any]:
    """POST /api/workflows/{name}/run — fire a workflow on an idle conversation.

    Returns {accepted, status} — the fire response does NOT carry the runId
    (WS1.4 #3); correlate it afterwards via `latest_run_for_conversation`.
    """
    result = _request(
        "POST",
        f"/api/workflows/{name}/run",
        json={"conversationId": conversation_id, "message": message},
    )
    return result if isinstance(result, dict) else {}


def latest_run_for_conversation(conversation_id: str) -> dict[str, Any] | None:
    """Best-effort correlate the just-fired run (the fire response omits runId).

    Run rows key on the orchestrator-internal conversation id. A fresh idle
    conversation has exactly one run, so any match is the one we fired.
    """

    def _conv(row: dict[str, Any]) -> str | None:
        return row.get("conversation_id") or row.get("conversationId")

    mine = [r for r in list_runs() if _conv(r) == conversation_id]
    return mine[0] if mine else None


# --- HITL resume of `approval:` nodes --------------------------------------


def approve_run(run_id: str, comment: str | None = None) -> dict[str, Any]:
    """POST /api/workflows/runs/{runId}/approve — resume a paused approval node."""
    body: dict[str, Any] = {"comment": comment} if comment else {}
    result = _request(
        "POST", f"/api/workflows/runs/{run_id}/approve", json=body
    )
    return result if isinstance(result, dict) else {}


def reject_run(run_id: str, reason: str | None = None) -> dict[str, Any]:
    """POST /api/workflows/runs/{runId}/reject — reject a paused approval node."""
    body: dict[str, Any] = {"reason": reason} if reason else {}
    result = _request(
        "POST", f"/api/workflows/runs/{run_id}/reject", json=body
    )
    return result if isinstance(result, dict) else {}
