"""Tests for the Fredis MCP read-only tools (OB1 Phase 1.1).

Uses a temp SQLite DB + a synthetic vault on tmp_path so the real vault and
production DB are never touched. Embeddings are stubbed to avoid the FastEmbed
model load.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sqlite_vec")

import fredis_mcp_tools as tools  # noqa: E402
from db import SQLiteMemoryDB  # noqa: E402
from secret_patterns import SECRET_PATTERNS  # noqa: E402

USER_MD_BODY = (
    "# USER.md\n\n"
    "Linards Berzins. UK + Latvia. Consultancy, research, and product lanes.\n\n"
    "## Identity\n"
    "Owner: Linards. Birthday: 1990-01-01. Time zone: Europe/London.\n\n"
    "## Service Lines\n"
    "- AI agentic systems\n"
    "- Custom apps\n"
    "- SaaS\n"
    "- Marketing ops\n"
    "- Agri AI\n"
    "- Advisory\n\n"
    "## Geography\n"
    "Bridge angle: UK ↔ LV. Riga + London + Hertford.\n\n"
    "## Integrations\n"
    "- Gmail OAuth via google_token.json\n"
    "- Slack bot at #second-brain\n"
    "- HubSpot CRM (Free tier)\n\n"
    "## Communications\n"
    "Voice: direct, evidence-first, no hedging.\n\n"
    "## Notes\n"
    "Reflect daily. Heartbeats every 2h.\n"
)

# Planted fake secrets — never real. One per pattern category we want covered.
PLANTED_SECRETS = [
    "SLACK_BOT_TOKEN=xoxb-FAKEFAKEFAKEFAKEFAKEFAKE-injected",
    "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE",
    "GITHUB_TOKEN=ghp_FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE",
]


def _seeded_user_md(extra_secret_lines: list[str] | None = None) -> str:
    body = USER_MD_BODY
    if extra_secret_lines:
        body += "\n## Secrets (planted)\n"
        for line in extra_secret_lines:
            body += line + "\n"
    return body


@pytest.fixture
def stub_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_embed(_q: str) -> np.ndarray:
        return np.ones(384, dtype=np.float32) * 0.1

    monkeypatch.setattr("embeddings.embed_text", fake_embed)


@pytest.fixture
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    db_path = tmp_path / "memory.db"
    monkeypatch.setattr("db.DATABASE_URL", "")
    monkeypatch.setattr("db.DATABASE_PATH", db_path)

    db = SQLiteMemoryDB(str(db_path))
    db.init_schema()
    vec = np.ones(384, dtype=np.float32) * 0.1

    rows = [
        ("USER.md", "Linards works with Atis on the Cab application."),
        ("daily/2026-04-26.md", "Atis call: discussed VTV pilot timing."),
        # The unique sentinel lets slice-02 denylist tests assert 0 hits
        # without false positives from the other rows.
        (
            "retainers/example.md",
            "Confidential retainer billing details. DENYTOKEN_TESTSENTINEL_42.",
        ),
    ]
    for path, text in rows:
        db.upsert_file(path, "h", 0, len(text), 0)
        cid = db.insert_chunk(
            file_path=path,
            start_line=1,
            end_line=1,
            section_title="",
            content=text,
            content_hash="c",
            created_at_epoch=0,
        )
        db.insert_vector(cid, vec)
    db.commit()
    db.close()
    return db_path


@pytest.fixture
def fake_vault(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a synthetic Fredis/Memory tree on tmp_path and patch the tool
    module's path constants to point at it."""
    vault = tmp_path / "Memory"
    vault.mkdir()

    soul = vault / "SOUL.md"
    soul.write_text("# SOUL\nName: Fredis. Voice: direct.\n", encoding="utf-8")

    user = vault / "USER.md"
    user.write_text(_seeded_user_md(PLANTED_SECRETS), encoding="utf-8")

    memory = vault / "MEMORY.md"
    memory.write_text(
        "# MEMORY.md\n\n"
        "## Key Decisions\n\n"
        "- **Strategic pivot (2026-04-19).** Build products instead of consult.\n"
        "- **Heartbeat priority-1 whitelist (2026-04-22).** Whitelisted senders.\n"
        "- **Old decision (2020-01-01).** Should be filtered by date window.\n",
        encoding="utf-8",
    )

    daily = vault / "daily"
    daily.mkdir()
    from datetime import date

    today = date.today().isoformat()
    (daily / f"{today}.md").write_text(
        "# Daily log\n\n- We decided to ship Phase 1.1 today.\n"
        "- Random non-decision line about the weather.\n",
        encoding="utf-8",
    )

    drafts = vault / "drafts"
    (drafts / "active" / "draft-reply").mkdir(parents=True)
    (drafts / "active" / "draft-reply" / "2026-04-26_atis.md").write_text(
        "Reply draft body.\n", encoding="utf-8"
    )
    (drafts / "sent").mkdir()
    (drafts / "expired").mkdir()

    # Patch the constants the tools module imported.
    monkeypatch.setattr(tools, "MEMORY_DIR", vault)
    monkeypatch.setattr(tools, "SOUL_FILE", soul)
    monkeypatch.setattr(tools, "USER_FILE", user)
    monkeypatch.setattr(tools, "MEMORY_FILE", memory)
    monkeypatch.setattr(tools, "DAILY_DIR", daily)
    monkeypatch.setattr(tools, "DRAFTS_DIR", drafts)
    return vault


