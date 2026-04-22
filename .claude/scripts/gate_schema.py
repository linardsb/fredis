"""Gate schema — YAML kill-criteria surfaced by the heartbeat.

A Gate is a pre-committed kill trigger on a product lane (Email Hub / VTV / Cab).
`launch-governance/metrics-gate` writes these; the heartbeat reads them on each
tick and emits breach drafts when a gate fires.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

GateStatus = Literal["open", "breached", "closed"]
VALID_STATUSES: set[str] = {"open", "breached", "closed"}


@dataclass
class Gate:
    """Pre-committed kill criterion for a product lane.

    Fields:
        lane: product lane slug ("email-hub" | "vtv" | "cab" | free-form)
        metric: short slug naming what is measured
        threshold: human-readable threshold (e.g., "signed LOI", "< 10 users")
        deadline: date by which the threshold must be met
        observable_source: free-form tag describing how to observe the metric
            (e.g., 'gmail_search:"from:merkle"', 'hubspot:contacts/urgent_alert')
        pre_committed_at: date the gate was committed
        status: open / breached / closed
        rationale: why the gate exists
        invalidator: what evidence would retire the gate (the opposite of
            "kill trigger fires"; forces pre-commitment honesty)
    """

    lane: str
    metric: str
    threshold: str
    deadline: date
    observable_source: str
    pre_committed_at: date
    status: GateStatus = "open"
    rationale: str = ""
    invalidator: str = ""


@dataclass
class GateBreach:
    """The result of evaluating an open gate against current state."""

    gate: Gate
    reason: str  # human-readable — e.g., "deadline elapsed 2026-04-18"
    breach_keys: list[str] = field(default_factory=list)  # ["deadline"] or ["threshold"]


def gate_from_dict(data: Mapping[str, object]) -> Gate:
    """Construct a Gate from a parsed-YAML dict.

    Coerces ISO date strings to date objects. Raises ValueError on bad input.
    """

    def _as_str(key: str, required: bool = True, default: str = "") -> str:
        val = data.get(key, default)
        if required and not val:
            raise ValueError(f"gate field '{key}' is required")
        if not isinstance(val, str):
            raise ValueError(f"gate field '{key}' must be string, got {type(val).__name__}")
        return val

    def _as_date(key: str) -> date:
        val = data.get(key)
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            return date.fromisoformat(val)
        raise ValueError(
            f"gate field '{key}' must be ISO date string or date, got {type(val).__name__}"
        )

    status = data.get("status", "open")
    if status not in VALID_STATUSES:
        raise ValueError(f"gate status must be one of {VALID_STATUSES}, got {status!r}")

    return Gate(
        lane=_as_str("lane"),
        metric=_as_str("metric"),
        threshold=_as_str("threshold"),
        deadline=_as_date("deadline"),
        observable_source=_as_str("observable_source"),
        pre_committed_at=_as_date("pre_committed_at"),
        status=status,  # type: ignore[arg-type]
        rationale=_as_str("rationale", required=False),
        invalidator=_as_str("invalidator", required=False),
    )
