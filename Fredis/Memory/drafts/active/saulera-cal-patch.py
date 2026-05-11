"""One-shot patch for /Users/Berzins/Desktop/saulera/talk.html.

Swaps the mock booking widget for the Cal.com inline embed
(linards-berzins-saulera/build-review). Idempotent: re-running is a no-op.

Run from anywhere:
    python3 /Users/Berzins/Desktop/claude-code-second-brain/Fredis/Memory/drafts/active/saulera-cal-patch.py
"""

from pathlib import Path
import re
import sys

TARGET = Path("/Users/Berzins/Desktop/saulera/talk.html")

OLD_HTML = '''          <div class="booking-body" id="booking-body">
            <h3>pick a slot</h3>
            <p class="sub">all times in your local timezone. we reply within one uk working day if anything moves.</p>

            <div class="slot-label">this week</div>
            <div class="cal-week" id="cal-week"></div>

            <div class="slot-label" id="slots-label">select a day to see times</div>
            <div class="slots" id="slots"></div>
          </div>

          <div class="confirmed" id="confirmed">
            <div class="check">✓</div>
            <h3>booked.</h3>
            <p id="confirmed-detail">a calendar invite is on its way.</p>
          </div>

          <div class="booking-foot" id="booking-foot">
            <div class="summary empty" id="summary">no slot selected</div>
            <button class="btn btn-primary" id="confirm-btn" disabled style="opacity: 0.4; cursor: not-allowed;">confirm booking</button>
          </div>'''

NEW_HTML = '''          <div class="booking-body">
            <div id="cal-booking-inline" style="width:100%; min-height:600px;"></div>
          </div>'''

NEW_JS = '''    // ---------- Cal.com inline embed ----------
    (function (C, A, L) { let p = function (a, ar) { a.q.push(ar); }; let d = C.document; C.Cal = C.Cal || function () { let cal = C.Cal; let ar = arguments; if (!cal.loaded) { cal.ns = {}; cal.q = cal.q || []; d.head.appendChild(d.createElement("script")).src = A; cal.loaded = true; } if (ar[0] === L) { const api = function () { p(api, arguments); }; const namespace = ar[1]; api.q = api.q || []; if(typeof namespace === "string"){cal.ns[namespace] = cal.ns[namespace] || api;p(cal.ns[namespace], ar);p(cal, ["initNamespace", namespace]);} else p(cal, ar); return;} p(cal, ar); }; })(window, "https://app.cal.com/embed/embed.js", "init");
    Cal("init", "build-review", {origin:"https://cal.com"});
    Cal.ns["build-review"]("inline", {
      elementOrSelector:"#cal-booking-inline",
      config: {"layout":"month_view"},
      calLink: "linards-berzins-saulera/build-review",
    });
    Cal.ns["build-review"]("ui", {"hideEventTypeDetails":false,"layout":"month_view"});
'''

OLD_JS_PATTERN = re.compile(
    r"    // ---------- Mock booking widget ----------\n    \(function \(\) \{.*?\n    \}\)\(\);\n",
    re.DOTALL,
)


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found", file=sys.stderr)
        return 1

    src = TARGET.read_text()

    if "cal-booking-inline" in src and "Cal.com inline embed" in src:
        print("Already patched — no changes made.")
        return 0

    if OLD_HTML not in src:
        print("ERROR: mock HTML block not found — file may have been edited", file=sys.stderr)
        return 2
    src = src.replace(OLD_HTML, NEW_HTML)

    src, n = OLD_JS_PATTERN.subn(NEW_JS, src, count=1)
    if n != 1:
        print(f"ERROR: mock JS block matched {n} times (expected 1)", file=sys.stderr)
        return 3

    TARGET.write_text(src)
    print(f"OK — patched {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
