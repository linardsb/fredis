"""Tests for the Fredis MCP read-only tools (OB1 Phase 1.1).

Uses a temp SQLite DB + a synthetic vault on tmp_path so the real vault and
production DB are never touched. Embeddings are stubbed to avoid the FastEmbed
model load.
"""

from __future__ import annotations

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
        ("retainers/example.md", "Confidential retainer billing details."),
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
