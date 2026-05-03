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

# Alias → concrete Claude model ID. Kept here (not in YAML) so version pins
# live in code and can be code-reviewed.
MODEL_IDS: dict[str, str] = {
    "opus":   "claude-opus-4-7",
    "sonnet": "claude-sonnet-4-6",
    "haiku":  "claude-haiku-4-5-20251001",
}

# Always-on built-in tool palette. Every channel including DMs gets these;
# scoping only adds *extra* tools on top. Kept in code (not YAML) — these are
# the fundamental capabilities the engine assumes are always available.
TOOL_BASE: tuple[str, ...] = ("Read", "Write", "Edit", "Glob", "Grep", "Skill")

# Legacy "everything everywhere" sets used when scoping_enabled=false. Mirror
# the engine's pre-Phase-1 hardcoded values so the kill switch is a true revert.
_LEGACY_TOOL_EXTRAS: tuple[str, ...] = ("Bash", "WebSearch", "WebFetch", "NotebookEdit")
_LEGACY_MCP_SERVERS: tuple[str, ...] = ("fredis",)

# Sentinel: skills.defaults.dm = ALL means "no allowlist clause; every skill
# in .claude/skills/ is invocable." Not a list — distinct type so callers
# can branch cleanly on `is "ALL"` vs receiving a list.
SKILLS_ALL = "ALL"


