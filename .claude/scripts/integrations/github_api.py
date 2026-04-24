"""
GitHub Direct Integration for Second Brain.

Uses GitHub REST API v3. Raw `requests` (no PyGithub) for consistency with
the Monday integration and to avoid an extra dependency.

The heartbeat uses this primarily to auto-tick the Ship habit pillar: if
Linards has ≥1 PushEvent in the last 24h, Ship is ticked. PR review requests
and issue mentions are secondary signals.

Usage:
    uv run python -m integrations.github_api recent --hours 24
    uv run python -m integrations.github_api review-requests
    uv run python -m integrations.github_api mentions --hours 168

Setup:
    1. https://github.com/settings/tokens → generate token (classic or
       fine-grained) with `repo` + `read:user` scopes
    2. Add GITHUB_TOKEN + GITHUB_USERNAME to .env
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import GITHUB_TOKEN, GITHUB_USERNAME  # noqa: E402
from sanitize import sanitize_external_text, wrap_external_data  # noqa: E402
from shared import with_retry  # noqa: E402

GITHUB_API_URL = "https://api.github.com"


@dataclass
class GitHubEvent:
    """A simplified GitHub user event (Push, PR, PR review comment, etc.)."""

    id: str
    type: str  # PushEvent | PullRequestEvent | IssuesEvent | ...
    repo: str
    created_at: datetime
    summary: str  # human-readable one-liner
    url: str = ""


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------


def _headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise ValueError(
            "GITHUB_TOKEN not set in .env\n"
            "Generate a PAT at https://github.com/settings/tokens "
            "with `repo` + `read:user` scopes."
        )
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fredis-secondbrain",
    }


def _get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET a GitHub endpoint, returning the decoded JSON body.

    Respects rate-limit responses by logging the remaining quota.
    """
    url = path if path.startswith("http") else f"{GITHUB_API_URL}{path}"

    def do_get() -> requests.Response:
        return requests.get(url, headers=_headers(), params=params, timeout=30)

    resp: requests.Response = with_retry(do_get)
    if resp.status_code == 401:
        raise RuntimeError("GitHub returned 401 — rotate GITHUB_TOKEN")
    if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
        reset = resp.headers.get("X-RateLimit-Reset", "?")
        raise RuntimeError(f"GitHub rate limit exhausted; resets at unix={reset}")
    resp.raise_for_status()

    remaining = resp.headers.get("X-RateLimit-Remaining")
    if remaining and int(remaining) < 100:
        print(f"[github] rate-limit warning: {remaining} requests left this hour")

    return resp.json()


def _parse_created_at(raw: str) -> datetime:
    """Parse GitHub's ISO 8601 Z-suffixed timestamps into aware datetimes."""
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def recent_commits(hours: int = 24) -> list[GitHubEvent]:
    """Return PushEvents by GITHUB_USERNAME in the last N hours.

    Used by HABITS.md Ship-pillar auto-detection: a single push in the window
    is enough to tick Ship.
    """
    if not GITHUB_USERNAME:
        return []
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    events = _get(f"/users/{GITHUB_USERNAME}/events", {"per_page": 100})

    out: list[GitHubEvent] = []
    for ev in events or []:
        if ev.get("type") != "PushEvent":
            continue
        created = _parse_created_at(ev["created_at"])
        if created < cutoff:
            continue
        repo = (ev.get("repo") or {}).get("name", "")
        payload = ev.get("payload") or {}
        commit_count = len(payload.get("commits") or [])
        branch = (payload.get("ref") or "").replace("refs/heads/", "")
        summary = f"{commit_count} commit(s) → {repo}@{branch}"
        out.append(
            GitHubEvent(
                id=str(ev.get("id", "")),
                type="PushEvent",
                repo=repo,
                created_at=created,
                summary=summary,
                url=f"https://github.com/{repo}/commits/{branch}" if repo else "",
            )
        )
    return out


def review_requests() -> list[GitHubEvent]:
    """Open PRs that request review from GITHUB_USERNAME (across all repos)."""
    if not GITHUB_USERNAME:
        return []
    q = f"is:pr state:open review-requested:{GITHUB_USERNAME}"
    data = _get("/search/issues", {"q": q, "per_page": 25})
    out: list[GitHubEvent] = []
    for item in data.get("items", []) or []:
        try:
            created = _parse_created_at(item["updated_at"])
        except (KeyError, ValueError):
            created = datetime.now(UTC)
        repo_url = item.get("repository_url", "")
        repo = repo_url.rsplit("/", 2)[-2] + "/" + repo_url.rsplit("/", 1)[-1] if repo_url else ""
        out.append(
            GitHubEvent(
                id=str(item.get("id", "")),
                type="PullRequestReviewRequest",
                repo=repo,
                created_at=created,
                summary=str(item.get("title", "")),
                url=str(item.get("html_url", "")),
            )
        )
    return out


def issues_mentioning_me(hours: int = 168) -> list[GitHubEvent]:
    """Open issues that @-mention GITHUB_USERNAME, updated in the last N hours."""
    if not GITHUB_USERNAME:
        return []
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    q = f"is:issue state:open mentions:{GITHUB_USERNAME}"
    data = _get("/search/issues", {"q": q, "sort": "updated", "per_page": 25})
    out: list[GitHubEvent] = []
    for item in data.get("items", []) or []:
        try:
            updated = _parse_created_at(item["updated_at"])
        except (KeyError, ValueError):
            continue
        if updated < cutoff:
            continue
        repo_url = item.get("repository_url", "")
        repo = repo_url.rsplit("/", 2)[-2] + "/" + repo_url.rsplit("/", 1)[-1] if repo_url else ""
        out.append(
            GitHubEvent(
                id=str(item.get("id", "")),
                type="IssueMention",
                repo=repo,
                created_at=updated,
                summary=str(item.get("title", "")),
                url=str(item.get("html_url", "")),
            )
        )
    return out


def ship_signal(hours: int = 24) -> bool:
    """True if Linards has pushed at least one commit in the window (Ship-pillar signal)."""
    return len(recent_commits(hours=hours)) > 0


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def format_events_for_context(events: list[GitHubEvent]) -> str:
    """Format a mixed list of events for Claude's context, XML-wrapped."""
    if not events:
        return wrap_external_data("No GitHub activity.", "github")

    by_type: dict[str, list[GitHubEvent]] = {}
    for ev in events:
        by_type.setdefault(ev.type, []).append(ev)

    sections: list[str] = []
    for ev_type in sorted(by_type):
        sections.append(f"## {ev_type}")
        for ev in by_type[ev_type]:
            summary = sanitize_external_text(ev.summary, "github")
            when = ev.created_at.strftime("%Y-%m-%d %H:%M UTC")
            line = f"- **{summary}** ({ev.repo})\n  {when}"
            sections.append(line)

    return wrap_external_data("\n".join(sections), "github")


# ---------------------------------------------------------------------------
# CLI for testing
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub integration")
    parser.add_argument("command", choices=["recent", "review-requests", "mentions", "ship"])
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()

    if args.command == "recent":
        print(format_events_for_context(recent_commits(hours=args.hours)))
    elif args.command == "review-requests":
        print(format_events_for_context(review_requests()))
    elif args.command == "mentions":
        print(format_events_for_context(issues_mentioning_me(hours=args.hours)))
    elif args.command == "ship":
        print("ship_signal:", ship_signal(hours=args.hours))
