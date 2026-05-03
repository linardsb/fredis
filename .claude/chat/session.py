"""Session stores for persistent chat conversations (SQLite + Postgres)."""

from __future__ import annotations

import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Session:
    """Represents a chat session tied to a platform thread."""

    session_id: str  # Composite: {platform}:{channel_id}:{thread_id}
    agent_session_id: str  # Claude Agent SDK session ID for resume
    platform: str
    channel_id: str
    thread_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    total_cost_usd: float = 0.0
    status: str = "active"
    # Phase 11.1: when set, chat summaries for this thread write here instead
    # of the channel-routed default. Absolute path string (resolved at
    # override-set time) so process restarts re-hydrate the target unchanged.
    summary_folder_override: str | None = None
    # Phase A (thread-consolidation): per-turn token usage + single-fire
    # nudge flags. ``last_turn_context_tokens`` = ``usage.input_tokens +
    # cache_read_input_tokens + cache_creation_input_tokens`` from the latest
    # ResultMessage — i.e. the *current* attention surface, not a running
    # sum (each turn's input already includes prior turns once the SDK
    # resumes the session). The two ``nudged_*_at`` fields hold ISO
    # timestamps when the soft / hard threshold fired so each fires at most
    # once per thread.
    last_turn_context_tokens: int = 0
    nudged_soft_at: str | None = None
    nudged_hard_at: str | None = None


@dataclass
class HeartbeatThread:
    """Tracks a heartbeat notification posted to Slack so thread replies can start conversations."""

    channel_id: str
    thread_ts: str  # The Slack message ts — becomes the thread_ts for replies
    alert_text: str
    created_at: datetime


