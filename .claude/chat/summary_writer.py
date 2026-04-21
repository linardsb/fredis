"""Per-turn chat summary writer — Phase 11 channel-routed vault capture.

After each successful chat turn (`ResultMessage` received), the engine calls
`append_summary()`. The writer creates or appends to a markdown file under the
channel's vault folder with one block per turn.

Lazy-create policy: the target folder is created on first write (plan §5.5 = B).

Failure policy: `append_summary()` is non-fatal — callers should wrap in
try/except. Any exception here must NOT break the user-facing chat reply.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

# Cap the summary heading at this length so we don't dump an entire prompt
# into the top of the file.
_SUMMARY_HEADING_MAX = 80

# Cap the filename slug at this length.
_SLUG_MAX = 40

_SLUG_SANITIZE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class SummaryWriteResult:
    """Outcome of an `append_summary` call — returned for observability."""

    path: Path
    turn_number: int
    created: bool


def append_summary(
    folder: Path,
    channel: str | None,
    channel_id: str,
    thread_ts: str,
    user_text: str,
    bot_text: str,
    timestamp: datetime,
    cost_usd: float | None = None,
    slack_permalink: str | None = None,
) -> SummaryWriteResult:
    """Create or append a per-turn summary file in ``folder``.

    Filename: ``YYYY-MM-DD_<thread_ts>_<slug>.md`` where slug derives from
    the first turn's user text. Subsequent turns in the same thread find the
    existing file via a `YYYY-MM-DD_<thread_ts>_*.md` glob and append to it.
    """
    folder.mkdir(parents=True, exist_ok=True)

    date_str = timestamp.strftime("%Y-%m-%d")
    ts_safe = thread_ts  # dots are filesystem-safe everywhere we run

    existing = _find_existing(folder, date_str, ts_safe)

    if existing is None:
        path = folder / f"{date_str}_{ts_safe}_{_slugify(user_text)}.md"
        content = _render_initial(
            channel=channel,
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_text=user_text,
            bot_text=bot_text,
            timestamp=timestamp,
            cost_usd=cost_usd,
            slack_permalink=slack_permalink,
        )
        path.write_text(content, encoding="utf-8")
        return SummaryWriteResult(path=path, turn_number=1, created=True)

    # Append mode: bump frontmatter, add turn block.
    new_text, turn_number = _render_append(
        existing_text=existing.read_text(encoding="utf-8"),
        user_text=user_text,
        bot_text=bot_text,
        timestamp=timestamp,
        cost_usd=cost_usd,
    )
    existing.write_text(new_text, encoding="utf-8")
    return SummaryWriteResult(path=existing, turn_number=turn_number, created=False)


def _find_existing(folder: Path, date_str: str, thread_ts: str) -> Path | None:
    """Locate a prior summary file for this thread on this date."""
    pattern = f"{date_str}_{thread_ts}_*.md"
    matches = sorted(folder.glob(pattern))
    return matches[0] if matches else None


def _slugify(text: str) -> str:
    """Filesystem-safe short slug from the first-turn user text."""
    cleaned = _SLUG_SANITIZE.sub("-", text.lower()).strip("-")
    if not cleaned:
        return "thread"
    return cleaned[:_SLUG_MAX].rstrip("-") or "thread"


def _summary_heading(text: str) -> str:
    """One-line summary from the first turn. Strips leading `#` so it doesn't
    collide with the literal heading marker we emit on top of the file."""
    one_line = " ".join(text.split())
    one_line = one_line.lstrip("#").strip()
    if len(one_line) > _SUMMARY_HEADING_MAX:
        one_line = one_line[: _SUMMARY_HEADING_MAX - 1].rstrip() + "…"
    return one_line or "Conversation"


def _render_initial(
    *,
    channel: str | None,
    channel_id: str,
    thread_ts: str,
    user_text: str,
    bot_text: str,
    timestamp: datetime,
    cost_usd: float | None,
    slack_permalink: str | None,
) -> str:
    frontmatter: dict[str, object] = {
        "channel": channel or "",
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "created_at": timestamp.isoformat(),
        "updated_at": timestamp.isoformat(),
        "turns": 1,
    }
    if slack_permalink:
        frontmatter["slack_permalink"] = slack_permalink
    if cost_usd is not None:
        frontmatter["total_cost_usd"] = round(cost_usd, 6)

    fm = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    heading = _summary_heading(user_text)
    block = _format_turn_block(1, timestamp, user_text, bot_text, cost_usd)

    return f"---\n{fm}\n---\n\n# {heading}\n\n{block}\n"


def _render_append(
    *,
    existing_text: str,
    user_text: str,
    bot_text: str,
    timestamp: datetime,
    cost_usd: float | None,
) -> tuple[str, int]:
    """Parse existing frontmatter, bump `turns` + `updated_at`, append turn block.

    Preserves the body (including the `# <heading>` line) verbatim.
    """
    fm_data, body = _split_frontmatter(existing_text)
    turns_before = int(fm_data.get("turns") or 1)
    turn_number = turns_before + 1

    fm_data["turns"] = turn_number
    fm_data["updated_at"] = timestamp.isoformat()
    if cost_usd is not None:
        prior = float(fm_data.get("total_cost_usd") or 0.0)
        fm_data["total_cost_usd"] = round(prior + cost_usd, 6)

    new_fm = yaml.safe_dump(fm_data, sort_keys=False, allow_unicode=True).strip()
    trimmed_body = body.rstrip() + "\n\n"
    block = _format_turn_block(turn_number, timestamp, user_text, bot_text, cost_usd)

    new_text = f"---\n{new_fm}\n---\n{trimmed_body}{block}\n"
    return new_text, turn_number


def _split_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Return `(frontmatter_dict, body_including_leading_blank_line)`.

    Tolerant: if the file has no frontmatter, returns an empty dict plus the
    whole text as body. Later writes will then re-render with fresh frontmatter
    driven by `turns_before = 1`.
    """
    if not text.startswith("---"):
        return {}, text

    # Split into `["", fm_yaml, body...]`
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    fm_yaml = parts[1].strip()
    body = parts[2]
    try:
        data = yaml.safe_load(fm_yaml) or {}
    except yaml.YAMLError:
        return {}, text
    if not isinstance(data, dict):
        return {}, text
    # Strip leading newline left by `---\n` so callers control spacing.
    return data, body.lstrip("\n")


def _format_turn_block(
    turn_number: int,
    timestamp: datetime,
    user_text: str,
    bot_text: str,
    cost_usd: float | None,
) -> str:
    when = timestamp.strftime("%H:%M")
    cost_suffix = f" · ${cost_usd:.4f}" if cost_usd is not None else ""
    return (
        f"## Turn {turn_number} · {when}{cost_suffix}\n\n"
        f"**You:** {user_text.strip()}\n\n"
        f"**Fredis:** {bot_text.strip()}\n"
    )
