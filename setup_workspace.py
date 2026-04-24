"""
Workspace Setup Script
======================
Clones all repos and distributes env vars from a single master .env file.

Usage:
    python setup_workspace.py                      # uses master.env in current dir
    python setup_workspace.py --env /path/to/.env  # specify master env file
    python setup_workspace.py --env-only           # skip cloning, just write .env files
    python setup_workspace.py --dry-run             # show what would happen
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository definitions
# ---------------------------------------------------------------------------
REPOS: list[dict[str, str]] = []

# ---------------------------------------------------------------------------
# Env file definitions
#
# Each entry maps: target_var_name -> master_var_name
# ---------------------------------------------------------------------------
ENV_FILES = {
    # --- Second Brain (Heartbeat & Scripts) ---
    # NOTE: Monday boards must be supplied via the combined MONDAY_BOARD_IDS
    # form in master.env (e.g. "Deals:1234,Client Projects:5678"). The
    # per-board MONDAY_BOARD_<NAME>=<id> form isn't propagated — see
    # config.py for the parsing rules.
    ".claude/scripts/.env": {
        "OWNER_NAME": "OWNER_NAME",
        "DATABASE_URL": "SB_DATABASE_URL",
        "HEARTBEAT_INTERVAL_MINUTES": "HEARTBEAT_INTERVAL_MINUTES",
        "HEARTBEAT_ACTIVE_HOURS_START": "HEARTBEAT_ACTIVE_HOURS_START",
        "HEARTBEAT_ACTIVE_HOURS_END": "HEARTBEAT_ACTIVE_HOURS_END",
        "HEARTBEAT_TIMEZONE": "HEARTBEAT_TIMEZONE",
        "REFLECTION_HOUR": "REFLECTION_HOUR",
        "DRAFT_EXPIRY_HOURS": "DRAFT_EXPIRY_HOURS",
        "EXPIRED_DRAFT_RETENTION_DAYS": "EXPIRED_DRAFT_RETENTION_DAYS",
        "SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN": "SLACK_APP_TOKEN",
        "SLACK_OWNER_USER_ID": "SLACK_OWNER_USER_ID",
        "SLACK_NOTIFICATION_CHANNEL": "SLACK_NOTIFICATION_CHANNEL",
        "SLACK_MONITORED_CHANNELS": "SLACK_MONITORED_CHANNELS",
        "GOOGLE_CALENDAR_ID": "GOOGLE_CALENDAR_ID",
        "MONDAY_API_TOKEN": "MONDAY_API_TOKEN",
        "MONDAY_USER_ID": "MONDAY_USER_ID",
        "MONDAY_BOARD_IDS": "MONDAY_BOARD_IDS",
        "GITHUB_TOKEN": "GITHUB_TOKEN",
        "GITHUB_USERNAME": "GITHUB_USERNAME",
    },
}

# ---------------------------------------------------------------------------
# Defaults — written to target .env if the master doesn't define them.
# Must stay in sync with .claude/scripts/config.py's os.getenv() fallbacks,
# otherwise the per-script .env will silently override the config defaults.
# ---------------------------------------------------------------------------
DEFAULTS = {
    "HEARTBEAT_INTERVAL_MINUTES": "120",
    "HEARTBEAT_ACTIVE_HOURS_START": "05:00",
    "HEARTBEAT_ACTIVE_HOURS_END": "20:00",
    "HEARTBEAT_TIMEZONE": "Europe/London",
}


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file into a dict, skipping comments and blank lines."""
    env = {}
    if not path.exists():
        print(f"  ERROR: Master env file not found: {path}")
        sys.exit(1)
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip()
    return env


def clone_repos(root: Path, dry_run: bool = False) -> None:
    """Clone sub-repos into the workspace root. Skips repos that fail (they're optional)."""
    for repo in REPOS:
        target = root / repo["path"]
        if target.exists():
            print(f"  SKIP  {repo['path']}/ (already exists)")
            continue
        cmd = ["git", "clone", repo["url"], str(target)]
        if dry_run:
            print(f"  CLONE {repo['url']} -> {repo['path']}/")
        else:
            print(f"  CLONE {repo['url']} -> {repo['path']}/")
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError:
                print(f"  WARN  {repo['path']}: clone failed (skipping) — this companion repo is optional")


