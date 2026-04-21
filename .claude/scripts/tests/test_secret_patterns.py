"""Tests for the shared SECRET_PATTERNS module + scrub_secrets helper."""

from __future__ import annotations

import pytest

from secret_patterns import REPLACEMENT_TEMPLATE, SECRET_PATTERNS, scrub_secrets


@pytest.mark.parametrize(
    "kind,example",
    [
        ("slack_bot", "xoxb-1234567890-abcdefghijklmnop"),
        ("slack_app", "xapp-1-A0000000-0-000000abcdef00000000000000000000"),
        ("slack_user", "xoxp-1234567890-abcdefghij-klmnopqrst"),
        ("github_pat", "ghp_abcdefghijklmnopqrstuvwxyz0123456789AB"),
        ("github_oauth", "gho_abcdefghijklmnopqrstuvwxyz01"),
        ("github_server", "ghs_abcdefghijklmnopqrstuvwxyz01"),
        ("github_fine", "github_pat_11ABCDEFG_abcdefghij"),
        ("anthropic", "sk-ant-api-01234567890abcdef_GHIJKLmn"),
        ("openai", "sk-proj01234567890abcdefghijklmnopqrst"),
        ("google_oauth", "ya29.a0AfH6SMA.abcdefghijklm-nop_qr01234567"),
        ("google_client_secret", "GOCSPX-abcdefghijklmnopqrst"),
        ("aws_access_key", "AKIAIOSFODNN7EXAMPLE"),
        (
            "aws_secret_key",
            "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        ),
        (
            "jwt",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ),
        (
            "asana_pat",
            "1/1234567890:abcdef0123456789abcdef0123456789",
        ),
        (
            "asana_pat_legacy",
            "2/12345/67890:abcdef0123456789abcd",
        ),
    ],
)
def test_pattern_positive_match(kind: str, example: str) -> None:
    """Each pattern matches its canonical example shape."""
    pattern = SECRET_PATTERNS[kind]
    assert pattern.search(example), f"{kind} did not match: {example}"


def test_scrub_secrets_replaces_and_counts() -> None:
    text = (
        "token: ghp_abcdefghijklmnopqrstuvwxyz0123456789AB\n"
        "other: xoxb-1234567890-abcdefghijklmnop\n"
        "plain prose"
    )
    scrubbed, count = scrub_secrets(text)
    assert count == 2
    assert "ghp_" not in scrubbed
    assert "xoxb-" not in scrubbed
    assert REPLACEMENT_TEMPLATE.format(kind="github_pat") in scrubbed
    assert REPLACEMENT_TEMPLATE.format(kind="slack_bot") in scrubbed
    assert "plain prose" in scrubbed


def test_scrub_secrets_preserves_aws_assignment_context() -> None:
    """aws_secret_key pattern redacts the token, not the key=value prefix."""
    text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    scrubbed, count = scrub_secrets(text)
    assert count == 1
    assert "aws_secret_access_key" in scrubbed  # prefix preserved
    assert "wJalrXUtnFEMI/K7MDENG" not in scrubbed
    assert REPLACEMENT_TEMPLATE.format(kind="aws_secret_key") in scrubbed


@pytest.mark.parametrize(
    "benign",
    [
        # git SHA — 40 hex chars, must not be matched by any pattern
        "abc1234567890abcdef1234567890abcdef123456",
        # MD5 hash — 32 hex chars
        "5d41402abc4b2a76b9719d911017c592",
        # SHA-256 hash — 64 hex chars
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        # 40-char base64 blob (embedding fragment, not prefixed with aws context)
        "ZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZmZm",
        # UUID without dashes
        "6ba7b8109dad11d180b400c04fd430c8",
        # plain prose
        "please send me the invoice by Friday",
    ],
)
def test_scrub_secrets_does_not_match_benign(benign: str) -> None:
    """Benign high-entropy strings must not be falsely redacted."""
    scrubbed, count = scrub_secrets(benign)
    assert count == 0, f"false positive: {benign!r} → {scrubbed!r}"
    assert scrubbed == benign


def test_empty_string_is_noop() -> None:
    scrubbed, count = scrub_secrets("")
    assert count == 0
    assert scrubbed == ""
