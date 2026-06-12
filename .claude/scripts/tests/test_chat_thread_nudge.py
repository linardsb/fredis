"""Tests for the Phase A thread-degradation nudge logic in `engine.py`.

The nudge decision function is pure — these tests pin its behaviour:
  - single-fire per threshold per thread,
  - hard supersedes soft (and consumes the soft slot to avoid re-fire),
  - threshold is OR (turns OR tokens, either alone is enough),
  - missing usage / new sessions never fire negatively,
  - Phase 3: hard holds off until the soft fire is at least
    NUDGE_MIN_TURNS_BETWEEN_TIERS turns old (min-tier-gap guard).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add the chat dir to sys.path so we can import engine directly.
_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))

from engine import (  # noqa: E402
    NUDGE_HARD_TOKENS,
    NUDGE_HARD_TURNS,
    NUDGE_MIN_TURNS_BETWEEN_TIERS,
    NUDGE_SOFT_TOKENS,
    NUDGE_SOFT_TURNS,
    _extract_context_tokens,
    compute_thread_nudge,
)

# ---------------------------------------------------------------------------
# compute_thread_nudge — no-fire baselines
# ---------------------------------------------------------------------------


def test_no_nudge_when_below_both_thresholds() -> None:
    text, soft, hard = compute_thread_nudge(
        prior_message_count=10,
        last_turn_context_tokens=50_000,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert text == ""
    assert soft is False
    assert hard is False


def test_no_nudge_for_brand_new_thread() -> None:
    """Turn 1 with empty usage stays silent — the common case for fresh threads."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=0,
        last_turn_context_tokens=0,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert (text, soft, hard) == ("", False, False)


# ---------------------------------------------------------------------------
# Soft tier
# ---------------------------------------------------------------------------


def test_soft_fires_at_exactly_30_turns() -> None:
    """Boundary: the 30th turn (prior_count=29) crosses the soft turn threshold."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_SOFT_TURNS - 1,
        last_turn_context_tokens=10_000,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert "30 turns" in text
    assert "consolidate" in text.lower()
    assert soft is True
    assert hard is False


def test_soft_fires_at_120k_tokens_even_at_low_turn_count() -> None:
    """Token threshold OR turn threshold — either alone is enough."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=5,
        last_turn_context_tokens=NUDGE_SOFT_TOKENS,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert text != ""
    assert soft is True
    assert hard is False


def test_soft_does_not_refire_after_already_set() -> None:
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_SOFT_TURNS + 5,
        last_turn_context_tokens=NUDGE_SOFT_TOKENS + 5_000,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
    )
    assert text == ""
    assert soft is False
    assert hard is False


# ---------------------------------------------------------------------------
# Hard tier
# ---------------------------------------------------------------------------


def test_hard_fires_at_50_turns_after_soft_already_fired() -> None:
    """Soft already fired earlier; later, the 50th turn fires hard."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_HARD_TURNS - 1,
        last_turn_context_tokens=140_000,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
    )
    assert "50 turns" in text
    assert "degrading" in text.lower()
    assert soft is False  # already fired previously, don't re-claim
    assert hard is True


def test_hard_fires_at_180k_tokens_at_low_turn_count() -> None:
    text, soft, hard = compute_thread_nudge(
        prior_message_count=10,
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
    )
    assert text != ""
    assert "degrading" in text.lower()
    assert hard is True


def test_hard_from_cold_consumes_soft_slot() -> None:
    """A thread that crosses 50 turns / 180k in one turn (no prior soft fire)
    fires hard AND marks soft consumed so soft can't fire later."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_HARD_TURNS - 1,
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert "degrading" in text.lower()
    assert soft is True
    assert hard is True


def test_hard_does_not_refire_after_already_set() -> None:
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_HARD_TURNS + 20,
        last_turn_context_tokens=NUDGE_HARD_TOKENS + 50_000,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at="2026-05-03T15:00:00",
    )
    assert text == ""
    assert soft is False
    assert hard is False


def test_hard_never_fires_soft_text_when_both_would_qualify() -> None:
    """Sanity: when prior_count is high enough for hard AND no flags set,
    the rendered text talks about degradation, not consolidation-as-option."""
    text, _soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_HARD_TURNS - 1,
        last_turn_context_tokens=200_000,
        nudged_soft_at=None,
        nudged_hard_at=None,
    )
    assert hard is True
    assert "degrading" in text.lower()
    assert "before context gets noisy" not in text


# ---------------------------------------------------------------------------
# Phase 3 — min-tier-gap guard
# ---------------------------------------------------------------------------


def test_hard_suppressed_when_soft_fired_within_min_gap() -> None:
    """Soft fired on turn 30; hard qualifies on turn 31 — held back until the
    soft fire is NUDGE_MIN_TURNS_BETWEEN_TIERS turns old (Saulera anti-pattern)."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=30,  # current turn 31
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
        nudged_soft_turn_count=30,
    )
    assert (text, soft, hard) == ("", False, False)


def test_hard_fires_once_min_gap_elapsed() -> None:
    """Same thread three turns later — the guard releases and hard fires."""
    soft_turn = 30
    current_prior = soft_turn + NUDGE_MIN_TURNS_BETWEEN_TIERS - 1  # current = 33
    text, soft, hard = compute_thread_nudge(
        prior_message_count=current_prior,
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
        nudged_soft_turn_count=soft_turn,
    )
    assert "degrading" in text.lower()
    assert soft is False
    assert hard is True


def test_hard_unheld_when_soft_turn_count_unknown() -> None:
    """Legacy rows (soft fired before the turn-count column existed) carry
    NULL — no gap info, so hard keeps its pre-Phase-3 behaviour."""
    text, _soft, hard = compute_thread_nudge(
        prior_message_count=30,
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at="2026-05-03T14:00:00",
        nudged_hard_at=None,
        nudged_soft_turn_count=None,
    )
    assert "degrading" in text.lower()
    assert hard is True


def test_hard_from_cold_not_held_by_gap_guard() -> None:
    """No prior soft fire — the guard only applies after soft has fired."""
    text, soft, hard = compute_thread_nudge(
        prior_message_count=NUDGE_HARD_TURNS - 1,
        last_turn_context_tokens=NUDGE_HARD_TOKENS,
        nudged_soft_at=None,
        nudged_hard_at=None,
        nudged_soft_turn_count=None,
    )
    assert "degrading" in text.lower()
    assert soft is True
    assert hard is True


# ---------------------------------------------------------------------------
# _extract_context_tokens
# ---------------------------------------------------------------------------


def test_extract_context_tokens_sums_all_three_components() -> None:
    usage = {
        "input_tokens": 1_000,
        "cache_read_input_tokens": 50_000,
        "cache_creation_input_tokens": 4_000,
        "output_tokens": 800,  # ignored — only input-side tokens matter
    }
    assert _extract_context_tokens(usage) == 55_000


def test_extract_context_tokens_handles_missing_keys() -> None:
    assert _extract_context_tokens({"input_tokens": 100}) == 100
    assert _extract_context_tokens({}) == 0
    assert _extract_context_tokens(None) == 0


def test_extract_context_tokens_skips_non_int_values() -> None:
    """Defensive: SDK could in principle return None or stringy values."""
    usage = {
        "input_tokens": None,
        "cache_read_input_tokens": "5000",  # not an int — skip
        "cache_creation_input_tokens": 7,
    }
    assert _extract_context_tokens(usage) == 7
