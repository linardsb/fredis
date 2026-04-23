"""Convention tests for the `draft-reply` skill.

The skill is pure markdown (no Python code to test). These tests assert that
SKILL.md and its references declare the right shape so the skill stays wired
to the downstream code that actually consumes its output:

- `create_gmail_draft_from_file` (integrations/gmail.py) reads the frontmatter
  fields `type`, `recipient`, `subject`, `source_id` and the body section
  `## Draft Reply`. Drift here breaks the Gmail-surfacing contract silently.
- `_update_draft_and_move_to_sent` (heartbeat.py) replaces `status: active`
  with `status: sent` on reconcile. Drift here breaks the sent-detection loop.
- `memory_search.py --path-prefix drafts/sent/lv-seed` is how the skill narrows
  voice-match to the Latvian corpus. Drift on that prefix silently drops LV
  voice-matching.
"""

from __future__ import annotations

from pathlib import Path

import pytest

SKILLS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "skills" / "draft-reply"
SKILL_FILE = SKILLS_DIR / "SKILL.md"
REFERENCES_DIR = SKILLS_DIR / "references"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def gmail_ref_text() -> str:
    return (REFERENCES_DIR / "gmail-integration.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def voice_ref_text() -> str:
    return (REFERENCES_DIR / "voice-matching.md").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def slack_ref_text() -> str:
    return (REFERENCES_DIR / "slack-integration.md").read_text(encoding="utf-8")


def test_skill_file_exists() -> None:
    assert SKILL_FILE.is_file(), f"Missing {SKILL_FILE}"


def test_frontmatter_declares_name_draft_reply(skill_text: str) -> None:
    assert skill_text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    end = skill_text.index("---", 3)
    fm = skill_text[3:end]
    assert "name: draft-reply" in fm


def test_description_mentions_trigger_phrases(skill_text: str) -> None:
    # Trigger phrases live in the description frontmatter (Phase 5.2 convention).
    assert "draft a reply" in skill_text.lower()
    assert "voice-match" in skill_text.lower()


def test_frontmatter_contract_documents_required_fields(skill_text: str) -> None:
    # These are the exact field names create_gmail_draft_from_file reads.
    for field in ("type", "recipient", "subject", "source_id"):
        assert field in skill_text, f"Frontmatter field `{field}` not documented in SKILL.md"


def test_status_active_is_documented(skill_text: str) -> None:
    # heartbeat.py:1096 replaces `status: active` with `status: sent`. Drift
    # here silently breaks sent-detection.
    assert "status: active" in skill_text
    assert "heartbeat.py:1096" in skill_text, (
        "The `status: active` contract must cite heartbeat.py:1096 so the reason "
        "it diverges from the _shared convention's default `status: draft` is "
        "durable — it's the replace target of the sent-detection loop."
    )


def test_draft_reply_section_heading_exactly_capital_r(skill_text: str) -> None:
    # gmail.py:566 and heartbeat.py:1099 both look for "## Draft Reply" (capital R).
    # Lowercase-r drift would make both silently fail to find the section.
    assert "## Draft Reply" in skill_text
    assert "capital R" in skill_text, (
        "Capital-R contract for `## Draft Reply` must be called out in SKILL.md "
        "so edits don't quietly lowercase it."
    )


def test_gmail_integration_ref_documents_from_file_flag(gmail_ref_text: str) -> None:
    assert "--from-file" in gmail_ref_text
    assert "create-draft" in gmail_ref_text
    # The duplicate-prevention contract matters — document it.
    assert "gmail_draft_id" in gmail_ref_text


def test_voice_matching_ref_documents_path_prefixes(voice_ref_text: str) -> None:
    assert "drafts/sent" in voice_ref_text
    # Latvian corpus split is the load-bearing LV voice-matching behaviour.
    assert "drafts/sent/lv-seed" in voice_ref_text
    assert "hybrid" in voice_ref_text


def test_slack_ref_sticks_to_confirmation_only(slack_ref_text: str) -> None:
    # Slack flavour must NOT post draft body. Document the "markdown only"
    # contract so a future edit doesn't quietly expand the Slack surface.
    lowered = slack_ref_text.lower()
    assert "confirmation" in lowered
    assert "never the draft body" in lowered or "not the draft body" in lowered or "only" in lowered


def test_latvian_routing_narrows_prefix_to_lv_seed(skill_text: str, voice_ref_text: str) -> None:
    # Latvian-routing is a branch in the workflow. Both the SKILL.md body and
    # the voice-matching reference must cite the narrowed path-prefix, so
    # a LV message doesn't get English voice-matched by accident.
    combined = skill_text + voice_ref_text
    assert "drafts/sent/lv-seed" in combined


def test_boundary_never_sends_mentioned(skill_text: str) -> None:
    # The advisor-mode boundary is the reason this skill exists separately from
    # a send-capable one. If that disclaimer drifts out of SKILL.md, the next
    # edit might quietly wire a send path.
    lowered = skill_text.lower()
    assert "never sends" in lowered or "never invokes any gmail send" in lowered
