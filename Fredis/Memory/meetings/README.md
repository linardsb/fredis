# Meetings

Structured meeting captures written by the `meeting-notes` skill.

- One file per meeting, named `YYYY-MM-DD_<slug>.md`.
- Frontmatter: `type: meeting`, `date`, `attendees`, `lane`, `tags`.
- Body sections (fixed order): Attendees, Agenda, Discussion, Decisions, Action items, Open questions.

Retrieval:
- Obsidian — browse the folder directly.
- Memory search — `cd .claude/scripts && uv run python memory_search.py "<query>" --mode hybrid --path-prefix meetings/ --limit 5`.

See `.claude/skills/meeting-notes/SKILL.md` for the capture flow and template.