# --------------------------------------------------------------------------- #
# search_memory
# --------------------------------------------------------------------------- #


def test_search_memory_returns_expected_keys(
    seeded_db: Path, stub_embed: None
) -> None:
    out = tools.search_memory("Atis", mode="hybrid", limit=10)
    assert "results" in out
    assert isinstance(out["results"], list)
    assert out["results"], "expected ≥1 hit for 'Atis' against the seeded fixture"
    first = out["results"][0]
    assert {"file_path", "score", "snippet"}.issubset(first.keys())
    # Forward-compat keys from the slice 1.1 contract.
    assert {"start_line", "end_line", "match_type", "section_title"}.issubset(
        first.keys()
    )


def test_search_memory_filter_path_narrows(
    seeded_db: Path, stub_embed: None
) -> None:
    out = tools.search_memory("Atis", mode="keyword", filter_path="daily")
    assert out["results"], "expected at least one daily-scoped hit"
    for r in out["results"]:
        assert r["file_path"].startswith("daily/")


def test_search_memory_filter_type_is_noop(
    seeded_db: Path, stub_embed: None
) -> None:
    """filter_type is reserved for Phase 2c — must accept it without erroring."""
    out = tools.search_memory("Atis", mode="keyword", filter_type="decision")
    assert "results" in out


# --------------------------------------------------------------------------- #
# get_file
# --------------------------------------------------------------------------- #


def test_get_file_reads_vault_relative_path(fake_vault: Path) -> None:
    out = tools.get_file("SOUL.md")
    assert out["content"] is not None
    assert "Fredis" in out["content"]


def test_get_file_rejects_absolute_path(fake_vault: Path) -> None:
    out = tools.get_file("/etc/passwd")
    assert out["content"] is None
    assert out["reason"] == "path not accessible"


def test_get_file_rejects_traversal(fake_vault: Path) -> None:
    out = tools.get_file("../../etc/passwd")
    assert out["content"] is None
    assert out["reason"] == "path not accessible"


def test_get_file_missing_file(fake_vault: Path) -> None:
    out = tools.get_file("does/not/exist.md")
    assert out["content"] is None


# --------------------------------------------------------------------------- #
# list_drafts
# --------------------------------------------------------------------------- #


def test_list_drafts_active(fake_vault: Path) -> None:
    out = tools.list_drafts("active")
    assert "drafts" in out
    assert any(
        d["path"].endswith("2026-04-26_atis.md") for d in out["drafts"]
    )


def test_list_drafts_unknown_status_rejected(fake_vault: Path) -> None:
    out = tools.list_drafts("evil")
    assert out["drafts"] == []
    assert "invalid status" in out["reason"]


def test_list_drafts_empty_sent(fake_vault: Path) -> None:
    out = tools.list_drafts("sent")
    assert out["drafts"] == []


# --------------------------------------------------------------------------- #
# list_recent_decisions
# --------------------------------------------------------------------------- #


def test_list_recent_decisions_pulls_memory_md_and_daily(
    fake_vault: Path,
) -> None:
    out = tools.list_recent_decisions(days=10_000)
    assert out["decisions"], "expected at least one decision pulled from MEMORY.md"
    sources = {d["source"] for d in out["decisions"]}
    assert "MEMORY.md" in sources
    # Each entry must carry the contract keys.
    for d in out["decisions"]:
        assert {"date", "text", "source"}.issubset(d.keys())


def test_list_recent_decisions_filters_by_window(fake_vault: Path) -> None:
    out = tools.list_recent_decisions(days=14)
    dates = [d["date"] for d in out["decisions"]]
    # The 2020 entry must be filtered by a 14-day window.
    assert "2020-01-01" not in dates


