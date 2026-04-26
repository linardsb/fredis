"""
Fredis MCP read-only tool implementations (OB1 Phase 1.1).

Pure functions — no MCP server state. Each function accepts typed arguments and
returns a JSON-serialisable dict. The MCP server (`fredis_mcp_server.py`) wraps
these with FastMCP decorators.

Tools shipped in this slice:
- search_memory       — hybrid/keyword/semantic search via memory_search.search
- get_file            — vault-relative read (no denylist yet — slice 02)
- list_drafts         — listdir on Fredis/Memory/drafts/<status>/
- list_recent_decisions — bullets from MEMORY.md + grep daily logs window
- get_soul_summary    — returns SOUL.md
- get_user_profile    — USER.md filtered through secret_patterns
- index_status        — same shape as memory_index.py --stats
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from config import (
    DAILY_DIR,
    DRAFTS_DIR,
    MEMORY_DIR,
    MEMORY_FILE,
    SOUL_FILE,
    USER_FILE,
)
from db import get_memory_db
from memory_search import search as _search
from secret_patterns import SECRET_PATTERNS

USER_PROFILE_MIN_CHARS = 200
ALLOWED_DRAFT_STATUSES = {"active", "sent", "expired"}


def search_memory(
    query: str,
    mode: str = "hybrid",
    limit: int = 10,
    filter_path: str | None = None,
    filter_type: str | None = None,
) -> dict[str, Any]:
    """Search the memory index.

    Args:
        query: Search text.
        mode: 'keyword' | 'semantic' | 'hybrid' (default 'hybrid').
        limit: Maximum results to return.
        filter_path: Optional vault-relative path prefix (e.g. 'drafts/sent').
        filter_type: Frontmatter type filter (e.g. 'decision'). No-op until
            Phase 2c adds the index column; accepted for forward compatibility.

    Returns:
        ``{"results": [{"file_path", "start_line", "end_line", "score",
        "match_type", "section_title", "snippet"}, ...]}``.
    """
    if filter_type is not None:
        # Forward-compatible no-op; documented in docstring.
        pass

    raw = _search(
        query,
        mode=mode,
        limit=limit,
        path_prefix=filter_path or "",
    )
    results = [
        {
            "file_path": r.path,
            "start_line": r.start_line,
            "end_line": r.end_line,
            "score": r.score,
            "match_type": r.match_type,
            "section_title": r.section_title,
            "snippet": r.text,
        }
        for r in raw
    ]
    return {"results": results}


def _resolve_vault_path(path: str) -> Path | None:
    """Return absolute vault path if `path` is a safe vault-relative file.

    Rejects absolute paths and any segment containing `..`. Returns None if
    the resolved path escapes MEMORY_DIR or doesn't exist as a file.
    """
    p = Path(path)
    if p.is_absolute():
        return None
    if any(part == ".." for part in p.parts):
        return None

    resolved = (MEMORY_DIR / p).resolve()
    memory_root = MEMORY_DIR.resolve()
    try:
        resolved.relative_to(memory_root)
    except ValueError:
        return None
    if not resolved.is_file():
        return None
    return resolved


def get_file(path: str) -> dict[str, Any]:
    """Read a file from the vault by relative path.

    Path traversal (`..`) and absolute paths are rejected. Slice 02 layers a
    content denylist on top; this slice only enforces basic resolution safety.
    """
    resolved = _resolve_vault_path(path)
    if resolved is None:
        return {"path": path, "content": None, "reason": "path not accessible"}
    return {"path": path, "content": resolved.read_text(encoding="utf-8")}


def list_drafts(status: str = "active", limit: int = 20) -> dict[str, Any]:
    """List drafts under ``Fredis/Memory/drafts/<status>/``.

    Args:
        status: 'active' | 'sent' | 'expired'.
        limit: Maximum entries to return (most recent first).
    """
    if status not in ALLOWED_DRAFT_STATUSES:
        return {"drafts": [], "reason": f"invalid status: {status}"}

    base = DRAFTS_DIR / status
    if not base.is_dir():
        return {"drafts": []}

    files = [p for p in base.rglob("*.md") if p.is_file()]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    drafts = [
        {
            "path": p.relative_to(MEMORY_DIR).as_posix(),
            "size_bytes": p.stat().st_size,
            "mtime": int(p.stat().st_mtime),
        }
        for p in files[:limit]
    ]
    return {"drafts": drafts}


_BULLET_DECISION_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<title>[^*]+?)\s*\((?P<date>\d{4}-\d{2}-\d{2})\)\.?\*\*\.?\s*(?P<body>.*)$",
    re.MULTILINE,
)
_DAILY_DECISION_RE = re.compile(
    r"^\s*[-*]\s+(?P<line>.*\b(?:decision|decided|chose|chosen|will\s+(?:ship|build|drop))\b.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def list_recent_decisions(days: int = 14) -> dict[str, Any]:
    """Return bullets from MEMORY.md within `days` plus decision-shaped lines
    from the corresponding daily logs window.

    Each entry: ``{"date", "text", "source"}``. ``source`` is the vault-relative
    file path the line came from.
    """
    today = date.today()
    cutoff = today - timedelta(days=days)
    out: list[dict[str, str]] = []

    if MEMORY_FILE.is_file():
        memory_text = MEMORY_FILE.read_text(encoding="utf-8")
        for m in _BULLET_DECISION_RE.finditer(memory_text):
            try:
                d = date.fromisoformat(m.group("date"))
            except ValueError:
                continue
            if d < cutoff:
                continue
            text = f"{m.group('title').strip()} — {m.group('body').strip()}".rstrip(" —")
            out.append(
                {
                    "date": d.isoformat(),
                    "text": text,
                    "source": MEMORY_FILE.relative_to(MEMORY_DIR).as_posix(),
                }
            )

    if DAILY_DIR.is_dir():
        for n in range(days + 1):
            d = today - timedelta(days=n)
            log = DAILY_DIR / f"{d.isoformat()}.md"
            if not log.is_file():
                continue
            log_text = log.read_text(encoding="utf-8")
            for m in _DAILY_DECISION_RE.finditer(log_text):
                out.append(
                    {
                        "date": d.isoformat(),
                        "text": m.group("line").strip(),
                        "source": log.relative_to(MEMORY_DIR).as_posix(),
                    }
                )

    out.sort(key=lambda e: e["date"], reverse=True)
    return {"decisions": out}


def get_soul_summary() -> dict[str, Any]:
    """Return the contents of SOUL.md. Always allowed — exposing the persona
    is the point of MCP portability."""
    if not SOUL_FILE.is_file():
        return {"soul": None, "reason": "SOUL.md not found"}
    return {"soul": SOUL_FILE.read_text(encoding="utf-8")}


def _strip_secret_lines(text: str) -> str:
    """Drop any line where any pattern in SECRET_PATTERNS matches."""
    kept: list[str] = []
    for line in text.splitlines():
        if any(p.search(line) for p in SECRET_PATTERNS.values()):
            continue
        kept.append(line)
    return "\n".join(kept)


def get_user_profile() -> dict[str, Any]:
    """Return USER.md with secret-shape lines stripped.

    If the stripped content is below ``USER_PROFILE_MIN_CHARS`` or empty,
    returns ``{"profile": None, "reason": "USER profile is restricted"}``.
    """
    if not USER_FILE.is_file():
        return {"profile": None, "reason": "USER profile is restricted"}

    stripped = _strip_secret_lines(USER_FILE.read_text(encoding="utf-8"))
    if len(stripped.strip()) < USER_PROFILE_MIN_CHARS:
        return {"profile": None, "reason": "USER profile is restricted"}
    return {"profile": stripped}


def index_status() -> dict[str, Any]:
    """Return the same shape as ``memory_index.py --stats``."""
    db = get_memory_db()
    db.init_schema()
    stats = db.get_stats()
    db.close()
    return dict(stats)
