---
title: Saulera — Brand Sheet (Sunrise + Bauhaus)
status: Draft for Linards review
date: 2026-05-01
service: brand
---

# Saulera — Brand Sheet (Sunrise + Bauhaus Direction)

**Wordmark:** saulera
**Domain:** saulera.com (acquired 2026-05-01)
**Brand metaphor:** *Saulera = a new day starting. Sunrise upon, a new era begins.* The brand carries that literally — sunrise palette pulled from Latvian and Argentinean dawn landscapes, Bauhaus typography for discipline.
**Positioning bet:** AI-agentic build studio for small-and-medium businesses. The "sunrise era" of small-business AI ops — warm, optimistic, disciplined. Differentiated from cold enterprise-blue AI tooling on one side and hand-wavy AI consulting on the other.

---

## 1. Palette — canonical Saulera tokens (final)

**The unlock:** in Bauhaus colour theory (Itten / Klee / Albers), the sun is the *red disc*, not the yellow circle. Yellow is the radiant *quality* of red. Saulera's sun lives in `#D94E2A` Vermillion Rise — the specific oxidised-red of the disc just clearing the horizon — and the brand earns the sun motif without ever using yellow. The teal counterweight reads as the cool side of the dawn sky before the sun fully clears.

| Role | Hex | Name | Usage |
|------|------|------|-------|
| Anchor | `#0A0A0A` | Bauhaus Black | Headers, body, dark UI, wordmark |
| Signature | `#D94E2A` | Vermillion Rise | The sun — disc, primary CTA fills, accent shapes |
| Counterweight | `#2A7E8F` | Dawn Teal | Secondary CTAs, infographic counter-tone |
| Background | `#EAE6DE` | Warm Stone | Page background, light mode |
| Surface | `#F4F1EA` | Light Cream | Cards, panels (one layer above background) |
| Border | `#C8C0B0` | Warm Grey | Dividers, input borders, muted edges |
| Mid | `#5A5A5A` | Iron Grey | Secondary text, captions |

**WCAG contrast:**
- Bauhaus Black on Warm Stone — 16:1 ✓ AAA
- Bauhaus Black on Vermillion Rise — 6.1:1 ✓ AA — **use Black for CTA labels, not White**
- White on Vermillion Rise — 3.4:1 ✗ FAILS AA body (Large only)
- Dawn Teal on Warm Stone — 4.8:1 ✓ AA body
- Dawn Teal on Light Cream — 5.0:1 ✓ AA body
- Iron Grey on Warm Stone — 6.3:1 ✓ AA body

**Practical rule:** Black-on-Vermillion CTAs only. Dawn Teal works for body text on stone or cream — that's the upgrade over a pure red-and-blue Bauhaus pair: the teal carries weight without shouting.

**Usage proportions (modified 60/30/10):**
- 60% Warm Stone or Bauhaus Black (ground)
- 30% the opposite anchor (text on stone, or stone on black)
- 10% combined Vermillion Rise + Dawn Teal (signal, never decoration)

---

## 2. Logo — Concept #1: Red Disc + Wordmark (full construction spec)

### 2.1 Construction grid

Set up a 1000-unit square canvas. All measurements relative — scale to any output size.

| Element | Value | Notes |
|---------|-------|-------|
| Disc diameter (X) | `280u` | Vermillion Rise `#D94E2A` fill, no stroke |
| Disc left edge | `100u` from canvas left | Left padding |
| Disc vertical position | offset `28u` (10% of X) **upward** from canvas optical centre | The asymmetric rule — never centred |
| Wordmark cap-height | `196u` (= 0.7X) | Josefin Sans 700, lowercase `saulera` |
| Wordmark baseline | disc-bottom-line + 4u optical adjust | Use optical alignment, not pure mathematical |
| Disc → wordmark gap | `32u` minus `4u` optical overlap | Disc visually nudges into the "s" |
| Right padding | `60u` after wordmark | Breathing room |
| Clear-space (all sides) | min `40u` | Never crowd to canvas edge |

### 2.2 The Saulera asymmetric rule (concrete spec)

The single most important rule — without this, you have a generic Bauhaus revival.

- Disc offset **upward** by `8-12%` of disc diameter relative to wordmark optical centre
- For `X = 280u`, that's `22u-34u` upward
- Default to `28u` (10%)
- Never offset downward, never centre, never exceed 12%
- Reference: Latvian folk-weaving weights upward toward the warp — the disc inherits this composition without literal folk imagery

### 2.3 Forbidden elements (AI negative prompt list)

These MUST NOT appear in any generated variant:

- Yellow, gold, orange, mustard, ochre — anything in the yellow/orange family
- Sun rays, sunbursts, light beams, halos, radial lines
- Gradients, glows, drop shadows, glassmorphism, 3D bevels, embosses
- Centred or symmetric disc placement (kills the asymmetric rule)
- Sans-serif typefaces other than Josefin Sans for the wordmark
- Decorative flourishes, ornaments, swooshes, ligature curls
- Initial caps, title case, ALL CAPS, mixed case — lowercase only
- Multiple discs, broken discs, partial discs, disc segments — single solid filled circle only
- Any text other than `saulera`
- Backgrounds other than `#EAE6DE` Warm Stone or `#0A0A0A` Bauhaus Black
- Patterns, textures, noise, paper-grain effects

