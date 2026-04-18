"""Tests for chunk_markdown + sync_index orchestration."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("sqlite_vec")

from memory_index import chunk_markdown, sync_index  # noqa: E402


def test_chunk_empty_returns_empty_list() -> None:
    assert chunk_markdown("") == []


def test_chunk_single_line_returns_one_chunk() -> None:
    chunks = chunk_markdown("hello world")
    assert len(chunks) == 1
    assert chunks[0].content == "hello world"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 1


def test_chunk_tracks_section_title() -> None:
    chunks = chunk_markdown("# Heading\n\nsome body text")
    assert len(chunks) >= 1
    assert chunks[0].section_title == "Heading"


def test_chunk_overlap() -> None:
    # Force multiple chunks with a small max_tokens.
    lines = [f"line {i} with enough chars to fill quickly" for i in range(40)]
    content = "\n".join(lines)
    chunks = chunk_markdown(content, max_tokens=20, overlap_tokens=5)
    assert len(chunks) >= 2
    # Second chunk should start somewhere inside the first chunk's line range.
    assert chunks[1].start_line <= chunks[0].end_line
    # Each chunk spans at least one line.
    for c in chunks:
        assert c.end_line >= c.start_line


def test_chunk_content_hash_deterministic() -> None:
    a = chunk_markdown("same content here\nsecond line")
    b = chunk_markdown("same content here\nsecond line")
    assert a[0].content_hash == b[0].content_hash


def test_sync_index_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Force SQLite backend + isolate DB to tmp_path
    monkeypatch.setattr("db.DATABASE_URL", "")
    monkeypatch.setattr("db.DATABASE_PATH", tmp_path / "test.db")

    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "a.md").write_text("# A\n\ncontent A", encoding="utf-8")
    (memory_dir / "b.md").write_text("# B\n\ncontent B", encoding="utf-8")

    first = sync_index(memory_dir=memory_dir, generate_embeddings=False)
    assert first["files_indexed"] == 2
    assert first["files_skipped"] == 0

    second = sync_index(memory_dir=memory_dir, generate_embeddings=False)
    assert second["files_indexed"] == 0
    assert second["files_skipped"] == 2
