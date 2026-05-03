"""Tests for the Fredis MCP server entry point — transport switch (Phase 1B).

The point of this slice is that the stdio path is unchanged from Phase 1.1
and the streamable-http path is opt-in, gated on env, and refuses to start
without an auth token.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

import fredis_mcp_server as server

# --------------------------------------------------------------------------- #
# CRITICAL — load-bearing security tests come first.
# Silent open access on the network surface is the worst failure mode.
# --------------------------------------------------------------------------- #


def test_remote_mode_refuses_to_start_without_auth_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Streamable-http transport with no FREDIS_MCP_AUTH_TOKEN MUST exit 1
    and print a stderr error. A silent default would expose every read tool
    to anyone who can route to the port."""
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "streamable-http")
    monkeypatch.delenv("FREDIS_MCP_AUTH_TOKEN", raising=False)

    rc = server.main()

    assert rc == 1
    err = capsys.readouterr().err
    assert "FREDIS_MCP_AUTH_TOKEN" in err
    assert "refusing to start" in err


def test_remote_mode_refuses_with_blank_auth_token(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Whitespace-only token is treated as empty — same hard refusal."""
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("FREDIS_MCP_AUTH_TOKEN", "   ")

    rc = server.main()
    assert rc == 1
    assert "FREDIS_MCP_AUTH_TOKEN" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# main() — gating + transport routing
# --------------------------------------------------------------------------- #


def test_main_refuses_when_enabled_flag_unset(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Phase 1.1 contract — the master kill-switch still works."""
    monkeypatch.delenv("FREDIS_MCP_ENABLED", raising=False)

    rc = server.main()

    assert rc == 1
    assert "FREDIS_MCP_ENABLED" in capsys.readouterr().err


def test_main_refuses_when_enabled_flag_not_one(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "true")

    rc = server.main()

    assert rc == 1
    assert "FREDIS_MCP_ENABLED" in capsys.readouterr().err


def test_main_defaults_to_stdio_when_transport_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No FREDIS_MCP_TRANSPORT == stdio (Phase 1.1 default behaviour)."""
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.delenv("FREDIS_MCP_TRANSPORT", raising=False)

    called: dict[str, Any] = {}

    def fake_build_server() -> Any:
        class _M:
            def run(self, transport: str) -> None:
                called["transport"] = transport

        return _M()

    monkeypatch.setattr(server, "build_server", fake_build_server)

    rc = server.main()

    assert rc == 0
    assert called == {"transport": "stdio"}


def test_main_runs_stdio_when_transport_explicitly_stdio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "stdio")

    called: dict[str, Any] = {}

    def fake_build_server() -> Any:
        class _M:
            def run(self, transport: str) -> None:
                called["transport"] = transport

        return _M()

    monkeypatch.setattr(server, "build_server", fake_build_server)

    rc = server.main()

    assert rc == 0
    assert called == {"transport": "stdio"}


def test_main_routes_to_streamable_http_branch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When transport=streamable-http, main() delegates to
    _run_streamable_http and returns its exit code."""
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "streamable-http")

    called: dict[str, Any] = {}

    def fake_run(_logger: logging.Logger) -> int:
        called["ran"] = True
        return 0

    monkeypatch.setattr(server, "_run_streamable_http", fake_run)

    rc = server.main()

    assert rc == 0
    assert called == {"ran": True}


def test_main_rejects_unknown_transport(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "websocket")

    rc = server.main()

    assert rc == 1
    err = capsys.readouterr().err
    assert "websocket" in err
    assert "stdio" in err  # error message lists supported values


def test_main_transport_value_is_case_insensitive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FREDIS_MCP_ENABLED", "1")
    monkeypatch.setenv("FREDIS_MCP_TRANSPORT", "Streamable-HTTP")

    called: dict[str, Any] = {}

    def fake_run(_logger: logging.Logger) -> int:
        called["ran"] = True
        return 0

    monkeypatch.setattr(server, "_run_streamable_http", fake_run)

    rc = server.main()
    assert rc == 0
    assert called == {"ran": True}


# --------------------------------------------------------------------------- #
# _run_streamable_http — input validation + uvicorn invocation
# --------------------------------------------------------------------------- #


