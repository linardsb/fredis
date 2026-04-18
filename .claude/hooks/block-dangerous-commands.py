"""
PreToolUse hook: block commands that would transmit state, delete data, or
send money. This is the second layer of the advisor-mode belt; the first is
the tool allowlist passed to the Agent SDK.

Families blocked:
  1. Outbound mutations on messaging / task platforms (Slack postMessage,
     Gmail drafts.send, Asana/Linear/Monday write mutations, Discord webhook
     posts).
  2. Social-media posting (Twitter/X, LinkedIn, Facebook Graph).
  3. Writes targeting paths OUTSIDE the repo or the Fredis vault.
  4. Destructive shell/DB commands (rm -rf, git reset --hard, git clean -fd,
     DROP TABLE, DELETE FROM).
  5. Financial API calls (Stripe, Plaid, PayPal, checkout endpoints).

Exit codes:
  0 = allow
  2 = block (stderr shown to Claude as feedback; Linards sees the reason)

Philosophy: false positives are acceptable in advisor mode. The fix for a
false positive is to pass an explicit opt-in flag (--i-confirm-send, for
example) or to have Linards run the command himself outside the agent loop.
"""

from __future__ import annotations

import json
import os
import re
import sys

REPO_ROOT = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
FREDIS_DIR = os.path.join(REPO_ROOT, "Fredis")

# ---------------------------------------------------------------------------
# Pattern families
# ---------------------------------------------------------------------------

OUTBOUND_MUTATION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"chat\.postMessage", re.IGNORECASE), "Slack chat.postMessage"),
    (re.compile(r"chat\.postEphemeral", re.IGNORECASE), "Slack chat.postEphemeral"),
    (re.compile(r"chat\.scheduleMessage", re.IGNORECASE), "Slack chat.scheduleMessage"),
    (re.compile(r"slack_sdk.*(?:client|api_call).*chat_postMessage", re.IGNORECASE),
     "slack_sdk chat_postMessage call"),
    (re.compile(r"\.chat_postMessage\s*\(", re.IGNORECASE), "slack_sdk chat_postMessage call"),
    (re.compile(r"/api/chat\.postMessage", re.IGNORECASE), "Slack web API chat.postMessage"),
    (re.compile(r"gmail[./].*drafts[/.]send", re.IGNORECASE), "Gmail drafts.send / /drafts/send"),
    (re.compile(r"gmail[./].*messages[/.]send", re.IGNORECASE), "Gmail messages.send / /messages/send"),
    (re.compile(r"\.users\(\)\.drafts\(\)\.send", re.IGNORECASE), "Gmail drafts().send()"),
    (re.compile(r"\.users\(\)\.messages\(\)\.send", re.IGNORECASE), "Gmail messages().send()"),
    # Asana / Linear / Monday write mutations via curl
    (re.compile(r"curl[^\n]*\bapp\.asana\.com/api/1\.0/[^\s]*\s+-X\s+(POST|PUT|PATCH|DELETE)", re.IGNORECASE),
     "Asana write API via curl"),
    (re.compile(r"curl[^\n]*api\.linear\.app[^\s]*\s+-X\s+(POST|PUT|PATCH|DELETE)", re.IGNORECASE),
     "Linear write API via curl"),
    (re.compile(r"curl[^\n]*api\.monday\.com[^\s]*mutation", re.IGNORECASE),
     "Monday GraphQL mutation via curl"),
    (re.compile(r'"mutation\s*\{', re.IGNORECASE), "GraphQL mutation body"),
    # Discord/Telegram outbound
    (re.compile(r"discord\.com/api/webhooks", re.IGNORECASE), "Discord webhook POST"),
    (re.compile(r"api\.telegram\.org/bot[^/\s]+/sendMessage", re.IGNORECASE),
     "Telegram sendMessage"),
]

SOCIAL_POST_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"api\.twitter\.com/\d+/tweets", re.IGNORECASE), "Twitter/X tweet POST"),
    (re.compile(r"api\.x\.com/\d+/tweets", re.IGNORECASE), "X tweet POST"),
    (re.compile(r"api\.linkedin\.com/.*ugcPosts", re.IGNORECASE), "LinkedIn ugcPosts POST"),
    (re.compile(r"api\.linkedin\.com/.*shares", re.IGNORECASE), "LinkedIn shares POST"),
    (re.compile(r"graph\.facebook\.com/.*/feed", re.IGNORECASE), "Facebook Graph feed POST"),
    (re.compile(r"graph\.instagram\.com/.*/media", re.IGNORECASE), "Instagram Graph media POST"),
]

FINANCIAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"api\.stripe\.com/", re.IGNORECASE), "Stripe API call"),
    (re.compile(r"production\.plaid\.com/", re.IGNORECASE), "Plaid production API call"),
    (re.compile(r"api-m\.paypal\.com/", re.IGNORECASE), "PayPal live API call"),
    (re.compile(r"api\.paypal\.com/", re.IGNORECASE), "PayPal API call"),
    (re.compile(r"/v\d+/checkout/sessions", re.IGNORECASE), "Checkout session endpoint"),
    (re.compile(r"\bstripe\.(Charge|PaymentIntent|Transfer|Payout)\b", re.IGNORECASE),
     "Stripe SDK financial mutation"),
]

DESTRUCTIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+-[rRf]+\s+/(?!tmp/|var/folders/)", re.IGNORECASE),
     "rm -rf against a root-level path"),
    (re.compile(r"\brm\s+-[rRf]+\s+~", re.IGNORECASE), "rm -rf against $HOME"),
    (re.compile(r"\brm\s+-[rRf]+\s+\$HOME", re.IGNORECASE), "rm -rf against $HOME"),
    (re.compile(r"\brm\s+-[rRf]+\s+\*", re.IGNORECASE), "rm -rf with unrestricted glob"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f[a-z]*d", re.IGNORECASE), "git clean -fd"),
    (re.compile(r"\bgit\s+checkout\s+--\s+\.", re.IGNORECASE), "git checkout -- . (discards all)"),
    (re.compile(r"\bgit\s+push\s+(-f|--force)", re.IGNORECASE), "git push --force"),
    (re.compile(r"\bgit\s+branch\s+-D\b", re.IGNORECASE), "git branch -D (force-delete)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "SQL DROP TABLE"),
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "SQL DROP DATABASE"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "SQL TRUNCATE TABLE"),
    (re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?:;|$)", re.IGNORECASE),
     "SQL DELETE FROM without WHERE"),
    (re.compile(r"\bmkfs\b", re.IGNORECASE), "mkfs (filesystem format)"),
    (re.compile(r"\bdd\s+if=.*of=/dev/", re.IGNORECASE), "dd writing to /dev/"),
]


# Git subcommands whose output/content is documentation, not execution.
# Their command strings can legitimately quote any pattern family as text
# (commit messages mentioning blocked API names, git-log searches for
# destructive SQL keywords, etc.) — scanning them produces only false
# positives. Actually-dangerous git operations (push --force, reset
# --hard, clean -fd, branch -D) remain covered by DESTRUCTIVE_PATTERNS
# via explicit verb-flag regexes above.
_GIT_BENIGN_PREFIXES = (
    "git commit",
    "git log",
    "git show",
    "git blame",
    "git diff",
    "git status",
)


def _is_benign_git_subcommand(normalized: str) -> bool:
    return any(normalized.startswith(prefix) for prefix in _GIT_BENIGN_PREFIXES)


def check_bash_command(command: str) -> str | None:
    """Return a block reason if `command` trips any family pattern."""
    # Normalize: collapse whitespace so multi-line heredocs match single-line patterns
    normalized = " ".join(command.split()).strip()

    if _is_benign_git_subcommand(normalized):
        return None

    for family, label in [
        (OUTBOUND_MUTATION_PATTERNS, "outbound mutation"),
        (SOCIAL_POST_PATTERNS, "social-media post"),
        (FINANCIAL_PATTERNS, "financial API"),
        (DESTRUCTIVE_PATTERNS, "destructive command"),
    ]:
        for pattern, reason in family:
            if pattern.search(normalized):
                return f"Blocked ({label}): {reason}"
    return None


def check_write_target(file_path: str) -> str | None:
    """Block writes outside the repo or Fredis vault (advisor-mode sandbox)."""
    if not file_path:
        return None
    try:
        abs_path = os.path.realpath(file_path)
    except (OSError, ValueError):
        return f"Blocked (unresolvable write path): {file_path}"

    real_repo = os.path.realpath(REPO_ROOT)
    real_fredis = os.path.realpath(FREDIS_DIR)
    # Allow standard temp dirs (tests, hook staging).
    temp_prefixes = (
        "/tmp/",
        "/private/tmp/",
        "/var/folders/",
        os.path.realpath(os.path.expanduser("~/.claude")),
    )
    for prefix in temp_prefixes:
        if abs_path.startswith(prefix):
            return None
    if abs_path.startswith(real_repo) or abs_path.startswith(real_fredis):
        return None
    return f"Blocked (write outside repo/Fredis): {file_path}"


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("Failed to parse hook input JSON", file=sys.stderr)
        sys.exit(1)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {}) or {}

    reason: str | None = None

    if tool_name == "Bash":
        reason = check_bash_command(tool_input.get("command", ""))

    elif tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        reason = check_write_target(file_path)
        # Also scan the written content for outbound/destructive patterns —
        # stops scripts being created that would later ship off the agent loop.
        if not reason:
            content = tool_input.get("content", "") or tool_input.get("new_string", "")
            if content:
                # Exempt paths where deny-pattern strings appear legitimately:
                #   * tests/ — fixtures enumerate attack strings as parametrised inputs
                #   * .claude/hooks/ — hook source files ARE the pattern catalog
                exempt = re.search(r"(?:^|/)(tests?|\.claude/hooks)/", file_path)
                if not exempt:
                    reason = check_bash_command(content)

    if reason:
        print(
            f"ADVISOR-MODE: {reason}. "
            "Automated sends, destructive ops, and financial calls are disabled — "
            "draft into Fredis/Memory/drafts/active/ or ask Linards to run the command "
            "himself outside the agent loop.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