@dataclass(frozen=True)
class RoutingConfig:
    """Parsed routing config. Folders are stored as relative POSIX strings
    exactly as they appear in the YAML (e.g. ``Fredis/Memory/ideation/``)."""

    channels: dict[str, str]
    by_id: dict[str, str]
    default_dm: str
    default_fallback: str
    model_by_channel: dict[str, str]
    default_model: str
    # Phase-1 scoping additions.
    scoping_enabled: bool
    tools_by_channel: dict[str, tuple[str, ...]]
    tools_default_dm: tuple[str, ...]
    tools_default_fallback: tuple[str, ...]
    mcp_by_channel: dict[str, tuple[str, ...]]
    mcp_default_dm: tuple[str, ...]
    mcp_default_fallback: tuple[str, ...]
    skills_always: tuple[str, ...]
    # Per-channel skills: either a tuple of skill names or the "ALL" sentinel.
    # ALL means the channel inherits universal-surface semantics (same as
    # `defaults.dm: ALL`) — every skill in `.claude/skills/` is invocable and
    # the engine emits no skill-scope rule. Used today for #ideation, where
    # cross-domain prompting is the point.
    skills_by_channel: dict[str, tuple[str, ...] | str]
    skills_default_dm: tuple[str, ...] | str
    skills_default_fallback: tuple[str, ...]


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

        # Parse optional `models:` block. Expected shape:
        #   models:
        #     opus: [chan_a, chan_b]
        #     haiku: [chan_c]
        #     default: sonnet
        # Missing block → everything maps to the "sonnet" default.
        models_raw: Any = raw.get("models") or {}
        if not isinstance(models_raw, dict):
            raise ValueError("channel-routing.yaml: models must be a mapping")

        default_model = str(models_raw.get("default") or "sonnet")
        if default_model not in MODEL_IDS:
            raise ValueError(
                f"channel-routing.yaml: models.default={default_model!r} "
                f"is not one of {sorted(MODEL_IDS)}"
            )

        model_by_channel: dict[str, str] = {}
        for alias, chans in models_raw.items():
            if alias == "default":
                continue
            if alias not in MODEL_IDS:
                raise ValueError(
                    f"channel-routing.yaml: unknown model alias {alias!r}; "
                    f"expected one of {sorted(MODEL_IDS)}"
                )
            if not isinstance(chans, list):
                raise ValueError(
                    f"channel-routing.yaml: models.{alias} must be a list of "
                    f"channel names, got {type(chans).__name__}"
                )
            for chan in chans:
                name = str(chan)
                if name in model_by_channel:
                    raise ValueError(
                        f"channel-routing.yaml: channel {name!r} appears in "
                        f"multiple model tiers"
                    )
                model_by_channel[name] = alias

        # --- Phase-1 scoping blocks (tools / mcp_servers / skills). ---
        # Missing blocks default to "scoping disabled" semantics so older
        # configs keep working unchanged.
        scoping_enabled = bool(raw.get("scoping_enabled", False))

        tools_by_channel, tools_dm, tools_fallback = ChannelRouter._parse_scope_block(
            raw.get("tools"), known_channels=clean_channels, block_name="tools"
        )
        mcp_by_channel, mcp_dm, mcp_fallback = ChannelRouter._parse_scope_block(
            raw.get("mcp_servers"),
            known_channels=clean_channels,
            block_name="mcp_servers",
        )

        skills_always, skills_by_channel, skills_dm, skills_fallback = (
            ChannelRouter._parse_skills_block(
                raw.get("skills"), known_channels=clean_channels
            )
        )

        return RoutingConfig(
            channels=clean_channels,
            by_id=clean_by_id,
            default_dm=str(default_dm),
            default_fallback=str(default_fallback),
            model_by_channel=model_by_channel,
            default_model=default_model,
            scoping_enabled=scoping_enabled,
            tools_by_channel=tools_by_channel,
            tools_default_dm=tools_dm,
            tools_default_fallback=tools_fallback,
            mcp_by_channel=mcp_by_channel,
            mcp_default_dm=mcp_dm,
            mcp_default_fallback=mcp_fallback,
            skills_always=skills_always,
            skills_by_channel=skills_by_channel,
            skills_default_dm=skills_dm,
            skills_default_fallback=skills_fallback,
        )

    @staticmethod
    def _parse_scope_block(
        raw_block: Any,
        known_channels: dict[str, str],
        block_name: str,
    ) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...], tuple[str, ...]]:
        """Parse a `tools:` or `mcp_servers:` block. Both share the same shape:

            <block>:
              by_channel:
                <channel>: [item, item]
              defaults:
                dm:       [...]
                fallback: [...]

        Validates that every channel under `by_channel` is a known channel
        name (matches `channels:` map). Empty / missing block → empty
        everything (scoping is a no-op for that dimension).
        """
        if raw_block is None:
            return {}, (), ()
        if not isinstance(raw_block, dict):
            raise ValueError(
                f"channel-routing.yaml: {block_name} must be a mapping, "
                f"got {type(raw_block).__name__}"
            )

        by_channel_raw: Any = raw_block.get("by_channel") or {}
        if not isinstance(by_channel_raw, dict):
            raise ValueError(
                f"channel-routing.yaml: {block_name}.by_channel must be a mapping"
            )

        by_channel: dict[str, tuple[str, ...]] = {}
        for chan, items in by_channel_raw.items():
            chan_str = str(chan)
            if chan_str not in known_channels:
                raise ValueError(
                    f"channel-routing.yaml: {block_name}.by_channel.{chan_str!r} "
                    f"is not in `channels:` — fix the typo or add the channel"
                )
            if not isinstance(items, list):
                raise ValueError(
                    f"channel-routing.yaml: {block_name}.by_channel.{chan_str} "
                    f"must be a list, got {type(items).__name__}"
                )
            by_channel[chan_str] = tuple(str(x) for x in items)

        defaults_raw: Any = raw_block.get("defaults") or {}
        if not isinstance(defaults_raw, dict):
            raise ValueError(
                f"channel-routing.yaml: {block_name}.defaults must be a mapping"
            )

        def _list_field(name: str) -> tuple[str, ...]:
            v = defaults_raw.get(name) or []
            if not isinstance(v, list):
                raise ValueError(
                    f"channel-routing.yaml: {block_name}.defaults.{name} must be "
                    f"a list, got {type(v).__name__}"
                )
            return tuple(str(x) for x in v)

        return by_channel, _list_field("dm"), _list_field("fallback")

    @staticmethod
    def _parse_skills_block(
        raw_block: Any,
        known_channels: dict[str, str],
    ) -> tuple[
        tuple[str, ...],
        dict[str, tuple[str, ...]],
        tuple[str, ...] | str,
        tuple[str, ...],
    ]:
        """Parse the `skills:` block — distinct from tools/mcp because:

        - `always:` is a flat list, not nested under `by_channel`.
        - `defaults.dm` may be the literal string `"ALL"` (sentinel), not a list.
        """
        if raw_block is None:
            return (), {}, (), ()
        if not isinstance(raw_block, dict):
            raise ValueError(
                "channel-routing.yaml: skills must be a mapping, got "
                f"{type(raw_block).__name__}"
            )

        always_raw: Any = raw_block.get("always") or []
        if not isinstance(always_raw, list):
            raise ValueError(
                "channel-routing.yaml: skills.always must be a list, "
                f"got {type(always_raw).__name__}"
            )
        always = tuple(str(x) for x in always_raw)

        by_channel_raw: Any = raw_block.get("by_channel") or {}
        if not isinstance(by_channel_raw, dict):
            raise ValueError(
                "channel-routing.yaml: skills.by_channel must be a mapping"
            )
        by_channel: dict[str, tuple[str, ...] | str] = {}
        for chan, items in by_channel_raw.items():
            chan_str = str(chan)
            if chan_str not in known_channels:
                raise ValueError(
                    f"channel-routing.yaml: skills.by_channel.{chan_str!r} is "
                    f"not in `channels:` — fix the typo or add the channel"
                )
            # Tolerate `<channel>:` with no list (None) — treat as base-only.
            if items is None:
                by_channel[chan_str] = ()
                continue
            # `ALL` sentinel: the channel inherits universal-surface semantics
            # (same as `defaults.dm: ALL`). Engine emits no skill-scope rule.
            if isinstance(items, str):
                if items != SKILLS_ALL:
                    raise ValueError(
                        f"channel-routing.yaml: skills.by_channel.{chan_str} "
                        f"string must be the {SKILLS_ALL!r} sentinel, "
                        f"got {items!r}"
                    )
                by_channel[chan_str] = SKILLS_ALL
                continue
            if not isinstance(items, list):
                raise ValueError(
                    f"channel-routing.yaml: skills.by_channel.{chan_str} must "
                    f"be a list or the {SKILLS_ALL!r} sentinel, got "
                    f"{type(items).__name__}"
                )
            by_channel[chan_str] = tuple(str(x) for x in items)

        defaults_raw: Any = raw_block.get("defaults") or {}
        if not isinstance(defaults_raw, dict):
            raise ValueError(
                "channel-routing.yaml: skills.defaults must be a mapping"
            )

        dm_value: Any = defaults_raw.get("dm")
        dm: tuple[str, ...] | str
        if isinstance(dm_value, str):
            if dm_value != SKILLS_ALL:
                raise ValueError(
                    f"channel-routing.yaml: skills.defaults.dm string must be "
                    f"the {SKILLS_ALL!r} sentinel, got {dm_value!r}"
                )
            dm = SKILLS_ALL
        elif isinstance(dm_value, list):
            dm = tuple(str(x) for x in dm_value)
        elif dm_value is None:
            dm = ()
        else:
            raise ValueError(
                "channel-routing.yaml: skills.defaults.dm must be a list or "
                f"the {SKILLS_ALL!r} sentinel, got {type(dm_value).__name__}"
            )

        fallback_value: Any = defaults_raw.get("fallback") or []
        if not isinstance(fallback_value, list):
            raise ValueError(
                "channel-routing.yaml: skills.defaults.fallback must be a list, "
                f"got {type(fallback_value).__name__}"
            )
        fallback = tuple(str(x) for x in fallback_value)

        return always, by_channel, dm, fallback

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

    def resolve_model(
        self,
        channel_id: str,
        channel_name: str | None,
        is_dm: bool,
    ) -> str:
        """Return the concrete Claude model ID to run for this channel.

        Lookup: DM or unknown channel → `models.default`. Otherwise match by
        channel name against `models.<alias>` lists. Alias → concrete ID via
        `MODEL_IDS` (version pins live there).
        """
        if is_dm or not channel_name:
            alias = self._config.default_model
        else:
            alias = self._config.model_by_channel.get(
                channel_name, self._config.default_model
            )
        return MODEL_IDS[alias]

    def resolve_tools(
        self,
        channel_name: str | None,
        is_dm: bool,
    ) -> list[str]:
        """Return the full built-in tool palette to expose for this channel.

        Result includes the always-on base (`TOOL_BASE`) plus the channel's
        configured extras. When `scoping_enabled=false` returns the legacy
        full set so the kill switch is a true revert.

        DMs always get `tools.defaults.dm`. Unknown / unmapped channel
        names hit `tools.defaults.fallback`.
        """
        if not self._config.scoping_enabled:
            return [*TOOL_BASE, *_LEGACY_TOOL_EXTRAS]
        if is_dm:
            extras = self._config.tools_default_dm
        elif channel_name and channel_name in self._config.tools_by_channel:
            extras = self._config.tools_by_channel[channel_name]
        else:
            extras = self._config.tools_default_fallback
        return [*TOOL_BASE, *extras]

    def resolve_mcp_servers(
        self,
        channel_name: str | None,
        is_dm: bool,
    ) -> list[str]:
        """Return MCP server names that should mount for this channel.

        DMs hit `mcp_servers.defaults.dm` (universal — every server). Unknown
        channels hit `mcp_servers.defaults.fallback` (typically empty).
        Kill switch returns the legacy mount set so behaviour matches
        pre-Phase-1.
        """
        if not self._config.scoping_enabled:
            return list(_LEGACY_MCP_SERVERS)
        if is_dm:
            return list(self._config.mcp_default_dm)
        if channel_name and channel_name in self._config.mcp_by_channel:
            return list(self._config.mcp_by_channel[channel_name])
        return list(self._config.mcp_default_fallback)

    def resolve_skills(
        self,
        channel_name: str | None,
        is_dm: bool,
    ) -> list[str] | Literal["ALL"]:
        """Return the skill allowlist for this channel.

        Returns either:
        - The string `"ALL"` (sentinel) — no allowlist, every skill in
          `.claude/skills/` is invocable. Kill switch + DM default both
          map here so the universal-surface promise holds.
        - A list of skill names — the channel's `always + by_channel` extras.
          The engine appends a system-prompt rule naming this list as the
          only invocable subset.
        """
        if not self._config.scoping_enabled:
            return "ALL"
        if is_dm:
            dm_default = self._config.skills_default_dm
            if dm_default == SKILLS_ALL:
                return "ALL"
            assert isinstance(dm_default, tuple)
            return [*self._config.skills_always, *dm_default]
        if channel_name and channel_name in self._config.skills_by_channel:
            extras = self._config.skills_by_channel[channel_name]
            # ALL sentinel under by_channel = universal surface for that channel.
            if extras == SKILLS_ALL:
                return "ALL"
            assert isinstance(extras, tuple)
        else:
            extras = self._config.skills_default_fallback
        return [*self._config.skills_always, *extras]

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
