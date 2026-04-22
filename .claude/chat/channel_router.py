"""Channel → vault-folder routing for the Slack chat interface.

Loads `.claude/config/channel-routing.yaml` once at startup and resolves incoming
messages to the folder under ``Fredis/Memory/`` where per-turn summaries land.

Lookup order for a non-DM channel:
    1. `by_id` map (channel ID → folder) — rename-resilient.
    2. `channels` map (channel name → folder).
    3. `defaults.fallback`.

DMs always hit `defaults.dm`. Unknown channel IDs with no name fall through to
`defaults.fallback`.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

MatchSource = Literal["by_id", "by_name", "dm_default", "fallback"]


@dataclass(frozen=True)
class RoutingConfig:
    """Parsed routing config. Folders are stored as relative POSIX strings
    exactly as they appear in the YAML (e.g. ``Fredis/Memory/ideation/``)."""

    channels: dict[str, str]
    by_id: dict[str, str]
    default_dm: str
    default_fallback: str


class ChannelRouter:
    """Resolve a Slack channel to the vault folder where chat summaries land."""

    def __init__(self, config_path: Path, project_root: Path) -> None:
        self._config_path = config_path
        self._project_root = project_root.resolve()
        self._config = self._load(config_path)

    @staticmethod
    def _load(path: Path) -> RoutingConfig:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError(
                f"channel-routing.yaml must be a mapping at top level, got {type(raw)}"
            )
        channels = raw.get("channels") or {}
        by_id = raw.get("by_id") or {}
        defaults = raw.get("defaults") or {}
        if (
            not isinstance(channels, dict)
            or not isinstance(by_id, dict)
            or not isinstance(defaults, dict)
        ):
            raise ValueError(
                "channel-routing.yaml: channels/by_id/defaults must all be mappings"
            )

        default_dm = defaults.get("dm") or "Fredis/Memory/daily/"
        default_fallback = defaults.get("fallback") or "Fredis/Memory/daily/"

        # Normalize: values must be strings, trailing slash tolerated.
        clean_channels = {str(k): str(v) for k, v in channels.items()}
        clean_by_id = {str(k): str(v) for k, v in by_id.items()}

        return RoutingConfig(
            channels=clean_channels,
            by_id=clean_by_id,
            default_dm=str(default_dm),
            default_fallback=str(default_fallback),
        )

    def resolve(
        self,
        channel_id: str,
        channel_name: str | None,
        is_dm: bool,
    ) -> Path:
        """Return the absolute vault folder for this channel/DM.

        Resolution order for non-DMs: `by_id[channel_id]` → `channels[channel_name]`
        → `defaults.fallback`. DMs always hit `defaults.dm`.

        The returned path is always under ``project_root`` and is NOT created —
        callers decide when to materialize (see `summary_writer.append_summary`).
        """
        path, _source = self.resolve_detail(channel_id, channel_name, is_dm)
        return path

    def resolve_detail(
        self,
        channel_id: str,
        channel_name: str | None,
        is_dm: bool,
    ) -> tuple[Path, MatchSource]:
        """Like `resolve()` but also returns how the match was made.

        The ``MatchSource`` tag lets callers decide whether a lookup was an
        explicit match (``"by_id"`` / ``"by_name"``) or a fallthrough
        (``"dm_default"`` / ``"fallback"``). Channel-scoped memory retrieval
        uses this to narrow search only for true channel matches.
        """
        source: MatchSource
        if is_dm:
            rel = self._config.default_dm
            source = "dm_default"
        else:
            rel = self._config.by_id.get(channel_id) or ""
            if rel:
                source = "by_id"
            else:
                if channel_name:
                    rel = self._config.channels.get(channel_name) or ""
                if rel:
                    source = "by_name"
                else:
                    rel = self._config.default_fallback
                    source = "fallback"

        return self._resolve_under_root(rel), source

    def resolve_override(self, target: str) -> Path:
        """Resolve a user-supplied save-to target to an absolute vault folder.

        Lookup order:
            1. `channels:` YAML map — if ``target`` is a configured channel
               name (e.g. ``"email-hub"``, ``"build-email-hub"``, ``"marketing"``),
               return its mapped folder.
            2. Treat ``target`` as a relative subpath under ``Fredis/Memory/``
               (e.g. ``"research/ai/sora"`` → ``Fredis/Memory/research/ai/sora/``).

        Raises ``ValueError`` if the target is empty, contains disallowed
        characters, or resolves outside the vault root.
        """
        if not target or not target.strip():
            raise ValueError("save target is empty")

        clean = target.strip().strip("/")
        # Defence-in-depth — the parser already filters these, but guard here
        # too so direct callers (e.g. scripts) can't smuggle traversal.
        if ".." in clean.split("/") or "\\" in clean:
            raise ValueError(f"save target {target!r} contains disallowed segments")

        # 1) Configured channel name.
        if clean in self._config.channels:
            rel = self._config.channels[clean]
            return self._resolve_under_root(rel)

        # 2) Free-form relative path under Fredis/Memory/.
        rel = f"Fredis/Memory/{clean}/"
        return self._resolve_under_root(rel)

    def memory_prefix(
        self,
        channel_id: str,
        channel_name: str | None,
        is_dm: bool,
        memory_dir: Path,
    ) -> str:
        """Return a `path_prefix` (e.g. ``"marketing/"``) suitable for
        `memory_search.search_hybrid(path_prefix=...)`, or ``""`` when the
        resolution was a DM default or fallback — in which case channel-scoped
        search would just mirror a subset of the global search and is skipped.
        """
        folder, source = self.resolve_detail(channel_id, channel_name, is_dm)
        if source in ("dm_default", "fallback"):
            return ""
        try:
            rel = folder.resolve().relative_to(memory_dir.resolve())
        except ValueError:
            # Folder is outside Memory/ — can't build a prefix; skip scoping.
            return ""
        prefix = rel.as_posix()
        return prefix + "/" if prefix and not prefix.endswith("/") else prefix

    def _resolve_under_root(self, rel: str) -> Path:
        """Join a relative vault path to project root, rejecting traversal."""
        candidate = (self._project_root / rel).resolve()
        # Guard: resolved path must remain inside project_root.
        try:
            candidate.relative_to(self._project_root)
        except ValueError as e:
            raise ValueError(
                f"channel-routing.yaml folder {rel!r} escapes project root"
            ) from e
        return candidate

    @property
    def config(self) -> RoutingConfig:
        return self._config
