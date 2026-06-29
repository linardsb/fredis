"""
Daily Brief Collector for Second Brain

Pre-fetches the free web feeds + YouTube channels defined in
`Fredis/Memory/research/sources-and-feeds.md` and writes a raw bundle that the
morning-brief synthesis pass (heartbeat SDK, or `claude -p`) turns into the brief.

Architecture (matches heartbeat.py — Phase 5 direct-integrations pattern):
  1. Python pulls Google News RSS per lane + BBC + YouTube uploads + transcripts
  2. Results are assembled into one markdown bundle
  3. Claude reasons over the bundle — no LLM call happens here (collector only)

Free, no paid APIs. Transcripts need `youtube-transcript-api`, which is NOT yet in
the venv — install it first (see Usage) or the bundle falls back to headlines plus
an "(unavailable)" note per video. The caption endpoint is also IP-sensitive: it
works from a residential IP but is often rate-gated on a datacenter/VPS IP.

Usage:
    uv pip install youtube-transcript-api         # one-time: enable transcripts
    uv run python daily_brief.py                  # collect, write today's bundle
    uv run python daily_brief.py --no-transcripts # headlines only (fast)
    uv run python daily_brief.py --days 7         # widen YouTube recency window
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "Fredis" / "Memory" / "drafts" / "active" / "daily-brief"

GN = "https://news.google.com/rss/search?q={q}&hl=en-GB&gl=GB&ceid=GB:en"

# Lane -> Google News keyword query. Mirrors sources-and-feeds.md Part B.
LANES = [
    ("AI / agentic eng",
     '"agentic AI" OR "AI agents" OR "Claude Code" OR "LLM agents"'),
    ("AI in agriculture",
     '"precision agriculture" OR "AI agriculture" OR "farm robotics" OR agritech'),
    ("AI robotics",
     '"humanoid robot" OR "embodied AI" OR "physical AI" OR "robot learning"'),
    ("Materials (mycelium/3DP)",
     'mycelium OR "mushroom leather" OR "additive manufacturing" OR biofabrication'),
    ("Building business",
     '"solo founder" OR "indie hacker" OR bootstrapped OR "AI automation agency"'),
    ("Markets & macro",
     '"commodity supercycle" OR "sector rotation" OR "Fed policy" OR "debt cycle"'),
    ("Investing / compounding",
     '"dividend growth" OR "index funds" OR "financial independence" OR "value investing"'),
    ("Policy & legislation",
     '"EU AI Act" OR "UK AI regulation" OR "AI governance" OR "EU tech regulation"'),
    ("Latvia",
     "Latvia economy OR Latvia transport OR Latvia startup OR Latvia AI"),
]

NATIVE_FEEDS = [("UK business (BBC)", "https://feeds.bbci.co.uk/news/business/rss.xml")]

# name, channel_id, lane
CHANNELS = [
    ("IndyDevDan", "UC_x36zCEGilGpB1m-V4gmjg", "AI / agentic eng"),
    ("David Shapiro", "UCvKRFNawVcuz4b9ihUTApCg", "AI / post-labour"),
    ("Nate B Jones", "UC0C-17n9iuUQPylguM1d-lQ", "AI strategy"),
    ("AI Engineer", "UCLKPca3kwwd-B59HNr-_lvA", "AI / agentic eng"),
    ("Matt Pocock", "UCswG6FSbgZjbWtdf_hMLaow", "AI / dev tooling"),
    ("YC Root Access", "UCcefcZRL2oaA_uBNeo5UOWg", "Building business"),
    ("Unsupervised Learning", "UCnCikd0s4i9KoDtaHPlK-JA", "AI + security"),
    ("20VC", "UC9jkoB5oKe1eAGZ5zOW6iZA", "VC / founders"),
]

MAX_PER_LANE = 4
TRANSCRIPT_CHARS = 6000
MAX_TRANSCRIPTS = 8  # all 8 channels, every day (Linards's choice 2026-06-23)
HDR = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en-GB,en;q=0.9", "Cookie": "CONSENT=YES+1"}
ATOM = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def fetch(url: str, timeout: int = 25) -> bytes:
    return urllib.request.urlopen(urllib.request.Request(url, headers=HDR), timeout=timeout).read()


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", text or ""))).strip()


def rss_items(xml_bytes: bytes, limit: int) -> list[dict]:
    """Parse RSS 2.0 <item> entries (title, source, date)."""
    out: list[dict] = []
    for item in ET.fromstring(xml_bytes).iter("item"):
        title = clean(item.findtext("title", ""))
        src = clean(item.findtext("source", "") or "")
        # Google News appends " - Source" to the title; strip it (prefer <source>).
        if " - " in title:
            head, tail = title.rsplit(" - ", 1)
            title, src = head, (src or tail)
        date = ""
        if pd := item.findtext("pubDate"):
            try:
                date = parsedate_to_datetime(pd).strftime("%Y-%m-%d")
            except Exception:
                date = pd[:16]
        link = clean(item.findtext("link", "") or "")
        out.append({"title": title, "source": src, "date": date, "link": link})
        if len(out) >= limit:
            break
    return out


def youtube_latest(channel_id: str) -> dict | None:
    feed = fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    entry = ET.fromstring(feed).find("a:entry", ATOM)
    if entry is None:
        return None
    return {
        "videoId": entry.findtext("yt:videoId", "", ATOM),
        "title": clean(entry.findtext("a:title", "", ATOM)),
        "published": (entry.findtext("a:published", "", ATOM) or "")[:10],
    }


def _vtt_text(vtt: str) -> str:
    """WEBVTT -> plain text: drop headers/cue-indexes/timestamps/inline tags, and
    dedupe the rolling-caption repeats YouTube auto-subs emit."""
    out: list[str] = []
    for ln in vtt.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")):
            continue
        if "-->" in ln or ln.isdigit():
            continue
        ln = clean(re.sub(r"<[^>]+>", "", ln))
        if ln and (not out or out[-1] != ln):
            out.append(ln)
    return clean(" ".join(out))


def get_transcript(video_id: str) -> str | None:
    """English auto-captions via yt-dlp (more block-resistant than the transcript
    API; uses curl_cffi impersonation when installed). None if blocked/missing."""
    import glob
    import subprocess
    import tempfile

    url = f"https://www.youtube.com/watch?v={video_id}"
    with tempfile.TemporaryDirectory() as td:
        try:
            subprocess.run(
                [sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs",
                 "--cookies-from-browser", "brave",
                 "--sub-langs", "en.*", "--sub-format", "vtt/best",
                 "--ignore-no-formats-error", "--no-warnings",
                 "-o", str(Path(td) / "%(id)s"), url],
                check=True, capture_output=True, timeout=120,
            )
        except Exception:
            return None
        vtts = glob.glob(str(Path(td) / f"{video_id}*.vtt"))
        if not vtts:
            return None
        try:
            text = _vtt_text(Path(vtts[0]).read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            return None
        return text[:TRANSCRIPT_CHARS] or None


def is_recent(published: str, days: int) -> bool:
    try:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        return datetime.fromisoformat(published).replace(tzinfo=UTC) >= cutoff
    except Exception:
        return True  # if unparseable, keep it


def web_section() -> list[str]:
    lines = ["## Web lane scan", ""]
    for label, query in LANES:
        lines.append(f"### {label}")
        try:
            items = rss_items(fetch(GN.format(q=quote(query))), MAX_PER_LANE)
            rows = [f"- {it['title']} — {it['source']} ({it['date']}) — {it['link']}" for it in items]
            lines += rows or ["- (no items)"]
        except Exception as e:
            lines.append(f"- FETCH FAILED: {type(e).__name__}")
        lines.append("")
    for label, url in NATIVE_FEEDS:
        lines.append(f"### {label}")
        try:
            items = rss_items(fetch(url), MAX_PER_LANE)
            lines += [f"- {it['title']} — {it['source']} ({it['date']}) — {it['link']}" for it in items]
        except Exception as e:
            lines.append(f"- FETCH FAILED: {type(e).__name__}")
        lines.append("")
    return lines


def channel_section(days: int, transcripts: bool) -> list[str]:
    lines = ["## Channels (latest upload per channel — all channels, every day)", ""]
    fetched = 0
    for name, cid, lane in CHANNELS:
        try:
            v = youtube_latest(cid)
        except Exception as e:
            lines.append(f"### {name} [{lane}] — FEED FAILED: {type(e).__name__}\n")
            continue
        if not v:
            continue
        stale = "" if is_recent(v["published"], days) else " (stale)"
        vurl = f"https://www.youtube.com/watch?v={v['videoId']}"
        lines.append(f"### {name} [{lane}] — {v['published']}{stale} — {v['title']} — {vurl}")
        if transcripts and fetched < MAX_TRANSCRIPTS:
            t = get_transcript(v["videoId"])
            fetched += 1
            if t:
                lines.append(f"\nTRANSCRIPT ({len(t.split())}+ words, truncated):\n{t}\n")
            else:
                lines.append("\n(transcript unavailable — fetch blocked or no captions)\n")
        lines.append("")
    return lines


def build(days: int, transcripts: bool) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    header = [
        f"# Daily Brief — raw bundle — {today}",
        "",
        "_Pre-fetched by daily_brief.py. Feed into the morning-brief synthesis._",
        "",
    ]
    return "\n".join(header + web_section() + channel_section(days, transcripts))


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect the daily-brief raw bundle.")
    ap.add_argument("--days", type=int, default=4, help="YouTube recency window")
    ap.add_argument("--no-transcripts", action="store_true", help="headlines only")
    args = ap.parse_args()

    bundle = build(args.days, transcripts=not args.no_transcripts)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{datetime.now():%Y-%m-%d}_bundle.md"
    out.write_text(bundle, encoding="utf-8")
    print(f"Wrote {out} ({len(bundle.splitlines())} lines)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
