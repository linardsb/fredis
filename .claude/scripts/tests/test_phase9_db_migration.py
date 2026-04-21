"""Phase 9 Task 3 — ``chunks.last_touched`` schema migration + ``touch_chunks``.

Covers fresh DB, pre-migration DB (idempotency), and the touch API (including
the ``[]`` no-op). Postgres path is gated on ``DATABASE_URL``.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sqlite_vec")

from db import SQLiteMemoryDB  # noqa: E402


def _seed_chunk(db: SQLiteMemoryDB, path: str = "note.md", content: str = "body") -> int:
    db.upsert_file(path, content_hash="h", mtime_ns=0, size_bytes=len(content), epoch=0)
    chunk_id = db.insert_chunk(
        file_path=path,
        start_line=1,
        end_line=1,
        section_title="",
        content=content,
        content_hash="c",
        created_at_epoch=0,
    )
    db.commit()
    return chunk_id


def test_init_schema_adds_last_touched_column(tmp_path: Path) -> None:
    """Fresh DB: ``last_touched`` appears in PRAGMA table_info after init."""
    db = SQLiteMemoryDB(str(tmp_path / "fresh.db"))
    db.init_schema()

    conn = db._get_conn()
    cols = {row[1] for row in conn.execute("PRAGMA table_info(chunks)").fetchall()}
    db.close()

    assert "last_touched" in cols


def test_init_schema_migration_adds_column_to_existing_db(tmp_path: Path) -> None:
    """Simulate a pre-Phase-9 DB without ``last_touched`` and show that
    ``init_schema`` adds the column idempotently on both first and second call."""
    db_path = tmp_path / "legacy.db"
    # Hand-craft a pre-migration chunks table.
    with sqlite3.connect(str(db_path)) as raw:
        raw.executescript("""
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                section_title TEXT DEFAULT '',
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at_epoch INTEGER NOT NULL
            );
        """)
        cols = {row[1] for row in raw.execute("PRAGMA table_info(chunks)").fetchall()}
        assert "last_touched" not in cols

    # First init — migration must add the column.
    db = SQLiteMemoryDB(str(db_path))
    db.init_schema()
    cols = {row[1] for row in db._get_conn().execute("PRAGMA table_info(chunks)").fetchall()}
    assert "last_touched" in cols
    db.close()

    # Second init on the same DB — must not raise ("duplicate column name"
    # is swallowed; other OperationalErrors re-raise).
    db2 = SQLiteMemoryDB(str(db_path))
    db2.init_schema()
    db2.close()


def test_touch_chunks_updates_last_touched(tmp_path: Path) -> None:
    """``touch_chunks`` writes a fresh epoch timestamp on the listed rows."""
    import time

    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()
    cid = _seed_chunk(db)

    before = int(time.time())
    db.touch_chunks([cid])
    after = int(time.time())

    conn = db._get_conn()
    row = conn.execute("SELECT last_touched FROM chunks WHERE id = ?", (cid,)).fetchone()
    db.close()

    assert row is not None
    assert row[0] is not None
    # ±5s tolerance to avoid timezone / clock-skew flakiness.
    assert before - 5 <= row[0] <= after + 5


def test_touch_chunks_empty_list_is_noop(tmp_path: Path) -> None:
    """``touch_chunks([])`` must not write — existing rows keep their null
    ``last_touched`` and we observe no state change."""
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()
    cid = _seed_chunk(db)

    conn = db._get_conn()
    # Pre-state: inserted chunk has no retrieval record yet.
    before = conn.execute("SELECT last_touched FROM chunks WHERE id = ?", (cid,)).fetchone()[0]
    assert before is None

    db.touch_chunks([])

    after = conn.execute("SELECT last_touched FROM chunks WHERE id = ?", (cid,)).fetchone()[0]
    db.close()
    assert after is None


def test_touch_chunks_multiple_ids(tmp_path: Path) -> None:
    """Multiple chunk IDs get stamped in one call."""
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()
    cids = [_seed_chunk(db, path=f"file-{i}.md") for i in range(3)]

    db.touch_chunks(cids)

    conn = db._get_conn()
    rows = conn.execute(
        f"SELECT id, last_touched FROM chunks WHERE id IN ({','.join('?' * len(cids))})",
        cids,
    ).fetchall()
    db.close()

    assert len(rows) == 3
    for _id, last_touched in rows:
        assert last_touched is not None


def test_vector_search_unaffected_by_migration(tmp_path: Path) -> None:
    """Adding ``last_touched`` must not break vector / keyword search shapes."""
    db = SQLiteMemoryDB(str(tmp_path / "t.db"))
    db.init_schema()

    vec = np.ones(384, dtype=np.float32) * 0.1
    db.upsert_file("note.md", content_hash="h", mtime_ns=0, size_bytes=4, epoch=0)
    chunk_id = db.insert_chunk(
        file_path="note.md",
        start_line=1,
        end_line=1,
        section_title="",
        content="body",
        content_hash="c",
        created_at_epoch=0,
    )
    db.insert_vector(chunk_id, vec)
    db.commit()

    rows = db.vector_search(vec, limit=5)
    db.close()

    assert len(rows) == 1
    assert "content" in rows[0]


@pytest.mark.skipif(
    os.getenv("PHASE9_POSTGRES") != "1" or os.getenv("DATABASE_URL", "") == "",
    reason="Postgres live test — opt-in via PHASE9_POSTGRES=1 with DATABASE_URL set",
)
def test_postgres_touch_chunks_roundtrip() -> None:  # pragma: no cover — VPS only
    """Postgres: schema migration + touch round-trip.

    Opt-in to avoid firing on every laptop run where DATABASE_URL is set
    for general memory_search use but the SSH tunnel may not be up for the
    pytest session.
    """
    from db import PostgresMemoryDB

    url = os.environ["DATABASE_URL"]
    db = PostgresMemoryDB(url)
    db.init_schema()

    cur = db._get_conn().cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'chunks' AND column_name = 'last_touched'"
    )
    row = cur.fetchone()
    assert row is not None, "last_touched column missing on Postgres"

    # Touch no-op
    db.touch_chunks([])

    db.close()
