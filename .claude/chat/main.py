"""
Multi-platform chat interface for Second Brain.

Usage:
    cd .claude/scripts && uv run python ../chat/main.py
    cd .claude/scripts && uv run python ../chat/main.py --test  # Dry run (no Slack connection)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add both chat dir and scripts dir to path for imports
_CHAT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _CHAT_DIR.parent / "scripts"
sys.path.insert(0, str(_CHAT_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR))

from engine import ConversationEngine  # noqa: E402
from router import ChatRouter  # noqa: E402
from session import get_session_store  # noqa: E402

from config import (  # noqa: E402
    CHAT_ALLOWED_USERS,
    CHAT_DB_PATH,
    CHAT_MAX_BUDGET_USD,
    CHAT_MAX_TURNS,
    PROJECT_ROOT,
    SLACK_APP_TOKEN,
    SLACK_BOT_TOKEN,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Second Brain Chat Interface")
    parser.add_argument("--test", action="store_true", help="Dry run — print config and exit")
    args = parser.parse_args()

    # Validate required env vars
    if not SLACK_BOT_TOKEN:
        print("ERROR: SLACK_BOT_TOKEN not set in .env")
        print("See .claude/scripts/.env.example for setup instructions")
        sys.exit(1)

    if not SLACK_APP_TOKEN:
        print("ERROR: SLACK_APP_TOKEN not set in .env")
        print("Socket Mode requires an app-level token (xapp-...)")
        print("See .claude/scripts/.env.example for setup instructions")
        sys.exit(1)

    # Print startup banner
    print(f"\n{'=' * 60}")
    print("Second Brain Chat Interface")
    print(f"{'=' * 60}")
    print(f"  Project root:  {PROJECT_ROOT}")
    print(f"  Database:      {CHAT_DB_PATH}")
    print(f"  Max turns:     {CHAT_MAX_TURNS}")
    print(f"  Max budget:    ${CHAT_MAX_BUDGET_USD:.2f}")
    print(f"  Allowed users: {', '.join(CHAT_ALLOWED_USERS)}")
    print(f"  Bot token:     {SLACK_BOT_TOKEN[:12]}...")
    print(f"  App token:     {SLACK_APP_TOKEN[:12]}...")
    print(f"{'=' * 60}\n")

    if args.test:
        print("Test mode — validating config and exiting.")

        # Validate session store can be created
        store = get_session_store(CHAT_DB_PATH)
        active = store.list_active()
        print(f"  Session store OK ({len(active)} active sessions)")

        # Validate engine can be instantiated
        engine = ConversationEngine(store, PROJECT_ROOT, CHAT_MAX_TURNS, CHAT_MAX_BUDGET_USD)
        print("  Engine OK")

        # Validate adapter can be instantiated
        from adapters.slack import SlackAdapter

        adapter = SlackAdapter(
            SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHAT_ALLOWED_USERS, session_store=store
        )
        print("  Slack adapter OK")

        # Validate router
        router = ChatRouter(engine)
        router.register(adapter)
        print("  Router OK")

        print("\nAll checks passed. Run without --test to start.")
        return

    # Initialize components
    store = get_session_store(CHAT_DB_PATH)
    engine = ConversationEngine(store, PROJECT_ROOT, CHAT_MAX_TURNS, CHAT_MAX_BUDGET_USD)

    from adapters.slack import SlackAdapter

    adapter = SlackAdapter(
        SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHAT_ALLOWED_USERS, session_store=store
    )

    router = ChatRouter(engine)
    router.register(adapter)

    print(f"[{datetime.now()}] Starting chat interface...")

    try:
        asyncio.run(router.run())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        asyncio.run(router.shutdown())
        print(f"[{datetime.now()}] Goodbye!")


if __name__ == "__main__":
    main()