### 2.4 Required uniqueness signatures (what makes it *Saulera*)

These five visual moves separate the logo from "another Bauhaus revival". An AI tool needs to be told these explicitly — it won't infer them.

1. **Off-axis disc placement** — disc above optical centre, never centred (§2.2)
2. **Lowercase Josefin Sans 700** wordmark — not Helvetica, not Futura, not Inter, not generic geometric sans
3. **Coral disc** (`#D94E2A`), not pure Bauhaus red, not yellow, not orange
4. **Optical disc-into-"s" nudge** — disc visually overlaps the start of the wordmark by `4u`, breaking pure mathematical alignment
5. **One design move per variant** — never combine the disc with halo, inner ring, secondary mark, or companion glyph. Pure single solid filled circle, always.

### 2.5 Variants to generate (priority order)

| Priority | Variant | Canvas | Use |
|----------|---------|--------|-----|
| P0 | Horizontal lockup | `1000×400` | Site header, signature, deck title |
| P0 | Mark only (disc) | `256×256` | Favicon, app icon, social avatar |
| P1 | Stacked lockup | `600×600` | Square — Instagram, app store, business card |
| P1 | Wordmark only | `800×200` | Footer, fine print, partner-logo bars |
| P2 | Mono Black | `1000×400` | Single-colour print, dark backgrounds |
| P2 | Mono Stone | `1000×400` | Single-colour print on Vermillion Rise backgrounds |

### 2.6 SVG output requirements

- `viewBox="0 0 1000 400"` for horizontal lockup (scales to all sizes via CSS)
- Disc as a single `<circle>` element, not a `<path>` — cleaner future edits
- Wordmark **converted to outlines** (not live text) — not every viewer will have Josefin licensed
- Named layers / IDs: `<circle id="disc">`, `<g id="wordmark">`
- No `<style>` blocks — inline `fill` and `transform` only
- No `<image>` raster embeds
- No `<filter>` (drop shadow / blur) elements
- One file per variant; do not bundle lockups inside a single SVG

### 2.7 AI image-generator prompt (copy-paste)

```
Minimal Bauhaus-modernist logo for "saulera". Single solid vermillion 
red filled circle (hex #D94E2A) sitting LEFT of lowercase wordmark "saulera" 
set in Josefin Sans bold (700 weight). Background: warm stone beige 
(hex #EAE6DE). The circle is offset UPWARD by 10% above the wordmark's 
optical centre — NEVER centred, never below. Wordmark cap-height equals 
70% of disc diameter. Style reference: Otl Aicher 1972 Munich Olympics 
signage — geometric, disciplined, lowercase, no decoration. Flat colour, 
hard edges, no gradients. 

Negative: NO yellow, NO orange, NO gold, NO sun rays, NO gradients, 
NO glow, NO 3D, NO shadows, NO patterns, NO texture, NO other text, 
NO decorative elements. Single solid circle + wordmark only.

Output: clean SVG-ready flat vector, transparent or stone background, 
1000×400 horizontal lockup.
```

### 2.8 AI SVG-generator prompt (Recraft / Vectorise / Claude SVG)

**Prompt A — mark only (256×256):**
```
Single solid filled circle, fill="#D94E2A", no stroke, no gradient, 
on transparent background. Diameter 200px centred horizontally on a 
256×256 canvas, but vertically offset 20px UPWARD from the canvas centre 
(asymmetric rule). Output: minimal SVG with one <circle> element, 
viewBox="0 0 256 256".
```

**Prompt B — horizontal lockup (1000×400):**
```
Horizontal logo lockup. 

Left element: solid filled circle, fill="#D94E2A", no stroke, 
diameter 280px, cx=240px, cy=172px (28px upward from canvas centre).

Right element: text "saulera" in Josefin Sans 700, lowercase, 
fill="#0A0A0A", font-size sized so cap-height equals 196px, 
baseline at y=300px, left edge of "s" at x=408px (28px right of 
disc rightmost edge minus 4px optical overlap).

Background: rect fill="#EAE6DE" covering full viewBox.
viewBox="0 0 1000 400". Text converted to outlined paths.
```

### 2.9 Iteration plan (40 variants in 4 rounds)

- **Round 1 — 10 horizontal lockups.** Vary only the asymmetric offset (8% / 10% / 12%) and disc-to-wordmark gap (24u / 32u / 40u). Pick best 3.
- **Round 2 — 10 mark-only.** Test pure filled circle vs hairline-stroked-only vs filled-with-2u-inset-light-tone. Pick best 1.
- **Round 3 — 10 stacked lockups.** Vary stack alignment (left-aligned to disc, centred on disc, centred on wordmark). Pick best 1.
- **Round 4 — 10 mono.** Black and Stone versions of chosen P0. Pick best 1.

