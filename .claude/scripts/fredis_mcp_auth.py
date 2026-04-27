"""
Fredis MCP security helpers.

Two layers ship here:

1. ``is_path_denied`` (Phase 1.2) — path-based sensitivity gate (D3 = A).
2. ``bearer_auth_app`` / ``_verify_bearer`` (Phase 1B) — ASGI bearer-token
   middleware for the streamable-http remote transport (D2.5 = B on VPS).

The bearer-token surface is only mounted when the server runs under
``FREDIS_MCP_TRANSPORT=streamable-http`` — Mac stdio sessions never load it.
The middleware logs only the verdict (``ok|missing|invalid|malformed``) and
never the header value or the token. Empty ``expected_token`` is rejected at
mount time so silent open access is impossible.
"""

from __future__ import annotations

import hmac
import json
import logging
from collections.abc import Awaitable, Callable, MutableMapping
from pathlib import PurePosixPath
from typing import Any

# ASGI types match the spec (and Starlette's surface): scope/message are
# MutableMapping[str, Any] so a Starlette / FastMCP app passes structurally
# through `bearer_auth_app(app=...)` without a cast.
ASGIScope = MutableMapping[str, Any]
ASGIMessage = MutableMapping[str, Any]
ASGIReceive = Callable[[], Awaitable[ASGIMessage]]
ASGISend = Callable[[ASGIMessage], Awaitable[None]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]

# Verdict labels — short tokens, safe to log, no PII.
AUTH_OK = "ok"
AUTH_MISSING = "missing"
AUTH_MALFORMED = "malformed"
AUTH_INVALID = "invalid"


def is_path_denied(file_path: str, denylist: list[str]) -> bool:
    """Return ``True`` if ``file_path`` is covered by any denylist entry.

    Match semantics:

    - Entry ending in ``/`` — directory prefix; ``path`` is denied if
      ``path`` starts with ``entry`` (so ``retainers/`` denies
      ``retainers/foo.md`` but not ``retainers``).
    - Entry without a trailing ``/`` — exact-file match; ``path`` is denied
      only if ``path == entry`` (so ``USER.md`` denies ``USER.md`` but
      **not** ``USER.md.bak``).

    Inputs are normalised by collapsing redundant separators via
    ``PurePosixPath``. Any path containing ``..`` segments is treated as
    denied (defence in depth — the resolver should already have rejected it).

    The helper takes a string list rather than reading from ``config`` so
    tests can drive it without monkey-patching module state.
    """
    if not file_path:
        return True
    parts = PurePosixPath(file_path).parts
    if any(part == ".." for part in parts):
        return True
    norm = PurePosixPath(file_path).as_posix()

    for raw in denylist:
        entry = raw.strip()
        if not entry:
            continue
        if entry.endswith("/"):
            if norm.startswith(entry):
                return True
        else:
            if norm == entry:
                return True
    return False


def _verify_bearer(header_value: str, expected_token: str) -> str:
    """Classify an ``Authorization`` header value against ``expected_token``.

    Returns one of:

    - ``"missing"`` — header empty or absent.
    - ``"malformed"`` — header doesn't start with ``Bearer `` (case-insensitive
      on the scheme name) or has no token after the prefix.
    - ``"invalid"`` — bearer token present but doesn't match (constant-time).
    - ``"ok"`` — token matches.

    The function never raises; an empty / unexpected input falls into one of
    the labelled buckets so the caller logs a known string.
    """
    if not header_value:
        return AUTH_MISSING
    if not header_value.lower().startswith("bearer "):
        return AUTH_MALFORMED
    candidate = header_value[7:].strip()
    if not candidate:
        return AUTH_MALFORMED
    if hmac.compare_digest(candidate, expected_token):
        return AUTH_OK
    return AUTH_INVALID


async def _send_unauthorized(send: ASGISend) -> None:
    """Send a minimal 401 response. Body never reveals the verdict — the
    caller's logs do that. Spec-compliant ``WWW-Authenticate`` advertises
    Bearer so well-behaved clients know what to send next."""
    body = json.dumps({"error": "unauthorized"}).encode("utf-8")
    await send(
        {
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b'Bearer realm="fredis-mcp"'),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body, "more_body": False})


def bearer_auth_app(
    app: ASGIApp,
    *,
    expected_token: str,
    logger: logging.Logger | None = None,
) -> ASGIApp:
    """Wrap an ASGI app with bearer-token authentication.

    Refuses to mount if ``expected_token`` is empty — silent open access is
    the worst failure mode and we want a loud error at startup, not at the
    first unauthenticated request.

    Non-HTTP scopes (lifespan, websocket) pass through untouched; only
    ``scope["type"] == "http"`` is gated. Verdicts are logged at INFO level
    on the supplied logger (or ``fredis_mcp.auth`` by default) — the token
    value and the raw header are never logged.
    """
    if not expected_token:
        raise ValueError(
            "expected_token must not be empty — refusing to mount bearer middleware"
        )
    log = logger or logging.getLogger("fredis_mcp.auth")

    async def wrapper(
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        if scope.get("type") != "http":
            await app(scope, receive, send)
            return

        auth_bytes = b""
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                auth_bytes = value
                break
        try:
            auth_str = auth_bytes.decode("latin-1")
        except UnicodeDecodeError:
            auth_str = ""

        verdict = _verify_bearer(auth_str, expected_token)
        log.info("auth: %s", verdict)
        if verdict != AUTH_OK:
            await _send_unauthorized(send)
            return
        await app(scope, receive, send)

    return wrapper
