"""
One-time auth setup for all direct platform integrations.

Walks through Google OAuth and Slack bot token validation.

Usage:
    uv run python setup_auth.py          # Full interactive setup
    uv run python setup_auth.py --check  # Status check only (no auth flows)
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime

from config import (
    GOOGLE_CREDENTIALS_FILE,
    SLACK_BOT_TOKEN,
    ensure_directories,
)


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def print_status(name: str, ok: bool, detail: str = "") -> None:
    """Print a status line."""
    icon = "[OK]" if ok else "[--]"
    suffix = f" - {detail}" if detail else ""
    print(f"  {icon} {name}{suffix}")


def check_google(check_only: bool = False, headless: bool = False) -> bool:
    """Check/setup Google OAuth for Gmail + Calendar + Sheets + Docs + Drive."""
    print_header("Google OAuth (Gmail + Calendar + Sheets + Docs + Drive)")

    from integrations.auth import is_google_authenticated

    if is_google_authenticated():
        print_status("Google OAuth", True, "Token exists and is valid/refreshable")

        # Quick validation - try building a service
        try:
            from integrations.auth import get_google_credentials

            creds = get_google_credentials()
            from googleapiclient.discovery import build

            # Test Gmail
            gmail = build("gmail", "v1", credentials=creds)
            profile = gmail.users().getProfile(userId="me").execute()
            print_status("Gmail", True, f"Connected as {profile.get('emailAddress', '?')}")

            # Test Calendar
            calendar = build("calendar", "v3", credentials=creds)
            cal_list = calendar.calendarList().list(maxResults=1).execute()
            num_cals = len(cal_list.get("items", []))
            print_status("Calendar", True, f"Access confirmed ({num_cals} calendars visible)")

            return True
        except Exception as e:
            print_status("API validation", False, str(e))
            return False

    if check_only:
        print_status("Google OAuth", False, "Not authenticated")
        if not GOOGLE_CREDENTIALS_FILE.exists():
            print(f"\n  Missing: {GOOGLE_CREDENTIALS_FILE}")
            print("  Download from Google Cloud Console:")
            print("    1. Go to https://console.cloud.google.com")
            print("    2. Select/create project, enable Gmail + Calendar APIs")
            print("    3. Create OAuth 2.0 Client ID (Desktop app)")
            print("    4. Download JSON, save as google_credentials.json in:")
            print(f"       {GOOGLE_CREDENTIALS_FILE.parent}")
        else:
            print("\n  Credentials file found but no token yet.")
            print("  Run without --check to authenticate.")
        return False

    # Interactive setup
    if not GOOGLE_CREDENTIALS_FILE.exists():
        print(f"  Google credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
        print()
        print("  To set up Google OAuth:")
        print("    1. Go to https://console.cloud.google.com")
        print("    2. Create/select project, enable Gmail API + Calendar API")
        print("    3. Configure OAuth consent screen:")
        print('       - User type: "External" (custom domain)')
        print('       - Publish to "Production" (non-sensitive scopes, no verification needed)')
        print("    4. Create OAuth 2.0 Client ID -> Desktop application")
        print("    5. Download JSON -> save as:")
        print(f"       {GOOGLE_CREDENTIALS_FILE}")
        print()
        input("  Press Enter when ready (or Ctrl+C to skip)...")

        if not GOOGLE_CREDENTIALS_FILE.exists():
            print_status("Google OAuth", False, "Credentials file still not found")
            return False

    # Run OAuth flow
    mode = "headless (manual URL)" if headless else "browser-based"
    print(f"  Starting {mode} OAuth flow...")
    try:
        from integrations.auth import run_initial_auth

        creds = run_initial_auth(headless=headless)
        print_status("Google OAuth", True, "Authenticated successfully!")

        # Validate
        from googleapiclient.discovery import build

        gmail = build("gmail", "v1", credentials=creds)
        profile = gmail.users().getProfile(userId="me").execute()
        print_status("Gmail", True, f"Connected as {profile.get('emailAddress', '?')}")

        calendar = build("calendar", "v3", credentials=creds)
        cal_list = calendar.calendarList().list(maxResults=1).execute()
        print_status("Calendar", True, "Access confirmed")

        return True
    except Exception as e:
        print_status("Google OAuth", False, str(e))
        return False


def check_slack(check_only: bool = False) -> bool:
    """Check/validate Slack bot token."""
    print_header("Slack (Bot Token)")

    if not SLACK_BOT_TOKEN:
        print_status("Slack", False, "SLACK_BOT_TOKEN not set in .env")
        print()
        print("  To set up Slack:")
        print("    1. Go to https://api.slack.com/apps -> Create New App -> From Scratch")
        print('    2. Name: "Second Brain", select your workspace')
        print("    3. OAuth & Permissions -> Add Bot Token Scopes:")
        print("       channels:read, channels:history, chat:write, chat:write.public, users:read")
        print("    4. Install to Workspace -> Copy Bot User OAuth Token")
        print("    5. Add to .claude/scripts/.env:")
        print("       SLACK_BOT_TOKEN=xoxb-...")
        return False

    # Validate token
    try:
        from slack_sdk import WebClient
        from slack_sdk.errors import SlackApiError

        client = WebClient(token=SLACK_BOT_TOKEN)
        auth = client.auth_test()

        bot_name = auth.get("user", "?")
        team = auth.get("team", "?")
        print_status("Slack", True, f"Connected as {bot_name} in {team}")

        return True
    except SlackApiError as e:
        print_status("Slack", False, f"API error: {e.response['error']}")
        return False
    except Exception as e:
        print_status("Slack", False, str(e))
        return False


def main() -> None:
    """Run auth setup."""
    parser = argparse.ArgumentParser(description="Set up direct platform integrations")
    parser.add_argument("--check", action="store_true", help="Check status only (no auth flows)")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Use manual URL copy-paste flow (for remote/headless machines)",
    )
    args = parser.parse_args()

    ensure_directories()

    print_header("Second Brain - Direct Integrations Setup")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    mode = (
        "Status Check"
        if args.check
        else ("Headless Setup" if args.headless else "Interactive Setup")
    )
    print(f"  Mode: {mode}")

    results = {
        "Google": check_google(check_only=args.check, headless=args.headless),
        "Slack": check_slack(check_only=args.check),
    }

    print_header("Summary")
    for name, ok in results.items():
        print_status(name, ok)

    configured = sum(1 for ok in results.values() if ok)
    total = len(results)
    print(f"\n  {configured}/{total} integrations configured")

    if configured < total and not args.check:
        print("\n  Re-run with --check to see what's still needed.")

    sys.exit(0 if configured == total else 1)


if __name__ == "__main__":
    main()
