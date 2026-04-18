"""
One-shot: seed drafts/sent/lv-seed/ with Latvian emails Linards has sent in
the last 2 years, so memory_search.py --path-prefix drafts/sent has a voice
corpus for Latvian drafting.

LV match heuristic (either condition → match):
  1. At least one recipient domain ends with `.lv`
  2. Body contains Latvian diacritics (ā ē ī ū š ž č ļ ņ ķ ģ and their caps)
     at >5% of non-whitespace character count

Run once:
    cd .claude/scripts && uv run python _lv_voice_seed.py

Then review Fredis/Memory/drafts/sent/lv-seed/ — once satisfied, delete both
this script and (optionally) the corpus folder.
"""

from __future__ import annotations

import base64
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import DRAFTS_SENT_DIR  # noqa: E402
from integrations.gmail import get_gmail_service  # noqa: E402

SEED_DIR = DRAFTS_SENT_DIR / "lv-seed"
PAGE_SIZE = 100
MAX_MESSAGES = 500  # safety cap to avoid runaway
LV_DIACRITIC_CHARS = "āēīūšžčļņķģĀĒĪŪŠŽČĻŅĶĢ"
LV_THRESHOLD = 0.05  # >5% of non-whitespace chars


def _header(msg: dict[str, Any], name: str) -> str:
    headers = (msg.get("payload") or {}).get("headers") or []
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return str(h.get("value", ""))
    return ""


def _extract_body(payload: dict[str, Any]) -> str:
    """Recurse through parts to find text/plain body."""
    body_data = payload.get("body", {}).get("data")
    if body_data:
        return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="replace")
    for part in payload.get("parts", []) or []:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if mime in ("multipart/alternative", "multipart/mixed", "multipart/related"):
            inner = _extract_body(part)
            if inner:
                return inner
    return ""


def _is_latvian(body: str, recipients: list[str]) -> bool:
    for addr in recipients:
        domain = addr.rsplit("@", 1)[-1].lower().strip(">")
        if domain.endswith(".lv"):
            return True
    # Diacritic density in body.
    visible = [c for c in body if not c.isspace()]
    if not visible:
        return False
    diacritic_count = sum(1 for c in visible if c in LV_DIACRITIC_CHARS)
    return (diacritic_count / len(visible)) > LV_THRESHOLD


def _parse_to_list(to_header: str) -> list[str]:
    """Extract bare email addresses from a To: header."""
    addrs: list[str] = []
    for chunk in to_header.split(","):
        chunk = chunk.strip()
        m = re.search(r"<([^>]+)>", chunk)
        if m:
            addrs.append(m.group(1).strip())
        elif "@" in chunk:
            addrs.append(chunk.strip())
    return addrs


def _slugify(text: str, maxlen: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s-]+", "-", text)
    return (text[:maxlen] or "no-subject").strip("-")


def _write_seed_file(
    sent_dt: datetime,
    subject: str,
    recipients: list[str],
    body: str,
) -> Path:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    date_str = sent_dt.strftime("%Y-%m-%d")
    slug = _slugify(subject)
    path = SEED_DIR / f"{date_str}_{slug}.md"

    # Avoid clobbering an existing file with the same slug on the same date.
    counter = 2
    while path.exists():
        path = SEED_DIR / f"{date_str}_{slug}-{counter}.md"
        counter += 1

    frontmatter = (
        "---\n"
        "type: email\n"
        f"recipient: {', '.join(recipients) if recipients else '(unknown)'}\n"
        f"subject: {subject}\n"
        f"date: {sent_dt.isoformat()}\n"
        "source: gmail-seed\n"
        "---\n\n"
    )
    path.write_text(frontmatter + body.strip() + "\n", encoding="utf-8")
    return path


def main() -> None:
    service = get_gmail_service()
    print(f"[lv-seed] Querying sent mail (last 2y, capped at {MAX_MESSAGES})...")

    all_ids: list[str] = []
    page_token: str | None = None
    while len(all_ids) < MAX_MESSAGES:
        params: dict[str, Any] = {
            "userId": "me",
            "q": "in:sent newer_than:2y",
            "maxResults": PAGE_SIZE,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = service.users().messages().list(**params).execute()
        for m in resp.get("messages", []) or []:
            all_ids.append(m["id"])
            if len(all_ids) >= MAX_MESSAGES:
                break
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    print(f"[lv-seed] Fetched {len(all_ids)} sent message IDs; scanning for Latvian content...")

    written = 0
    inspected = 0
    for msg_id in all_ids:
        try:
            msg = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full")
                .execute()
            )
        except Exception as e:
            print(f"[lv-seed] fetch error for {msg_id} (skip): {e}")
            continue

        inspected += 1
        to_header = _header(msg, "To")
        subject = _header(msg, "Subject") or "(no subject)"
        date_hdr = _header(msg, "Date")
        try:
            sent_dt = parsedate_to_datetime(date_hdr) if date_hdr else datetime.now()
        except (TypeError, ValueError):
            sent_dt = datetime.now()

        recipients = _parse_to_list(to_header)
        body = _extract_body(msg.get("payload") or {})

        if _is_latvian(body, recipients):
            try:
                path = _write_seed_file(sent_dt, subject, recipients, body)
                written += 1
                print(f"[lv-seed] wrote {path.name}")
            except OSError as e:
                print(f"[lv-seed] write error for {msg_id}: {e}")

    if written == 0:
        print("[lv-seed] 0 Latvian emails matched — nothing written.")
        print(
            "  Possible reasons: (a) no Latvian sent in last 2y, (b) diacritic threshold "
            "too strict, (c) recipients were UK/EN contacts only. Tune heuristic and rerun."
        )
        return

    print(f"[lv-seed] Done. {written} Latvian drafts written to {SEED_DIR} "
          f"(scanned {inspected} sent messages).")
    print(
        "[lv-seed] Review the corpus, then delete this script: "
        "rm .claude/scripts/_lv_voice_seed.py"
    )


if __name__ == "__main__":
    main()
