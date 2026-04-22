"""Tests for .claude/chat/channel_router.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_CHAT_DIR = Path(__file__).resolve().parents[2] / "chat"
sys.path.insert(0, str(_CHAT_DIR))


_MINIMAL_YAML = """\
version: 1
channels:
  ideation: Fredis/Memory/ideation/
  marketing: Fredis/Memory/marketing/
by_id:
  C01234ABC: Fredis/Memory/ideation/
defaults:
  dm: Fredis/Memory/daily/
  fallback: Fredis/Memory/daily/
"""


def _write_config(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "channel-routing.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def test_resolve_by_name_hits_channel_folder(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    resolved = router.resolve(channel_id="CNEW", channel_name="ideation", is_dm=False)

    assert resolved == (tmp_path / "Fredis/Memory/ideation").resolve()


def test_resolve_by_id_wins_over_name(tmp_path: Path) -> None:
    """`by_id` entries must take priority over `channels` name matches."""
    from channel_router import ChannelRouter

    # by_id C01234ABC → ideation, but name says "marketing".
    # The ID should win.
    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    resolved = router.resolve(
        channel_id="C01234ABC", channel_name="marketing", is_dm=False
    )

    assert resolved == (tmp_path / "Fredis/Memory/ideation").resolve()


def test_resolve_dm_always_hits_dm_default(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    # Even if the channel name is mapped, DMs go to daily.
    resolved = router.resolve(channel_id="D001", channel_name="ideation", is_dm=True)

    assert resolved == (tmp_path / "Fredis/Memory/daily").resolve()


def test_resolve_unknown_channel_falls_through_to_fallback(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    resolved = router.resolve(
        channel_id="CUNKNOWN", channel_name="random-channel", is_dm=False
    )

    assert resolved == (tmp_path / "Fredis/Memory/daily").resolve()


def test_resolve_unknown_id_with_no_name_falls_through(tmp_path: Path) -> None:
    """Channel ID not in `by_id` AND no name → fallback."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    resolved = router.resolve(channel_id="CZZZ", channel_name=None, is_dm=False)

    assert resolved == (tmp_path / "Fredis/Memory/daily").resolve()


def test_resolve_rejects_path_traversal(tmp_path: Path) -> None:
    """Folders that resolve outside project_root must error."""
    from channel_router import ChannelRouter

    bad = """\
version: 1
channels:
  sneaky: ../../etc/
by_id: {}
defaults:
  dm: Fredis/Memory/daily/
  fallback: Fredis/Memory/daily/
"""
    cfg = _write_config(tmp_path, bad)
    router = ChannelRouter(cfg, tmp_path)

    with pytest.raises(ValueError, match="escapes project root"):
        router.resolve(channel_id="C1", channel_name="sneaky", is_dm=False)


def test_empty_yaml_is_tolerated(tmp_path: Path) -> None:
    """Empty config should load; every resolve hits the built-in default."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, "version: 1\n")
    router = ChannelRouter(cfg, tmp_path)

    resolved = router.resolve(channel_id="CX", channel_name="none", is_dm=False)
    # Built-in default when `defaults:` is missing.
    assert resolved == (tmp_path / "Fredis/Memory/daily").resolve()

    dm_resolved = router.resolve(channel_id="D1", channel_name=None, is_dm=True)
    assert dm_resolved == (tmp_path / "Fredis/Memory/daily").resolve()


def test_top_level_list_rejected(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, "- ideation\n- marketing\n")

    with pytest.raises(ValueError, match="mapping at top level"):
        ChannelRouter(cfg, tmp_path)


def test_malformed_channels_section_rejected(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, "channels:\n  - bad\n")

    with pytest.raises(ValueError, match="channels/by_id/defaults"):
        ChannelRouter(cfg, tmp_path)


def test_resolve_detail_tags_match_source(tmp_path: Path) -> None:
    """`resolve_detail` must return the right `MatchSource` for each path."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    # by_id wins
    _, src_id = router.resolve_detail("C01234ABC", "random", is_dm=False)
    assert src_id == "by_id"

    # by_name
    _, src_name = router.resolve_detail("CNEW", "ideation", is_dm=False)
    assert src_name == "by_name"

    # DM
    _, src_dm = router.resolve_detail("D001", None, is_dm=True)
    assert src_dm == "dm_default"

    # Fallback
    _, src_fb = router.resolve_detail("CUNK", "unknown", is_dm=False)
    assert src_fb == "fallback"


