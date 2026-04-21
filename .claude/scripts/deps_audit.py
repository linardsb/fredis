"""
Weekly Dependency Audit

Runs `pip-audit` (primary) and `safety check` (second opinion) against
`.claude/scripts/pyproject.toml`. Appends a summary block to today's
daily log under the "Dependency Audit" section.

Exits non-zero on any HIGH or CRITICAL severity finding so the scheduler
surface (launchd StandardErrorPath / systemd journal) alerts.

Usage:
    uv run python deps_audit.py              # run + write daily-log entry
    uv run python deps_audit.py --test       # dry-run: stdout only, no log append

Scheduling (Phase 9.5):
    macOS launchd → com.linards.fredis-deps-audit.plist (Mon 09:00 local)
    Linux systemd → deps-audit.service + deps-audit.timer (OnCalendar=Mon *-*-* 09:00:00)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from config import PROJECT_ROOT, now_local
from shared import append_to_daily_log

SCRIPTS_DIR = Path(__file__).resolve().parent


def _run_pip_audit() -> dict[str, Any]:
    """Run `uv run --with pip-audit pip-audit --format=json`. Returns
    a parsed JSON dict with a ``vulnerabilities`` list or an ``error`` key
    on failure.
    """
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "pip-audit",
                "pip-audit",
                "--format=json",
            ],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError as e:
        return {"error": f"uv not found: {e}", "vulnerabilities": []}
    except subprocess.TimeoutExpired:
        return {"error": "pip-audit timed out after 10 min", "vulnerabilities": []}

    # pip-audit returns 0 = clean, 1 = vulns found, other = error.
    if result.returncode not in (0, 1):
        return {
            "error": f"pip-audit failed (exit={result.returncode}): {result.stderr[:500]}",
            "vulnerabilities": [],
        }

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {
            "error": f"pip-audit output not JSON: {e}; stdout={result.stdout[:200]}",
            "vulnerabilities": [],
        }

    # pip-audit 2.x schema: {"dependencies": [{..., "vulns": [...]}]}
    vulns: list[dict[str, Any]] = []
    for dep in parsed.get("dependencies", []):
        for v in dep.get("vulns", []):
            vulns.append(
                {
                    "package": dep.get("name"),
                    "installed": dep.get("version"),
                    "id": v.get("id"),
                    "description": v.get("description", "")[:200],
                    "fix_versions": v.get("fix_versions", []),
                }
            )
    return {"vulnerabilities": vulns}


def _run_safety() -> dict[str, Any]:
    """Run `uv run --with safety safety check --json`. Returns a dict
    similar to _run_pip_audit.
    """
    try:
        result = subprocess.run(
            [
                "uv",
                "run",
                "--with",
                "safety",
                "safety",
                "check",
                "--json",
            ],
            cwd=str(SCRIPTS_DIR),
            capture_output=True,
            text=True,
            timeout=600,
        )
    except FileNotFoundError as e:
        return {"error": f"uv not found: {e}", "vulnerabilities": []}
    except subprocess.TimeoutExpired:
        return {"error": "safety timed out after 10 min", "vulnerabilities": []}

    # safety exit codes: 0 = no vulns, 64 = vulns found, 65 = no requirements, etc.
    if result.returncode not in (0, 64):
        # Safety may require auth for some features — soft-fail on non-64 non-zero.
        return {
            "error": f"safety non-fatal exit={result.returncode}: {result.stderr[:500]}",
            "vulnerabilities": [],
        }

    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError:
        # Older safety versions emit non-JSON on clean runs.
        return {"vulnerabilities": []}

    vulns: list[dict[str, Any]] = []
    # safety JSON schema varies by version; handle the most common shape.
    items = parsed.get("vulnerabilities") or parsed.get("affected_packages") or []
    if isinstance(items, list):
        for v in items:
            vulns.append(
                {
                    "package": v.get("package_name") or v.get("package"),
                    "installed": v.get("analyzed_version") or v.get("installed_version"),
                    "id": v.get("vulnerability_id") or v.get("cve"),
                    "description": (v.get("advisory") or v.get("description", ""))[:200],
                    "fix_versions": v.get("fixed_versions") or [],
                }
            )
    return {"vulnerabilities": vulns}


def _format_summary(pip_audit: dict[str, Any], safety: dict[str, Any]) -> tuple[str, bool]:
    """Return (daily-log-block, has_high_or_critical)."""
    today = now_local().strftime("%Y-%m-%d")
    lines: list[str] = [f"### Dependency Audit — {today}", ""]

    has_critical = False

    # pip-audit section
    pa_err = pip_audit.get("error")
    pa_vulns = pip_audit.get("vulnerabilities", [])
    if pa_err:
        lines.append(f"- **pip-audit**: ERROR — {pa_err}")
    elif not pa_vulns:
        lines.append("- **pip-audit**: 0 vulnerabilities found")
    else:
        lines.append(f"- **pip-audit**: {len(pa_vulns)} vulnerabilities found")
        for v in pa_vulns:
            fix = ", ".join(v.get("fix_versions") or []) or "no fix"
            lines.append(
                f"    - `{v.get('package')}` {v.get('installed')} — "
                f"{v.get('id')}: {v.get('description', '')} (fix: {fix})"
            )
        # Heuristic: if any vuln description contains HIGH/CRITICAL tokens, flag it.
        for v in pa_vulns:
            desc = (v.get("description") or "").lower()
            if "critical" in desc or "high severity" in desc:
                has_critical = True

    # safety section
    sa_err = safety.get("error")
    sa_vulns = safety.get("vulnerabilities", [])
    if sa_err:
        lines.append(f"- **safety**: ERROR — {sa_err}")
    elif not sa_vulns:
        lines.append("- **safety**: 0 vulnerabilities found")
    else:
        lines.append(f"- **safety**: {len(sa_vulns)} vulnerabilities found")
        for v in sa_vulns:
            fix = ", ".join(v.get("fix_versions") or []) or "no fix"
            lines.append(
                f"    - `{v.get('package')}` {v.get('installed')} — "
                f"{v.get('id')}: {v.get('description', '')} (fix: {fix})"
            )
        for v in sa_vulns:
            desc = (v.get("description") or "").lower()
            if "critical" in desc or "high" in desc:
                has_critical = True

    return "\n".join(lines), has_critical


def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly dependency vulnerability audit")
    parser.add_argument("--test", action="store_true", help="Dry run — stdout only")
    args = parser.parse_args()

    print(f"[{now_local()}] Running pip-audit + safety in {PROJECT_ROOT}...")

    pip_audit = _run_pip_audit()
    safety = _run_safety()

    summary, has_critical = _format_summary(pip_audit, safety)

    if args.test:
        print("\n--- DRY RUN ---")
        print(summary)
        print("--- END DRY RUN ---")
        return 0

    append_to_daily_log(
        summary,
        "Dependency Audit",
        "Memory Maintenance",
        source="deps-audit",
    )
    print(f"[{now_local()}] Daily log updated with dependency audit summary")

    # Exit non-zero on HIGH/CRITICAL so the scheduler alerts.
    return 1 if has_critical else 0


if __name__ == "__main__":
    sys.exit(main())
