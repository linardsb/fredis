"""Tests for .claude/chat/session.py — SQLite store + Postgres timeout path."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

# Add the chat dir to sys.path so we can import session
_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))

from session import (  # noqa: E402
    HeartbeatThread,
    PostgresSessionStore,
    Session,
    SQLiteSessionStore,
)


def _make_session(session_id: str = "slack:C1:T1", agent_session_id: str = "agent-1") -> Session:
    now = datetime.now()
    return Session(
        session_id=session_id,
        agent_session_id=agent_session_id,
        platform="slack",
        channel_id="C1",
        thread_id="T1",
        user_id="U1",
        created_at=now,
        updated_at=now,
        message_count=0,
        total_cost_usd=0.0,
        status="active",
    )


# ---------------------------------------------------------------------------
# SQLite — CRUD round-trip + list_active + heartbeat + race fallback
# ---------------------------------------------------------------------------


def test_sqlite_create_get_roundtrip(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "c.db")
    s = _make_session()
    store.create(s)
    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.session_id == "slack:C1:T1"
    assert got.agent_session_id == "agent-1"
    assert got.platform == "slack"
    assert got.user_id == "U1"
    assert got.message_count == 0
    assert got.status == "active"


def test_sqlite_summary_folder_override_roundtrip(tmp_path: Path) -> None:
    """Phase 11.1: override column must round-trip through INSERT and SELECT."""
    store = SQLiteSessionStore(tmp_path / "c.db")
    s = _make_session()
    s.summary_folder_override = "/abs/vault/Fredis/Memory/builds/email-hub"
    store.create(s)

    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.summary_folder_override == "/abs/vault/Fredis/Memory/builds/email-hub"


def test_sqlite_summary_folder_override_default_none(tmp_path: Path) -> None:
    """A session created without an override must read back as None."""
    store = SQLiteSessionStore(tmp_path / "c.db")
    s = _make_session()
    store.create(s)

    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.summary_folder_override is None


def test_sqlite_update_clears_override(tmp_path: Path) -> None:
    """UPDATE must be able to revert the override back to NULL."""
    store = SQLiteSessionStore(tmp_path / "c.db")
    s = _make_session()
    s.summary_folder_override = "/abs/vault/Fredis/Memory/builds/email-hub"
    store.create(s)

    s.summary_folder_override = None
    store.update(s)

    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.summary_folder_override is None


def test_sqlite_migration_idempotent_on_existing_db(tmp_path: Path) -> None:
    """Re-opening a DB that already has the column must be a no-op."""
    path = tmp_path / "c.db"
    store1 = SQLiteSessionStore(path)
    s = _make_session()
    s.summary_folder_override = "/foo"
    store1.create(s)

    # Second open: schema migration should no-op, data intact.
    store2 = SQLiteSessionStore(path)
    got = store2.get("slack", "C1", "T1")
    assert got is not None
    assert got.summary_folder_override == "/foo"


def test_sqlite_update_mutates_fields(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "c.db")
    s = _make_session()
    store.create(s)

    s.agent_session_id = "agent-2"
    s.message_count = 3
    s.total_cost_usd = 0.125
    store.update(s)

    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.agent_session_id == "agent-2"
    assert got.message_count == 3
    assert got.total_cost_usd == pytest.approx(0.125)


def test_sqlite_list_active_filters_and_sorts(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "c.db")
    older = _make_session("slack:C1:T1", "a1")
    older.updated_at = datetime.now() - timedelta(hours=2)
    newer = _make_session("slack:C1:T2", "a2")
    newer.thread_id = "T2"
    newer.updated_at = datetime.now()
    other = _make_session("discord:D1:T1", "a3")
    other.platform = "discord"
    store.create(older)
    store.create(newer)
    store.create(other)

    slack_only = store.list_active(platform="slack")
    assert [s.session_id for s in slack_only] == ["slack:C1:T2", "slack:C1:T1"]

    every = store.list_active()
    assert {s.session_id for s in every} == {
        "slack:C1:T1",
        "slack:C1:T2",
        "discord:D1:T1",
    }


def test_sqlite_heartbeat_roundtrip(tmp_path: Path) -> None:
    store = SQLiteSessionStore(tmp_path / "c.db")
    thread = HeartbeatThread(
        channel_id="C1",
        thread_ts="1700000000.000100",
        alert_text="overdue task: invoice March",
        created_at=datetime.now(),
    )
    store.save_heartbeat_thread(thread)
    got = store.get_heartbeat_thread("C1", "1700000000.000100")
    assert got is not None
    assert got.alert_text == "overdue task: invoice March"
    missing = store.get_heartbeat_thread("C1", "does-not-exist")
    assert missing is None


def test_sqlite_create_race_falls_back_to_update(tmp_path: Path) -> None:
    """Task 2 race fix — duplicate session_id should NOT raise."""
    store = SQLiteSessionStore(tmp_path / "c.db")
    first = _make_session(agent_session_id="agent-first")
    store.create(first)

    # Simulate the racing second task that also sees get() == None
    second = _make_session(agent_session_id="agent-second")
    second.message_count = 5
    store.create(second)  # must not raise

    got = store.get("slack", "C1", "T1")
    assert got is not None
    assert got.agent_session_id == "agent-second"
    assert got.message_count == 5


# ---------------------------------------------------------------------------
# Postgres — startup timeout + retry (Task 3)
# ---------------------------------------------------------------------------


class _FakeOperationalError(Exception):
    """Stand-in for psycopg.OperationalError."""


class _FakePsycopgErrors:
    UniqueViolation = type("UniqueViolation", (Exception,), {})


class _FakePsycopgModule:
    OperationalError = _FakeOperationalError
    errors = _FakePsycopgErrors


def _install_fake_psycopg(monkeypatch: pytest.MonkeyPatch, connect: Any) -> None:
    fake = _FakePsycopgModule()
    fake.connect = connect  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "psycopg", fake)


def test_postgres_connect_succeeds_on_first_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connect_calls: list[dict[str, Any]] = []

    class _FakeConn:
        def cursor(self) -> Any:
            class _Cur:
                def execute(self, *_a: Any, **_k: Any) -> None:
                    return None

            return _Cur()

    def fake_connect(url: str, **kw: Any) -> _FakeConn:
        connect_calls.append(kw)
        return _FakeConn()

    _install_fake_psycopg(monkeypatch, fake_connect)

    store = PostgresSessionStore("postgres://test")
    assert isinstance(store._conn, _FakeConn)
    assert len(connect_calls) == 1
    assert connect_calls[0]["connect_timeout"] == 5
    assert connect_calls[0]["autocommit"] is True


def test_postgres_connect_retries_once_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attempts = {"n": 0}

    class _FakeConn:
        def cursor(self) -> Any:
            class _Cur:
                def execute(self, *_a: Any, **_k: Any) -> None:
                    return None

            return _Cur()

    def fake_connect(url: str, **kw: Any) -> _FakeConn:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise _FakeOperationalError("tunnel down")
        return _FakeConn()

    _install_fake_psycopg(monkeypatch, fake_connect)
    # Skip the 1-second sleep
    import time as _time

    monkeypatch.setattr(_time, "sleep", lambda _s: None)

    store = PostgresSessionStore("postgres://test")
    assert attempts["n"] == 2
    assert isinstance(store._conn, _FakeConn)


def test_postgres_connect_fails_after_two_attempts(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    attempts = {"n": 0}

    def fake_connect(url: str, **kw: Any) -> Any:
        attempts["n"] += 1
        raise _FakeOperationalError("timeout")

    _install_fake_psycopg(monkeypatch, fake_connect)
    import time as _time

    monkeypatch.setattr(_time, "sleep", lambda _s: None)

    with pytest.raises(SystemExit) as exc_info:
        PostgresSessionStore("postgres://test")

    assert exc_info.value.code == 1
    assert attempts["n"] == 2
    captured = capsys.readouterr()
    assert "Connect failed" in captured.err
    assert "nc -z localhost 5432" in captured.err


def test_postgres_respects_pg_connect_timeout_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_kw: dict[str, Any] = {}

    class _FakeConn:
        def cursor(self) -> Any:
            class _Cur:
                def execute(self, *_a: Any, **_k: Any) -> None:
                    return None

            return _Cur()

    def fake_connect(url: str, **kw: Any) -> _FakeConn:
        captured_kw.update(kw)
        return _FakeConn()

    _install_fake_psycopg(monkeypatch, fake_connect)
    monkeypatch.setenv("PG_CONNECT_TIMEOUT", "12")

    PostgresSessionStore("postgres://test")
    assert captured_kw["connect_timeout"] == 12
