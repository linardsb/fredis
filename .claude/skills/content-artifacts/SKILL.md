---
name: content-artifacts
description: Operational + presentation artefacts — slide decks and brand-aware LinkedIn carousels (pptx), architecture / workflow / concept diagrams as JSON (excalidraw), PDF operations (extract, merge, split, forms, image conversion), and runbooks / SOPs / playbooks for repeatable procedures (sop-creator). Use when user says "create slides", "presentation", "pptx", "carousel for LinkedIn", "excalidraw diagram", "architecture diagram", "workflow diagram", "concept diagram", "pdf extract", "pdf merge", "split pdf", "fill pdf form", "convert pdf to image", "runbook", "playbook", "SOP", "operational docs".
---

# content-artifacts

TL;DR — the "artefact-producing" skills: slides, diagrams, PDFs, runbooks. Four distinct output types; pick the reference whose output matches the ask.

## Routing table

| Trigger | Reference |
|---|---|
| "create slides", "presentation", "pptx", "LinkedIn carousel", "slide deck", "new layout", "brand cookbook" | `references/pptx.md` |
| "excalidraw diagram", "architecture diagram", "workflow diagram", "concept diagram", "visualise flow" | `references/excalidraw.md` |
| "pdf extract", "pdf merge", "split pdf", "fill pdf form", "convert pdf to image", "read pdf", "create pdf" | `references/pdf.md` |
| "runbook", "playbook", "SOP", "operational docs", "document this process" | `references/sop-runbook.md` |

## Shared assets

- `_shared/draft-path-convention.md`
- Brand assets for pptx carousels live in `references/pptx/brands/fredis/` (ported from original pptx-generator/brands/fredis/).

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/content-artifacts/<type>/YYYY-MM-DD-<slug>.<ext>`. Never:
- publish slides, diagrams, or SOPs to public surfaces automatically
- overwrite existing PDFs without explicit Linards ack
- auto-commit or auto-push

## References

| File | Load when |
|---|---|
| `references/pptx.md` | Slide decks, carousels, layout cookbook edits |
| `references/excalidraw.md` | Diagram JSON generation |
| `references/pdf.md` | PDF read/write/merge/split/form operations |
| `references/sop-runbook.md` | Runbooks, playbooks, operational docs |

## Anti-patterns

- Generating slides without a brand — `pptx` layouts are brand-aware; default to `fredis` brand when Linards doesn't name one.
- Runbooks for unrepeatable procedures. `sop-runbook.md` is for things that will happen more than once — a one-off incident write-up belongs in `daily/`, not an SOP.
- Excalidraw diagrams for code architecture that has no visual argument. If the text description is clearer than a diagram, skip the diagram.
