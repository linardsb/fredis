"""Slack adapter using Bolt AsyncApp with Socket Mode."""

from __future__ import annotations

import asyncio
import re
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from typing import Any

import aiohttp
from models import Attachment, Channel, IncomingMessage, OutgoingMessage, Platform, Thread, User

INBOX_DIR = Path(__file__).resolve().parent.parent.parent.parent / "inbox"

# Slack mention parser triggers — see
# https://api.slack.com/reference/surfaces/formatting#mentioning-users.
# Matches: <!channel>, <!here>, <!everyone>, <@USER_ID>, <!subteam^ID[|label]>.
_MENTION_RE = re.compile(
    r"<!(channel|here|everyone)>|<@[UW][A-Z0-9]+>|<!subteam\^[A-Z0-9]+(?:\|[^>]*)?>"
)
# Zero-width joiner — invisible to humans, breaks Slack's exact-match mention parser.
_ZWJ = "‍"


def _neutralise_mentions(text: str) -> str:
    """Neutralise Slack mention triggers in outgoing text.

    Zero-width-joins the first ``<`` of every broadcast / user / subteam
    mention so the text still *reads* the same to humans but Slack's
    mention parser no longer matches. URL links ``<https://…|label>`` pass
    through untouched.
    """
    if not text or "<" not in text:
        return text
    return _MENTION_RE.sub(lambda m: "<" + _ZWJ + m.group(0)[1:], text)


class RateLimiter:
    """Per-user sliding-window rate limiter.

    Two independent windows — a short burst limit and a long hourly limit.
    Defaults (5/60s + 30/3600s) are tuned for a single-user advisor bot:
    high enough not to trip normal use, low enough to slow a compromised
    Slack account that tries to burn API budget.

    In-memory only — restarts reset the windows. Acceptable for an abuse
    prevention layer (not a quota / audit mechanism).
    """

    def __init__(
        self,
        burst_limit: int = 5,
        burst_window_seconds: float = 60.0,
        hourly_limit: int = 30,
        hourly_window_seconds: float = 3600.0,
    ) -> None:
        self.burst_limit = burst_limit
        self.burst_window_seconds = burst_window_seconds
        self.hourly_limit = hourly_limit
        self.hourly_window_seconds = hourly_window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def _now(self) -> float:  # indirection so tests can monkeypatch time
        return time.monotonic()

    def check(self, user_id: str) -> tuple[bool, str]:
        """Return ``(ok, reason)``. ``ok=True`` means the caller may proceed.

        Records the event in the user's window; on limit trip, the event
        is NOT recorded (so the user isn't perpetually stuck — the limit
        auto-heals as old events age out).
        """
        now = self._now()
        history = self._events[user_id]

        # Prune anything outside the hourly window; that covers burst too.
        cutoff_hourly = now - self.hourly_window_seconds
        while history and history[0] < cutoff_hourly:
            history.popleft()

        burst_count = sum(1 for ts in history if ts >= now - self.burst_window_seconds)
        hourly_count = len(history)

        if burst_count >= self.burst_limit:
            return False, (
                f"burst: {burst_count} messages in last "
                f"{int(self.burst_window_seconds)}s — "
                f"limit {self.burst_limit}"
            )
        if hourly_count >= self.hourly_limit:
            return False, (
                f"hourly: {hourly_count} messages in last "
                f"{int(self.hourly_window_seconds)}s — "
                f"limit {self.hourly_limit}"
            )

        history.append(now)
        return True, ""


