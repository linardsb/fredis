"""
Shared secret-shape regex library.

Used by:
- ``.claude/hooks/redact-secrets.py`` — as a SECOND LAYER alongside the
  ``.env``-loaded value redactor (patterns catch shapes that live nowhere in
  ``.env`` today but might leak from tool results — e.g. a Gmail body that
  contains a forwarded PAT).
- ``.claude/scripts/memory_flush.py`` — pre-LLM scrubber on transcript
  excerpts before they reach the flush reasoner.
- ``.claude/scripts/tests/evals/`` — fixture-driven calibration harness
  (Phase 7).

Every pattern is shape-specific or context-anchored. Loose patterns that
match generic high-entropy blobs (40-char base64, 32-char hex) are avoided
because they collide with embedding serialisations, git SHAs, MD5/SHA-256
hashes, and docker digests. Calibrate against
``tests/evals/fixtures/benign_lookalikes.jsonl``.
"""

from __future__ import annotations

import re

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "slack_bot": re.compile(r"xoxb-[A-Za-z0-9-]{20,}"),
    "slack_app": re.compile(r"xapp-[A-Za-z0-9-]{20,}"),
    "slack_user": re.compile(r"xoxp-[A-Za-z0-9-]{20,}"),
    "github_pat": re.compile(r"ghp_[A-Za-z0-9]{36,}"),
    "github_oauth": re.compile(r"gho_[A-Za-z0-9]{20,}"),
    "github_server": re.compile(r"ghs_[A-Za-z0-9]{20,}"),
    "github_fine": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "anthropic": re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
    "openai": re.compile(r"sk-[A-Za-z0-9]{32,}"),
    "google_oauth": re.compile(r"ya29\.[A-Za-z0-9_-]+"),
    "google_client_secret": re.compile(r"GOCSPX-[A-Za-z0-9_-]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    # Anchor on assignment context so we don't match any arbitrary 40-char
    # base64 (image thumbnails, embeddings, docker digests).
    "aws_secret_key": re.compile(
        r"(?i)aws[_-]?secret[_-]?access[_-]?key[\"'\s]*[:=][\"'\s]*([A-Za-z0-9/+=]{40})"
    ),
    # JWT — also covers Monday.com API tokens (JWT-shaped).
    "jwt": re.compile(r"eyJ[A-Za-z0-9_=-]+\.eyJ[A-Za-z0-9_=-]+\.[A-Za-z0-9_=-]+"),
    # Asana PAT — require the `1/<numeric>:` prefix. Standalone 32+ hex is
    # too noisy (matches MD5, git SHAs, UUIDs without dashes).
    "asana_pat": re.compile(r"1/[0-9]+:[a-f0-9]{32,}"),
    # Legacy Asana PAT shape (pre-2024) — kept for transcripts that may still
    # echo older tokens.
    "asana_pat_legacy": re.compile(r"\b2/\d+/\d+:[0-9a-f]{20,}"),
}

REPLACEMENT_TEMPLATE = "[REDACTED:{kind}]"


def scrub_secrets(text: str) -> tuple[str, int]:
    """Apply every pattern to ``text`` and return ``(scrubbed, replacement_count)``.

    Replacement form is ``[REDACTED:<kind>]`` per
    ``agent-guardrails.md`` §4 convention.
    """
    if not text:
        return text, 0
    scrubbed = text
    total = 0
    # aws_secret_key is a capture group — replace just the token, not the
    # whole "aws_secret_access_key = <val>" anchor. All others match the
    # whole token.
    for kind, pattern in SECRET_PATTERNS.items():
        replacement = REPLACEMENT_TEMPLATE.format(kind=kind)
        if kind == "aws_secret_key":

            def _repl_aws(match: re.Match[str], _repl: str = replacement) -> str:
                # Preserve the "aws_secret_access_key = " prefix; redact only
                # the captured 40-char token.
                return match.group(0).replace(match.group(1), _repl)

            scrubbed, n = pattern.subn(_repl_aws, scrubbed)
        else:
            scrubbed, n = pattern.subn(replacement, scrubbed)
        total += n
    return scrubbed, total
