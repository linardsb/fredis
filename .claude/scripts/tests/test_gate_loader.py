"""Tests for gate_schema + gate_loader."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from gate_loader import evaluate_gates, load_gates, render_breach_draft
from gate_schema import Gate, gate_from_dict


def test_gate_from_dict_happy_path() -> None:
    data = {
        "lane": "vtv",
        "metric": "signed_loi",
        "threshold": "one signed LOI",
        "deadline": "2026-10-20",
        "observable_source": "gmail_search:'subject:LOI'",
        "pre_committed_at": "2026-04-20",
        "status": "open",
        "rationale": "VTV kill trigger — month-6",
        "invalidator": "signed LOI from any LV operator",
    }
    gate = gate_from_dict(data)
    assert gate.lane == "vtv"
    assert gate.deadline == date(2026, 10, 20)
    assert gate.pre_committed_at == date(2026, 4, 20)
    assert gate.status == "open"


def test_gate_from_dict_missing_required_field() -> None:
    data = {"lane": "vtv"}
    with pytest.raises(ValueError, match="required"):
        gate_from_dict(data)


def test_gate_from_dict_invalid_status() -> None:
    data = {
        "lane": "vtv",
        "metric": "x",
        "threshold": "y",
        "deadline": "2026-10-20",
        "observable_source": "z",
        "pre_committed_at": "2026-04-20",
        "status": "nope",
    }
    with pytest.raises(ValueError, match="status"):
        gate_from_dict(data)


def test_load_gates_missing_dir(tmp_path: Path) -> None:
    assert load_gates(tmp_path / "nope") == []


def test_load_gates_reads_valid_files(tmp_path: Path) -> None:
    yaml_content = """
lane: email-hub
metric: ip_answer
threshold: written carve-out from Merkle
deadline: 2026-06-20
observable_source: gmail_search:"from:merkle"
pre_committed_at: 2026-04-20
status: open
rationale: Email Hub kill trigger
invalidator: written carve-out received
"""
    (tmp_path / "email-hub.yaml").write_text(yaml_content, encoding="utf-8")
    gates = load_gates(tmp_path)
    assert len(gates) == 1
    assert gates[0].lane == "email-hub"
    assert gates[0].deadline == date(2026, 6, 20)


def test_load_gates_skips_invalid(tmp_path: Path) -> None:
    (tmp_path / "bad.yaml").write_text("not: a: valid: yaml :::", encoding="utf-8")
    (tmp_path / "good.yaml").write_text(
        """
lane: vtv
metric: loi
threshold: one LOI
deadline: 2026-10-20
observable_source: gmail
pre_committed_at: 2026-04-20
""",
        encoding="utf-8",
    )
    gates = load_gates(tmp_path)
    assert len(gates) == 1
    assert gates[0].lane == "vtv"


def test_evaluate_gates_deadline_elapsed_breaches() -> None:
    past_gate = Gate(
        lane="email-hub",
        metric="ip",
        threshold="carve-out",
        deadline=date(2020, 1, 1),
        observable_source="gmail",
        pre_committed_at=date(2019, 12, 1),
        status="open",
        rationale="test",
        invalidator="x",
    )
    breaches = evaluate_gates([past_gate], today=date(2026, 4, 20))
    assert len(breaches) == 1
    assert breaches[0].gate is past_gate
    assert "elapsed" in breaches[0].reason


def test_evaluate_gates_future_deadline_ok() -> None:
    future_gate = Gate(
        lane="vtv",
        metric="loi",
        threshold="one LOI",
        deadline=date(2030, 1, 1),
        observable_source="gmail",
        pre_committed_at=date(2026, 4, 20),
        status="open",
    )
    assert evaluate_gates([future_gate], today=date(2026, 4, 20)) == []


def test_evaluate_gates_skips_non_open_status() -> None:
    past_closed_gate = Gate(
        lane="cab",
        metric="vtv_traction",
        threshold="distribution base",
        deadline=date(2020, 1, 1),
        observable_source="crm",
        pre_committed_at=date(2019, 12, 1),
        status="closed",
    )
    assert evaluate_gates([past_closed_gate], today=date(2026, 4, 20)) == []


def test_render_breach_draft_substitutes_fields() -> None:
    gate = Gate(
        lane="vtv",
        metric="loi",
        threshold="one signed LOI",
        deadline=date(2026, 10, 20),
        observable_source="gmail_search",
        pre_committed_at=date(2026, 4, 20),
        rationale="VTV month-6 trigger",
        invalidator="signed LOI",
    )
    breaches = evaluate_gates([Gate(
        lane=gate.lane, metric=gate.metric, threshold=gate.threshold,
        deadline=date(2020, 1, 1), observable_source=gate.observable_source,
        pre_committed_at=gate.pre_committed_at, status="open",
        rationale=gate.rationale, invalidator=gate.invalidator,
    )], today=date(2026, 4, 20))
    template = (
        "lane={lane} metric={metric} reason={reason} "
        "rationale={rationale} invalidator={invalidator}"
    )
    rendered = render_breach_draft(breaches[0], template)
    assert "lane=vtv" in rendered
    assert "metric=loi" in rendered
    assert "elapsed" in rendered
    assert "VTV month-6 trigger" in rendered