def test_memory_prefix_only_for_explicit_matches(tmp_path: Path) -> None:
    """`memory_prefix` returns "" for DM / fallback, a real prefix for matches."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)
    memory_dir = tmp_path / "Fredis/Memory"

    # by_name → prefix
    prefix = router.memory_prefix("CX", "ideation", is_dm=False, memory_dir=memory_dir)
    assert prefix == "ideation/"

    # by_id → prefix
    prefix = router.memory_prefix(
        "C01234ABC", None, is_dm=False, memory_dir=memory_dir
    )
    assert prefix == "ideation/"

    # DM → empty
    prefix = router.memory_prefix("D1", None, is_dm=True, memory_dir=memory_dir)
    assert prefix == ""

    # Fallback → empty
    prefix = router.memory_prefix(
        "CUNK", "unmapped", is_dm=False, memory_dir=memory_dir
    )
    assert prefix == ""


def test_memory_prefix_nested_folder(tmp_path: Path) -> None:
    """Nested folders (e.g. builds/email-hub/) serialize with POSIX slashes."""
    from channel_router import ChannelRouter

    body = """\
version: 1
channels:
  build-email-hub: Fredis/Memory/builds/email-hub/
by_id: {}
defaults:
  dm: Fredis/Memory/daily/
  fallback: Fredis/Memory/daily/
"""
    cfg = _write_config(tmp_path, body)
    router = ChannelRouter(cfg, tmp_path)
    memory_dir = tmp_path / "Fredis/Memory"

    prefix = router.memory_prefix(
        "CX", "build-email-hub", is_dm=False, memory_dir=memory_dir
    )
    assert prefix == "builds/email-hub/"


def test_resolve_override_matches_channel_name(tmp_path: Path) -> None:
    """A target that matches a `channels:` YAML key resolves to its mapped folder."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    assert router.resolve_override("ideation") == (
        tmp_path / "Fredis/Memory/ideation"
    ).resolve()
    assert router.resolve_override("marketing") == (
        tmp_path / "Fredis/Memory/marketing"
    ).resolve()


def test_resolve_override_falls_back_to_free_form_path(tmp_path: Path) -> None:
    """Unknown target → treat as relative subpath under Fredis/Memory/."""
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    result = router.resolve_override("research/ai/sora")

    assert result == (tmp_path / "Fredis/Memory/research/ai/sora").resolve()


def test_resolve_override_strips_trailing_slash(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    result = router.resolve_override("research/ai/sora/")

    assert result == (tmp_path / "Fredis/Memory/research/ai/sora").resolve()


def test_resolve_override_rejects_empty_target(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    with pytest.raises(ValueError, match="empty"):
        router.resolve_override("")

    with pytest.raises(ValueError, match="empty"):
        router.resolve_override("   ")


def test_resolve_override_rejects_traversal(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    with pytest.raises(ValueError, match="disallowed"):
        router.resolve_override("../etc")

    with pytest.raises(ValueError, match="disallowed"):
        router.resolve_override("research/../../..")


def test_resolve_override_rejects_backslash(tmp_path: Path) -> None:
    from channel_router import ChannelRouter

    cfg = _write_config(tmp_path, _MINIMAL_YAML)
    router = ChannelRouter(cfg, tmp_path)

    with pytest.raises(ValueError, match="disallowed"):
        router.resolve_override("research\\ai")


def test_production_config_loads(tmp_path: Path) -> None:
    """Smoke test: the real shipping config file loads without errors."""
    from channel_router import ChannelRouter

    real = Path(__file__).resolve().parents[2] / "config" / "channel-routing.yaml"
    assert real.exists(), f"expected production config at {real}"

    router = ChannelRouter(real, tmp_path)

    # Spot-check a couple of known mappings.
    ideation = router.resolve(
        channel_id="CDOESNOTEXIST", channel_name="ideation", is_dm=False
    )
    assert ideation.name == "ideation"
    assert ideation.parent.name == "Memory"

    vtv = router.resolve(
        channel_id="CDOESNOTEXIST", channel_name="vtv", is_dm=False
    )
    assert vtv.name == "vtv"
    assert vtv.parent.name == "builds"

    # `by_id:` match wins over channel-name match — use the real VPS ID.
    vtv_by_id = router.resolve(
        channel_id="C0AUG4UD57C", channel_name="renamed", is_dm=False
    )
    assert vtv_by_id.name == "vtv"
    assert vtv_by_id.parent.name == "builds"

    gmail = router.resolve(
        channel_id="CDOESNOTEXIST", channel_name="gmail", is_dm=False
    )
    assert gmail.name == "gmail"
    assert gmail.parent.name == "integrations"

    clients = router.resolve(
        channel_id="CDOESNOTEXIST", channel_name="clients", is_dm=False
    )
    # `#clients` maps to retainers/ — verify that shim.
    assert clients.name == "retainers"
