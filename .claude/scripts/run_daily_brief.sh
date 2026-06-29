#!/usr/bin/env bash
# Daily brief: collect free web feeds + 8 YouTube channels (+transcripts), then
# synthesise a Fredis-voice brief. macOS launchd (com.linards.fredis-daily-brief).
# Mac-local by design — transcripts need a residential IP (VPS gets gated).

set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"

# uv (collector) + claude (synthesis) must be on PATH; launchd PATH is minimal.
export PATH="$HOME/.local/bin:$HOME/.nvm/versions/node/v20.20.2/bin:/usr/local/bin:/usr/bin:/bin"

DATE="$(date +%F)"
OUT_DIR="$ROOT/Fredis/Memory/drafts/active/daily-brief"
BUNDLE="$OUT_DIR/${DATE}_bundle.md"
BRIEF="$OUT_DIR/${DATE}_brief.md"
LOG="$SCRIPT_DIR/daily_brief_runs.log"

# 1. Collect the raw bundle (per-feed failures are swallowed inside the script).
if ! uv run python daily_brief.py; then
  echo "$(date '+%F %T') - collect FAILED" >> "$LOG"
  exit 1
fi

# 2. Synthesise the brief. Run claude from /tmp so the heavy project context /
#    hooks do not load; the prompt below carries the house style.
PROMPT="You are Fredis writing Linards morning brief for ${DATE} from the bundle on stdin. \
Produce four sections in British English, no emoji, neutral blunt voice, one screen. Output ONLY the brief — no preamble or meta-commentary. \
EXCLUDE ENTIRELY from every section — never mention them: party politics, elections, politicians, government appointments or reshuffles (e.g. 'who could be the next chancellor'); and all military, defence, weapons, NATO and war news (e.g. defence loans, troops, missiles, military drones). KEEP AI regulation and policy (EU AI Act, AI governance) and economic, business, startup and tech news — those are NOT what is excluded. \
Every headline or video you name MUST be a markdown link [text](url) using the exact URL given for that item in the bundle; for every WEB headline add the publication/source from the bundle right after the link in plain text (e.g. [headline](url) — Reuters; use the lane name if no source is given) so each item's origin is clear at a glance. \
(1) Three things that move today, tied to his priorities (lead generation, Email Hub, the Frontier pillar). \
(2) From your channels: include all 8 channels (his choice); link each video title to its URL; for each recent relevant video write a 5-7 \
sentence summary drawn from its transcript plus one So what line; for off-topic or stale uploads keep to a single line noting why (still linked). \
(3) Lane scan: the top NON-EXCLUDED web headline per lane as a markdown link, one line plus a So what; if a lane has only excluded items, drop that lane. \
(4) Skipped or failed: transparency on gaps. \
Anchor every So what to Email Hub, VTV, Cab, lead generation, or his research lanes."

if (cd /tmp && claude -p "$PROMPT") < "$BUNDLE" > "$BRIEF" 2>>"$LOG"; then
  echo "$(date '+%F %T') - brief OK -> $BRIEF" >> "$LOG"
else
  echo "$(date '+%F %T') - synthesis FAILED (raw bundle still at $BUNDLE)" >> "$LOG"
  exit 1
fi

# 3. Push to Slack as ONE top-level message + threaded overflow (Slack auto-splits
#    messages over ~4k chars). No title prefix — the brief's own heading is the
#    single title, so it is not duplicated. Format-agnostic: chunk by length on
#    paragraph boundaries, never by the model's exact wording. Markdown -> Slack
#    mrkdwn + links. Self-notification path. Non-fatal — brief file is still written.
if uv run python -c "
import re, sys
from pathlib import Path
from integrations.slack_api import send_notification
from config import SLACK_NOTIFICATION_CHANNEL as CH
LIMIT = 3500
t = Path('$BRIEF').read_text()
t = re.sub(r'\*\*(.+?)\*\*', r'*\1*', t)
t = re.sub(r'^#{1,6}\s*(.+)\$', r'*\1*', t, flags=re.M)
t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', t)
t = t.strip()
def chunks(s, n):
    out = []
    while len(s) > n:
        cut = s.rfind('\n\n', 0, n)
        if cut < n // 2: cut = n
        out.append(s[:cut].rstrip()); s = s[cut:].lstrip()
    if s: out.append(s)
    return out
parts = chunks(t, LIMIT)
parent = send_notification(CH, parts[0], unfurl_links=False, unfurl_media=False)
if not parent: sys.exit(1)
for piece in parts[1:]:
    send_notification(CH, piece, thread_ts=parent['ts'], unfurl_links=False, unfurl_media=False)
sys.exit(0)
" 2>>"$LOG"; then
  echo "$(date '+%F %T') - slack push OK" >> "$LOG"
else
  echo "$(date '+%F %T') - slack push FAILED (brief still at $BRIEF)" >> "$LOG"
fi
