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
from typing import Any

# Add both chat dir and scripts dir to path for imports
_CHAT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _CHAT_DIR.parent / "scripts"
sys.path.insert(0, str(_CHAT_DIR))
sys.path.insert(0, str(_SCRIPTS_DIR))

from channel_router import ChannelRouter  # noqa: E402
from engine import ConversationEngine  # noqa: E402
from router import ChatRouter  # noqa: E402
from session import get_session_store  # noqa: E402

from config import (  # noqa: E402
    CHAT_ALLOWED_USERS,
    CHAT_DB_PATH,
    CHAT_MAX_BUDGET_USD,
    CHAT_MAX_TURNS,
    CHAT_SLACK_RECONNECT_SEC,
    PROJECT_ROOT,
    SLACK_APP_TOKEN,
    SLACK_BOT_TOKEN,
)

_CHANNEL_ROUTING_CONFIG = PROJECT_ROOT / ".claude" / "config" / "channel-routing.yaml"


def _load_channel_router() -> ChannelRouter | None:
    """Load the channel routing config if it exists; return None otherwise.

    A missing config is tolerated — chat still works, summaries just don't land
    in per-channel folders. A malformed config raises at startup so we fail loud.
    """
    if not _CHANNEL_ROUTING_CONFIG.exists():
        print(f"WARN: channel routing config not found at {_CHANNEL_ROUTING_CONFIG}")
        print("      Per-channel vault summaries disabled.")
        return None
    return ChannelRouter(_CHANNEL_ROUTING_CONFIG, PROJECT_ROOT)


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

        # Validate channel router loads (optional — tolerant on missing config)
        channel_router = _load_channel_router()
        if channel_router is not None:
            print(f"  Channel router OK ({len(channel_router.config.channels)} channels)")

        # Validate engine can be instantiated
        engine = ConversationEngine(
            store,
            PROJECT_ROOT,
            CHAT_MAX_TURNS,
            CHAT_MAX_BUDGET_USD,
            channel_router=channel_router,
        )
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
    channel_router = _load_channel_router()
    engine = ConversationEngine(
        store,
        PROJECT_ROOT,
        CHAT_MAX_TURNS,
        CHAT_MAX_BUDGET_USD,
        channel_router=channel_router,
    )

    from adapters.slack import SlackAdapter

    adapter = SlackAdapter(
        SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CHAT_ALLOWED_USERS, session_store=store
    )

    router = ChatRouter(engine)
    router.register(adapter)

    print(f"[{datetime.now()}] Starting chat interface...")

    async def _socket_watchdog(slack_adapter: Any, interval_sec: int) -> None:
        """Force-reconnect the Slack WebSocket on a timer.

        Defends against the silent-drop class where Slack's autoping logic
        gets stuck and the process keeps running but never receives events
        again. Three consecutive reconnect failures → exit so systemd
        (`Restart=always`) brings us back fresh. A reconnect that returns
        False (turn in flight) is not a failure; we just retry next cycle.
        """
        consec_fail = 0
        while True:
            await asyncio.sleep(interval_sec)
            try:
                reconnected = await slack_adapter.reconnect()
                if reconnected:
                    consec_fail = 0
                # else: skipped because a turn is in flight — try next cycle.
            except Exception as e:
                consec_fail += 1
                print(
                    f"[{datetime.now()}] socket watchdog: reconnect failed "
                    f"({consec_fail}/3): {e}"
                )
                if consec_fail >= 3:
                    print(
                        f"[{datetime.now()}] socket watchdog: 3 consecutive "
                        f"failures — exiting for systemd to restart"
                    )
                    sys.exit(1)

    async def _run_with_watchdog() -> None:
        run_task = asyncio.create_task(router.run())
        watchdog_task: asyncio.Task[None] | None = None
        if CHAT_SLACK_RECONNECT_SEC > 0:
            print(
                f"[{datetime.now()}] socket watchdog: forced reconnect every "
                f"{CHAT_SLACK_RECONNECT_SEC}s"
            )
            watchdog_task = asyncio.create_task(
                _socket_watchdog(adapter, CHAT_SLACK_RECONNECT_SEC)
            )
        try:
            await run_task
        finally:
            if watchdog_task is not None:
                watchdog_task.cancel()
                try:
                    await watchdog_task
                except (asyncio.CancelledError, Exception):
                    pass

    try:
        asyncio.run(_run_with_watchdog())
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        asyncio.run(router.shutdown())
        print(f"[{datetime.now()}] Goodbye!")


if __name__ == "__main__":
    main()
