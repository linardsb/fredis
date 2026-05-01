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
PROJECT_ROOT = SCRIPTS_DIR.parent.parent  # repo root
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

# === Weekly Synthesis Configuration (Phase 9) ===
SYNTHESIS_STATE_FILE = STATE_DIR / "synthesis-state.json"
MEMORY_SYNTHESIS_DIR = MEMORY_DIR / "drafts" / "active" / "memory-synthesis"
SYNTHESIS_DAYS = int(os.getenv("SYNTHESIS_DAYS", "7"))

# MEMORY.md size cap — when reflection promotes entries and the file grows
# past this, the oldest entries are archived wholesale to MEMORY_ARCHIVE_DIR
# so the in-context file stays compact. Archived files remain searchable via
# the hybrid memory index.
MEMORY_LINE_LIMIT = int(os.getenv("MEMORY_LINE_LIMIT", "200"))
MEMORY_ARCHIVE_DIR = MEMORY_DIR / "archive"

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
# Periodic forced reconnect of the chat Socket Mode WebSocket. Defends
# against slack-sdk's silent-drop class (half-open WS, process alive but
# deaf). 0 disables. Default 1800s (30 min) — never too long for a silent
# drop to bite, never short enough to be disruptive.
CHAT_SLACK_RECONNECT_SEC = int(os.getenv("CHAT_SLACK_RECONNECT_SEC", "1800"))

# Calendar
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "")

# HubSpot CRM (replaces Monday.com as of 2026-04-22)
HUBSPOT_API_TOKEN = os.getenv("HUBSPOT_API_TOKEN", "")
HUBSPOT_HUB_ID = os.getenv("HUBSPOT_HUB_ID", "")
HUBSPOT_SCANS_ENABLED = os.getenv("HUBSPOT_SCANS_ENABLED", "false").lower() == "true"
HUBSPOT_SILENT_CONTACT_DAYS = int(os.getenv("HUBSPOT_SILENT_CONTACT_DAYS", "14"))
HUBSPOT_STALE_DEAL_DAYS = int(os.getenv("HUBSPOT_STALE_DEAL_DAYS", "14"))

# HubSpot Tickets — Fredis Review queue. Default off; flip to true after
# the bootstrap pipeline + properties exist and smoke tests pass.
HUBSPOT_TICKETS_ENABLED = (
    os.getenv("HUBSPOT_TICKETS_ENABLED", "false").lower() == "true"
)
HUBSPOT_TICKETS_PIPELINE_NAME = os.getenv(
    "HUBSPOT_TICKETS_PIPELINE_NAME", "Fredis Review"
)
HUBSPOT_TICKETS_SLACK_CHANNEL = os.getenv(
    "HUBSPOT_TICKETS_SLACK_CHANNEL", "hubspot"
)
HUBSPOT_TICKETS_REOPEN_DAYS = int(os.getenv("HUBSPOT_TICKETS_REOPEN_DAYS", "7"))
HUBSPOT_STALE_DEAL_TICKET_DAYS = int(
    os.getenv("HUBSPOT_STALE_DEAL_TICKET_DAYS", "30")
)

# GitHub Projects v2 — product lanes tracker (replaces Monday "Lanes & Features" board)
GITHUB_PROJECT_LANES_ID = os.getenv("GITHUB_PROJECT_LANES_ID", "")

# GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")

# === Drafts & Habits ===
DRAFTS_DIR = MEMORY_DIR / "drafts"
DRAFTS_ACTIVE_DIR = DRAFTS_DIR / "active"
DRAFTS_SENT_DIR = DRAFTS_DIR / "sent"
DRAFTS_EXPIRED_DIR = DRAFTS_DIR / "expired"

# === Gates (Phase 5.2 launch-governance/metrics-gate) ===
GATES_DIR = MEMORY_DIR / "gates"
GATE_BREACH_TEMPLATE = SCRIPTS_DIR / "templates" / "gate_breach.md.tmpl"
GATE_BREACH_DRAFTS_DIR = DRAFTS_ACTIVE_DIR / "launch-governance" / "metrics-gate"
HABITS_FILE = MEMORY_DIR / "HABITS.md"
DRAFT_EXPIRY_HOURS = int(os.getenv("DRAFT_EXPIRY_HOURS", "24"))

# === Onboarding (Phase 1 personalisation) ===
ONBOARDING_FILE = PROJECT_ROOT / ".agent" / "plans" / "phase1-onboarding-interview.md"
PRD_FILE = PROJECT_ROOT / ".agent" / "plans" / "second-brain-prd.md"
EXPIRED_DRAFT_RETENTION_DAYS = int(os.getenv("EXPIRED_DRAFT_RETENTION_DAYS", "7"))

# === Security / Guardrail ===
GUARDRAIL_STATE_FILE = STATE_DIR / "guardrail-state.json"

# === Fredis MCP server (OB1 Phase 1) ===
# Vault-relative path prefixes denied to MCP read tools. Entries ending in
# "/" match a directory prefix; entries without a trailing "/" match a single
# file exactly. Empty / missing env value → empty list (no filtering). Never
# log this list or its source env string.
MCP_DENYLIST: list[str] = [
    p.strip()
    for p in os.getenv("FREDIS_MCP_DENYLIST", "").split(",")
    if p.strip()
]

# === Search Configuration ===
SEARCH_CHUNK_MAX_TOKENS = 400
SEARCH_CHUNK_OVERLAP_TOKENS = 80
SEARCH_VECTOR_WEIGHT = 0.7
SEARCH_KEYWORD_WEIGHT = 0.3
SEARCH_DEFAULT_LIMIT = 10
SEARCH_MIN_SCORE = 0.2

# Path-prefix → score multiplier. PRD Phase 3 personalization note:
# draft voice-matching + meeting recall are primary use cases, so boost those.
SEARCH_PATH_PRIORS: dict[str, float] = {
    "drafts/sent/": 1.5,
    "meetings/": 1.3,
}
SEARCH_PATH_PRIOR_DEFAULT = 1.0

# === Authentication ===
# Claude Agent SDK inherits auth from Claude Code CLI automatically.
# No API key needed - uses credentials stored in ~/.claude/.credentials.json
# Task Scheduler runs as your user, so it has access to your credentials.

# === Heartbeat Configuration ===
HEARTBEAT_INTERVAL_MINUTES = int(os.getenv("HEARTBEAT_INTERVAL_MINUTES", "120"))
HEARTBEAT_ACTIVE_START = os.getenv("HEARTBEAT_ACTIVE_HOURS_START", "05:00")
HEARTBEAT_ACTIVE_END = os.getenv("HEARTBEAT_ACTIVE_HOURS_END", "20:00")
HEARTBEAT_TIMEZONE = os.getenv("HEARTBEAT_TIMEZONE", "Europe/London")

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
    for directory in [
        MEMORY_DIR,
        DAILY_DIR,
        MEMORY_ARCHIVE_DIR,
        STATE_DIR,
        DATA_DIR,
        INTEGRATIONS_DIR,
        DRAFTS_ACTIVE_DIR,
        DRAFTS_SENT_DIR,
        DRAFTS_EXPIRED_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