def test_list_recent_decisions_picks_up_daily_log_keyword(fake_vault: Path) -> None:
    out = tools.list_recent_decisions(days=1)
    daily_hits = [d for d in out["decisions"] if d["source"].startswith("daily/")]
    assert daily_hits, "expected the 'decided' line in today's daily log"


# --------------------------------------------------------------------------- #
# get_soul_summary
# --------------------------------------------------------------------------- #


def test_get_soul_summary_returns_soul(fake_vault: Path) -> None:
    out = tools.get_soul_summary()
    assert out["soul"] is not None
    assert "Fredis" in out["soul"]


# --------------------------------------------------------------------------- #
# get_user_profile  — the security-critical test
# --------------------------------------------------------------------------- #


def test_get_user_profile_strips_every_planted_secret(fake_vault: Path) -> None:
    out = tools.get_user_profile()
    assert out["profile"] is not None, "fixture body is well above the 200-char floor"
    profile = out["profile"]

    # Hard contract: zero pattern hits in the returned profile.
    for kind, pattern in SECRET_PATTERNS.items():
        assert pattern.search(profile) is None, (
            f"{kind} pattern leaked into get_user_profile() output"
        )

    # Each planted token must be gone.
    for line in PLANTED_SECRETS:
        token = line.split("=", 1)[1]
        assert token not in profile, f"planted secret leaked verbatim: {line!r}"

    # Sanity: legitimate non-secret content is preserved.
    assert "AI agentic systems" in profile
    assert "Linards" in profile


