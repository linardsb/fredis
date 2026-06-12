"""
Fredis MCP tool implementations (OB1 Phase 1).

Pure functions — no MCP server state. Each function accepts typed arguments and
returns a JSON-serialisable dict. The MCP server (`fredis_mcp_server.py`) wraps
these with FastMCP decorators.

Tools shipped in this slice:
- search_memory       — hybrid/keyword/semantic search via memory_search.search
- get_file            — vault-relative read with denylist gate
- list_drafts         — listdir on Fredis/Memory/drafts/<status>/
- list_recent_decisions — bullets from MEMORY.md + grep daily logs window
- get_soul_summary    — returns SOUL.md
- get_user_profile    — USER.md filtered through secret_patterns
- index_status        — same shape as memory_index.py --stats
- propose_draft       — only write surface; lands in drafts/active/<source>/
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from config import (
    DAILY_DIR,
    DRAFTS_DIR,
    MCP_DENYLIST,
    MEMORY_DIR,
    MEMORY_FILE,
    SOUL_FILE,
)
from config import (
    USER_FILE as USER_FILE,  # explicit re-export — tests monkeypatch tools.USER_FILE
)
from db import get_memory_db
from fredis_mcp_auth import is_path_denied
from memory_search import search as _search
from secret_patterns import SECRET_PATTERNS

USER_PROFILE_MIN_CHARS = 200
ALLOWED_DRAFT_STATUSES = {"active", "sent", "expired"}

# Strict allowlist for the `source` field on propose_draft. External AIs that
# don't appear here cannot write — adding a new client requires a code change,
# which is the point: the source name becomes the on-disk directory.
DRAFT_SOURCES: frozenset[str] = frozenset(
    {"chatgpt", "cursor", "gemini", "claude-desktop", "web-claude"}
)

# Frontmatter `type` field — mirrors the Phase 2a schema (decision/idea/...)
# so this slice writes future-compatible files without depending on 2a.
DRAFT_TYPES: frozenset[str] = frozenset(
    {
        "decision",
        "idea",
        "task",
        "insight",
        "reply",
        "meeting",
        "client-log",
        "research",
        "draft",
    }
)

_SLUG_MAX = 60
_COLLISION_MAX = 1000
_NON_SLUG_RE = re.compile(r"[^a-z0-9-]")
_DASH_REPEAT_RE = re.compile(r"-+")

# Cap on the over-fetch used to compensate for denylist drops, so a hostile
# query can't trigger an unbounded engine call.
_SEARCH_OVERFETCH_CAP = 60


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

    over_fetch = max(limit * 3, 1)
    raw = _search(
        query,
        mode=mode,
        limit=over_fetch,
        path_prefix=filter_path or "",
    )
    filtered = [r for r in raw if not is_path_denied(r.path, MCP_DENYLIST)]

    if (
        len(filtered) < limit
        and len(raw) >= over_fetch
        and over_fetch < _SEARCH_OVERFETCH_CAP
    ):
        retry_limit = min(limit * 6, _SEARCH_OVERFETCH_CAP)
        raw = _search(
            query,
            mode=mode,
            limit=retry_limit,
            path_prefix=filter_path or "",
        )
        filtered = [r for r in raw if not is_path_denied(r.path, MCP_DENYLIST)]

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
        for r in filtered[:limit]
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


def _denied(path: str) -> dict[str, Any]:
    """Canonical rejection shape — byte-identical regardless of the cause."""
    return {"path": path, "content": None, "reason": "path not accessible"}


def get_file(path: str) -> dict[str, Any]:
    """Read a file from the vault by relative path.

    Four rejection paths collapse into one response shape so callers cannot
    distinguish denied / missing / escape via the error text:

    - Input string is on the denylist (cheap pre-FS check).
    - Path traverses outside the vault (absolute, ``..``, or symlink escape).
    - Path resolves under the vault but no file exists there.
    - Path resolves to a denylisted target (e.g. an in-vault symlink whose
      alias name is safe but whose realpath sits under a denied prefix).
    """
    if is_path_denied(path, MCP_DENYLIST):
        return _denied(path)
    resolved = _resolve_vault_path(path)
    if resolved is None:
        return _denied(path)
    rel = resolved.relative_to(MEMORY_DIR.resolve()).as_posix()
    if is_path_denied(rel, MCP_DENYLIST):
        return _denied(path)
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


def _slugify_title(title: str) -> str:
    """Slugify a free-form title for use in a filename.

    Lowercase, ASCII-only, replace any non-``[a-z0-9-]`` with ``-``, collapse
    runs of dashes, trim, truncate to 60 chars (re-trimming any trailing dash
    left by truncation). Returns ``"untitled"`` when nothing survives — a
    title made entirely of slashes / dots / non-ASCII collapses to that.

    The point of this function is the security boundary: no slash, no dot,
    no path separator can survive into the filename. Path traversal via the
    title field is impossible by construction.
    """
    s = title.lower()
    s = _NON_SLUG_RE.sub("-", s)
    s = _DASH_REPEAT_RE.sub("-", s).strip("-")
    s = s[:_SLUG_MAX].strip("-")
    return s or "untitled"


def _yaml_inline_list(items: list[str]) -> str:
    """Render a list of strings as a YAML inline list with double-quoted
    items, escaping ``\\`` and ``"`` so values containing commas / quotes /
    brackets cannot break out of the field."""
    parts: list[str] = []
    for item in items:
        escaped = item.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f'"{escaped}"')
    return "[" + ", ".join(parts) + "]"


def propose_draft(
    source: str,
    title: str,
    body: str,
    type: str = "draft",
    people: list[str] | None = None,
    projects: list[str] | None = None,
) -> dict[str, Any]:
    """Write a candidate draft from an external AI into ``drafts/active/<source>/``.

    The ONLY write surface on the MCP server. Security perimeter:

    1. ``source`` is matched against the literal ``DRAFT_SOURCES`` allowlist
       before any filesystem call — bad sources cause a structured error and
       leave the vault untouched.
    2. ``title`` is slugified (no ``/``, no ``..``, no ``.``) before it ever
       reaches the filesystem.
    3. The destination dir is resolved (``Path.resolve``) and asserted to live
       under ``drafts/active/`` — an attacker who pre-creates a symlink at
       ``drafts/active/<source>/`` pointing elsewhere is rejected here.
    4. Files are written with ``open(path, "x")`` (``O_CREAT | O_EXCL``) so a
       collision never overwrites — a numeric suffix is appended on the next
       loop iteration.

    Returns ``{"ok": True, "path": "<vault-relative path>"}`` on success;
    ``{"ok": False, "error": "<reason>"}`` on any rejection.
    """
    if source not in DRAFT_SOURCES:
        return {"ok": False, "error": "invalid source"}
    if type not in DRAFT_TYPES:
        return {"ok": False, "error": "invalid type"}

    people_list = list(people) if people else []
    projects_list = list(projects) if projects else []

    base_dir = DRAFTS_DIR / "active"
    target_dir = base_dir / source
    target_dir.mkdir(parents=True, exist_ok=True)

    base_real = base_dir.resolve()
    target_real = target_dir.resolve()
    try:
        target_real.relative_to(base_real)
    except ValueError:
        return {"ok": False, "error": "destination outside drafts/active"}

    slug = _slugify_title(title)
    today = date.today().isoformat()
    created = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    frontmatter = (
        "---\n"
        f"type: {type}\n"
        f"source: mcp:{source}\n"
        f"people: {_yaml_inline_list(people_list)}\n"
        f"projects: {_yaml_inline_list(projects_list)}\n"
        f"created: {created}\n"
        "---\n"
        f"# {title}\n"
        "\n"
        f"{body}\n"
    )

    written: Path | None = None
    for n in range(1, _COLLISION_MAX):
        suffix = "" if n == 1 else f"_{n}"
        candidate = target_real / f"{today}_{slug}{suffix}.md"
        try:
            with candidate.open("x", encoding="utf-8") as fh:
                fh.write(frontmatter)
            written = candidate
            break
        except FileExistsError:
            continue

    if written is None:
        return {"ok": False, "error": "filename collision exhausted"}

    rel = written.resolve().relative_to(MEMORY_DIR.resolve()).as_posix()
    return {"ok": True, "path": rel}
