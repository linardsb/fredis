"""
Fredis MCP server (OB1 Phase 1).

FastMCP entry point exposing 7 read-only tools and 1 write tool
(``propose_draft``) over stdio. Refuses to start unless
``FREDIS_MCP_ENABLED=1``. ``FREDIS_MCP_DENYLIST`` is honoured by the read
tools as of slice 1.2; ``FREDIS_MCP_BIND`` / ``_PORT`` / ``_AUTH_TOKEN``
remain placeholders for the optional HTTP+SSE remote transport (slice 1B).

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


def build_server() -> FastMCP:
    """Construct a FastMCP instance with all tools registered (7 read +
    ``propose_draft`` write)."""
    mcp: FastMCP = FastMCP(name="fredis")

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
    """Server entry point. Refuses unless ``FREDIS_MCP_ENABLED=1``."""
    if os.getenv("FREDIS_MCP_ENABLED") != "1":
        print(
            "fredis-mcp: refusing to start — FREDIS_MCP_ENABLED is not set "
            "to '1'. Set it in .claude/scripts/.env to enable.",
            file=sys.stderr,
        )
        return 1

    logger = _configure_logging()
    logger.info("starting fredis-mcp server (stdio transport)")

    mcp = build_server()
    mcp.run("stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