def test_get_user_profile_returns_null_when_nothing_left(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If everything looks like a secret, the stripped body falls under the
    200-char floor and the tool returns null with a generic reason."""
    short = (
        "SLACK_BOT_TOKEN=xoxb-FAKEFAKEFAKEFAKEFAKEFAKE-aaa\n"
        "GITHUB_TOKEN=ghp_FAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKEFAKE\n"
    )
    tools.USER_FILE.write_text(short, encoding="utf-8")
    out = tools.get_user_profile()
    assert out["profile"] is None
    assert out["reason"] == "USER profile is restricted"


# --------------------------------------------------------------------------- #
# index_status
# --------------------------------------------------------------------------- #


def test_index_status_matches_stats_shape(seeded_db: Path) -> None:
    out = tools.index_status()
    for key in ("backend", "model", "files", "chunks", "vectors"):
        assert key in out, f"index_status missing '{key}' (memory_index --stats shape)"
    assert out["files"] >= 1
    assert out["chunks"] >= 1


# --------------------------------------------------------------------------- #
# Slice 1.2 — denylist integration
# --------------------------------------------------------------------------- #


def test_search_memory_drops_denylisted_chunks(
    seeded_db: Path, stub_embed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A chunk whose ``file_path`` falls under a denied prefix must never
    surface, even when its content is the only match for the query."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["retainers/"])
    out = tools.search_memory(
        "DENYTOKEN_TESTSENTINEL_42", mode="keyword", limit=20
    )
    assert out["results"] == [], (
        "denylist must filter out chunks under retainers/, even on direct hit"
    )


def test_search_memory_returns_denylisted_chunk_when_unguarded(
    seeded_db: Path, stub_embed: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sanity: with the denylist disabled, the same query reaches the chunk —
    proves the previous test was stopped by the filter, not by missing data."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", [])
    out = tools.search_memory(
        "DENYTOKEN_TESTSENTINEL_42", mode="keyword", limit=20
    )
    assert any(r["file_path"] == "retainers/example.md" for r in out["results"])


def test_get_file_denylist_input_string(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A request for a path under a denied prefix returns the canonical
    rejection shape — even when the file genuinely exists."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["retainers/"])
    retainers = fake_vault / "retainers"
    retainers.mkdir(exist_ok=True)
    (retainers / "billing.md").write_text("real content\n", encoding="utf-8")

    out = tools.get_file("retainers/billing.md")
    assert out == {
        "path": "retainers/billing.md",
        "content": None,
        "reason": "path not accessible",
    }


def test_get_file_denylist_exact_file_match(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exact-file entry (no trailing /) blocks the file but not its
    extension neighbours — covers the ``USER.md`` denylist semantics."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["USER.md"])

    blocked = tools.get_file("USER.md")
    assert blocked["content"] is None
    assert blocked["reason"] == "path not accessible"

    # Plant a sibling file the entry must NOT cover.
    (fake_vault / "USER.md.bak").write_text("backup\n", encoding="utf-8")
    sibling = tools.get_file("USER.md.bak")
    assert sibling["content"] == "backup\n"


def test_get_file_info_leak_parity(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Denied / denied-but-missing / non-denied-missing must all return
    byte-identical responses (modulo the requested path) so the caller
    cannot discriminate via timing-stable response text."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["retainers/"])
    retainers = fake_vault / "retainers"
    retainers.mkdir(exist_ok=True)
    (retainers / "real.md").write_text("x", encoding="utf-8")

    denied_existing = tools.get_file("retainers/real.md")
    denied_missing = tools.get_file("retainers/never.md")
    missing_not_denied = tools.get_file("does/not/exist.md")

    expected_keys = {"path", "content", "reason"}
    for resp in (denied_existing, denied_missing, missing_not_denied):
        assert set(resp.keys()) == expected_keys
        assert resp["content"] is None
        assert resp["reason"] == "path not accessible"


def test_get_file_soul_md_allowed_under_canonical_denylist(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SOUL.md must remain readable — exposing the persona is the point of
    the MCP server. The canonical shipped denylist must not cover it."""
    monkeypatch.setattr(
        tools,
        "MCP_DENYLIST",
        ["USER.md", "retainers/", "legal/", "investors/"],
    )
    out = tools.get_file("SOUL.md")
    assert out["content"] is not None
    assert "Fredis" in out["content"]


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="symlink creation requires elevated privileges on Windows",
)
def test_get_file_in_vault_symlink_to_denied_target_blocked(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Defence-in-depth: an in-vault symlink whose alias name is *not* on
    the denylist but whose realpath sits under a denied prefix must still
    be rejected. The post-resolve denylist check is what catches this."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["retainers/"])
    retainers = fake_vault / "retainers"
    retainers.mkdir(exist_ok=True)
    secret = retainers / "secret.md"
    secret.write_text("DENYTOKEN_SECRET_LEAK\n", encoding="utf-8")
    alias = fake_vault / "safe_alias.md"
    alias.symlink_to(secret)

    out = tools.get_file("safe_alias.md")
    assert out["content"] is None, "in-vault symlink must not surface denied content"
    assert out["reason"] == "path not accessible"


def test_get_file_traversal_still_rejected_with_denylist(
    fake_vault: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Slice-01 traversal/absolute rejection must still hold — denylist is
    additive defence, not a replacement for ``_resolve_vault_path``."""
    monkeypatch.setattr(tools, "MCP_DENYLIST", ["retainers/"])
    out = tools.get_file("../../etc/passwd")
    assert out["content"] is None
    assert out["reason"] == "path not accessible"


# --------------------------------------------------------------------------- #
# Slice 1.3 — propose_draft (the only write surface)
# --------------------------------------------------------------------------- #


def _vault_snapshot(vault: Path) -> set[Path]:
    """Return the set of every path under the vault — used to assert that a
    rejected call made no filesystem mutation."""
    return set(vault.rglob("*"))


def _read_frontmatter_block(text: str) -> dict[str, str]:
    """Naive YAML-frontmatter parser — splits on ``---`` markers and parses
    each ``key: value`` line. Avoids adding a python-frontmatter dep just for
    these assertions."""
    if not text.startswith("---\n"):
        raise AssertionError("expected file to start with frontmatter marker")
    rest = text[4:]
    end = rest.find("\n---\n")
    if end == -1:
        raise AssertionError("expected closing frontmatter marker")
    block = rest[:end]
    out: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        out[key.strip()] = value.strip()
    return out


def test_propose_draft_happy_path(fake_vault: Path) -> None:
    out = tools.propose_draft(
        source="chatgpt",
        title="Atis Q2 plan",
        body="Two paragraphs about VTV pilot timing.",
        type="idea",
        people=["Atis"],
        projects=["vtv"],
    )
    assert out["ok"] is True
    assert out["path"].startswith("drafts/active/chatgpt/")
    assert out["path"].endswith("_atis-q2-plan.md")

    written = fake_vault / out["path"]
    assert written.is_file(), "draft file must exist on disk"
    text = written.read_text(encoding="utf-8")

    fm = _read_frontmatter_block(text)
    assert fm["type"] == "idea"
    assert fm["source"] == "mcp:chatgpt"
    assert fm["people"] == '["Atis"]'
    assert fm["projects"] == '["vtv"]'
    # ISO-8601 with Z suffix.
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", fm["created"]
    ), f"unexpected created stamp: {fm['created']!r}"

    # Body section after the frontmatter.
    assert "# Atis Q2 plan" in text
    assert "Two paragraphs about VTV pilot timing." in text


def test_propose_draft_invalid_source_makes_no_fs_call(fake_vault: Path) -> None:
    before = _vault_snapshot(fake_vault)
    out = tools.propose_draft(
        source="../../etc",  # type: ignore[arg-type]
        title="malicious",
        body="x",
    )
    assert out == {"ok": False, "error": "invalid source"}
    after = _vault_snapshot(fake_vault)
    assert before == after, (
        "rejected source must not touch the filesystem — "
        f"diff: {(after - before) | (before - after)}"
    )


def test_propose_draft_invalid_type_rejected(fake_vault: Path) -> None:
    out = tools.propose_draft(
        source="chatgpt",
        title="t",
        body="b",
        type="evil-type",  # type: ignore[arg-type]
    )
    assert out == {"ok": False, "error": "invalid type"}


def test_propose_draft_traversal_via_title_lands_in_right_dir(
    fake_vault: Path,
) -> None:
    out = tools.propose_draft(
        source="chatgpt",
        title="../../etc/passwd",
        body="should not escape",
    )
    assert out["ok"] is True

    rel = out["path"]
    # No path traversal artefacts can survive into the slug.
    assert "/.." not in rel
    assert "/etc/" not in rel.replace("drafts/active/", "", 1)
    # The file lands strictly under drafts/active/chatgpt/.
    assert rel.startswith("drafts/active/chatgpt/")

    written = fake_vault / rel
    assert written.is_file()
    # Realpath of the written file must be under realpath of drafts/active/.
    base_real = (fake_vault / "drafts" / "active").resolve()
    assert written.resolve().is_relative_to(base_real)


def test_propose_draft_collision_appends_suffix(fake_vault: Path) -> None:
    first = tools.propose_draft(
        source="chatgpt", title="Collision Test", body="first"
    )
    second = tools.propose_draft(
        source="chatgpt", title="Collision Test", body="second"
    )
    third = tools.propose_draft(
        source="chatgpt", title="Collision Test", body="third"
    )
    assert first["ok"] is True
    assert second["ok"] is True
    assert third["ok"] is True
    assert first["path"] != second["path"]
    assert second["path"] != third["path"]
    assert second["path"].endswith("_2.md")
    assert third["path"].endswith("_3.md")

    # Original is untouched.
    first_text = (fake_vault / first["path"]).read_text(encoding="utf-8")
    assert "first" in first_text
    assert "second" not in first_text


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="symlink creation requires elevated privileges on Windows",
)
def test_propose_draft_rejects_symlinked_destination(
    fake_vault: Path, tmp_path: Path
) -> None:
    """If ``drafts/active/chatgpt/`` is a symlink whose realpath escapes
    drafts/active, the write must fail. The realpath assertion catches this
    before any file is written."""
    evil = tmp_path / "evil"
    evil.mkdir()
    alias = fake_vault / "drafts" / "active" / "chatgpt"
    # The fixture didn't create chatgpt/, so we make the symlink fresh.
    assert not alias.exists()
    alias.symlink_to(evil, target_is_directory=True)

    before_evil = set(evil.iterdir())
    before_drafts = _vault_snapshot(fake_vault / "drafts")

    out = tools.propose_draft(
        source="chatgpt",
        title="symlink probe",
        body="should not land",
    )

    assert out["ok"] is False, (
        "symlinked destination must be rejected — got " + repr(out)
    )
    assert "drafts/active" in out["error"]

    # Nothing landed in the evil dir.
    assert set(evil.iterdir()) == before_evil
    # The drafts subtree change is limited to the symlink itself (already
    # there before the call), no new file under it.
    assert _vault_snapshot(fake_vault / "drafts") == before_drafts


def test_propose_draft_yaml_inline_list_escapes_quotes(fake_vault: Path) -> None:
    out = tools.propose_draft(
        source="cursor",
        title="quote escape",
        body="x",
        people=['Alice "the boss"', "Bob, the famous"],
    )
    assert out["ok"] is True
    text = (fake_vault / out["path"]).read_text(encoding="utf-8")
    fm = _read_frontmatter_block(text)
    # The `people:` line stays a single line with both items intact —
    # commas / quotes inside names did not break the YAML field.
    assert "Alice" in fm["people"]
    assert "Bob" in fm["people"]
    # Embedded double quotes are backslash-escaped, not raw.
    assert '\\"the boss\\"' in fm["people"]


def test_propose_draft_empty_optional_fields(fake_vault: Path) -> None:
    out = tools.propose_draft(
        source="claude-desktop",
        title="t",
        body="b",
    )
    assert out["ok"] is True
    text = (fake_vault / out["path"]).read_text(encoding="utf-8")
    fm = _read_frontmatter_block(text)
    assert fm["people"] == "[]"
    assert fm["projects"] == "[]"
    assert fm["type"] == "draft"
