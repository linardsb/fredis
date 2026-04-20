"""Gate loader + evaluator for the heartbeat.

Reads YAML gate files from `Fredis/Memory/gates/*.yaml`, evaluates each open
gate against current time (and, where applicable, the heartbeat snapshot),
and returns a list of breaches. Pure: no side effects, no I/O beyond reading
the gates directory.

Heartbeat writes breach drafts to `Fredis/Memory/drafts/active/launch-governance/metrics-gate/`.
"""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from gate_schema import Gate, GateBreach, gate_from_dict

logger = logging.getLogger(__name__)


def load_gates(gates_dir: Path) -> list[Gate]:
    """Load every `*.yaml` in gates_dir into Gate objects.

    Skips files that fail to parse (logged at WARNING). Never raises.
    """
    gates: list[Gate] = []
    if not gates_dir.exists():
        return gates
    for path in sorted(gates_dir.glob("*.yaml")):
        try:
            text = path.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
            if data is None:
                continue
            if isinstance(data, dict):
                gates.append(gate_from_dict(data))
            elif isinstance(data, list):
                for entry in data:
                    if isinstance(entry, dict):
                        gates.append(gate_from_dict(entry))
            else:
                logger.warning("gate_loader.skip %s — top-level must be mapping or list", path.name)
        except (yaml.YAMLError, ValueError, KeyError) as exc:
            logger.warning("gate_loader.parse_failed %s — %s", path.name, exc)
    return gates


def evaluate_gates(
    gates: list[Gate],
    snapshot: dict[str, Any] | None = None,
    today: date | None = None,
) -> list[GateBreach]:
    """Evaluate open gates against today's date.

    Current logic: a gate breaches when status=open AND deadline has passed.
    Threshold-evaluation against `snapshot` is a future extension; the
    `observable_source` string is passed through to the breach draft so
    Linards can see how to verify manually.

    Returns an empty list when no gates breach. Closed and already-breached
    gates are skipped (the breach has already been surfaced).
    """
    when = today if today is not None else date.today()
    breaches: list[GateBreach] = []
    for gate in gates:
        if gate.status != "open":
            continue
        if gate.deadline < when:
            days_over = (when - gate.deadline).days
            reason = f"deadline {gate.deadline.isoformat()} elapsed ({days_over}d overdue)"
            breaches.append(GateBreach(gate=gate, reason=reason, breach_keys=["deadline"]))
    return breaches


def render_breach_draft(breach: GateBreach, template: str) -> str:
    """Substitute gate fields into the breach template."""
    gate = breach.gate
    return (
        template.replace("{lane}", gate.lane)
        .replace("{metric}", gate.metric)
        .replace("{threshold}", gate.threshold)
        .replace("{deadline}", gate.deadline.isoformat())
        .replace("{reason}", breach.reason)
        .replace("{rationale}", gate.rationale or "(not specified)")
        .replace("{invalidator}", gate.invalidator or "(not specified)")
        .replace("{observable_source}", gate.observable_source)
    )
