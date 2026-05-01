---
title: Saulera — Bauhaus Brand Sheet (working draft)
status: Draft for Linards review
date: 2026-05-01
service: brand
---

# Saulera — Brand Sheet (Bauhaus Direction)

**Wordmark:** saulera
**Domain:** saulera.com (acquired 2026-05-01)
**Positioning bet:** AI-agentic advisory + build studio for SMBs across UK / LV / AR. Bauhaus discipline → engineer-grade brand without becoming corporate-blue or generic AI-tooling.

---

## 1. Palette — canonical Saulera tokens

**The unlock:** in Bauhaus colour theory (Itten / Klee / Albers), the sun is the *red disc*, not the yellow circle. Yellow is the radiant *quality* of red. Saulera's sun therefore lives in `#FF6B5C` — coral-red — and the brand earns the sun motif without ever using yellow.

| Role | Hex | Name | Usage |
|------|------|------|-------|
| Anchor | `#0A0A0A` | Bauhaus Black | Headers, body, dark UI, wordmark |
| Signature | `#FF6B5C` | Saule Red / Coral | The sun — disc, primary CTA fills, accent shapes |
| Counterweight | `#1F76B0` | Pacific Blue | Secondary CTAs, infographic counter-tone |
| Background | `#EAE6DE` | Warm Stone | Page background, light mode |
| Surface | `#F4F1EA` | Light Cream | Cards, panels (one layer above background) |
| Border | `#C8C0B0` | Warm Grey | Dividers, input borders, muted edges |
| Mid | `#5A5A5A` | Iron Grey | Secondary text, captions |

**WCAG contrast — read carefully, the coral changes the rules:**
- Black on Warm Stone — 16:1 ✓ AAA
- Black on Saule Red — 8:1 ✓ AAA — **use Black for CTA labels, not White**
- White on Saule Red — 2.6:1 ✗ FAILS AA
- Pacific Blue on Warm Stone — 3.8:1 ✓ AA Large only (headlines, icons — not body)
- Pacific Blue on White / Light Cream — 4.8:1 ✓ AA body

**Practical rule:** Black-on-Saule-Red CTAs only. Pacific Blue is for display sizes, icons, and accents — not for body text on the Warm Stone background.

**Usage proportions (modified 60/30/10):**
- 60% Warm Stone or Black (ground)
- 30% the opposite anchor (text on stone, or stone on black)
- 10% combined Saule Red + Pacific Blue (signal, never decoration)

---

## 2. Logo — Concept #1: Red Disc + Wordmark

**Construction:**
- Saule Red disc (`#FF6B5C`) of diameter `X`
- Wordmark `saulera` in Josefin Sans 700 lowercase, cap-height = `0.7X`
- Disc sits left of wordmark; rightmost edge of the disc aligned to start of "s", minus one optical-correction unit so the disc visually overlaps slightly

**The Saulera asymmetric rule (the twist that prevents generic Bauhaus revival):**
- Disc is *never* centred on the cap-line. Sits offset upward by 8-12% of disc diameter
- References Latvian folk-weaving's off-grid weight, not German Bauhaus orthodoxy
- This single rule is what differentiates the mark

**Variants to ship day one:**
- Horizontal lockup: disc + wordmark (default)
- Stacked lockup: disc above wordmark (square / social)
- Mark only: disc (favicon, app icon)
- Wordmark only: saulera in Bauhaus Black (footer, fine print)

**What to reject during sketching:**
- Centred / symmetric disc → reads corporate
- Sun rays → reads childish
- Gradient on disc → kills the Bauhaus discipline
- Yellow anywhere → kills the concept

---

## 3. Typography

| Role | Family | Weight |
|------|---------|--------|
| Display / Headings | Josefin Sans | 700 |
| Body | Hubot Sans | 400-600 |
| Mono / Labels | JetBrains Mono | 500 |

**Why this pairing works.** Josefin Sans is geometric and disciplined (Bauhaus DNA). Hubot Sans is its humanist sibling (GitHub's commissioned counterpart to Mona Sans). The combination diverges from strict Bauhaus mono-typography by pairing a geometric display with a humanist body — that's deliberate. It softens the brand for SMB-owner readers without losing the modernist structure.

**Type scale (4 steps):**
- Display: 56/64
- H2: 32/40
- Body: 17/26
- Caption: 14/22

Never pair a serif. Never set anything in title-case headers. Lowercase rules apply (see §6). Alternative pairings on file in §8 if Josefin/Hubot needs to be swapped later.

---

## 4. Voice line — working positioning sentence

> saulera builds ai-agentic operations for smbs that need real automation, not generic ai consulting.

Refine after the first three client conversations. Tone register: confident, lowercase, no jargon, British English.

---

## 5. Asset checklist — ship-tonight

- [ ] Logo SVG — horizontal, stacked, mark-only, wordmark-only
- [ ] Favicon — 32×32, just the Saule Red disc
- [ ] saulera.com landing page — black on Warm Stone, Saule Red disc, one bold sentence
- [ ] LinkedIn header — 1584×396, black ground, Saule Red disc, wordmark
- [ ] Email signature — wordmark + role + saulera.com

All five fit in one Figma file with shared components. Realistic build time: 2-3 hours at email-developer-level vector chops.

---

## 6. Saulera-specific Bauhaus rules (the twist)

Three rules that separate Saulera from a generic Bauhaus revival:

1. **Asymmetric disc.** Disc never centred — always off-axis upward.
2. **Auseklis primitive (reserved).** The Latvian Morning Star (8-pointed) rendered in pure Bauhaus geometry — disciplined, not folkloric — appears only on case-study covers, deck dividers, large-format work. Never on the primary mark.
3. **Lowercase always.** Wordmark, headlines, CTAs all lowercase. References Otl Aicher / 1972 Munich Olympics Bauhaus heir lineage. Signals advisor-not-corporation.

---

## 7. Open decisions (before saulera.com goes live)

- **Logo: concept #1 vs #3.** Ship #1 now (red disc + wordmark). Prototype concept #3 (geometric S monogram built from disc primitives) in month 2.
- **Bridge accent.** Add `#B5563E` Pampa Terracotta as Direction C subtle bridge nod, or stay pure A? Recommend pure A for v1; revisit when the UK ↔ LV ↔ AR bridge becomes an explicit sales angle.
- **First brand-led artefact.** Essay, case-study cover, or landing manifesto? Choice determines whether tonight's templates favour editorial or pitch.

---

## 8. Alternative Bauhaus-inspired font pairings

Reserve list — for swap-out later if Josefin / Hubot needs to change. Imported from the Saulera Design System artefact in claude.ai.

| Pairing | Display | Body | Mono | Character |
|---------|---------|------|------|-----------|
| Geometric Classic | Futura | Avenir | JetBrains Mono | True Bauhaus geometry |
| Swiss Precision | Archivo | Manrope | JetBrains Mono | Engineered, tight, modern |
| Modernist Grid | Unbounded | Manrope | Fira Code | Bold geometric display |
| Clean Minimal | Geist | Geist | Geist Mono | Vercel / Linear neutrality |
| Mechanical | Space Mono | Space Grotesk | Space Mono | Retro-futurist, code-forward |
| Humanist Modern | Mona Sans | Hubot Sans | JetBrains Mono | GitHub's commissioned pair |

---

*Working draft for Linards's review — not a final spec.*