class SQLiteSessionStore:
    """Persistent session storage backed by SQLite."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Create the chat_sessions and heartbeat_threads tables if they don't exist."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL UNIQUE,
                    agent_session_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    channel_id TEXT NOT NULL,
                    thread_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    total_cost_usd REAL DEFAULT 0.0,
                    status TEXT DEFAULT 'active',
                    summary_folder_override TEXT,
                    last_turn_context_tokens INTEGER DEFAULT 0,
                    nudged_soft_at TEXT,
                    nudged_hard_at TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_platform_thread
                    ON chat_sessions(platform, channel_id, thread_id);
                CREATE TABLE IF NOT EXISTS heartbeat_threads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    thread_ts TEXT NOT NULL,
                    alert_text TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_hb_channel_thread
                    ON heartbeat_threads(channel_id, thread_ts);
            """)
            # Phase 11.1 + Phase A migrations: add new columns if missing.
            # SQLite has no `ADD COLUMN IF NOT EXISTS`, so inspect schema first.
            cols = {
                row[1]
                for row in conn.execute("PRAGMA table_info(chat_sessions)").fetchall()
            }
            if "summary_folder_override" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN summary_folder_override TEXT"
                )
            if "last_turn_context_tokens" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN "
                    "last_turn_context_tokens INTEGER DEFAULT 0"
                )
            if "nudged_soft_at" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN nudged_soft_at TEXT"
                )
            if "nudged_hard_at" not in cols:
                conn.execute(
                    "ALTER TABLE chat_sessions ADD COLUMN nudged_hard_at TEXT"
                )

    def _row_to_session(self, row: sqlite3.Row) -> Session:
        """Convert a database row to a Session object."""
        # Newer columns may be absent on rows from older clients reading
        # mid-migration — tolerate them on the row view.
        keys = set(row.keys()) if hasattr(row, "keys") else set()
        override = (
            row["summary_folder_override"] if "summary_folder_override" in keys else None
        )
        last_tokens = (
            row["last_turn_context_tokens"]
            if "last_turn_context_tokens" in keys
            else 0
        ) or 0
        soft_at = row["nudged_soft_at"] if "nudged_soft_at" in keys else None
        hard_at = row["nudged_hard_at"] if "nudged_hard_at" in keys else None
        return Session(
            session_id=row["session_id"],
            agent_session_id=row["agent_session_id"],
            platform=row["platform"],
            channel_id=row["channel_id"],
            thread_id=row["thread_id"],
            user_id=row["user_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            message_count=row["message_count"],
            total_cost_usd=row["total_cost_usd"],
            status=row["status"],
            summary_folder_override=override,
            last_turn_context_tokens=int(last_tokens),
            nudged_soft_at=soft_at,
            nudged_hard_at=hard_at,
        )

    def get(self, platform: str, channel_id: str, thread_id: str) -> Session | None:
        """Look up a session by platform, channel, and thread."""
        session_id = f"{platform}:{channel_id}:{thread_id}"
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM chat_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_session(row)

    def create(self, session: Session) -> None:
        """Insert a new session; fall back to update on unique-collision.

        Two messages hitting the same thread inside a single engine turn can
        both see `get()` → None and race into `create()`. SQLite raises
        IntegrityError on the second INSERT; treat that as "another task
        already created it" and update the existing row instead.
        """
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                conn.execute(
                    """INSERT INTO chat_sessions
                       (session_id, agent_session_id, platform, channel_id, thread_id,
                        user_id, created_at, updated_at, message_count, total_cost_usd,
                        status, summary_folder_override,
                        last_turn_context_tokens, nudged_soft_at, nudged_hard_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session.session_id,
                        session.agent_session_id,
                        session.platform,
                        session.channel_id,
                        session.thread_id,
                        session.user_id,
                        session.created_at.isoformat(),
                        session.updated_at.isoformat(),
                        session.message_count,
                        session.total_cost_usd,
                        session.status,
                        session.summary_folder_override,
                        session.last_turn_context_tokens,
                        session.nudged_soft_at,
                        session.nudged_hard_at,
                    ),
                )
        except sqlite3.IntegrityError:
            self.update(session)

    def update(self, session: Session) -> None:
        """Update an existing session's mutable fields."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute(
                """UPDATE chat_sessions
                   SET agent_session_id = ?, updated_at = ?, message_count = ?,
                       total_cost_usd = ?, status = ?, summary_folder_override = ?,
                       last_turn_context_tokens = ?, nudged_soft_at = ?, nudged_hard_at = ?
                   WHERE session_id = ?""",
                (
                    session.agent_session_id,
                    datetime.now().isoformat(),
                    session.message_count,
                    session.total_cost_usd,
                    session.status,
                    session.summary_folder_override,
                    session.last_turn_context_tokens,
                    session.nudged_soft_at,
                    session.nudged_hard_at,
                    session.session_id,
                ),
            )

    def list_active(self, platform: str | None = None) -> list[Session]:
        """List active sessions, optionally filtered by platform."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            if platform:
                rows = conn.execute(
                    "SELECT * FROM chat_sessions WHERE status = 'active' AND platform = ? "
                    "ORDER BY updated_at DESC",
                    (platform,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chat_sessions WHERE status = 'active' ORDER BY updated_at DESC"
                ).fetchall()
            return [self._row_to_session(row) for row in rows]

    def save_heartbeat_thread(self, thread: HeartbeatThread) -> None:
        """Record a heartbeat notification so thread replies can be linked."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO heartbeat_threads
                   (channel_id, thread_ts, alert_text, created_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    thread.channel_id,
                    thread.thread_ts,
                    thread.alert_text,
                    thread.created_at.isoformat(),
                ),
            )

    def get_heartbeat_thread(self, channel_id: str, thread_ts: str) -> HeartbeatThread | None:
        """Look up a heartbeat thread by channel and ts."""
        with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM heartbeat_threads WHERE channel_id = ? AND thread_ts = ?",
                (channel_id, thread_ts),
            ).fetchone()
            if row is None:
                return None
            return HeartbeatThread(
                channel_id=row["channel_id"],
                thread_ts=row["thread_ts"],
                alert_text=row["alert_text"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )


class PostgresSessionStore:
    """Persistent session storage backed by PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        import time

        import psycopg

        self._url = database_url
        timeout = int(os.getenv("PG_CONNECT_TIMEOUT", "5"))

        last_err: Exception | None = None
        for attempt in (1, 2):
            try:
                self._conn = psycopg.connect(
                    database_url, autocommit=True, connect_timeout=timeout
                )
                break
            except psycopg.OperationalError as e:
                last_err = e
                if attempt == 1:
                    time.sleep(1)
        else:
            print(
                f"[PostgresSessionStore] Connect failed after 2 attempts "
                f"(timeout={timeout}s): {last_err}. "
                f"Check the SSH tunnel: `nc -z localhost 5432` on macOS, "
                f"`systemctl status vault-sync.timer` on the VPS.",
                file=sys.stderr,
            )
            sys.exit(1)

        self._init_db()

    def _init_db(self) -> None:
        """Create the chat_sessions and heartbeat_threads tables if they don't exist."""
        cur = self._conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                agent_session_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL,
                message_count INTEGER DEFAULT 0,
                total_cost_usd DOUBLE PRECISION DEFAULT 0.0,
                status TEXT DEFAULT 'active',
                summary_folder_override TEXT,
                last_turn_context_tokens INTEGER DEFAULT 0,
                nudged_soft_at TEXT,
                nudged_hard_at TEXT
            )
        """)
        # Phase 11.1 + Phase A migrations — add new columns on existing
        # deployments too.
        cur.execute("""
            ALTER TABLE chat_sessions
                ADD COLUMN IF NOT EXISTS summary_folder_override TEXT
        """)
        cur.execute("""
            ALTER TABLE chat_sessions
                ADD COLUMN IF NOT EXISTS last_turn_context_tokens INTEGER DEFAULT 0
        """)
        cur.execute("""
            ALTER TABLE chat_sessions
                ADD COLUMN IF NOT EXISTS nudged_soft_at TEXT
        """)
        cur.execute("""
            ALTER TABLE chat_sessions
                ADD COLUMN IF NOT EXISTS nudged_hard_at TEXT
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_platform_thread
                ON chat_sessions(platform, channel_id, thread_id)
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS heartbeat_threads (
                id SERIAL PRIMARY KEY,
                channel_id TEXT NOT NULL,
                thread_ts TEXT NOT NULL,
                alert_text TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
        """)
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_hb_channel_thread
                ON heartbeat_threads(channel_id, thread_ts)
        """)

    def _row_to_session(self, row: tuple[Any, ...]) -> Session:
        """Convert a database row to a Session object.

        Column layout after Phase 11.1 + Phase A migrations:
        ``(id, session_id, agent_session_id, platform, channel_id, thread_id,
        user_id, created_at, updated_at, message_count, total_cost_usd,
        status, summary_folder_override, last_turn_context_tokens,
        nudged_soft_at, nudged_hard_at)``.
        """
        override = row[12] if len(row) > 12 else None
        last_tokens = int(row[13]) if len(row) > 13 and row[13] is not None else 0
        soft_at = row[14] if len(row) > 14 else None
        hard_at = row[15] if len(row) > 15 else None
        return Session(
            session_id=row[1],
            agent_session_id=row[2],
            platform=row[3],
            channel_id=row[4],
            thread_id=row[5],
            user_id=row[6],
            created_at=row[7]
            if isinstance(row[7], datetime)
            else datetime.fromisoformat(str(row[7])),
            updated_at=row[8]
            if isinstance(row[8], datetime)
            else datetime.fromisoformat(str(row[8])),
            message_count=row[9],
            total_cost_usd=float(row[10]),
            status=row[11],
            summary_folder_override=override,
            last_turn_context_tokens=last_tokens,
            nudged_soft_at=soft_at,
            nudged_hard_at=hard_at,
        )

    def get(self, platform: str, channel_id: str, thread_id: str) -> Session | None:
        """Look up a session by platform, channel, and thread."""
        session_id = f"{platform}:{channel_id}:{thread_id}"
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM chat_sessions WHERE session_id = %s",
            (session_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return self._row_to_session(row)

    def create(self, session: Session) -> None:
        """Insert a new session; fall back to update on unique-collision."""
        import psycopg

        try:
            cur = self._conn.cursor()
            cur.execute(
                """INSERT INTO chat_sessions
                   (session_id, agent_session_id, platform, channel_id, thread_id,
                    user_id, created_at, updated_at, message_count, total_cost_usd,
                    status, summary_folder_override,
                    last_turn_context_tokens, nudged_soft_at, nudged_hard_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    session.session_id,
                    session.agent_session_id,
                    session.platform,
                    session.channel_id,
                    session.thread_id,
                    session.user_id,
                    session.created_at,
                    session.updated_at,
                    session.message_count,
                    session.total_cost_usd,
                    session.status,
                    session.summary_folder_override,
                    session.last_turn_context_tokens,
                    session.nudged_soft_at,
                    session.nudged_hard_at,
                ),
            )
        except psycopg.errors.UniqueViolation:
            self.update(session)

    def update(self, session: Session) -> None:
        """Update an existing session's mutable fields."""
        cur = self._conn.cursor()
        cur.execute(
            """UPDATE chat_sessions
               SET agent_session_id = %s, updated_at = %s, message_count = %s,
                   total_cost_usd = %s, status = %s, summary_folder_override = %s,
                   last_turn_context_tokens = %s, nudged_soft_at = %s, nudged_hard_at = %s
               WHERE session_id = %s""",
            (
                session.agent_session_id,
                datetime.now(),
                session.message_count,
                session.total_cost_usd,
                session.status,
                session.summary_folder_override,
                session.last_turn_context_tokens,
                session.nudged_soft_at,
                session.nudged_hard_at,
                session.session_id,
            ),
        )

    def list_active(self, platform: str | None = None) -> list[Session]:
        """List active sessions, optionally filtered by platform."""
        cur = self._conn.cursor()
        if platform:
            cur.execute(
                "SELECT * FROM chat_sessions WHERE status = 'active' AND platform = %s "
                "ORDER BY updated_at DESC",
                (platform,),
            )
        else:
            cur.execute(
                "SELECT * FROM chat_sessions WHERE status = 'active' ORDER BY updated_at DESC"
            )
        return [self._row_to_session(row) for row in cur.fetchall()]

    def save_heartbeat_thread(self, thread: HeartbeatThread) -> None:
        """Record a heartbeat notification so thread replies can be linked."""
        cur = self._conn.cursor()
        cur.execute(
            """INSERT INTO heartbeat_threads (channel_id, thread_ts, alert_text, created_at)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (channel_id, thread_ts) DO UPDATE SET
                   alert_text = EXCLUDED.alert_text,
                   created_at = EXCLUDED.created_at""",
            (thread.channel_id, thread.thread_ts, thread.alert_text, thread.created_at),
        )

    def get_heartbeat_thread(self, channel_id: str, thread_ts: str) -> HeartbeatThread | None:
        """Look up a heartbeat thread by channel and ts."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT channel_id, thread_ts, alert_text, created_at FROM heartbeat_threads "
            "WHERE channel_id = %s AND thread_ts = %s",
            (channel_id, thread_ts),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return HeartbeatThread(
            channel_id=row[0],
            thread_ts=row[1],
            alert_text=row[2],
            created_at=row[3]
            if isinstance(row[3], datetime)
            else datetime.fromisoformat(str(row[3])),
        )

    def close(self) -> None:
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()


def get_session_store(
    chat_db_path: Path | None = None,
) -> SQLiteSessionStore | PostgresSessionStore:
    """Factory: returns Postgres if DATABASE_URL is set, else SQLite."""
    url = os.getenv("DATABASE_URL", "")
    if url:
        return PostgresSessionStore(url)
    if chat_db_path is None:
        from config import CHAT_DB_PATH

        chat_db_path = CHAT_DB_PATH
    return SQLiteSessionStore(chat_db_path)