def write_env_files(root: Path, master: dict[str, str], dry_run: bool = False) -> None:
    """Write .env files from the master env vars. Skips targets whose parent directory doesn't exist."""
    for rel_path, mapping in ENV_FILES.items():
        target = root / rel_path

        # Skip env files for companion repos that weren't cloned
        repo_dir = target.parent
        if not repo_dir.exists() and not dry_run:
            print(f"  SKIP  {rel_path} (directory not found — companion repo not cloned)")
            continue

        lines: list[str] = []
        missing: list[str] = []

        for target_var, master_var in mapping.items():
            if master_var in master:
                lines.append(f"{target_var}={master[master_var]}")
            elif target_var in DEFAULTS:
                lines.append(f"{target_var}={DEFAULTS[target_var]}")
            else:
                missing.append(master_var)

        if missing:
            print(f"  WARN  {rel_path}: missing vars in master: {', '.join(missing)}")

        content = "\n".join(lines) + "\n"

        if dry_run:
            print(f"  WRITE {rel_path} ({len(lines)} vars)")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"  WRITE {rel_path} ({len(lines)} vars)")


def generate_hooks_settings(root: Path, dry_run: bool = False) -> None:
    """Generate .claude/settings.local.json with platform-specific hook commands."""
    target = root / ".claude" / "settings.local.json"

    if sys.platform == "win32":
        # Windows cmd.exe: cd /d, %VAR%, backslashes
        def cmd(script: str) -> str:
            return (
                f'cd /d "%CLAUDE_PROJECT_DIR%\\.claude\\scripts" '
                f'&& uv run python "%CLAUDE_PROJECT_DIR%\\.claude\\hooks\\{script}"'
            )
    else:
        # Linux/macOS sh: $VAR, forward slashes
        def cmd(script: str) -> str:
            return (
                f'cd "$CLAUDE_PROJECT_DIR/.claude/scripts" '
                f'&& uv run python "$CLAUDE_PROJECT_DIR/.claude/hooks/{script}"'
            )

    settings = {
        "hooks": {
            "PreCompact": [
                {
                    "matcher": "",
                    "hooks": [
                        {
                            "type": "command",
                            "command": cmd("pre-compact-flush.py"),
                            "timeout": 10,
                        }
                    ],
                }
            ],
            "SessionEnd": [
                {
                    "matcher": "prompt_input_exit|clear|other",
                    "hooks": [
                        {
                            "type": "command",
                            "command": cmd("session-end-flush.py"),
                            "timeout": 10,
                        }
                    ],
                }
            ],
            "SessionStart": [
                {
                    "matcher": "startup|resume|clear|compact",
                    "hooks": [
                        {
                            "type": "command",
                            "command": cmd("session-start-context.py"),
                            "timeout": 15,
                        }
                    ],
                }
            ],
        }
    }

    if dry_run:
        platform = "Windows" if sys.platform == "win32" else "Linux/macOS"
        print(f"  WRITE .claude/settings.local.json ({platform} hooks)")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        platform = "Windows" if sys.platform == "win32" else "Linux/macOS"
        print(f"  WRITE .claude/settings.local.json ({platform} hooks)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Set up Fredis workspace")
    parser.add_argument(
        "--env",
        default="master.env",
        help="Path to master .env file (default: master.env)",
    )
    parser.add_argument(
        "--env-only",
        action="store_true",
        help="Skip cloning, only write .env files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without doing it",
    )
    args = parser.parse_args()

    # Root is wherever this script lives (fredis root)
    root = Path(__file__).parent.resolve()
    print(f"Workspace root: {root}")
    print()

    # Parse master env
    master_path = Path(args.env)
    if not master_path.is_absolute():
        master_path = root / master_path
    print(f"[1/4] Reading master env: {master_path}")
    master = parse_env_file(master_path)
    print(f"       Loaded {len(master)} variables")
    print()

    # Clone repos
    if args.env_only:
        print("[2/4] Skipping clone (--env-only)")
    else:
        print("[2/4] Cloning repositories...")
        clone_repos(root, dry_run=args.dry_run)
    print()

    # Write env files
    print("[3/4] Writing environment files...")
    write_env_files(root, master, dry_run=args.dry_run)
    print()

    # Generate platform-specific hooks
    print("[4/4] Generating platform-specific hooks...")
    generate_hooks_settings(root, dry_run=args.dry_run)
    print()

    if args.dry_run:
        print("Dry run complete. No changes made.")
    else:
        print("Setup complete!")
        print()
        print("Next steps:")
        print("  1. cd .claude/scripts && uv sync")


if __name__ == "__main__":
    main()
