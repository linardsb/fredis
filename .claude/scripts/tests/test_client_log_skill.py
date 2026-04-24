"""Convention tests for the `client-log` skill.

Verifies SKILL.md declares the append + create-new-file + slug-disambiguation
contracts.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_FILE = REPO_ROOT / ".claude" / "skills" / "client-log" / "SKILL.md"
CONVENTION_FILE = REPO_ROOT / ".claude" / "skills" / "_shared" / "draft-path-convention.md"
RETAINERS_DIR = REPO_ROOT / "Fredis" / "Memory" / "retainers"


@pytest.fixture(scope="module")
def skill_text() -> str:
    return SKILL_FILE.read_text(encoding="utf-8")


def test_skill_file_exists() -> None:
    assert SKILL_FILE.is_file()


def test_frontmatter_declares_name(skill_text: str) -> None:
    fm = skill_text[3 : skill_text.index("---", 3)]
    assert "name: client-log" in fm


def test_retainers_directory_exists() -> None:
    # The skill assumes retainers/ already exists. If the vault drifts, the
    # skill's "append only" branch would silently create the folder with an
    # inconsistent shape.
    assert RETAINERS_DIR.is_dir(), (
        f"Expected {RETAINERS_DIR} to exist — client-log appends into it"
    )


def test_append_contract_has_required_fields(skill_text: str) -> None:
    # The append entry shape is the retrieval contract. Drift silently breaks
    # later memory-search entries that rely on structured retainer history.
    for field in ("**Context:**", "**Decisions:**", "**Open items:**", "**Sources:**"):
        assert field in skill_text, f"Append format missing `{field}` section marker"


def test_first_entry_scaffold_has_log_anchor(skill_text: str) -> None:
    # `## Log` is the stable anchor for future appends. If it drifts, future
    # appends land in the wrong place in the file.
    assert "## Log" in skill_text


def test_first_entry_frontmatter_fields_documented(skill_text: str) -> None:
    for key in ("type: retainer", "client:", "lane:", "engaged:", "status:"):
        assert key in skill_text, f"First-entry frontmatter missing `{key}`"


def test_slug_disambiguation_is_documented(skill_text: str) -> None:
    # The skill MUST ask when slug is ambiguous — silent overwrites would merge
    # two clients' records. This is the behavioural contract.
    lowered = skill_text.lower()
    assert "which client" in lowered or "disambiguation" in lowered or "collision" in lowered
    assert "overwrite" in lowered  # explicit "never silently overwrite" clause


def test_create_vs_append_branch_is_documented(skill_text: str) -> None:
    # Three branches: append-to-existing, create-new, ask-on-collision.
    # If any disappears, the skill's behavioural contract narrows silently.
    lowered = skill_text.lower()
    assert "append" in lowered
    assert "new client" in lowered or "create" in lowered


def test_carve_out_referenced(skill_text: str) -> None:
    lowered = skill_text.lower()
    assert "carve-out" in lowered or "exception" in lowered
    # Should point to the shared convention doc.
    assert "_shared/draft-path-convention.md" in skill_text


def test_shared_convention_lists_client_log_carve_out() -> None:
    text = CONVENTION_FILE.read_text(encoding="utf-8")
    assert "client-log" in text
    assert "retainers/" in text


def test_boundary_no_task_dispatch(skill_text: str) -> None:
    lowered = skill_text.lower()
    # Explicitly not dispatching open-items to HubSpot tasks/tickets is part
    # of the advisor-mode boundary. If the skill quietly starts creating
    # tasks, drafts escape.
    assert "hubspot tasks or tickets" in lowered
    assert "never" in lowered
