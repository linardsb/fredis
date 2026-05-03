"""Tests for the Fredis MCP path-based denylist helper (OB1 Phase 1.2).

Pure-string semantics — these tests don't touch the filesystem. The
in-vault-symlink + ``get_file`` integration sits in
``test_fredis_mcp_tools.py``.
"""

from __future__ import annotations

import pytest

from fredis_mcp_auth import is_path_denied

# The canonical production denylist is also exercised here so that any future
# change to ``.env``'s shipped value (or the parser in ``config.py``) breaks
# these tests rather than silently leaking. Match this to ``.env.example``.
CANONICAL_DENYLIST = ["USER.md", "retainers/", "legal/", "investors/"]


# --------------------------------------------------------------------------- #
# Empty / degenerate inputs
# --------------------------------------------------------------------------- #


def test_empty_denylist_allows_anything() -> None:
    assert is_path_denied("retainers/foo.md", []) is False
    assert is_path_denied("USER.md", []) is False
    assert is_path_denied("anything/at/all.md", []) is False


def test_empty_path_is_denied() -> None:
    assert is_path_denied("", CANONICAL_DENYLIST) is True


def test_blank_entries_are_skipped() -> None:
    """Whitespace/empty entries inside the denylist must not deny everything."""
    assert is_path_denied("daily/2026-04-26.md", ["", "   ", "USER.md"]) is False


def test_whitespace_in_denylist_entry_is_stripped() -> None:
    """An entry with leading / trailing whitespace must still match."""
    assert is_path_denied("retainers/foo.md", ["  retainers/  "]) is True


# --------------------------------------------------------------------------- #
# Exact-file vs directory-prefix semantics
# --------------------------------------------------------------------------- #


def test_exact_file_match() -> None:
    assert is_path_denied("USER.md", ["USER.md"]) is True


def test_exact_file_does_not_match_extension_neighbour() -> None:
    """``USER.md`` (no trailing slash) denies the file exactly — not
    siblings that happen to share the prefix as a substring."""
    assert is_path_denied("USER.md.bak", ["USER.md"]) is False
    assert is_path_denied("USER.md.old", ["USER.md"]) is False


def test_directory_prefix_denies_descendants() -> None:
    deny = ["retainers/"]
    assert is_path_denied("retainers/foo.md", deny) is True
    assert is_path_denied("retainers/sub/nested.md", deny) is True


def test_directory_prefix_does_not_match_sibling_file() -> None:
    """``retainers/`` is a directory prefix — it must not deny a same-named
    file (``retainers``) or a name that begins with the same letters."""
    deny = ["retainers/"]
    assert is_path_denied("retainers", deny) is False
    assert is_path_denied("retainers2/foo.md", deny) is False
    assert is_path_denied("ret/foo.md", deny) is False


# --------------------------------------------------------------------------- #
# Normalisation — `.`, `..`, and redundant separators
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "path",
    [
        "retainers/foo.md",
        "./retainers/foo.md",
        "retainers//foo.md",
    ],
)
def test_normalised_paths_are_denied(path: str) -> None:
    assert is_path_denied(path, ["retainers/"]) is True


@pytest.mark.parametrize(
    "path",
    [
        "retainers/../retainers/foo.md",
        "../retainers/foo.md",
        "../../etc/passwd",
        "..",
    ],
)
def test_dotdot_segments_always_denied(path: str) -> None:
    """Defence in depth: any traversal segment is treated as denied even if
    the prefix wouldn't otherwise match. ``_resolve_vault_path`` is the
    primary line — this is the secondary."""
    assert is_path_denied(path, ["retainers/"]) is True


# --------------------------------------------------------------------------- #
# Multiple-entry behaviour + canonical denylist sanity
# --------------------------------------------------------------------------- #


def test_first_matching_entry_decides() -> None:
    deny = ["USER.md", "retainers/", "legal/"]
    assert is_path_denied("legal/contract.md", deny) is True
    assert is_path_denied("retainers/x/y.md", deny) is True
    assert is_path_denied("USER.md", deny) is True


