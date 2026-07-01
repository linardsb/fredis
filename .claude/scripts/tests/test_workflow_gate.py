"""Tests for the Archon PRD gate (integrations.archon_gate).

Fully hermetic — every case runs against a tmp_path `the-team/` dir passed via
`base_dir`, never the live vault. The gate is the whole of Phase-1 task item #2
("no approved PRD -> no run"), so its refusal paths are pinned here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

from integrations.archon_gate import (  # noqa: E402
    ApprovedPRD,
    GateError,
    _split_frontmatter,
    resolve_prd,
)

APPROVED = "---\napproved: true\ntitle: Test\n---\n\n## Problem\nReal body.\n"
UNAPPROVED = "---\ntitle: Test\n---\n\n## Problem\nReal body.\n"
NO_FM = "# Just a heading\nNo front-matter here.\n"


def _write(d: Path, name: str, text: str) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(text, encoding="utf-8")
    return p


# --- front-matter parsing --------------------------------------------------


def test_split_frontmatter_none() -> None:
    meta, body = _split_frontmatter(NO_FM)
    assert meta == {}
    assert body == NO_FM


def test_split_frontmatter_bool() -> None:
    meta, body = _split_frontmatter(APPROVED)
    assert meta["approved"] is True  # real bool, not the string "true"
    assert body.startswith("## Problem")
    assert "approved" not in body  # front-matter stripped from the run input


# --- happy path (not runnable against the live vault: needs an approved file) --


def test_resolve_auto_single_approved(tmp_path: Path) -> None:
    _write(tmp_path, "phase1-PRD.md", APPROVED)
    prd = resolve_prd(None, base_dir=tmp_path)
    assert isinstance(prd, ApprovedPRD)
    assert prd.path.name == "phase1-PRD.md"
    assert prd.message.startswith("## Problem")
    assert "approved: true" not in prd.message


def test_resolve_by_slug_approved(tmp_path: Path) -> None:
    _write(tmp_path, "email-hub-issue-12.md", APPROVED)
    prd = resolve_prd("email-hub-issue-12", base_dir=tmp_path)
    assert prd.path.name == "email-hub-issue-12.md"


# --- refusals (task item #2) -----------------------------------------------


def test_refuse_missing_dir(tmp_path: Path) -> None:
    with pytest.raises(GateError, match="No PRD directory"):
        resolve_prd(None, base_dir=tmp_path / "does-not-exist")


def test_refuse_empty_dir(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    with pytest.raises(GateError, match="No approved PRD"):
        resolve_prd(None, base_dir=tmp_path)


def test_refuse_unapproved_only(tmp_path: Path) -> None:
    _write(tmp_path, "draft.md", UNAPPROVED)
    with pytest.raises(GateError, match="No approved PRD"):
        resolve_prd(None, base_dir=tmp_path)


def test_refuse_no_frontmatter(tmp_path: Path) -> None:
    _write(tmp_path, "draft.md", NO_FM)
    with pytest.raises(GateError, match="No approved PRD"):
        resolve_prd(None, base_dir=tmp_path)


def test_refuse_multiple_approved(tmp_path: Path) -> None:
    _write(tmp_path, "a.md", APPROVED)
    _write(tmp_path, "b.md", APPROVED)
    with pytest.raises(GateError, match="Multiple approved PRDs"):
        resolve_prd(None, base_dir=tmp_path)


def test_refuse_slug_unapproved(tmp_path: Path) -> None:
    _write(tmp_path, "draft.md", UNAPPROVED)
    with pytest.raises(GateError, match="not approved"):
        resolve_prd("draft", base_dir=tmp_path)


def test_refuse_nonexistent_slug(tmp_path: Path) -> None:
    tmp_path.mkdir(exist_ok=True)
    with pytest.raises(GateError, match="No PRD artifact"):
        resolve_prd("nope", base_dir=tmp_path)


def test_refuse_free_text_input(tmp_path: Path) -> None:
    """A free-form string can never become a run input — it resolves to a
    (missing) slug file, not raw text. This is what stops gate bypass."""
    tmp_path.mkdir(exist_ok=True)
    with pytest.raises(GateError):
        resolve_prd("just do the thing", base_dir=tmp_path)


def test_refuse_path_traversal(tmp_path: Path) -> None:
    _write(tmp_path, "ok.md", APPROVED)
    with pytest.raises(GateError, match="outside the gate"):
        resolve_prd("../../etc/passwd", base_dir=tmp_path)


def test_refuse_subdir_path(tmp_path: Path) -> None:
    """Only files DIRECTLY in the gate dir count — not nested paths."""
    _write(tmp_path / "sub", "nested.md", APPROVED)
    with pytest.raises(GateError, match="outside the gate"):
        resolve_prd("sub/nested.md", base_dir=tmp_path)


def test_refuse_approved_string_not_bool(tmp_path: Path) -> None:
    """`approved: "true"` (a string) does NOT pass — approval must be an
    unambiguous boolean."""
    _write(tmp_path, "d.md", '---\napproved: "true"\n---\n\nBody.\n')
    with pytest.raises(GateError, match="No approved PRD"):
        resolve_prd(None, base_dir=tmp_path)


def test_refuse_approved_false(tmp_path: Path) -> None:
    _write(tmp_path, "d.md", "---\napproved: false\n---\n\nBody.\n")
    with pytest.raises(GateError, match="not approved"):
        resolve_prd("d", base_dir=tmp_path)


def test_refuse_approved_empty_body(tmp_path: Path) -> None:
    _write(tmp_path, "d.md", "---\napproved: true\n---\n")
    with pytest.raises(GateError, match="no body"):
        resolve_prd("d", base_dir=tmp_path)
