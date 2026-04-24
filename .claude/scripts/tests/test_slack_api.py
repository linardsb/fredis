"""Tests for integrations.slack_api — owner-reply thread detection."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["SLACK_BOT_TOKEN"] = "xoxb-fake-for-unit-tests"
os.environ["SLACK_OWNER_USER_ID"] = "U0OWNER123"

import config as _config  # noqa: E402 — must follow os.environ override
import integrations.slack_api as slack_api  # noqa: E402

importlib.reload(_config)
importlib.reload(slack_api)


def _msg(
    user: str,
    ts: str,
    text: str = "reply body",
    subtype: str | None = None,
) -> dict[str, Any]:
    """Build a Slack API message dict shaped like conversations.replies returns."""
    m: dict[str, Any] = {"user": user, "ts": ts, "text": text}
    if subtype:
        m["subtype"] = subtype
    return m


def _mock_client(messages: list[dict[str, Any]]) -> MagicMock:
    """Return a mocked WebClient whose conversations_replies yields given messages."""
    client = MagicMock()
    client.conversations_replies.return_value = {"messages": messages}
    return client


# =============================================================================
# check_owner_reply_in_thread
# =============================================================================


def test_returns_owner_reply_text_posted_after_draft() -> None:
    messages = [
        _msg(user="U0OWNER123", ts="1713880000.0"),  # the thread parent
        _msg(user="UOTHER", ts="1713880500.0", text="some other reply"),
        _msg(user="U0OWNER123", ts="1713881000.0", text="here's my actual reply"),
    ]
    with patch.object(slack_api, "get_slack_client", return_value=_mock_client(messages)):
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713880000.0",
            after_unix_ts=1713880001.0,  # after thread parent, before owner reply
        )
    assert result == "here's my actual reply"


def test_returns_none_when_owner_never_replied() -> None:
    messages = [
        _msg(user="U0OWNER123", ts="1713880000.0"),  # thread parent
        _msg(user="UOTHER", ts="1713881000.0", text="reply from someone else"),
    ]
    with patch.object(slack_api, "get_slack_client", return_value=_mock_client(messages)):
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713880000.0",
            after_unix_ts=1713880001.0,
        )
    assert result is None


def test_skips_owner_replies_that_predate_draft() -> None:
    messages = [
        # Owner posted twice before the draft was created, once after.
        _msg(user="U0OWNER123", ts="1713879000.0", text="before draft"),
        _msg(user="U0OWNER123", ts="1713880000.0", text="also before"),
        _msg(user="U0OWNER123", ts="1713900000.0", text="after draft"),
    ]
    with patch.object(slack_api, "get_slack_client", return_value=_mock_client(messages)):
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713879000.0",
            after_unix_ts=1713881000.0,
        )
    assert result == "after draft"


def test_skips_bot_messages_and_empty_text() -> None:
    messages = [
        _msg(user="U0OWNER123", ts="1713881000.0", text="", subtype="bot_message"),
        _msg(user="U0OWNER123", ts="1713882000.0", text="   "),  # whitespace-only
        _msg(user="U0OWNER123", ts="1713883000.0", text="real reply"),
    ]
    with patch.object(slack_api, "get_slack_client", return_value=_mock_client(messages)):
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713880000.0",
            after_unix_ts=1713880001.0,
        )
    assert result == "real reply"


def test_returns_none_on_malformed_source_id() -> None:
    with patch.object(slack_api, "get_slack_client") as mock_get:
        # No colon → parser bails before ever calling Slack
        result = slack_api.check_owner_reply_in_thread(
            source_id="not-a-valid-source-id",
            after_unix_ts=0.0,
        )
    assert result is None
    mock_get.assert_not_called()


def test_returns_none_when_owner_id_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(slack_api, "SLACK_OWNER_USER_ID", "")
    with patch.object(slack_api, "get_slack_client") as mock_get:
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713880000.0",
            after_unix_ts=0.0,
        )
    assert result is None
    mock_get.assert_not_called()


def test_raises_on_not_in_channel() -> None:
    err = Exception("not_in_channel")
    err.response = {"error": "not_in_channel"}  # type: ignore[attr-defined]

    client = MagicMock()
    client.conversations_replies.side_effect = err

    with patch.object(slack_api, "get_slack_client", return_value=client):
        with pytest.raises(slack_api.SlackChannelNotJoinedError) as exc:
            slack_api.check_owner_reply_in_thread(
                source_id="C01234ABCD:1713880000.0",
                after_unix_ts=0.0,
            )
    assert exc.value.channel_id == "C01234ABCD"


def test_returns_none_on_other_slack_errors(capsys: pytest.CaptureFixture[str]) -> None:
    client = MagicMock()
    client.conversations_replies.side_effect = Exception("channel_not_found")

    with patch.object(slack_api, "get_slack_client", return_value=client):
        result = slack_api.check_owner_reply_in_thread(
            source_id="C01234ABCD:1713880000.0",
            after_unix_ts=0.0,
        )
    assert result is None
    captured = capsys.readouterr()
    assert "Error fetching thread replies" in captured.out