def test_canonical_denylist_blocks_each_listed_target() -> None:
    """Lock in the production shipping list — if a future env edit drops
    one of these prefixes, this test fires."""
    assert is_path_denied("USER.md", CANONICAL_DENYLIST) is True
    assert is_path_denied("retainers/anything.md", CANONICAL_DENYLIST) is True
    assert is_path_denied("legal/anything.md", CANONICAL_DENYLIST) is True
    assert is_path_denied("investors/anything.md", CANONICAL_DENYLIST) is True


def test_canonical_denylist_allows_soul_md() -> None:
    """SOUL.md must remain readable — exposing the persona is the point of
    the MCP server. The canonical denylist must not cover it."""
    assert is_path_denied("SOUL.md", CANONICAL_DENYLIST) is False


def test_canonical_denylist_allows_drafts_and_daily_logs() -> None:
    """Sanity — the broad working surfaces stay open."""
    assert is_path_denied("daily/2026-04-26.md", CANONICAL_DENYLIST) is False
    assert is_path_denied("drafts/active/draft-reply/foo.md", CANONICAL_DENYLIST) is False
    assert is_path_denied("MEMORY.md", CANONICAL_DENYLIST) is False


# =========================================================================== #
# Phase 1B — bearer-token middleware (streamable-http remote transport)
# =========================================================================== #


import asyncio  # noqa: E402
import inspect  # noqa: E402
import io  # noqa: E402
import logging  # noqa: E402
from collections.abc import MutableMapping  # noqa: E402
from typing import Any  # noqa: E402

import fredis_mcp_auth  # noqa: E402
from fredis_mcp_auth import (  # noqa: E402
    AUTH_INVALID,
    AUTH_MALFORMED,
    AUTH_MISSING,
    AUTH_OK,
    _verify_bearer,
    bearer_auth_app,
)

# --------------------------------------------------------------------------- #
# CRITICAL — load-bearing security test goes first.
# Silent open access is the worst failure mode, so the middleware refuses to
# mount with an empty expected_token. Fail fast at construction, not at the
# first unauthenticated request.
# --------------------------------------------------------------------------- #


def test_bearer_middleware_refuses_empty_expected_token() -> None:
    """Mounting with an empty token is the silent-open-access bug."""
    with pytest.raises(ValueError, match="expected_token"):
        bearer_auth_app(_dummy_ok_app, expected_token="")


def test_bearer_middleware_refuses_none_expected_token() -> None:
    with pytest.raises(ValueError, match="expected_token"):
        bearer_auth_app(_dummy_ok_app, expected_token=None)  # type: ignore[arg-type]


# --------------------------------------------------------------------------- #
# _verify_bearer — pure classifier
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "header,expected,want",
    [
        ("Bearer correcthorse", "correcthorse", AUTH_OK),
        ("bearer correcthorse", "correcthorse", AUTH_OK),
        ("BEARER correcthorse", "correcthorse", AUTH_OK),
        ("Bearer wrong", "correcthorse", AUTH_INVALID),
        ("Bearer ", "correcthorse", AUTH_MALFORMED),
        ("Bearer", "correcthorse", AUTH_MALFORMED),
        ("Basic dXNlcjpwYXNz", "correcthorse", AUTH_MALFORMED),
        ("Token foo", "correcthorse", AUTH_MALFORMED),
        ("", "correcthorse", AUTH_MISSING),
    ],
)
def test_verify_bearer_classifies(header: str, expected: str, want: str) -> None:
    assert _verify_bearer(header, expected) == want


def test_verify_bearer_uses_constant_time_compare() -> None:
    """Source-level enforcement: comparison MUST go through hmac.compare_digest.
    A naive ``==`` would short-circuit on the first byte mismatch and leak
    timing info. Unit tests can't reliably measure the timing — this is the
    next-best gate."""
    src = inspect.getsource(fredis_mcp_auth._verify_bearer)
    assert "hmac.compare_digest" in src, (
        "_verify_bearer must use hmac.compare_digest for constant-time compare"
    )