class SlackAdapter:
    """Slack platform adapter using Bolt AsyncApp + Socket Mode.

    Connects via outbound WebSocket (no public URL needed). Handles
    @mentions in channels, direct messages, thread replies to heartbeat
    notifications, and — once Fredis has replied in a channel thread —
    subsequent non-mention replies in that same thread (thread auto-engage).
    Each Slack thread maps to a separate conversation.

    Thread auto-engage rule: a channel ``message`` event is processed if
    the thread has either (a) a heartbeat alert posted by Fredis or
    (b) an existing chat session. Top-level channel chatter still
    requires an explicit ``@Fredis`` mention.
    """

    def __init__(
        self,
        bot_token: str,
        app_token: str,
        allowed_users: list[str],
        session_store: Any | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        from slack_bolt.async_app import AsyncApp

        self.bot_token = bot_token
        self.app_token = app_token
        self.allowed_users = [u.strip() for u in allowed_users if u.strip()]
        self.session_store = session_store  # For heartbeat thread lookups
        self.rate_limiter = rate_limiter or RateLimiter()
        self._queue: asyncio.Queue[IncomingMessage] = asyncio.Queue()
        self._bot_user_id: str | None = None
        # Lazy cache: channel_id -> channel name (or None if unresolvable).
        # Populated on first sight of a channel ID; survives until process restart.
        self._channel_name_cache: dict[str, str | None] = {}

        # Create the Bolt async app
        self.app = AsyncApp(token=bot_token)

        # Register event handlers
        self.app.event("app_mention")(self._on_app_mention)
        self.app.event("message")(self._on_message)

        # Socket mode handler (created on connect)
        self._handler: Any = None
        # Watchdog state — counts router turns currently in flight so the
        # periodic reconnect skips a cycle rather than tearing down the
        # WebSocket mid-reply. Lock serialises concurrent reconnects.
        self._in_flight_turns: int = 0
        self._reconnect_lock = asyncio.Lock()

    @property
    def platform(self) -> Platform:
        return Platform.SLACK

    async def _get_bot_user_id(self) -> str:
        """Lazily fetch the bot's own user ID via auth.test()."""
        if self._bot_user_id is None:
            result = await self.app.client.auth_test()
            self._bot_user_id = result["user_id"]
        return self._bot_user_id

    async def _resolve_channel_name(
        self, channel_id: str, is_dm: bool
    ) -> str | None:
        """Return the human-readable name for a channel ID, or None for DMs.

        DMs are skipped — the "channel" is an IM ID with no meaningful name.
        Regular channels hit `conversations.info` on first sight and cache the
        result for the life of the process. Failure (missing `channels:read`
        scope, network error, private channel the bot isn't in) returns None
        — routing will fall through to the by_id map or the default folder.
        """
        if is_dm or not channel_id:
            return None
        if channel_id in self._channel_name_cache:
            return self._channel_name_cache[channel_id]

        try:
            info = await self.app.client.conversations_info(channel=channel_id)
            name = info.get("channel", {}).get("name")
            resolved: str | None = name if isinstance(name, str) and name else None
        except Exception as e:
            # Missing scope or private channel — log once and cache miss.
            print(
                f"[{datetime.now()}] conversations_info({channel_id}) failed: {e} "
                f"(channel routing will fall back to defaults)"
            )
            resolved = None

        self._channel_name_cache[channel_id] = resolved
        return resolved

    async def connect(self) -> None:
        """Start the Socket Mode connection."""
        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

        self._handler = AsyncSocketModeHandler(self.app, self.app_token)
        await self._handler.connect_async()
        bot_id = await self._get_bot_user_id()
        print(f"[{datetime.now()}] Slack adapter connected (bot user: {bot_id})")

    async def disconnect(self) -> None:
        """Close the Socket Mode connection."""
        if self._handler:
            await self._handler.close_async()
            print(f"[{datetime.now()}] Slack adapter disconnected")

    async def reconnect(self) -> bool:
        """Force a fresh Socket Mode WebSocket — the silent-drop escape hatch.

        Slack's Socket Mode autoping/reconnect logic occasionally fails
        silently (half-open WebSocket, process alive but deaf to events).
        Cycling the handler on a timer makes that class of failure
        impossible: the connection is never older than one watchdog
        interval. See `main._socket_watchdog`.

        Returns True if the reconnect happened, False if it was skipped
        because a turn is currently in flight (watchdog will retry next
        cycle). Exceptions propagate to the watchdog, which counts
        consecutive failures and exits for systemd to restart us.
        """
        if self._in_flight_turns > 0:
            return False  # busy — skip this cycle

        from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

        async with self._reconnect_lock:
            old_handler = self._handler
            self._handler = AsyncSocketModeHandler(self.app, self.app_token)
            await self._handler.connect_async()
            if old_handler is not None:
                try:
                    await old_handler.close_async()
                except Exception as e:
                    # Old handler refusing to close cleanly is non-fatal —
                    # the new one is already up.
                    print(
                        f"[{datetime.now()}] old handler close_async failed during "
                        f"reconnect (non-fatal): {e}"
                    )
            print(f"[{datetime.now()}] Slack adapter reconnected (forced refresh)")
            return True

    def note_turn_start(self) -> None:
        """Router calls this before invoking the engine. Pairs with note_turn_end."""
        self._in_flight_turns += 1

    def note_turn_end(self) -> None:
        """Router calls this once the response is delivered (or errored)."""
        self._in_flight_turns = max(0, self._in_flight_turns - 1)

    async def listen(self) -> Any:
        """Yield incoming messages from the queue (infinite loop)."""
        while True:
            message = await self._queue.get()
            yield message

    async def send(self, message: OutgoingMessage) -> str | None:
        """Send or update a message in Slack. Returns the message ts for updates."""
        # Neutralise mention-trigger patterns BEFORE markdown conversion so a
        # `<!channel>` embedded in Claude's response never fires the parser.
        text = _neutralise_mentions(message.text)
        text = self._markdown_to_mrkdwn(text)
        channel_id = message.channel.platform_id
        thread_ts = message.thread.thread_id if message.thread else None

        # Update an existing message
        if message.is_update and message.update_message_id:
            for chunk in self._split_message(text):
                try:
                    await self.app.client.chat_update(
                        channel=channel_id,
                        ts=message.update_message_id,
                        text=chunk,
                    )
                except Exception as e:
                    print(f"[{datetime.now()}] Error updating message: {e}")
            result_ts: str | None = message.update_message_id
            return result_ts

        # Send new message(s)
        chunks = self._split_message(text)
        first_ts: str | None = None
        for chunk in chunks:
            try:
                kwargs: dict[str, Any] = {"channel": channel_id, "text": chunk}
                if thread_ts:
                    kwargs["thread_ts"] = thread_ts
                result = await self.app.client.chat_postMessage(**kwargs)
                if first_ts is None:
                    first_ts = result["ts"]
            except Exception as e:
                print(f"[{datetime.now()}] Error sending message: {e}")
        return first_ts

    async def update(self, message: OutgoingMessage) -> None:
        """Edit an existing message (convenience wrapper around send)."""
        await self.send(message)

    async def send_files(
        self, file_paths: list[str], channel_id: str, thread_ts: str | None = None
    ) -> None:
        """Upload files to a Slack channel/thread using files_upload_v2."""
        for path_str in file_paths:
            path = Path(path_str)
            if not path.exists():
                print(f"[{datetime.now()}] File not found for upload: {path}")
                continue
            try:
                kwargs: dict[str, Any] = {
                    "file": str(path),
                    "filename": path.name,
                    "channel": channel_id,
                }
                if thread_ts:
                    kwargs["thread_ts"] = thread_ts
                await self.app.client.files_upload_v2(**kwargs)
                print(
                    f"[{datetime.now()}] Uploaded {path.name} to {channel_id}"
                    f"{f' (thread {thread_ts})' if thread_ts else ''}"
                )
            except Exception as e:
                print(f"[{datetime.now()}] Error uploading {path.name}: {e}")

    async def send_typing(self, channel: Channel) -> None:
        """No-op — Slack doesn't support outbound typing indicators for bots."""

    # ── Event Handlers ──────────────────────────────────────────────

    async def _on_app_mention(self, event: dict[str, Any], say: Any, client: Any) -> None:
        """Handle @bot mentions in channels."""
        user_id = event.get("user", "")
        if not self._is_allowed(user_id):
            return

        # Rate-limit check: bypassed for heartbeat-context threads since
        # those are Linards following up on our own notifications.
        channel_id = event.get("channel", "")
        thread_ts = event.get("thread_ts") or event.get("ts", "")
        if not self._is_heartbeat_thread(channel_id, thread_ts):
            ok, reason = self.rate_limiter.check(user_id)
            if not ok:
                await self._reply_rate_limited(event, reason)
                return

        incoming = await self._normalize_event(event, is_dm=False)
        await self._queue.put(incoming)

    async def _on_message(self, event: dict[str, Any], say: Any, client: Any) -> None:
        """Handle direct messages and thread replies to heartbeat notifications."""
        # Skip bot messages and most subtypes (joins, leaves, etc.)
        # Allow file_share through so users can send images
        if event.get("bot_id"):
            return
        subtype = event.get("subtype")
        if subtype and subtype != "file_share":
            return

        user_id = event.get("user", "")
        if not self._is_allowed(user_id):
            return

        is_dm = event.get("channel_type") == "im"
        channel_id = event.get("channel", "")
        thread_ts_raw = event.get("thread_ts")

        if not is_dm:
            # Channel message — only process if it's a threaded reply AND
            # the thread is one Fredis is already engaged in: either a
            # heartbeat alert thread or a thread with an existing chat
            # session (meaning Fredis previously replied there, so the
            # user expects follow-ups without re-mentioning).
            if not thread_ts_raw:
                return  # Top-level channel chatter — needs @Fredis
            is_heartbeat = self._is_heartbeat_thread(channel_id, thread_ts_raw)
            is_chat = self._is_existing_chat_session(channel_id, thread_ts_raw)
            if not (is_heartbeat or is_chat):
                return  # Thread Fredis is not engaged in — stay quiet

        # Rate-limit check: bypass heartbeat-context threads (Linards
        # following up on our own notifications may legitimately spike).
        thread_for_check = thread_ts_raw or event.get("ts", "")
        if not self._is_heartbeat_thread(channel_id, thread_for_check):
            ok, reason = self.rate_limiter.check(user_id)
            if not ok:
                await self._reply_rate_limited(event, reason)
                return

        incoming = await self._normalize_event(event, is_dm=is_dm)
        await self._queue.put(incoming)

    async def _reply_rate_limited(self, event: dict[str, Any], reason: str) -> None:
        """Post a short rate-limit reply in the same thread."""
        channel_id = event.get("channel", "")
        thread_ts = event.get("thread_ts") or event.get("ts")
        try:
            kwargs: dict[str, Any] = {
                "channel": channel_id,
                "text": f":hourglass: rate limit — wait a bit ({reason})",
            }
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            await self.app.client.chat_postMessage(**kwargs)
        except Exception as e:
            print(f"[{datetime.now()}] Error posting rate-limit reply: {e}")

    # ── Private Helpers ─────────────────────────────────────────────

    def _is_allowed(self, user_id: str) -> bool:
        """Check if a user is in the allowlist. Fails closed — empty list blocks everyone."""
        if not self.allowed_users:
            return False  # Fail closed - no allowlist means deny all
        return user_id in self.allowed_users

    def _is_heartbeat_thread(self, channel_id: str, thread_ts: str) -> bool:
        """Check if a thread_ts corresponds to a heartbeat notification."""
        if not self.session_store:
            return False
        try:
            return self.session_store.get_heartbeat_thread(channel_id, thread_ts) is not None
        except Exception:
            return False

    def _is_existing_chat_session(self, channel_id: str, thread_ts: str) -> bool:
        """True if Fredis has already replied in this thread (by session presence).

        Fails closed on any store error — if we can't tell, don't engage.
        """
        if not self.session_store:
            return False
        try:
            return self.session_store.get("slack", channel_id, thread_ts) is not None
        except Exception:
            return False

    async def _download_slack_file(self, file_info: dict[str, Any]) -> Attachment | None:
        """Download a file from Slack and save it locally.

        Slack file URLs require the bot token as a Bearer header.
        Returns an Attachment with the local path set in the url field, or None on failure.
        """
        url = file_info.get("url_private_download") or file_info.get("url_private")
        if not url:
            return None

        filename = file_info.get("name", "unknown")
        mimetype = file_info.get("mimetype", "")

        # Only download images
        if not mimetype.startswith("image/"):
            return None

        # Save to dated inbox folder
        inbox = INBOX_DIR / date.today().isoformat()
        inbox.mkdir(parents=True, exist_ok=True)

        # Avoid collisions by prepending timestamp
        safe_name = re.sub(r"[^\w.\-]", "_", filename)
        local_path = inbox / f"{datetime.now().strftime('%H%M%S')}_{safe_name}"

        try:
            headers = {"Authorization": f"Bearer {self.bot_token}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status != 200:
                        print(
                            f"[{datetime.now()}] Failed to download {filename}: HTTP {resp.status}"
                        )
                        return None
                    data = await resp.read()

            local_path.write_bytes(data)
            print(f"[{datetime.now()}] Downloaded {filename} -> {local_path}")

            return Attachment(
                filename=filename,
                mimetype=mimetype,
                url=str(local_path),
                size_bytes=len(data),
            )
        except Exception as e:
            print(f"[{datetime.now()}] Error downloading {filename}: {e}")
            return None

    async def _normalize_event(self, event: dict[str, Any], is_dm: bool) -> IncomingMessage:
        """Convert a Slack event into a platform-agnostic IncomingMessage."""
        user_id = event.get("user", "")
        channel_id = event.get("channel", "")
        text = event.get("text", "")
        ts = event.get("ts", "")

        # Always thread - use thread_ts if replying, otherwise start a new thread on ts
        thread_ts = event.get("thread_ts") or ts

        # Strip bot mentions from text
        text = re.sub(r"<@[A-Z0-9]+>\s*", "", text).strip()

        # Download any attached files (images)
        attachments: list[Attachment] = []
        for file_info in event.get("files", []):
            attachment = await self._download_slack_file(file_info)
            if attachment:
                attachments.append(attachment)

        user = User(Platform.SLACK, user_id)
        channel_name = await self._resolve_channel_name(channel_id, is_dm)
        channel = Channel(Platform.SLACK, channel_id, name=channel_name, is_dm=is_dm)
        thread = Thread(thread_id=thread_ts)

        return IncomingMessage(
            text=text,
            user=user,
            channel=channel,
            platform=Platform.SLACK,
            thread=thread,
            platform_message_id=ts,
            attachments=attachments,
            raw_event=event,
        )

    def _markdown_to_mrkdwn(self, text: str) -> str:
        """Convert standard markdown to Slack's mrkdwn format.

        Key differences:
        - **bold** → *bold* (single asterisk)
        - [text](url) → <url|text>
        - ## Heading → *Heading* (bold, no heading support)
        - Code blocks and inline code are compatible as-is
        """
        # Protect code blocks from conversion
        code_blocks: list[str] = []

        def _save_code_block(match: re.Match[str]) -> str:
            code_blocks.append(match.group(0))
            return f"\x00CODEBLOCK{len(code_blocks) - 1}\x00"

        # Save fenced code blocks
        result = re.sub(r"```[\s\S]*?```", _save_code_block, text)
        # Save inline code
        result = re.sub(r"`[^`]+`", _save_code_block, result)

        # Convert **bold** to *bold* (but not inside code)
        result = re.sub(r"\*\*(.+?)\*\*", r"*\1*", result)

        # Convert [text](url) to <url|text>
        result = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<\2|\1>", result)

        # Convert headings to bold
        result = re.sub(r"^#{1,6}\s+(.+)$", r"*\1*", result, flags=re.MULTILINE)

        # Restore code blocks
        for i, block in enumerate(code_blocks):
            result = result.replace(f"\x00CODEBLOCK{i}\x00", block)

        return result

    def _split_message(self, text: str, max_length: int = 3900) -> list[str]:
        """Split long messages at natural boundaries.

        Respects code blocks — never splits inside a fenced block.
        """
        if len(text) <= max_length:
            return [text]

        chunks: list[str] = []
        remaining = text

        while remaining:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break

            # Find a good split point
            split_at = max_length

            # Don't split inside a code block
            open_fence = remaining[:split_at].rfind("```")
            if open_fence != -1:
                # Check if there's a closing fence after the open
                close_fence = remaining[open_fence + 3 : split_at].find("```")
                if close_fence == -1:
                    # Open code block — split before it
                    split_at = open_fence

            # Try to split at double newline
            double_nl = remaining[:split_at].rfind("\n\n")
            if double_nl > max_length // 2:
                split_at = double_nl + 2
            else:
                # Try single newline
                single_nl = remaining[:split_at].rfind("\n")
                if single_nl > max_length // 2:
                    split_at = single_nl + 1
                else:
                    # Try space
                    space = remaining[:split_at].rfind(" ")
                    if space > max_length // 2:
                        split_at = space + 1

            chunks.append(remaining[:split_at])
            remaining = remaining[split_at:]

        return chunks
