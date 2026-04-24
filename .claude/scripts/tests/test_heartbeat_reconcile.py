"""End-to-end tests for heartbeat.reconcile_active_drafts — email + slack paths."""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-fake-for-tests")
os.environ.setdefault("SLACK_OWNER_USER_ID", "U0OWNER123")

import heartbeat  # noqa: E402,I001  — must follow env overrides


# =============================================================================
# Fixtures
# =============================================================================


def _write_draft(
    path: Path,
    *,
    draft_type: str,
    source_id: str,
    created: str = "2026-04-23",
    recipient: str = "atis@example.com",
) -> Path:
    """Write a minimal draft file with the frontmatter reconcile_active_drafts reads."""
    body = f"""---
skill: draft-reply
lane: cab
created: {created}
status: active
type: {draft_type}
source_id: {source_id}
recipient: {recipient}
---

# Reply draft

## Draft Reply

Some draft content.
"""
    path.write_text(body, encoding="utf-8")
    return path


@pytest.fixture
def reconcile_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    active = tmp_path / "active"
    sent = tmp_path / "sent"
    active.mkdir()
    sent.mkdir()
    monkeypatch.setattr(heartbeat, "DRAFTS_ACTIVE_DIR", active)
    monkeypatch.setattr(heartbeat, "DRAFTS_SENT_DIR", sent)
    return active, sent


# =============================================================================
# _iso_date_to_unix
# =============================================================================


def test_iso_date_to_unix_converts_valid_date() -> None:
    ts = heartbeat._iso_date_to_unix("2026-04-23")
    # 2026-04-23 UTC midnight = 1777334400
    expected = datetime(2026, 4, 23, tzinfo=UTC).timestamp()
    assert ts == expected


def test_iso_date_to_unix_returns_zero_on_malformed_input() -> None:
    assert heartbeat._iso_date_to_unix("not-a-date") == 0.0
    assert heartbeat._iso_date_to_unix("") == 0.0


# =============================================================================
# reconcile_active_drafts — slack path
# =============================================================================


def test_slack_draft_moved_to_sent_on_owner_reply(
    reconcile_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, sent = reconcile_dirs
    draft = _write_draft(
        active / "2026-04-23-slack-atis-cab.md",
        draft_type="slack",
        source_id="C01234ABCD:1713880000.0",
    )

    from integrations import slack_api

    monkeypatch.setattr(
        slack_api,
        "check_owner_reply_in_thread",
        lambda source_id, after_unix_ts: "pushing Q3 to next week",
    )

    summary = heartbeat.reconcile_active_drafts()

    assert not draft.exists(), "draft should have been moved out of active/"
    moved = sent / draft.name
    assert moved.exists(), "draft should now live in sent/"

    content = moved.read_text(encoding="utf-8")
    assert "status: sent" in content
    assert "## Actual Reply" in content
    assert "pushing Q3 to next week" in content

    assert "1 slack draft" in summary
    assert "C01234ABCD" in summary


def test_slack_draft_unchanged_when_no_reply(
    reconcile_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, sent = reconcile_dirs
    draft = _write_draft(
        active / "2026-04-23-slack-no-reply.md",
        draft_type="slack",
        source_id="C01234ABCD:1713880000.0",
    )

    from integrations import slack_api

    monkeypatch.setattr(
        slack_api,
        "check_owner_reply_in_thread",
        lambda source_id, after_unix_ts: None,
    )

    summary = heartbeat.reconcile_active_drafts()

    assert draft.exists(), "draft should stay in active/"
    assert not (sent / draft.name).exists()
    assert "no replies detected" in summary


def test_slack_reconcile_handles_api_error_gracefully(
    reconcile_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A Slack API error on one draft shouldn't blow up the whole reconcile run."""
    active, sent = reconcile_dirs
    failing = _write_draft(
        active / "2026-04-23-slack-broken.md",
        draft_type="slack",
        source_id="C01234ABCD:1713880000.0",
    )

    from integrations import slack_api

    def blow_up(source_id: str, after_unix_ts: float) -> str | None:
        raise RuntimeError("slack API blew up")

    monkeypatch.setattr(slack_api, "check_owner_reply_in_thread", blow_up)

    summary = heartbeat.reconcile_active_drafts()

    assert failing.exists(), "failing draft should stay in active/"
    assert "no replies detected" in summary


# =============================================================================
# reconcile_active_drafts — mixed types
# =============================================================================


def test_mixed_email_and_slack_drafts_reconcile_independently(
    reconcile_dirs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    active, sent = reconcile_dirs
    email_draft = _write_draft(
        active / "2026-04-23-email-atis.md",
        draft_type="email",
        source_id="thread-id-123",
    )
    slack_draft = _write_draft(
        active / "2026-04-23-slack-atis.md",
        draft_type="slack",
        source_id="C01234ABCD:1713880000.0",
    )

    from integrations import gmail, slack_api

    monkeypatch.setattr(gmail, "check_sent_reply", lambda tid, ts: "my email reply")
    monkeypatch.setattr(gmail, "get_thread_id", lambda mid: mid)
    monkeypatch.setattr(
        slack_api,
        "check_owner_reply_in_thread",
        lambda source_id, after_unix_ts: "my slack reply",
    )

    summary = heartbeat.reconcile_active_drafts()

    assert not email_draft.exists()
    assert not slack_draft.exists()
    assert (sent / email_draft.name).exists()
    assert (sent / slack_draft.name).exists()
    assert "1 email draft" in summary
    assert "1 slack draft" in summary


# =============================================================================
# reconcile_active_drafts — empty / skip conditions
# =============================================================================


def test_reconcile_skips_drafts_missing_type_or_source_id(
    reconcile_dirs: tuple[Path, Path],
) -> None:
    active, _sent = reconcile_dirs
    # No type field
    (active / "2026-04-23-broken.md").write_text(
        "---\nstatus: active\nsource_id: foo\n---\n\nBody",
        encoding="utf-8",
    )
    # No source_id field
    (active / "2026-04-23-broken-2.md").write_text(
        "---\nstatus: active\ntype: slack\n---\n\nBody",
        encoding="utf-8",
    )

    summary = heartbeat.reconcile_active_drafts()
    assert "no replies detected" in summary or "No drafts" in summary


def test_reconcile_returns_helpful_message_when_active_dir_empty(
    reconcile_dirs: tuple[Path, Path],
) -> None:
    summary = heartbeat.reconcile_active_drafts()
    assert "No active drafts" in summary or "no replies detected" in summary
