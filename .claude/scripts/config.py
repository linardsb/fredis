"""
Configuration for the Second Brain heartbeat system.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

# Load environment variables from .env in scripts directory
load_dotenv(Path(__file__).parent / ".env")

# === Paths ===
SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent.parent  # dynamous-engine
CLAUDE_DIR = PROJECT_ROOT / ".claude"
MEMORY_DIR = PROJECT_ROOT / "Fredis" / "Memory"

# Memory file paths
SOUL_FILE = MEMORY_DIR / "SOUL.md"
USER_FILE = MEMORY_DIR / "USER.md"
MEMORY_FILE = MEMORY_DIR / "MEMORY.md"
HEARTBEAT_FILE = MEMORY_DIR / "HEARTBEAT.md"
DAILY_DIR = MEMORY_DIR / "daily"

# === Owner Identity ===
OWNER_NAME = os.getenv("OWNER_NAME", "")

# === Data Directory (databases, model caches) ===
DATA_DIR = CLAUDE_DIR / "data"
DATABASE_PATH = DATA_DIR / "memory.db"
DATABASE_URL = os.getenv("DATABASE_URL", "")

# State files — per-machine operational data, NOT synced via Obsidian
STATE_DIR = DATA_DIR / "state"
HEARTBEAT_STATE_FILE = STATE_DIR / "heartbeat-state.json"

# === Reflection Configuration ===
REFLECTION_STATE_FILE = STATE_DIR / "reflection-state.json"
REFLECTION_HOUR = int(os.getenv("REFLECTION_HOUR", "8"))

# === Embedding Configuration ===
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384
EMBEDDING_CACHE_DIR = DATA_DIR / "models"

# === Integration Configuration (Phase 5) ===
INTEGRATIONS_DIR = SCRIPTS_DIR / "integrations"

# Google OAuth
GOOGLE_CREDENTIALS_FILE = INTEGRATIONS_DIR / "google_credentials.json"
GOOGLE_TOKEN_FILE = INTEGRATIONS_DIR / "google_token.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

# Asana
ASANA_ACCESS_TOKEN = os.getenv("ASANA_ACCESS_TOKEN", "")
ASANA_WORKSPACE_ID = os.getenv("ASANA_WORKSPACE_ID", "")
ASANA_PROJECT_ID = os.getenv("ASANA_PROJECT_ID", "")

# Asana user mapping — friendly name to GID (format: "name:gid,name:gid")
_asana_users_raw = os.getenv("ASANA_USERS", "")
ASANA_USERS: dict[str, str] = {}
if _asana_users_raw:
    for pair in _asana_users_raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            name, gid = pair.split(":", 1)
            ASANA_USERS[name.strip().lower()] = gid.strip()

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_NOTIFICATION_CHANNEL = os.getenv("SLACK_NOTIFICATION_CHANNEL", "#second-brain")
SLACK_MONITORED_CHANNELS = os.getenv("SLACK_MONITORED_CHANNELS", "second-brain").split(",")
SLACK_OWNER_USER_ID = os.getenv("SLACK_OWNER_USER_ID", "")

# Chat Interface
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")
CHAT_DB_PATH = DATA_DIR / "chat.db"
CHAT_MAX_TURNS = int(os.getenv("CHAT_MAX_TURNS", "25"))
CHAT_MAX_BUDGET_USD = float(os.getenv("CHAT_MAX_BUDGET_USD", "2.0"))
CHAT_ALLOWED_USERS = os.getenv("CHAT_ALLOWED_USERS", SLACK_OWNER_USER_ID).split(",")

# Calendar
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# Circle
CIRCLE_ADMIN_TOKEN = os.getenv("CIRCLE_ADMIN_TOKEN", "")
CIRCLE_HEADLESS_TOKEN = os.getenv("CIRCLE_HEADLESS_TOKEN", "")
CIRCLE_MEMBER_EMAIL = os.getenv("CIRCLE_MEMBER_EMAIL", "")
CIRCLE_COMMUNITY_MEMBER_ID = int(os.getenv("CIRCLE_COMMUNITY_MEMBER_ID", "0"))

# === Drafts & Habits ===
DRAFTS_DIR = MEMORY_DIR / "drafts"
DRAFTS_ACTIVE_DIR = DRAFTS_DIR / "active"
DRAFTS_SENT_DIR = DRAFTS_DIR / "sent"
DRAFTS_EXPIRED_DIR = DRAFTS_DIR / "expired"
HABITS_FILE = MEMORY_DIR / "HABITS.md"
DRAFT_EXPIRY_HOURS = int(os.getenv("DRAFT_EXPIRY_HOURS", "24"))

# === Onboarding (Phase 1 personalisation) ===
ONBOARDING_FILE = PROJECT_ROOT / ".agent" / "plans" / "phase1-onboarding-interview.md"
PRD_FILE = PROJECT_ROOT / ".agent" / "plans" / "second-brain-prd.md"
EXPIRED_DRAFT_RETENTION_DAYS = int(os.getenv("EXPIRED_DRAFT_RETENTION_DAYS", "7"))

# === Security / Guardrail ===
GUARDRAIL_STATE_FILE = STATE_DIR / "guardrail-state.json"

# === Search Configuration ===
SEARCH_CHUNK_MAX_TOKENS = 400
SEARCH_CHUNK_OVERLAP_TOKENS = 80
SEARCH_VECTOR_WEIGHT = 0.7
SEARCH_KEYWORD_WEIGHT = 0.3
SEARCH_DEFAULT_LIMIT = 10
SEARCH_MIN_SCORE = 0.2

# === Authentication ===
# Claude Agent SDK inherits auth from Claude Code CLI automatically.
# No API key needed - uses credentials stored in ~/.claude/.credentials.json
# Task Scheduler runs as your user, so it has access to your credentials.

# === Heartbeat Configuration ===
HEARTBEAT_INTERVAL_MINUTES = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", "30"))
HEARTBEAT_ACTIVE_START = os.getenv("HEARTBEAT_ACTIVE_HOURS_START", "08:00")
HEARTBEAT_ACTIVE_END = os.getenv("HEARTBEAT_ACTIVE_HOURS_END", "22:00")
HEARTBEAT_TIMEZONE = os.getenv("HEARTBEAT_TIMEZONE", "America/Chicago")

# === Daily Log Template ===
DAILY_LOG_SECTIONS = ["Sessions", "Heartbeats", "Memory Maintenance"]

# Note: Model is determined by the claude_code system prompt preset
# No need to override - uses your subscription's default model


LOCAL_TZ = ZoneInfo(HEARTBEAT_TIMEZONE)


def now_local() -> datetime:
    """Return the current time in the configured timezone (HEARTBEAT_TIMEZONE)."""
    return datetime.now(LOCAL_TZ)


def get_today_log_path() -> Path:
    """Get path to today's daily log (based on local date)."""
    today = now_local().strftime("%Y-%m-%d")
    return DAILY_DIR / f"{today}.md"


def is_within_active_hours() -> bool:
    """Check if current time is within active hours (local timezone)."""
    current_time = now_local().strftime("%H:%M")
    return HEARTBEAT_ACTIVE_START <= current_time <= HEARTBEAT_ACTIVE_END


def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for directory in [MEMORY_DIR, DAILY_DIR, STATE_DIR, DATA_DIR, INTEGRATIONS_DIR,
                       DRAFTS_ACTIVE_DIR, DRAFTS_SENT_DIR, DRAFTS_EXPIRED_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
