"""Fixture-driven calibration suite for the injection & secret pipelines.

Runs three labelled JSONL fixture files through ``check_injection_patterns``
and ``scrub_secrets`` and asserts each payload's expected verdict / expected
redaction kind. Acts as a regression ratchet: a prompt or pattern change that
flips any fixture's verdict without updating the fixture will fail CI.

Haiku/LLM semantic eval is NOT exercised here (kept offline to avoid real
API calls). See ``agent-guardrails.md`` §8 for how this fits the stack.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from sanitize import check_injection_patterns
from secret_patterns import SECRET_PATTERNS, scrub_secrets

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise AssertionError(f"{path}:{line_no} — invalid JSON: {e}") from e
    return rows


# =============================================================================
# INJECTION — injection_attacks.jsonl
# =============================================================================


@pytest.mark.parametrize(
    "fixture", _load_jsonl(FIXTURES_DIR / "injection_attacks.jsonl"), ids=lambda f: f["id"]
)
def test_injection_fixture_matches_expected_verdict(fixture: dict[str, Any]) -> None:
    payload = fixture["payload"]
    expected = fixture["expected_verdict"]
    flags = check_injection_patterns(payload)
    actual = "pass" if not flags else "fail"
    assert actual == expected, (
        f"{fixture['id']} expected={expected} actual={actual} "
        f"notes={fixture.get('notes', '')}"
    )


# =============================================================================
# BENIGN — benign_lookalikes.jsonl
# =============================================================================


@pytest.mark.parametrize(
    "fixture", _load_jsonl(FIXTURES_DIR / "benign_lookalikes.jsonl"), ids=lambda f: f["id"]
)
def test_benign_fixture_matches_expected(fixture: dict[str, Any]) -> None:
    payload = fixture["payload"]
    expected = fixture["expected_verdict"]
    flags = check_injection_patterns(payload)
    actual = "pass" if not flags else "fail"
    # For benign-looking-secret fixtures, also assert scrub_secrets does not
    # redact them (zero replacements).
    if fixture.get("category") == "looks_like_secret_but_not":
        _scrubbed, count = scrub_secrets(payload)
        assert count == 0, f"{fixture['id']} false-positive: {count} redactions"
    assert actual == expected, (
        f"{fixture['id']} expected={expected} actual={actual} "
        f"notes={fixture.get('notes', '')}"
    )


# =============================================================================
# SECRETS — secret_shapes.jsonl
# =============================================================================


@pytest.mark.parametrize(
    "fixture", _load_jsonl(FIXTURES_DIR / "secret_shapes.jsonl"), ids=lambda f: f["id"]
)
def test_secret_fixture_is_redacted(fixture: dict[str, Any]) -> None:
    payload = fixture["payload"]
    expected_kind = fixture["expected_kind"]
    # The expected pattern must match.
    pattern = SECRET_PATTERNS[expected_kind]
    assert pattern.search(payload), (
        f"{fixture['id']}: pattern {expected_kind} did not match fixture"
    )
    scrubbed, count = scrub_secrets(payload)
    assert count >= 1, f"{fixture['id']}: scrub_secrets returned 0 replacements"
    assert f"[REDACTED:{expected_kind}]" in scrubbed, (
        f"{fixture['id']}: expected [REDACTED:{expected_kind}] in output, got {scrubbed!r}"
    )
