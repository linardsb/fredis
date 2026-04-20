---
name: content-social
description: Social-content drafting for AI / tech education — LinkedIn posts and carousels (long-form thought leadership); X / Twitter posts and threads (short-form, thread structure); Instagram carousels, reels scripts, captions. Voice matching, hook design, CTA conventions. Advisor-mode only — drafts to Fredis/Memory/drafts/active/, never auto-post. Use when user says "LinkedIn post", "linkedin thread", "twitter thread", "tweet", "X post", "instagram post", "instagram carousel", "reels script", "social content", "repurpose for social".
---

# content-social

TL;DR — three platforms, one voice. References encode platform-specific format/hook/cadence rules; voice comes from Linards's sent-draft corpus (Tim-Jackson English sample, LV seed). Draft only; Linards posts manually.

## Routing table

| Trigger | Reference |
|---|---|
| "LinkedIn post", "LinkedIn carousel", "LinkedIn thread", "long-form post", "professional post" | `references/linkedin.md` |
| "tweet", "X post", "Twitter thread", "X thread", "short-form social" | `references/x-twitter.md` |
| "Instagram post", "Instagram carousel", "reels script", "Instagram caption" | `references/instagram.md` |

## Shared assets

- `_shared/draft-path-convention.md`
- Voice-match corpus: `Fredis/Memory/drafts/sent/` (English via Tim-Jackson sample; Latvian via `lv-seed/`).

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/content-social/<platform>/YYYY-MM-DD-<slug>.md`. Never:
- post to LinkedIn, X, or Instagram — none of these have send-gated APIs wired; drafts only
- auto-commit or auto-push

Social content is high-visibility. SOUL rules apply hard here: no politics, no emojis, no celebrity takes, evidence-first when correcting.

## References

| File | Load when |
|---|---|
| `references/linkedin.md` | LinkedIn drafting (posts, carousels, threads) |
| `references/x-twitter.md` | X / Twitter drafting (posts, threads) |
| `references/instagram.md` | Instagram drafting (carousels, reels, captions) |

## Anti-patterns

- Drafting without reading a voice sample. Before first draft for a platform, skim 2–3 recent sent examples via `memory_search.py --path-prefix drafts/sent`.
- Cross-platform copy-paste. Each reference's format rules are different — tone, length, hook structure, CTA convention.
- Generic "AI is changing everything" hooks. If the post could be written by any AI content mill, it's the wrong draft.
