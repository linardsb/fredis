"""Morning-brief mode wiring."""

from __future__ import annotations

import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-fake-for-tests")
os.environ.setdefault("SLACK_OWNER_USER_ID", "U0OWNER123")

import heartbeat  # noqa: E402,I001  — must follow env overrides


def test_brief_template_shape() -> None:
    tpl = heartbeat.BRIEF_OVERRIDE_TEMPLATE
    assert "MORNING BRIEF OVERRIDE" in tpl
    assert "NEVER return HEARTBEAT_OK" in tpl
    assert "Top 3 today" in tpl
    assert "Priority: NORMAL" in tpl


def test_brief_template_formats_owner() -> None:
    formatted = heartbeat.BRIEF_OVERRIDE_TEMPLATE.format(owner="Linards")
    assert "Linards" in formatted
    assert "{owner}" not in formatted
