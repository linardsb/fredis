"""Tests for the search layer (keyword / semantic / hybrid + priors)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sqlite_vec")

from db import SQLiteMemoryDB  # noqa: E402
from memory_search import search_hybrid, search_keyword, search_semantic  # noqa: E402


@pytest.fixture
def stub_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid loading FastEmbed by returning a fixed vector."""

    def fake_embed(q: str) -> np.ndarray:
        return np.ones(384, dtype=np.float32) * 0.1

    monkeypatch.setattr("embeddings.embed_text", fake_embed)


@pytest.fixture
def seeded_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point `get_memory_db()` at a tmp SQLite file and pre-seed it."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("db.DATABASE_URL", "")
    monkeypatch.setattr("db.DATABASE_PATH", db_path)

    db = SQLiteMemoryDB(str(db_path))
    db.init_schema()

    vec = np.ones(384, dtype=np.float32) * 0.1

    for path, text in [
        ("drafts/sent/a.md", "client reply draft voice"),
        ("research/b.md", "client reply draft voice"),
    ]:
        db.upsert_file(path, "h", 0, len(text), 0)
        chunk_id = db.insert_chunk(
            file_path=path,
            start_line=1,
            end_line=1,
            section_title="",
            content=text,
            content_hash="c",
            created_at_epoch=0,
        )
        db.insert_vector(chunk_id, vec)

    db.commit()
    db.close()
    return db_path


def test_search_empty_query_returns_empty() -> None:
    for q in ("", "   "):
        assert search_keyword(q) == []
        assert search_semantic(q) == []
        assert search_hybrid(q) == []


def test_path_prefix_narrows_results(seeded_db: Path) -> None:
    results = search_keyword("client reply", path_prefix="drafts/sent")
    assert len(results) == 1
    assert results[0].path.startswith("drafts/sent/")


def test_hybrid_merge_key_dedups(seeded_db: Path, stub_embed: None) -> None:
    # Both keyword + semantic hit the same chunks → one merged row per chunk.
    results = search_hybrid("client reply", limit=10, min_score=0.0)
    keys = {(r.path, r.start_line, r.end_line) for r in results}
    assert len(keys) == len(results)


def test_prior_boost_reorders_results(seeded_db: Path, stub_embed: None) -> None:
    results = search_hybrid("client reply", limit=10, min_score=0.0)
    assert len(results) == 2
    # drafts/sent/ gets a 1.5× multiplier → must rank first.
    assert results[0].path.startswith("drafts/sent/")
    assert results[1].path.startswith("research/")
    assert results[0].score > results[1].score
    # Explicit: with identical content + vector, raw scores should match, so
    # priors alone must account for the ordering.
    drafts_raw = results[0].score / 1.5
    research_raw = results[1].score / 1.0
    assert abs(drafts_raw - research_raw) < 1e-6


def test_min_score_filters_below_threshold(seeded_db: Path, stub_embed: None) -> None:
    results = search_hybrid("client reply", limit=10, min_score=99.0)
    assert results == []


def test_prior_longest_prefix_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """Overlapping prefixes: the most specific match wins regardless of dict order."""
    import memory_search

    monkeypatch.setattr(
        memory_search,
        "_SORTED_PATH_PRIORS",
        tuple(
            sorted(
                {"drafts/": 1.2, "drafts/sent/": 1.5}.items(),
                key=lambda kv: -len(kv[0]),
            )
        ),
    )
    assert memory_search._prior("drafts/sent/a.md") == 1.5
    assert memory_search._prior("drafts/active/b.md") == 1.2
    assert memory_search._prior("research/c.md") == 1.0