def test_run_streamable_http_rejects_non_integer_port(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("FREDIS_MCP_AUTH_TOKEN", "any-non-empty")
    monkeypatch.setenv("FREDIS_MCP_PORT", "not-a-number")

    rc = server._run_streamable_http(logging.getLogger("test"))

    assert rc == 1
    err = capsys.readouterr().err
    assert "FREDIS_MCP_PORT" in err
    assert "integer" in err


def test_run_streamable_http_invokes_uvicorn_with_wrapped_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path — verifies that with a token set, the server builds the
    streamable-http app, wraps it in bearer middleware, and hands the wrapped
    callable to uvicorn.run with the configured bind/port."""
    monkeypatch.setenv("FREDIS_MCP_AUTH_TOKEN", "secret-test-token")
    monkeypatch.setenv("FREDIS_MCP_BIND", "127.0.0.1")
    monkeypatch.setenv("FREDIS_MCP_PORT", "4747")

    # Stub mcp.streamable_http_app() so we don't pay the real FastMCP cost.
    sentinel_inner_app = object()

    def fake_build_server(**kwargs: Any) -> Any:
        class _M:
            def streamable_http_app(self) -> Any:
                return sentinel_inner_app

        return _M()

    monkeypatch.setattr(server, "build_server", fake_build_server)

    captured: dict[str, Any] = {}

    # Stub uvicorn at import-time inside the function. The function does
    # `import uvicorn` lazily so we need to patch sys.modules before it runs.
    import sys
    import types

    fake_uvicorn = types.ModuleType("uvicorn")

    def fake_run(app: Any, **kwargs: Any) -> None:
        captured["app"] = app
        captured["kwargs"] = kwargs

    fake_uvicorn.run = fake_run  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    rc = server._run_streamable_http(logging.getLogger("test"))

    assert rc == 0
    # The app handed to uvicorn must be the bearer-wrapped callable, not the
    # raw inner app — the wrapper is a closure, so identity-distinct.
    assert captured["app"] is not sentinel_inner_app
    assert callable(captured["app"])
    assert captured["kwargs"]["host"] == "127.0.0.1"
    assert captured["kwargs"]["port"] == 4747
    # Defence: uvicorn access log must be off (avoids logging tokens that
    # might appear in malformed query strings).
    assert captured["kwargs"]["access_log"] is False


def test_run_streamable_http_threads_allowed_hosts_env_to_build_server(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """FREDIS_MCP_ALLOWED_HOSTS (comma-separated) must reach build_server as
    a parsed list. Required when fronted by Tailscale Serve so FastMCP's
    DNS-rebinding protection accepts the tailnet hostname."""
    monkeypatch.setenv("FREDIS_MCP_AUTH_TOKEN", "secret-test-token")
    monkeypatch.setenv("FREDIS_MCP_BIND", "127.0.0.1")
    monkeypatch.setenv("FREDIS_MCP_PORT", "4747")
    monkeypatch.setenv(
        "FREDIS_MCP_ALLOWED_HOSTS",
        "127.0.0.1, localhost ,fredis-vps.tail5d589c.ts.net,",
    )

    captured_kwargs: dict[str, Any] = {}

    def fake_build_server(**kwargs: Any) -> Any:
        captured_kwargs.update(kwargs)

        class _M:
            def streamable_http_app(self) -> Any:
                return object()

        return _M()

    monkeypatch.setattr(server, "build_server", fake_build_server)

    import sys
    import types

    fake_uvicorn = types.ModuleType("uvicorn")
    fake_uvicorn.run = lambda *a, **k: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    server._run_streamable_http(logging.getLogger("test"))

    # Whitespace-trimmed, blanks dropped, order preserved.
    assert captured_kwargs.get("allowed_hosts") == [
        "127.0.0.1",
        "localhost",
        "fredis-vps.tail5d589c.ts.net",
    ]


def test_run_streamable_http_passes_none_when_allowed_hosts_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No FREDIS_MCP_ALLOWED_HOSTS env => build_server gets None (= preserve
    FastMCP default behaviour). Stdio path is unaffected by this test."""
    monkeypatch.setenv("FREDIS_MCP_AUTH_TOKEN", "secret-test-token")
    monkeypatch.setenv("FREDIS_MCP_BIND", "127.0.0.1")
    monkeypatch.setenv("FREDIS_MCP_PORT", "4747")
    monkeypatch.delenv("FREDIS_MCP_ALLOWED_HOSTS", raising=False)

    captured_kwargs: dict[str, Any] = {}

    def fake_build_server(**kwargs: Any) -> Any:
        captured_kwargs.update(kwargs)

        class _M:
            def streamable_http_app(self) -> Any:
                return object()

        return _M()

    monkeypatch.setattr(server, "build_server", fake_build_server)

    import sys
    import types

    fake_uvicorn = types.ModuleType("uvicorn")
    fake_uvicorn.run = lambda *a, **k: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)

    server._run_streamable_http(logging.getLogger("test"))

    assert captured_kwargs.get("allowed_hosts") is None