# --------------------------------------------------------------------------- #
# bearer_auth_app — ASGI middleware behaviour
# --------------------------------------------------------------------------- #


async def _dummy_ok_app(
    scope: MutableMapping[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """Minimal ASGI app — always returns 200/hello. Used to assert the
    middleware passes valid traffic through unmodified."""
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": b"hello", "more_body": False})


def _http_scope(
    authorization: str | None = None,
    path: str = "/mcp",
) -> dict[str, Any]:
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("latin-1")))
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": headers,
        "scheme": "http",
        "server": ("127.0.0.1", 4747),
        "client": ("127.0.0.1", 0),
    }


async def _drive(
    app: Any,
    scope: dict[str, Any],
) -> tuple[int | None, dict[str, str], bytes]:
    """Drive an ASGI app with an empty-body GET; return (status, headers, body)."""
    sent_first = False

    async def receive() -> MutableMapping[str, Any]:
        nonlocal sent_first
        if sent_first:
            return {"type": "http.disconnect"}
        sent_first = True
        return {"type": "http.request", "body": b"", "more_body": False}

    messages: list[MutableMapping[str, Any]] = []

    async def send(msg: MutableMapping[str, Any]) -> None:
        messages.append(msg)

    await app(scope, receive, send)

    status: int | None = None
    raw_headers: list[tuple[bytes, bytes]] = []
    body = b""
    for msg in messages:
        if msg["type"] == "http.response.start":
            status = msg["status"]
            raw_headers = msg.get("headers", [])
        elif msg["type"] == "http.response.body":
            body += msg.get("body", b"")
    headers = {
        k.decode("ascii").lower(): v.decode("latin-1") for k, v in raw_headers
    }
    return status, headers, body


async def _drive_lifespan(
    app: Any,
) -> bool:
    """Drive a lifespan handshake against a non-HTTP scope; return True if it
    passed through to the inner app (i.e. middleware did not gate it)."""
    received_called = False

    async def receive() -> MutableMapping[str, Any]:
        nonlocal received_called
        if received_called:
            return {"type": "lifespan.shutdown"}
        received_called = True
        return {"type": "lifespan.startup"}

    sent: list[MutableMapping[str, Any]] = []

    async def send(msg: MutableMapping[str, Any]) -> None:
        sent.append(msg)

    # Inner app records the call and acks startup.
    inner_called = False

    async def inner(
        scope: MutableMapping[str, Any],
        recv: Any,
        snd: Any,
    ) -> None:
        nonlocal inner_called
        inner_called = True
        await recv()  # consume startup
        await snd({"type": "lifespan.startup.complete"})

    wrapped = bearer_auth_app(inner, expected_token="t")
    await wrapped({"type": "lifespan", "asgi": {"version": "3.0"}}, receive, send)
    return inner_called


def test_bearer_app_passes_valid_token() -> None:
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        return await _drive(app, _http_scope("Bearer goodtoken"))

    status, _, body = asyncio.run(_run())
    assert status == 200
    assert body == b"hello"


def test_bearer_app_rejects_missing_header() -> None:
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        return await _drive(app, _http_scope(None))

    status, headers, body = asyncio.run(_run())
    assert status == 401
    assert "bearer" in headers.get("www-authenticate", "").lower()
    # Body never reveals the verdict — only logs do.
    assert b"missing" not in body
    assert b"invalid" not in body
    assert b"malformed" not in body


def test_bearer_app_rejects_wrong_token() -> None:
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        return await _drive(app, _http_scope("Bearer not-the-right-token"))

    status, _, _ = asyncio.run(_run())
    assert status == 401


def test_bearer_app_rejects_malformed_scheme() -> None:
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        return await _drive(app, _http_scope("Basic dXNlcjpwYXNz"))

    status, _, _ = asyncio.run(_run())
    assert status == 401


