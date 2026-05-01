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

## 1. Palette — Direction A (Classic Bauhaus + Saule)

**The unlock:** in Bauhaus colour theory (Itten / Klee / Albers), the sun is the *red disc*, not the yellow circle. Yellow is the radiant *quality* of red. Saulera's sun therefore lives in `#D62828` — and the brand earns the sun motif without ever using yellow.

| Role | Hex | Name | Usage |
|------|------|------|-------|
| Anchor | `#0A0A0A` | Bauhaus Black | Headers, body, dark UI, wordmark |
| Signature | `#D62828` | Saule Red | The sun — disc, primary CTA fills, accent shapes |
| Counterweight | `#003F88` | Pure Blue | Secondary CTAs, infographic counter-tone |
| Mid | `#5A5A5A` | Iron Grey | Borders, secondary text, muted UI |
| Ground | `#EAE6DE` | Studio Stone | Page background, light mode (avoid pure white) |

**WCAG contrast:**
- Black on Studio Stone — 16:1 (AAA)
- Blue on Studio Stone — 9:1 (AAA)
- Red on Studio Stone — 4.7:1 (AA — not for small body text)
- White on Saule Red — 4.6:1 (AA — use for CTA labels)

**Usage proportions (modified 60/30/10):**
- 60% Studio Stone or Black (ground)
- 30% the opposite anchor (text on stone, or stone on black)
- 10% combined Saule Red + Pure Blue (signal, never decoration)

---

## 2. Logo — Concept #1: Red Disc + Wordmark

**Construction:**
- Red disc (`#D62828`) of diameter `X`
- Wordmark `saulera` in lowercase geometric sans, cap-height = `0.7X`
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

One family, two weights. Bauhaus is mono-typographic.

**Display + body:** geometric sans with Bauhaus DNA
- Free first choice: **Pangram Sans Rounded** or **Mona Sans** (GitHub)
- Paid alternatives: **Söhne Breit**, **GT America**, **ABC Diatype**, **Neue Haas Grotesk Display**
- Avoid: Futura PT (overused), Helvetica (wrong DNA — Swiss not German Bauhaus)

**Code:** **JetBrains Mono** or **GT America Mono**

**Type scale (4 steps):**
- Display: 56/64
- H2: 32/40
- Body: 17/26
- Caption: 14/22

Never pair a serif. Never set anything in title-case headers. Lowercase rules apply (see §6).

---

## 4. Voice line — working positioning sentence

> saulera builds ai-agentic operations for smbs that need real automation, not generic ai consulting.

Refine after the first three client conversations. Tone register: confident, lowercase, no jargon, British English.

---

## 5. Asset checklist — ship-tonight

- [ ] Logo SVG — horizontal, stacked, mark-only, wordmark-only
- [ ] Favicon — 32×32, just the red disc
- [ ] saulera.com landing page — black on Studio Stone, red disc, one bold sentence
- [ ] LinkedIn header — 1584×396, black ground, red disc, wordmark
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

*Working draft for Linards's review — not a final spec.*
