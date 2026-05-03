"""
Fredis MCP server (OB1 Phase 1).

FastMCP entry point exposing 7 read-only tools and 1 write tool
(``propose_draft``). Two transports are supported, selected by env:

- ``FREDIS_MCP_TRANSPORT`` unset or ``stdio`` (default): runs over stdio for
  per-client subprocess use (Mac wrapper, Claude Desktop, Cursor, etc.).
  ``FREDIS_MCP_DENYLIST`` is honoured; no network surface, no auth needed.

- ``FREDIS_MCP_TRANSPORT=streamable-http`` (Phase 1B, VPS only): builds the
  FastMCP streamable-http ASGI app, wraps it in
  ``fredis_mcp_auth.bearer_auth_app``, and serves it via uvicorn on
  ``FREDIS_MCP_BIND:FREDIS_MCP_PORT``. ``FREDIS_MCP_AUTH_TOKEN`` is required
  — the server refuses to start without it. Bind defaults to ``127.0.0.1``;
  on the VPS it stays loopback and Tailscale Serve fronts it on HTTPS.

Refuses to start unless ``FREDIS_MCP_ENABLED=1``.

Run via wrapper:

    cd .claude/scripts && ./run_mcp_server.sh

Tool implementations live in ``fredis_mcp_tools.py`` so the unit tests can
import them without bringing up the server.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

import fredis_mcp_tools as tools
from config import DATA_DIR

LOG_DIR = DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "mcp-server.log"


def _configure_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("fredis_mcp")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        logger.addHandler(handler)
    return logger


def build_server(allowed_hosts: list[str] | None = None) -> FastMCP:
    """Construct a FastMCP instance with all tools registered (7 read +
    ``propose_draft`` write).

    ``allowed_hosts`` whitelists Host header values for FastMCP's DNS-rebinding
    protection — required when the streamable-http transport is fronted by a
    hostname (e.g. Tailscale Serve). The stdio path leaves it ``None``; the
    streamable-http path threads ``FREDIS_MCP_ALLOWED_HOSTS`` from env.
    """
    fastmcp_kwargs: dict[str, Any] = {"name": "fredis"}
    if allowed_hosts:
        from mcp.server.transport_security import TransportSecuritySettings

        fastmcp_kwargs["transport_security"] = TransportSecuritySettings(
            allowed_hosts=allowed_hosts,
        )
    mcp: FastMCP = FastMCP(**fastmcp_kwargs)

    @mcp.tool(
        description=(
            "Search Fredis memory (vault). Modes: 'keyword' | 'semantic' | "
            "'hybrid'. filter_path narrows by vault-relative prefix "
            "(e.g. 'drafts/sent'). filter_type accepts frontmatter types "
            "(decision/idea/task/etc.) but is a no-op until Phase 2c."
        )
    )
    def search_memory(
        query: str,
        mode: str = "hybrid",
        limit: int = 10,
        filter_path: str | None = None,
        filter_type: str | None = None,
    ) -> dict[str, Any]:
        return tools.search_memory(query, mode, limit, filter_path, filter_type)

    @mcp.tool(
        description=(
            "Read a vault file by relative path (e.g. 'SOUL.md'). Absolute "
            "paths and `..` traversal are rejected. Sensitive paths return "
            "'path not accessible' with the same shape as a missing file."
        )
    )
    def get_file(path: str) -> dict[str, Any]:
        return tools.get_file(path)

    @mcp.tool(
        description=(
            "List drafts under Fredis/Memory/drafts/<status>/. status is "
            "'active' (default), 'sent', or 'expired'. Returns most-recent first."
        )
    )
    def list_drafts(status: str = "active", limit: int = 20) -> dict[str, Any]:
        return tools.list_drafts(status, limit)

    @mcp.tool(
        description=(
            "Bulleted decisions from MEMORY.md within `days` plus "
            "decision-shaped lines from daily logs in the same window."
        )
    )
    def list_recent_decisions(days: int = 14) -> dict[str, Any]:
        return tools.list_recent_decisions(days)

    @mcp.tool(description="Return SOUL.md (always allowed).")
    def get_soul_summary() -> dict[str, Any]:
        return tools.get_soul_summary()

    @mcp.tool(
        description=(
            "Return USER.md with lines containing secret-shaped tokens "
            "stripped. Returns null if the stripped profile is too short."
        )
    )
    def get_user_profile() -> dict[str, Any]:
        return tools.get_user_profile()

    @mcp.tool(description="Return memory_index --stats shape.")
    def index_status() -> dict[str, Any]:
        return tools.index_status()

    @mcp.tool(
        description=(
            "Propose a draft from an external AI client. The draft is written "
            "to Fredis/Memory/drafts/active/<source>/<YYYY-MM-DD>_<slug>.md "
            "with YAML frontmatter. This is the ONLY write surface; it cannot "
            "create files outside drafts/active/<source>/. `source` must be "
            "one of the listed clients; `type` is the frontmatter type "
            "(decision, idea, task, insight, reply, meeting, client-log, "
            "research, draft). Returns {ok, path} on success, {ok: false, "
            "error} on rejection."
        )
    )
    def propose_draft(
        source: Literal[
            "chatgpt", "cursor", "gemini", "claude-desktop", "web-claude"
        ],
        title: str,
        body: str,
        type: Literal[
            "decision",
            "idea",
            "task",
            "insight",
            "reply",
            "meeting",
            "client-log",
            "research",
            "draft",
        ] = "draft",
        people: list[str] | None = None,
        projects: list[str] | None = None,
    ) -> dict[str, Any]:
        return tools.propose_draft(
            source=source,
            title=title,
            body=body,
            type=type,
            people=people,
            projects=projects,
        )

    return mcp


def main() -> int:
    """Server entry point. Refuses unless ``FREDIS_MCP_ENABLED=1``.

    Selects transport from ``FREDIS_MCP_TRANSPORT`` (default ``stdio``).
    Stdio path is unchanged from Phase 1.1; streamable-http branch is the
    Phase 1B addition for VPS-side remote use.
    """
    if os.getenv("FREDIS_MCP_ENABLED") != "1":
        print(
            "fredis-mcp: refusing to start — FREDIS_MCP_ENABLED is not set "
            "to '1'. Set it in .claude/scripts/.env to enable.",
            file=sys.stderr,
        )
        return 1

    logger = _configure_logging()

    transport = (os.getenv("FREDIS_MCP_TRANSPORT", "stdio") or "stdio").strip().lower()

    if transport == "stdio":
        logger.info("starting fredis-mcp server (stdio transport)")
        mcp = build_server()
        mcp.run("stdio")
        return 0

    if transport == "streamable-http":
        return _run_streamable_http(logger)

    print(
        f"fredis-mcp: unknown FREDIS_MCP_TRANSPORT value: {transport!r}. "
        "Supported: 'stdio' (default), 'streamable-http'.",
        file=sys.stderr,
    )
    return 1


def _run_streamable_http(logger: logging.Logger) -> int:
    """Build and serve the streamable-http transport with bearer auth.

    Refuses to start without ``FREDIS_MCP_AUTH_TOKEN`` — silent open access
    is the worst failure mode for a network-exposed MCP. Bind defaults to
    ``127.0.0.1`` so the deploy targets Tailscale Serve fronting loopback,
    not direct exposure on the Tailscale interface.
    """
    bind = (os.getenv("FREDIS_MCP_BIND", "127.0.0.1") or "127.0.0.1").strip()
    port_raw = (os.getenv("FREDIS_MCP_PORT", "4747") or "4747").strip()
    try:
        port = int(port_raw)
    except ValueError:
        print(
            f"fredis-mcp: FREDIS_MCP_PORT must be an integer, got {port_raw!r}.",
            file=sys.stderr,
        )
        return 1

    token = (os.getenv("FREDIS_MCP_AUTH_TOKEN", "") or "").strip()
    if not token:
        print(
            "fredis-mcp: refusing to start — FREDIS_MCP_TRANSPORT=streamable-http "
            "requires FREDIS_MCP_AUTH_TOKEN. Set it in /etc/secondbrain.env (VPS) "
            "or .claude/scripts/.env (local).",
            file=sys.stderr,
        )
        return 1

    # Lazy imports — only the remote path needs uvicorn / Starlette / the auth
    # middleware. Stdio sessions never load these modules.
    import uvicorn

    from fredis_mcp_auth import bearer_auth_app

    hosts_raw = (os.getenv("FREDIS_MCP_ALLOWED_HOSTS", "") or "").strip()
    allowed_hosts: list[str] | None = (
        [h.strip() for h in hosts_raw.split(",") if h.strip()]
        if hosts_raw
        else None
    )
    mcp = build_server(allowed_hosts=allowed_hosts)
    app = mcp.streamable_http_app()
    wrapped = bearer_auth_app(app, expected_token=token, logger=logger)

    logger.info(
        "starting fredis-mcp server (streamable-http transport on %s:%d)",
        bind,
        port,
    )
    uvicorn.run(wrapped, host=bind, port=port, log_config=None, access_log=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