Final output: 6 SVG files (horizontal, stacked, mark-only, wordmark-only, mono-black, mono-stone) reconciled into one Figma file with shared components.

### 2.10 Uniqueness check before exporting any final SVG

- [ ] Would this logo look identical if dropped onto 10 other AI-tooling brand sites? If yes → discard, iterate
- [ ] Is the asymmetric disc rule visually obvious without explanation? If no → increase offset toward 12%
- [ ] Does the wordmark read clearly at 16px on a low-res monitor? If no → consider Josefin 600 instead of 700
- [ ] Does the favicon (disc only) read clearly at 16×16? If no → disc must fill more of the favicon canvas (consider 240u/256u)
- [ ] Would a non-Latvian SMB owner find anything *memorable* after a 2-second glance? If no → the asymmetric rule is too subtle; push it harder

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

> saulera — a new day for small-business operations. ai-agentic builds that turn ops into momentum.

Short form for headers and signatures: *saulera. the sunrise era of small-business ai.*

Refine after the first three client conversations. Tone register: confident, lowercase, no jargon, British English.

---

## 5. Asset checklist — ship-tonight

- [ ] Logo SVG — horizontal, stacked, mark-only, wordmark-only
- [ ] Favicon — 32×32, just the Vermillion Rise disc
- [ ] saulera.com landing page — black on Warm Stone, Vermillion Rise disc, one bold sentence
- [ ] LinkedIn header — 1584×396, black ground, Vermillion Rise disc, wordmark
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

- **Logo v1.** Ship full disc + wordmark now (decided 2026-05-01). Month-2 sister mark: half-disc resting on a horizon line — explicit sunrise — reserved for case-study covers and large-format social only, never as the primary mark.
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

---

## 9. Brand metaphor — Sunrise Era

*Saulera = a new day starting. A sunrise is upon, and a new era begins.*

The metaphor isn't decorative — it determines every brand decision:

- **Vermillion disc = the sun, just risen.** Not yellow, not orange — the specific oxidised-red of the sun two minutes after horizon-break, before atmospheric scatter washes it out.
- **Dawn Teal = the cool side of the sky** before full light. Reads as the calm that precedes momentum — counterweight to the vermillion's energy.
- **Asymmetric disc upward** (§2.2) reads as *ascending* — the sun is still rising, not noon-overhead.
- **Lowercase always** — quiet morning register, not midday corporate shout.
- **Bauhaus Black anchor** — the residue of night, the discipline holding the optimism. Without it, the brand drifts toward greeting-card warmth.
- **Audience read:** SMB owner waking up to AI's possibility. The brand promises a disciplined start to a real new day, not a hype cycle.

When in doubt about a brand decision, ask: *does this read as 06:00 or 12:00?* Saulera is always 06:00.

---

## 10. Hero gradient (locked-use brand asset)

The full sunrise-stack gradient. **This is a brand asset, not a utility colour.** Use only on landing-page hero, deck cover slides, and large-format social cards. Never on UI surfaces, buttons, cards, or body backgrounds.

```css
background: linear-gradient(180deg,
  #0A0A0A 0%,    /* Bauhaus Black — pre-dawn sky */
  #2A7E8F 40%,   /* Dawn Teal — twilight band */
  #D94E2A 80%,   /* Vermillion Rise — sun line */
  #EAE6DE 100%   /* Warm Stone — ground */
);
```

**Allowed surfaces:**
- saulera.com landing hero (full-bleed, top of fold)
- Deck cover slide (1920×1080 or 16:9)
- Large-format social cards (1200×630 OG image, LinkedIn header 1584×396)

**Forbidden surfaces:** buttons, cards, body backgrounds, email signatures, favicons, mobile UI fills, content sections beyond the hero.

When the gradient appears, the wordmark sits on top in Warm Stone (`#EAE6DE`) — never on black or vermillion alone. Logo on gradient: wordmark in Warm Stone, disc still Vermillion Rise but with a 1u Warm Stone outer breathing-ring to hold it visible against the dawn-teal-to-vermillion band.

---

## 11. Mission

> saulera turns the daily operations of small and medium businesses into compounding momentum — building ai agents for the work owners actually do, not the work consultants imagine.

**Why this line.** Two moves carry the weight: *compounding momentum* names the real outcome (ops that improve the longer agents run, not a one-off automation), and *the work owners actually do, not the work consultants imagine* draws the line between Saulera and generic AI consulting. That second clause is the moat — twelve years of MarTech depth means the agents are built around real workflows, not whiteboard ones.

**Where the mission shows up:**
- Landing page hero (sub-headline under the wordmark)
- Deck slide 2 (after cover)
- Email signature long-form
- Linkedin "About" section first paragraph
- First sentence of any cold outreach where space allows

**Where it does not appear:** business cards, favicon-adjacent contexts, anywhere shorter than 200 characters of usable space. For tight surfaces, fall back to the §4 short voice line.

---

*Working draft for Linards's review — not a final spec.*
