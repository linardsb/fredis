"""PRD gate for the Archon build harness — HITL #1.

A run's input is ONLY ever an APPROVED lean-PRD / enriched-issue artifact from
`Fredis/Memory/drafts/active/the-team/` — never a free-form string. This is the
first of the two HITL gates a solo operator can afford (the second is the
draft-PR review). **No approved PRD -> no run.**

Approval is a **Linards-only action**, as hard a boundary as never-send: Fredis
DRAFTS the PRD *without* the flag; only Linards sets `approved: true` in the
front-matter. The gate enforces the flag's presence — the convention that only
Linards flips it is what makes the file flag equivalent to human sign-off. (The
impl-plan's open-Q5 floats a stronger form — a HubSpot "Needs send" stage — but
the front-matter flag is the chosen mechanism.)

Pure module: filesystem + parsing only, no network. Fully unit-testable, and the
gate is checked BEFORE any HTTP call so a refusal never touches the engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from config import THE_TEAM_DRAFTS_DIR


class GateError(RuntimeError):
    """The run is refused — no resolvable APPROVED PRD artifact."""


@dataclass
class ApprovedPRD:
    """A resolved, approved run input."""

    path: Path
    message: str  # the run input ($ARGUMENTS) — the PRD body, front-matter stripped


def _split_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Return (front_matter_dict, body). No/invalid front-matter -> ({}, text).

    Same `---`-delimited convention as the rest of the vault (cf.
    `gmail.create_gmail_draft_from_file`), parsed with PyYAML so `approved: true`
    is a real bool, not the string "true".
    """
    if not text.startswith("---"):
        return {}, text
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, text
    fm_raw = text[3:end]
    body = text[end + 3 :].lstrip("\n")
    try:
        data = yaml.safe_load(fm_raw)
    except yaml.YAMLError:
        return {}, body
    return (data if isinstance(data, dict) else {}), body


def _is_approved(meta: dict[str, Any]) -> bool:
    """True only for a real boolean `approved: true` — the string "true" or a
    truthy-but-not-True value does NOT pass (approval must be unambiguous)."""
    return meta.get("approved") is True


def load_prd(path: Path) -> ApprovedPRD:
    """Load one artifact, enforcing approval + non-empty body. Raises GateError."""
    text = path.read_text(encoding="utf-8")
    meta, body = _split_frontmatter(text)
    if not _is_approved(meta):
        raise GateError(
            f"'{path.name}' is not approved. A run needs front-matter "
            f"`approved: true` — which only Linards sets (Fredis drafts without "
            f"it). No approved PRD -> no run."
        )
    if not body.strip():
        raise GateError(
            f"'{path.name}' is approved but has no body — nothing to dispatch."
        )
    return ApprovedPRD(path=path, message=body.strip())


def _resolve_candidate(slug_or_path: str, base: Path) -> Path:
    """Map a slug or path to a concrete file confined to `base`.

    A slug (`phase1-PRD`) -> `base/phase1-PRD.md`. A path is resolved and must sit
    DIRECTLY inside `base` — this is what stops `--prd ../../etc/passwd` (or any
    file outside the gate dir) from becoming a run input.
    """
    raw = slug_or_path.strip()
    p = Path(raw)
    if "/" in raw or p.suffix == ".md":
        resolved = (p if p.is_absolute() else base / p).resolve()
    else:
        resolved = (base / f"{raw}.md").resolve()
    if resolved.parent != base.resolve():
        raise GateError(
            f"PRD must be a file directly inside {base}/ — '{slug_or_path}' "
            f"resolves outside the gate."
        )
    return resolved


def resolve_prd(
    slug_or_path: str | None, base_dir: Path | None = None
) -> ApprovedPRD:
    """Resolve the run input from an APPROVED artifact under the-team/.

    - `slug_or_path` given: resolve to `<base>/<slug>.md` (or a path that MUST be
      inside `base`); the file must exist and be approved.
    - omitted: auto-discover the single approved artifact under `base`. Zero ->
      refuse; more than one -> refuse and ask for an explicit `--prd <slug>`.

    A free-form string is never accepted as the input — it always comes from a
    resolved file, so the gate cannot be bypassed with `--prd "just do X"`.
    """
    base = base_dir or THE_TEAM_DRAFTS_DIR

    if slug_or_path:
        cand = _resolve_candidate(slug_or_path, base)
        if not cand.is_file():
            raise GateError(
                f"No PRD artifact at '{cand}'. Approved PRDs live in {base}/ as "
                f"<slug>.md with front-matter `approved: true`."
            )
        return load_prd(cand)

    if not base.is_dir():
        raise GateError(f"No PRD directory at {base} — nothing to dispatch.")
    approved: list[Path] = []
    for p in sorted(base.glob("*.md")):
        meta, body = _split_frontmatter(p.read_text(encoding="utf-8"))
        if _is_approved(meta) and body.strip():
            approved.append(p)
    if not approved:
        raise GateError(
            f"No approved PRD in {base}/. Approve one by setting front-matter "
            f"`approved: true` (a Linards-only action). No approved PRD -> no run."
        )
    if len(approved) > 1:
        names = ", ".join(p.stem for p in approved)
        raise GateError(
            f"Multiple approved PRDs ({names}) — pick one with --prd <slug>."
        )
    return load_prd(approved[0])
