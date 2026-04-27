"""
Fredis MCP security helpers (OB1 Phase 1.2).

This slice ships the path-based sensitivity gate (D3 = A). The bearer-token
validator listed in the plan is gated on D2.5 = B (HTTP+SSE transport); slice
01 chose stdio (D2.5 = A), so no auth helper is needed here.

The helper is intentionally narrow — pure-string prefix matching. Filesystem
escape (symlinks, ``..``) is handled by ``fredis_mcp_tools._resolve_vault_path``;
combining the two checks is the caller's responsibility.
"""

from __future__ import annotations

from pathlib import PurePosixPath


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
