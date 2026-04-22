"""Parse save-to-override directives from chat messages.

Supported phrasings (case-insensitive):
    - ``save this to <target>``
    - ``save it to <target>``
    - ``save this in <target>``
    - ``save this under <target>``
    - ``clear save target`` — revokes the current thread override

The target token is a channel name from `channel-routing.yaml` or a relative
vault subpath (``research/ai/sora`` etc.). Parsing is strict by design:
only matches the explicit verb phrases, so natural chat like *"save your
thoughts"* or *"let's save this for later"* never trips the directive.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Allowed characters in a target: slug chars + forward slash for nested paths.
# Explicitly excludes backslash, dots, whitespace, and quotes.
_TARGET_CHARS = r"[a-z0-9_][a-z0-9_\-/]*"

_SAVE_RE = re.compile(
    rf"\bsave\s+(?:this|it)\s+(?:to|in|under)\s+({_TARGET_CHARS})",
    re.IGNORECASE,
)
_CLEAR_RE = re.compile(r"\bclear\s+save\s+target\b", re.IGNORECASE)


@dataclass(frozen=True)
class SaveDirective:
    """Parsed result of scanning a user message for a save directive.

    Exactly one of ``target`` and ``is_clear`` is ever truthy for a given
    directive match. When no directive is found, ``target`` is ``None`` and
    ``is_clear`` is ``False``; ``cleaned_text`` equals the input unchanged.
    """

    target: str | None
    is_clear: bool
    cleaned_text: str

    @property
    def matched(self) -> bool:
        return self.target is not None or self.is_clear


def parse(text: str) -> SaveDirective:
    """Scan ``text`` for a save/clear directive.

    Returns a ``SaveDirective`` with ``target`` set (save-to), ``is_clear``
    set (revoke override), or neither (no directive). The directive span is
    stripped from ``cleaned_text`` so Claude's reply focuses on the user's
    substantive content; trailing whitespace collapses but surrounding
    sentences stay intact.

    Multiple save directives in one message take the LAST one (user's most
    recent intent). A ``clear`` directive anywhere in the message wins over
    any save — if you're clearing, you're clearing.
    """
    if not text:
        return SaveDirective(target=None, is_clear=False, cleaned_text=text)

    clear_match = _CLEAR_RE.search(text)
    if clear_match is not None:
        cleaned = _strip_spans(text, [clear_match.span()])
        return SaveDirective(target=None, is_clear=True, cleaned_text=cleaned)

    matches = list(_SAVE_RE.finditer(text))
    if not matches:
        return SaveDirective(target=None, is_clear=False, cleaned_text=text)

    last = matches[-1]
    target = last.group(1).lower().rstrip("/")
    cleaned = _strip_spans(text, [m.span() for m in matches])
    return SaveDirective(target=target, is_clear=False, cleaned_text=cleaned)


def _strip_spans(text: str, spans: list[tuple[int, int]]) -> str:
    """Remove the given spans from ``text`` and collapse redundant whitespace."""
    if not spans:
        return text
    # Rebuild text with the spans removed.
    pieces: list[str] = []
    cursor = 0
    for start, end in sorted(spans):
        pieces.append(text[cursor:start])
        cursor = end
    pieces.append(text[cursor:])
    result = "".join(pieces)
    # Collapse runs of whitespace left by a mid-sentence excision, trim edges.
    result = re.sub(r"[ \t]+", " ", result)
    result = re.sub(r"\s*\n\s*\n\s*", "\n\n", result)
    return result.strip()
