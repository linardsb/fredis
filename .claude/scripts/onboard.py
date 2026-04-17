"""
Second Brain — Onboarding TUI.

Walks the user through `.agent/plans/phase1-onboarding-interview.md` with a
one-question-per-screen interface. Writes answers back to the interview file
in place — no sidecar state, no data duplication. ★★★ questions can drop the
user into ``$EDITOR`` (Ctrl+E) for long-form composition.

Usage::

    uv run python onboard.py                # all tiers (★+★★+★★★)
    uv run python onboard.py --tier core    # only ★ questions
    uv run python onboard.py --tier rich    # ★ + ★★
    uv run python onboard.py --tier all     # everything (default)
    uv run python onboard.py --from A1      # jump to a specific question
    uv run python onboard.py --dry-run      # render but never write to disk

Key bindings (priority — work even while the TextArea is focused):

    Ctrl+N   next question (saves current answer first)
    Ctrl+P   previous question (saves current answer first)
    Ctrl+S   save current answer and exit
    Ctrl+E   open ``$EDITOR`` on the current answer line, then resume
    Ctrl+J   jump to a section by letter
    Ctrl+Q   quit (saves current answer first)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Input, ProgressBar, Static, TextArea

from config import ONBOARDING_FILE
from interview_parser import Interview, Question, parse_interview
from interview_writer import write_answer

_TIER_MAP = {"core": 1, "rich": 2, "all": 3}
_TIER_DOTS = {1: "● ○ ○", 2: "● ● ○", 3: "● ● ●"}

# Editors that recognise `+N` for line-jump on the command line.
_PLUS_LINE_EDITORS = {"vim", "nvim", "vi", "nano", "emacs", "hx", "micro", "joe"}


def _resolve_editor() -> str | None:
    """Return a usable terminal editor command, or ``None``.

    Prefers ``$VISUAL``, falls back to ``$EDITOR``, then platform defaults.
    Never returns ``open -t`` style GUI launchers — they don't block, which
    breaks the suspend/resume contract with Textual.
    """
    for env in ("VISUAL", "EDITOR"):
        candidate = os.environ.get(env, "").strip()
        if candidate:
            return candidate
    if sys.platform == "win32":
        return "notepad"
    # Last-resort blocking terminal editor that's nearly always available.
    return "nano"


def _editor_command(editor: str, path: Path, line: int) -> list[str]:
    """Build an editor command that opens *path* at *line* (best-effort)."""
    basename = Path(editor.split()[0]).name.lower()
    parts = editor.split()
    if basename in _PLUS_LINE_EDITORS:
        return [*parts, f"+{line}", str(path)]
    if basename in {"code", "code-insiders", "cursor"}:
        return [*parts, "--goto", f"{path}:{line}"]
    if basename in {"subl", "sublime_text"}:
        return [*parts, f"{path}:{line}"]
    return [*parts, str(path)]


class JumpModal(ModalScreen[str]):
    """Prompt the user for a section letter and dismiss with the input."""

    BINDINGS = [Binding("escape", "dismiss_blank", "Cancel", priority=True)]

    DEFAULT_CSS = """
    JumpModal { align: center middle; }
    JumpModal > Vertical {
        background: $surface;
        border: thick $accent;
        padding: 1 2;
        width: 50;
        height: auto;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("Jump to section (letter, e.g. A or AA):")
            yield Input(placeholder="A", id="section-input")
            yield Static("[Enter] go · [Esc] cancel", classes="hint")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip().upper())

    def action_dismiss_blank(self) -> None:
        self.dismiss("")


