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
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Repository definitions
# ---------------------------------------------------------------------------
REPOS = [
    {
        "name": "content-engine",
        "url": "https://github.com/your-username/content-engine.git",
        "path": "content-engine",
    },
    {
        "name": "video-processor",
        "url": "https://github.com/your-username/video-processor.git",
        "path": "video-processor",
    },
    {
        "name": "obsidian-ai-agent",
        "url": "https://github.com/dynamous-community/obsidian-ai-agent.git",
        "path": "obsidian-ai-agent",
    },
]

# ---------------------------------------------------------------------------
# Env file definitions
#
# Each entry maps: target_var_name -> master_var_name
# When names conflict across repos, the master file uses prefixed names
# (CE_ for content-engine, OA_ for obsidian-agent).
# ---------------------------------------------------------------------------
ENV_FILES = {
    # --- Content Engine ---
    "content-engine/.env": {
        "DATABASE_URL": "CE_DATABASE_URL",
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
        "SUPADATA_API_KEY": "SUPADATA_API_KEY",
        "BRAVE_API_KEY": "CE_BRAVE_API_KEY",
        "PERPLEXITY_API_KEY": "PERPLEXITY_API_KEY",
        "REDDIT_CLIENT_ID": "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET": "REDDIT_CLIENT_SECRET",
        "GITHUB_TOKEN": "GITHUB_TOKEN",
        "TRIAGE_MODEL": "TRIAGE_MODEL",
        "ANALYSIS_MODEL": "ANALYSIS_MODEL",
        "SYNTHESIS_MODEL": "SYNTHESIS_MODEL",
    },
    # --- Video Processor ---
    "video-processor/.env": {
        "OPENAI_API_KEY": "OPENAI_API_KEY",
        "WHISPER_MODEL": "WHISPER_MODEL",
        "GEMINI_API_KEY": "GEMINI_API_KEY",
        "GEMINI_MODEL": "GEMINI_MODEL",
        "GEMINI_THUMBNAIL_MODEL": "GEMINI_THUMBNAIL_MODEL",
        "REPLICATE_API_TOKEN": "REPLICATE_API_TOKEN",
    },
    # --- Obsidian AI Agent ---
    "obsidian-ai-agent/.env": {
        "APP_NAME": "APP_NAME",
        "VERSION": "VERSION",
        "ENVIRONMENT": "ENVIRONMENT",
        "LOG_LEVEL": "LOG_LEVEL",
        "API_PREFIX": "API_PREFIX",
        "ALLOWED_ORIGINS": "ALLOWED_ORIGINS",
        "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
        "LLM_MODEL": "LLM_MODEL",
        "BRAVE_API_KEY": "OA_BRAVE_API_KEY",
        "OBSIDIAN_VAULT_PATH": "OBSIDIAN_VAULT_PATH",
        "DATABASE_URL": "OA_DATABASE_URL",
        "SUPABASE_PROJECT_URL": "SUPABASE_PROJECT_URL",
        "SUPABASE_KEY": "SUPABASE_KEY",
        "ENABLE_RAG": "ENABLE_RAG",
        "RAG_PIPELINE_ID": "RAG_PIPELINE_ID",
        "SUPABASE_URL": "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY": "SUPABASE_SERVICE_KEY",
        "EMBEDDING_BASE_URL": "EMBEDDING_BASE_URL",
        "EMBEDDING_API_KEY": "EMBEDDING_API_KEY",
        "EMBEDDING_MODEL_CHOICE": "EMBEDDING_MODEL_CHOICE",
    },
    # --- Second Brain (Heartbeat & Scripts) ---
    ".claude/scripts/.env": {
        "OWNER_NAME": "OWNER_NAME",
        "DATABASE_URL": "SB_DATABASE_URL",
        "HEARTBEAT_INTERVAL_MINUTES": "HEARTBEAT_INTERVAL_MINUTES",
        "HEARTBEAT_ACTIVE_HOURS_START": "HEARTBEAT_ACTIVE_HOURS_START",
        "HEARTBEAT_ACTIVE_HOURS_END": "HEARTBEAT_ACTIVE_HOURS_END",
        "HEARTBEAT_TIMEZONE": "HEARTBEAT_TIMEZONE",
        "ASANA_ACCESS_TOKEN": "ASANA_ACCESS_TOKEN",
        "ASANA_WORKSPACE_ID": "ASANA_WORKSPACE_ID",
        "ASANA_PROJECT_ID": "ASANA_PROJECT_ID",
        "ASANA_USERS": "ASANA_USERS",
        "SLACK_BOT_TOKEN": "SLACK_BOT_TOKEN",
        "SLACK_APP_TOKEN": "SLACK_APP_TOKEN",
        "SLACK_OWNER_USER_ID": "SLACK_OWNER_USER_ID",
        "SLACK_NOTIFICATION_CHANNEL": "SLACK_NOTIFICATION_CHANNEL",
        "SLACK_MONITORED_CHANNELS": "SLACK_MONITORED_CHANNELS",
        "GOOGLE_CALENDAR_ID": "GOOGLE_CALENDAR_ID",
    },
}

