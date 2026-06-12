"""Stale-draft digest note — gather_stale_drafts_summary + context wiring."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-fake-for-tests")
os.environ.setdefault("SLACK_OWNER_USER_ID", "U0OWNER123")

import heartbeat  # noqa: E402,I001  — must follow env overrides
from config import now_local  # noqa: E402


@pytest.fixture
def active_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    active = tmp_path / "active"
    active.mkdir()
    monkeypatch.setattr(heartbeat, "DRAFTS_ACTIVE_DIR", active)
    return active


def _write(path: Path, body: str = "content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_empty_dir_returns_empty(active_dir: Path) -> None:
    assert heartbeat.gather_stale_drafts_summary() == ""


def test_old_subdir_draft_reported_via_frontmatter_date(active_dir: Path) -> None:
    _write(
        active_dir / "draft-reply" / "old-reply.md",
        "---\ndate: 2026-01-01\n---\n\nbody\n",
    )
    note = heartbeat.gather_stale_drafts_summary()
    assert "1 active draft(s)" in note
    assert "draft-reply/old-reply.md" in note


def test_filename_date_fallback(active_dir: Path) -> None:
    _write(active_dir / "product-shape" / "2026-01-15_deck-plan.md", "no frontmatter")
    note = heartbeat.gather_stale_drafts_summary()
    assert "2026-01-15_deck-plan.md" in note


def test_research_digests_excluded(active_dir: Path) -> None:
    _write(active_dir / "research" / "ai.md", "---\ndate: 2026-01-01\n---\nliving digest")
    assert heartbeat.gather_stale_drafts_summary() == ""


def test_fresh_draft_not_reported(active_dir: Path) -> None:
    today = now_local().strftime("%Y-%m-%d")
    _write(active_dir / "draft-reply" / f"{today}_fresh.md", f"---\ndate: {today}\n---\nbody")
    assert heartbeat.gather_stale_drafts_summary() == ""


def test_mtime_fallback(active_dir: Path) -> None:
    f = _write(active_dir / "ciso-advisor" / "undated.md", "no dates anywhere")
    old = now_local().timestamp() - 90 * 86400
    os.utime(f, (old, old))
    note = heartbeat.gather_stale_drafts_summary()
    assert "undated.md" in note


def test_context_includes_note_with_no_top_level_drafts(active_dir: Path) -> None:
    """Skill-subfolder drafts surface even when the top level is empty."""
    _write(
        active_dir / "draft-reply" / "old-reply.md",
        "---\ndate: 2026-01-01\n---\n\nbody\n",
    )
    ctx = heartbeat.gather_active_drafts_context()
    assert "No active drafts pending review." in ctx
    assert "older than" in ctx