class OnboardScreen(Screen[None]):
    """Single-question screen rendered in place as the cursor advances."""

    BINDINGS = [
        Binding("ctrl+n", "next_question", "Next", priority=True),
        Binding("ctrl+p", "prev_question", "Prev", priority=True),
        Binding("ctrl+s", "save_and_quit", "Save+Quit", priority=True),
        Binding("ctrl+e", "open_editor", "Editor", priority=True),
        Binding("ctrl+j", "jump_section", "Jump", priority=True),
        Binding("ctrl+q", "quit_app", "Quit", priority=True),
    ]

    DEFAULT_CSS = """
    OnboardScreen { background: $background; }
    #section-header { text-style: bold; color: $primary; padding: 1 1 0 1; }
    #progress-row { padding: 0 1; height: 1; }
    #prompt { text-style: bold; padding: 1 1 0 1; }
    #hint { color: $text-muted; text-style: italic; padding: 0 1 1 1; }
    .tier-banner {
        background: $warning 20%;
        color: $warning;
        padding: 0 1;
        margin: 0 1;
    }
    TextArea { border: solid $accent; height: 1fr; margin: 0 1 1 1; }
    ProgressBar { margin: 0 1; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="section-header")
        yield ProgressBar(total=100, show_eta=False, id="progress")
        yield Static("", id="prompt")
        yield Static("", id="hint")
        yield Static("", id="tier-banner", classes="tier-banner")
        yield TextArea("", id="answer", show_line_numbers=False)
        yield Footer()

    def on_mount(self) -> None:
        app = self._typed_app()
        bar = self.query_one("#progress", ProgressBar)
        bar.total = max(len(app.filtered), 1)
        self._refresh_question()

    # ---- helpers -----------------------------------------------------------

    def _typed_app(self) -> OnboardApp:
        # Narrow the App reference for type checkers.
        assert isinstance(self.app, OnboardApp)
        return self.app

    def _current_question(self) -> Question | None:
        app = self._typed_app()
        if not app.filtered:
            return None
        return app.filtered[app.cursor]

    def _refresh_question(self) -> None:
        app = self._typed_app()
        question = self._current_question()
        section_header = self.query_one("#section-header", Static)
        prompt = self.query_one("#prompt", Static)
        hint = self.query_one("#hint", Static)
        banner = self.query_one("#tier-banner", Static)
        textarea = self.query_one("#answer", TextArea)
        progress = self.query_one("#progress", ProgressBar)

        if question is None:
            section_header.update("No questions match this tier filter.")
            prompt.update("")
            hint.update("")
            banner.update("")
            banner.display = False
            textarea.text = ""
            textarea.disabled = True
            progress.update(progress=0)
            return

        section = next(s for s in app.interview.sections if s.letter == question.section)
        section_header.update(
            f"Section {section.letter} — {section.title}   "
            f"[{_TIER_DOTS[question.tier]}]   {section.part}"
        )
        progress.total = max(len(app.filtered), 1)
        progress.update(progress=app.cursor + 1)
        prompt.update(f"{question.id}. {question.prompt}")
        if question.hint:
            hint.update(f"({question.hint})")
            hint.display = True
        else:
            hint.update("")
            hint.display = False
        if question.tier == 3:
            banner.update("Recommended: press Ctrl+E to open your editor for long-form answers.")
            banner.display = True
        else:
            banner.update("")
            banner.display = False
        textarea.text = question.answer
        textarea.disabled = False
        textarea.focus()

    def _persist_current(self) -> None:
        """Write the focused TextArea contents to disk (or log in dry-run)."""
        app = self._typed_app()
        question = self._current_question()
        if question is None:
            return
        textarea = self.query_one("#answer", TextArea)
        new_text = textarea.text
        if new_text == question.answer:
            return  # no change, nothing to write
        if app.dry_run:
            print(f"[DRY] Would write {question.id} = {new_text!r}", file=sys.stderr)
            return
        try:
            app.interview = write_answer(app.interview, question.id, new_text)
        except TimeoutError as exc:
            self.notify(f"Could not acquire lock: {exc}", severity="error")
            return
        # Rebuild filtered list — line offsets shifted, ID-stable cursor.
        prior_id = question.id
        app.refresh_filtered()
        for idx, q in enumerate(app.filtered):
            if q.id == prior_id:
                app.cursor = idx
                break

    # ---- actions -----------------------------------------------------------

    def action_next_question(self) -> None:
        app = self._typed_app()
        self._persist_current()
        if app.cursor + 1 < len(app.filtered):
            app.cursor += 1
            self._refresh_question()
        else:
            self.notify("End of interview reached. Ctrl+S to save and exit.")

    def action_prev_question(self) -> None:
        app = self._typed_app()
        self._persist_current()
        if app.cursor > 0:
            app.cursor -= 1
            self._refresh_question()
        else:
            self.app.bell()

    def action_save_and_quit(self) -> None:
        self._persist_current()
        self.app.exit()

    def action_quit_app(self) -> None:
        self._persist_current()
        self.app.exit()

    def action_jump_section(self) -> None:
        def _on_letter(letter: str | None) -> None:
            if not letter:
                return
            app = self._typed_app()
            for idx, q in enumerate(app.filtered):
                if q.section == letter:
                    app.cursor = idx
                    self._refresh_question()
                    return
            self.notify(f"Section {letter} not found in current tier filter.", severity="warning")

        self.app.push_screen(JumpModal(), _on_letter)

    def action_open_editor(self) -> None:
        app = self._typed_app()
        question = self._current_question()
        if question is None:
            return
        editor = _resolve_editor()
        if editor is None:
            self.notify(
                "No editor available — set $EDITOR to vim/nano/nvim/hx/micro.",
                severity="error",
            )
            return
        # Persist current buffer before handing off — the editor sees a fresh file.
        self._persist_current()
        cmd = _editor_command(editor, app.onboarding_path, question.answer_start_line + 1)
        prior_id = question.id
        try:
            with self.app.suspend():
                subprocess.run(cmd, check=False)
        except FileNotFoundError:
            self.notify(
                f"Editor '{editor}' not found on PATH. Set $EDITOR to a working command.",
                severity="error",
            )
            return
        # Reload from disk in case the user (or Obsidian) edited any answers.
        app.interview = parse_interview(app.onboarding_path)
        app.refresh_filtered()
        for idx, q in enumerate(app.filtered):
            if q.id == prior_id:
                app.cursor = idx
                break
        self._refresh_question()


class OnboardApp(App[None]):
    """Top-level Textual app that owns the interview state and cursor."""

    TITLE = "Second Brain — Phase 1 Onboarding"
    # Disable Textual's built-in command palette — its default Ctrl+P binding
    # collides with our "previous question" binding.
    ENABLE_COMMAND_PALETTE = False

    def __init__(
        self,
        *,
        onboarding_path: Path,
        tier_max: int,
        start_at: str | None = None,
        dry_run: bool = False,
    ) -> None:
        super().__init__()
        self.onboarding_path = onboarding_path
        self.tier_max = tier_max
        self.dry_run = dry_run
        self.interview: Interview = parse_interview(onboarding_path)
        self.filtered: tuple[Question, ...] = ()
        self.refresh_filtered()
        self.cursor: int = self._initial_cursor(start_at)

    def refresh_filtered(self) -> None:
        self.filtered = tuple(q for q in self.interview.questions if q.tier <= self.tier_max)

    def _initial_cursor(self, start_at: str | None) -> int:
        if start_at:
            for idx, q in enumerate(self.filtered):
                if q.id == start_at.upper():
                    return idx
            print(
                f"[onboard] --from {start_at} not found in tier filter; starting at first question",
                file=sys.stderr,
            )
        for idx, q in enumerate(self.filtered):
            if not q.answer.strip():
                return idx
        return 0

    def on_mount(self) -> None:
        self.push_screen(OnboardScreen())


def main() -> None:
    parser = argparse.ArgumentParser(description="Second Brain Phase 1 onboarding TUI.")
    parser.add_argument(
        "--tier",
        choices=list(_TIER_MAP.keys()),
        default="all",
        help="Question tier filter: core (★), rich (★+★★), all (default).",
    )
    parser.add_argument(
        "--from",
        dest="start_at",
        default=None,
        help="Jump to a specific question ID (e.g. A1).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the TUI but never persist answers to disk.",
    )
    args = parser.parse_args()

    if not ONBOARDING_FILE.exists():
        print(
            f"[onboard] Interview file not found: {ONBOARDING_FILE}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    app = OnboardApp(
        onboarding_path=ONBOARDING_FILE,
        tier_max=_TIER_MAP[args.tier],
        start_at=args.start_at,
        dry_run=args.dry_run,
    )
    app.run()


if __name__ == "__main__":
    main()
