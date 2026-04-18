"""Tests for the SQLite memory DB backend."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

pytest.importorskip("sqlite_vec")

from db import SQLiteMemoryDB  # noqa: E402


def _seed_chunk(
    db: SQLiteMemoryDB,
    path: str,
    content: str,
    embedding: NDArray[np.float32] | None = None,
    start: int = 1,
    end: int = 1,
    section_title: str = "",
) -> int:
    db.upsert_file(path, content_hash="h", mtime_ns=0, size_bytes=len(content), epoch=0)
    chunk_id = db.insert_chunk(
        file_path=path,
        start_line=start,
        end_line=end,
        section_title=section_title,
        content=content,
        content_hash="c",
        created_at_epoch=0,
    )
    if embedding is not None:
        db.insert_vector(chunk_id, embedding)
    db.commit()
    return chunk_id


def test_init_schema_creates_tables(tmp_path: Path) -> None:
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    conn = db._get_conn()
    names = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
        ).fetchall()
    }
    db.close()

    for required in ("files", "chunks", "meta", "chunks_fts", "vec_chunks"):
        assert required in names, f"missing table: {required}"


def test_upsert_file_roundtrip(tmp_path: Path) -> None:
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    db.upsert_file("a.md", "hash1", 100, 50, 10)
    assert db.get_file_hash("a.md") == "hash1"

    db.upsert_file("a.md", "hash2", 200, 60, 20)
    assert db.get_file_hash("a.md") == "hash2"

    db.close()


def test_insert_chunk_triggers_fts(tmp_path: Path) -> None:
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    _seed_chunk(db, "note.md", "proactive reminder about meetings")

    rows = db.keyword_search("proactive meetings", limit=10)
    db.close()

    assert len(rows) == 1
    assert rows[0]["file_path"] == "note.md"
    assert rows[0]["score"] > 0


def test_insert_vector_and_vector_search(tmp_path: Path) -> None:
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    vec = np.ones(384, dtype=np.float32) * 0.1
    _seed_chunk(db, "note.md", "content", embedding=vec)

    rows = db.vector_search(vec, limit=5)
    db.close()

    assert len(rows) == 1
    assert rows[0]["file_path"] == "note.md"
    # Exact match should score at distance ~0 → score close to 1.0
    assert rows[0]["score"] > 0.99


def test_path_prefix_filter_vector_search(tmp_path: Path) -> None:
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    vec = np.ones(384, dtype=np.float32) * 0.2
    _seed_chunk(db, "drafts/sent/a.md", "reply", embedding=vec)
    _seed_chunk(db, "research/b.md", "paper notes", embedding=vec)

    rows = db.vector_search(vec, limit=5, path_prefix="drafts/sent/")
    db.close()

    assert len(rows) == 1
    assert rows[0]["file_path"] == "drafts/sent/a.md"