# ---------------------------------------------------------------------------
# Defaults — written to target .env if the master doesn't define them
# ---------------------------------------------------------------------------
DEFAULTS = {
    "TRIAGE_MODEL": "openrouter:anthropic/claude-haiku-4.5",
    "ANALYSIS_MODEL": "openrouter:anthropic/claude-sonnet-4.5",
    "SYNTHESIS_MODEL": "openrouter:anthropic/claude-sonnet-4.5",
    "WHISPER_MODEL": "whisper-1",
    "GEMINI_MODEL": "gemini-3-flash-preview",
    "GEMINI_THUMBNAIL_MODEL": "gemini-3-pro-image-preview",
    "APP_NAME": "Obsidian Agent Project",
    "VERSION": "0.1.0",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "INFO",
    "API_PREFIX": "/api",
    "ALLOWED_ORIGINS": '["http://localhost:3000","http://localhost:8123","app://obsidian.md","capacitor://localhost"]',
    "LLM_MODEL": "claude-haiku-4-5",
    "ENABLE_RAG": "true",
    "RAG_PIPELINE_ID": "obsidian-vault-rag",
    "EMBEDDING_BASE_URL": "https://api.openai.com/v1",
    "EMBEDDING_MODEL_CHOICE": "text-embedding-3-small",
    "HEARTBEAT_INTERVAL_MINUTES": "30",
    "HEARTBEAT_ACTIVE_HOURS_START": "08:00",
    "HEARTBEAT_ACTIVE_HOURS_END": "22:00",
    "HEARTBEAT_TIMEZONE": "America/Chicago",
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


def generate_master_template(root: Path) -> None:
    """Generate a master.env.example with all required variables."""
    template = root / "master.env.example"
    sections = [
        (
            "Shared / Multi-Repo Keys",
            [
                ("OPENAI_API_KEY", "OpenAI (video-processor transcription + obsidian-agent embeddings)"),
                ("ANTHROPIC_API_KEY", "Anthropic (obsidian-agent LLM)"),
                ("GITHUB_TOKEN", "GitHub PAT (content-engine rate limit)"),
            ],
        ),
        (
            "Content Engine",
            [
                ("CE_DATABASE_URL", "PostgreSQL connection (e.g. postgresql://user:pass@host:6543/db)"),
                ("CE_BRAVE_API_KEY", "Brave Search API key for content-engine"),
                ("OPENROUTER_API_KEY", "OpenRouter API key"),
                ("SUPADATA_API_KEY", "Supadata API key (YouTube transcripts)"),
                ("PERPLEXITY_API_KEY", "Perplexity API key"),
                ("REDDIT_CLIENT_ID", "Reddit app client ID"),
                ("REDDIT_CLIENT_SECRET", "Reddit app client secret"),
            ],
        ),
        (
            "Video Processor",
            [
                ("GEMINI_API_KEY", "Google Gemini API key"),
                ("REPLICATE_API_TOKEN", "Replicate API token (face swap)"),
            ],
        ),
        (
            "Obsidian AI Agent",
            [
                ("OA_DATABASE_URL", "PostgreSQL+asyncpg connection for obsidian-agent"),
                ("OA_BRAVE_API_KEY", "Brave Search API key for obsidian-agent"),
                ("OBSIDIAN_VAULT_PATH", "Absolute path to Obsidian vault"),
                ("SUPABASE_PROJECT_URL", "Supabase project URL"),
                ("SUPABASE_KEY", "Supabase anon/service key"),
                ("SUPABASE_URL", "Supabase URL (for RAG)"),
                ("SUPABASE_SERVICE_KEY", "Supabase service role key (for RAG)"),
                ("EMBEDDING_API_KEY", "Embedding API key (usually same as OPENAI_API_KEY)"),
            ],
        ),
        (
            "Second Brain (Heartbeat & Scripts)",
            [
                ("OWNER_NAME", "Your name (used in heartbeat prompts)"),
                ("SB_DATABASE_URL", "PostgreSQL connection (leave empty for local SQLite)"),
                ("ASANA_ACCESS_TOKEN", "Asana Personal Access Token"),
                ("ASANA_WORKSPACE_ID", "Asana Workspace ID"),
                ("ASANA_PROJECT_ID", "Asana Project ID"),
                ("SLACK_BOT_TOKEN", "Slack Bot Token (xoxb-...)"),
                ("SLACK_APP_TOKEN", "Slack App Token for Socket Mode (xapp-...)"),
                ("SLACK_OWNER_USER_ID", "Your Slack user ID (for @mention filtering)"),
                ("GOOGLE_CALENDAR_ID", "Google Calendar ID (usually your email)"),
            ],
        ),
    ]

    lines = [
        "# =============================================================================",
        "# Master Environment File — All variables for the Fredis workspace",
        "# =============================================================================",
        "# Copy to master.env and fill in your values.",
        "# Run: python setup_workspace.py --env master.env",
        "# Variables with defaults (models, config) are auto-filled if omitted.",
        "",
    ]

    for section_name, vars_list in sections:
        lines.append(f"# === {section_name} ===")
        for var, comment in vars_list:
            lines.append(f"# {comment}")
            lines.append(f"{var}=")
        lines.append("")

    lines.append("# === Optional Overrides (defaults used if omitted) ===")
    for var, default in sorted(DEFAULTS.items()):
        lines.append(f"# {var}={default}")
    lines.append("")

    content = "\n".join(lines) + "\n"
    template.write_text(content, encoding="utf-8")
    print(f"  WRITE master.env.example ({len(sections)} sections)")


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


TEMPLATE_FILES = ["SOUL.md", "USER.md", "MEMORY.md", "HEARTBEAT.md", "BOOTSTRAP.md"]


def init_memory_templates(root: Path, dry_run: bool = False) -> None:
    """Copy memory templates to Fredis/Memory/ if files don't already exist."""
    templates_dir = root / "templates" / "memory"
    memory_dir = root / "Fredis" / "Memory"

    if not templates_dir.exists():
        print("  SKIP  templates/memory/ not found")
        return

    # Ensure memory directory exists
    if not dry_run:
        memory_dir.mkdir(parents=True, exist_ok=True)
        (memory_dir / "daily").mkdir(parents=True, exist_ok=True)

    for filename in TEMPLATE_FILES:
        src = templates_dir / filename
        dst = memory_dir / filename

        if not src.exists():
            continue

        if dst.exists():
            print(f"  SKIP  {filename} (already exists)")
        elif dry_run:
            print(f"  COPY  templates/memory/{filename} -> Fredis/Memory/{filename}")
        else:
            shutil.copy2(src, dst)
            print(f"  COPY  templates/memory/{filename} -> Fredis/Memory/{filename}")

    # Copy tone-of-voice template to .claude/ if it doesn't exist
    tov_src = root / "templates" / "tone-of-voice.md"
    tov_dst = root / ".claude" / "tone-of-voice.md"
    if tov_src.exists() and not tov_dst.exists():
        if dry_run:
            print("  COPY  templates/tone-of-voice.md -> .claude/tone-of-voice.md")
        else:
            shutil.copy2(tov_src, tov_dst)
            print("  COPY  templates/tone-of-voice.md -> .claude/tone-of-voice.md")
    elif tov_dst.exists():
        print("  SKIP  tone-of-voice.md (already exists)")


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
    parser.add_argument(
        "--generate-template",
        action="store_true",
        help="Generate master.env.example template and exit",
    )
    args = parser.parse_args()

    # Root is wherever this script lives (dynamous-engine root)
    root = Path(__file__).parent.resolve()
    print(f"Workspace root: {root}")
    print()

    if args.generate_template:
        print("[1/1] Generating master.env.example...")
        generate_master_template(root)
        print("\nDone! Fill in master.env.example -> save as master.env -> run setup.")
        return

    # Parse master env
    master_path = Path(args.env)
    if not master_path.is_absolute():
        master_path = root / master_path
    print(f"[1/5] Reading master env: {master_path}")
    master = parse_env_file(master_path)
    print(f"       Loaded {len(master)} variables")
    print()

    # Clone repos
    if args.env_only:
        print("[2/5] Skipping clone (--env-only)")
    else:
        print("[2/5] Cloning repositories...")
        clone_repos(root, dry_run=args.dry_run)
    print()

    # Write env files
    print("[3/5] Writing .env files...")
    write_env_files(root, master, dry_run=args.dry_run)
    print()

    # Generate platform-specific hooks
    print("[4/5] Generating platform-specific hooks...")
    generate_hooks_settings(root, dry_run=args.dry_run)
    print()

    # Initialize memory templates
    print("[5/5] Initializing memory templates...")
    init_memory_templates(root, dry_run=args.dry_run)
    print()

    if args.dry_run:
        print("Dry run complete. No changes made.")
    else:
        print("Setup complete!")
        print()
        print("Next steps:")
        print("  1. cd content-engine && uv sync")
        print("  2. cd video-processor && uv sync")
        print("  3. cd obsidian-ai-agent && uv sync")
        print("  4. cd .claude/scripts && uv sync")


if __name__ == "__main__":
    main()