@pytest.mark.parametrize(
    "discovery_path",
    [
        "/.well-known/oauth-authorization-server",
        "/.well-known/openid-configuration",
        "/.well-known/oauth-protected-resource",
    ],
)
def test_bearer_app_bypasses_well_known_oauth_discovery(
    discovery_path: str,
) -> None:
    """OAuth/OIDC discovery probes under ``/.well-known/`` must skip the
    bearer check so dynamic-client-registration bridges (mcp-remote and
    similar) see a clean 404 from the inner app and fall through to the
    static bearer header for actual MCP requests instead of triggering a
    failing OAuth flow."""
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        # No Authorization header — would normally 401 on /mcp.
        return await _drive(app, _http_scope(None, path=discovery_path))

    status, _, body = asyncio.run(_run())
    # The dummy inner app responds 200/hello — proves the request passed
    # through the middleware without the bearer check kicking in.
    assert status == 200
    assert body == b"hello"


def test_bearer_app_does_not_bypass_paths_only_containing_well_known() -> None:
    """The bypass anchors on the leading ``/.well-known/`` prefix; a path
    that merely contains the substring elsewhere must still be bearer-checked."""
    app = bearer_auth_app(_dummy_ok_app, expected_token="goodtoken")

    async def _run() -> tuple[int | None, dict[str, str], bytes]:
        return await _drive(app, _http_scope(None, path="/mcp/.well-known/foo"))

    status, _, _ = asyncio.run(_run())
    assert status == 401


def test_bearer_app_passes_lifespan_through_unchanged() -> None:
    """Non-HTTP scopes (lifespan, websocket) must pass through — they have no
    Authorization header and gating them would break uvicorn startup."""
    inner_was_called = asyncio.run(_drive_lifespan(None))
    assert inner_was_called is True


# --------------------------------------------------------------------------- #
# Logging contract — token value MUST NEVER appear in the log stream.
# --------------------------------------------------------------------------- #


def _captured_logger(name: str) -> tuple[logging.Logger, io.StringIO]:
    """Build an isolated logger writing to an in-memory StringIO."""
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setFormatter(logging.Formatter("%(message)s"))
    log = logging.getLogger(name)
    log.handlers.clear()
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False
    return log, buf


def test_bearer_app_logs_only_verdict_no_token_value() -> None:
    """The token value (correct or wrong) must NEVER appear in the log
    stream. The middleware logs only short verdict labels."""
    log, buf = _captured_logger("test_bearer_no_leak")
    expected = "EXPECTED_TOKEN_SECRETSENTINEL_42"
    wrong = "ATTACKER_GUESS_SECRETSENTINEL_99"
    app = bearer_auth_app(_dummy_ok_app, expected_token=expected, logger=log)

    async def _run() -> None:
        # One bad request and one good request — both must log only the verdict.
        await _drive(app, _http_scope(f"Bearer {wrong}"))
        await _drive(app, _http_scope(f"Bearer {expected}"))

    asyncio.run(_run())

    output = buf.getvalue()
    assert expected not in output, "expected token leaked into log output"
    assert wrong not in output, "wrong-token candidate leaked into log output"
    # Sanity — verdict labels DID land.
    assert "auth: invalid" in output
    assert "auth: ok" in output


def test_bearer_app_logs_missing_verdict_for_missing_header() -> None:
    log, buf = _captured_logger("test_bearer_missing_verdict")
    app = bearer_auth_app(
        _dummy_ok_app, expected_token="t", logger=log
    )

    async def _run() -> None:
        await _drive(app, _http_scope(None))

    asyncio.run(_run())
    assert "auth: missing" in buf.getvalue()


def test_bearer_app_logs_malformed_verdict_for_basic_scheme() -> None:
    log, buf = _captured_logger("test_bearer_malformed_verdict")
    app = bearer_auth_app(
        _dummy_ok_app, expected_token="t", logger=log
    )

    async def _run() -> None:
        await _drive(app, _http_scope("Basic dXNlcjpwYXNz"))

    asyncio.run(_run())
    assert "auth: malformed" in buf.getvalue()
