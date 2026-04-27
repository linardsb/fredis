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
