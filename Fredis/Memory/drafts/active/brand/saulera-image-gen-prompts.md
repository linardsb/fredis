---
title: Saulera — image-generation prompt pack
status: Draft for Linards review
date: 2026-05-03
service: brand
---

# Saulera — image-generation prompt pack

How to use: every prompt = **Master Style Prefix** + **Module Suffix**. The prefix locks the palette, geometry, and negative rules so AI tools can't drift into yellow / gradient / generic-tech-illustration territory. The suffix specifies the surface.

---

## 1. Master Style Prefix (paste at the top of every prompt)

```
Style: Saulera brand system — Bauhaus modernist geometric illustration
in the lineage of Otl Aicher 1972 Munich Olympics signage and early
El Lissitzky / Constructivist composition. Flat colour, hard vector
edges, no gradients, no drop shadow, no glow, no 3D, no glassmorphism,
no photorealism, no texture, no noise, no grain.

Palette — use ONLY these, no other colours allowed:
- Bauhaus Black #0A0A0A
- Vermillion Rise #D94E2A (the sun / signal red — sparingly)
- Dawn Teal #2A7E8F (cool counterweight)
- Warm Stone #EAE6DE (background / ground default)
- Light Cream #F4F1EA (secondary surface only)
- Warm Grey #C8C0B0 (borders, dividers)
- Iron Grey #5A5A5A (mid tones)

Composition rules:
- Asymmetric, NEVER centred — the primary mark sits off-axis
- Any disc/circle sits ABOVE the optical centre (sunrise rule)
- Geometric primitives only: circles, half-circles, rectangles,
  straight lines, triangles
- Maximum 4 primitive shapes per illustration — restraint is the point
- Negative space carries equal weight to the marks
- Lowercase only if any text appears

NEGATIVE — must NOT appear:
- Yellow, gold, orange, ochre, mustard, amber, beige-yellow
- Gradients, glow, halo, sun rays, light beams, lens flare
- Drop shadow, inner shadow, bevel, emboss, 3D depth, perspective
- Photorealism, faces, hands, people, animals, body parts
- Decorative flourishes, ornaments, swooshes, sparkles, stars
- Text other than lowercase "saulera" if explicitly specified
- Mixed case or uppercase typography
- AI artefacts, blurry edges, soft focus, painted strokes
- Stock-illustration tropes: arrows, gears, lightbulbs, brain icons,
  chatbot bubbles, cloud icons, neural-net diagrams, robot figures

Output: clean vector-ready flat illustration, hard edges, scalable.
```

---

## 2. Module Suffixes — paste one after the prefix

### A. Hero illustration (1920×1080)

```
Subject: abstract sunrise rendered as Bauhaus geometry. Background
fill: Warm Stone #EAE6DE covering full canvas. Composition: one solid
Vermillion Rise #D94E2A circle, diameter 320px, positioned at upper
LEFT third of canvas (cx=560, cy=380 — above optical centre). Below
the disc: one horizontal Dawn Teal #2A7E8F band, 60px tall, spanning
full width at y=720. One Bauhaus Black #0A0A0A thin horizontal line,
4px tall, at y=80 (residue of night). Nothing else. Asymmetric, weighted
left. Output: 1920×1080 PNG or SVG.
```

### B. Service-card illustration (800×800 square)

Pick the variant matching the service:

```
Variant — "AI agents":
Solid Vermillion Rise #D94E2A circle diameter 240px at cx=300, cy=300.
Three Dawn Teal #2A7E8F straight lines, each 6px stroke, radiating
asymmetrically DOWNWARD from the disc (NOT sun rays — diagonal
connection lines, angles roughly -30°, -50°, -70° from horizontal).
Warm Stone #EAE6DE background. Empty upper-right quadrant.
```

```
Variant — "ops automation":
Four Dawn Teal #2A7E8F solid rectangles in a non-grid arrangement
(deliberately misaligned, like Mondrian early-period). Sizes vary
80–180px. One Vermillion Rise #D94E2A circle diameter 120px anchoring
upper-right corner area (cx=600, cy=200). Warm Stone background.
```

```
Variant — "advisory / strategy":
One thick Bauhaus Black #0A0A0A quarter-circle arc, stroke 24px,
sitting bottom-left (centre at 0,800, radius 480px, sweep from 0° to
90°). One Vermillion Rise #D94E2A solid circle diameter 160px upper-
right (cx=620, cy=200). Warm Stone background. Two-element composition.
```

```
Variant — "discovery":
Vertical pairing — one Vermillion Rise #D94E2A solid circle diameter
180px at cx=400, cy=280 (upper portion). Below it, one Dawn Teal
#2A7E8F half-circle (filled, flat side up) diameter 240px at cx=400,
cy=560. Warm Stone background. Reads as sun + horizon.
```

### C. Blog header (1200×400 wide horizon strip)

```
Three horizontal bands: top 80px Bauhaus Black #0A0A0A, middle 200px
Dawn Teal #2A7E8F, bottom 120px Warm Stone #EAE6DE. One Vermillion
Rise #D94E2A solid circle diameter 140px at cx=380, cy=180 (left third,
intersecting black/teal boundary). No text.
```

### D. Open Graph / share card (1200×630)

```
Warm Stone #EAE6DE background. Lowercase wordmark "saulera" set in
Josefin Sans 700, fill Bauhaus Black #0A0A0A, baseline y=380, x=80
(left-aligned). Vermillion Rise #D94E2A solid circle diameter 180px
at cx=1000, cy=200 (upper right). One Dawn Teal #2A7E8F straight line,
4px stroke, connecting wordmark end to disc edge diagonally. No other
elements.
```

### E. Section divider (1600×120 thin strip)

```
Warm Stone #EAE6DE background. One Dawn Teal #2A7E8F horizontal line,
2px stroke, at y=36 spanning full width. One Vermillion Rise #D94E2A
solid circle diameter 24px at cx=520, cy=36 (intersecting the line).
Nothing else. Pure breathing-room divider.
```

### F. Spot icons (80×80 each, transparent background)

```
Single solid silhouette icon, ONE geometric primitive only, two-colour
max. Use either: Bauhaus Black #0A0A0A + Vermillion Rise #D94E2A OR
Dawn Teal #2A7E8F alone. No outlines, no strokes — solid filled
silhouettes only. Asymmetric placement within 80×80 bounds. Examples:
filled disc upper-left, filled half-circle bottom, single thick
diagonal line corner-to-corner, three vertical bars varying height.
Transparent background.
```

### G. Process diagram (1400×800)

```
Three stages, left to right, asymmetrically spaced (not equal gaps —
30% / 25% / 45% of canvas). Each stage: one Dawn Teal #2A7E8F filled
rectangle (varying heights 200–320px) anchored at the bottom. ONE of
the three rectangles has a Vermillion Rise #D94E2A solid circle
floating above it (current focus). Connecting elements: thin Bauhaus
Black #0A0A0A horizontal line at y=600 running across all three
rectangles. Warm Stone background. No labels, no arrows.
```

---

## 3. Tool routing — which AI for which output

| Surface | Best tool | Why |
|---------|-----------|-----|
| Hero / mood pieces | **Midjourney 7** | Style cohesion across batches; respects hex when given clearly |
| Vector-clean shapes | **Recraft V3** or **Ideogram 3** | Native vector output, palette obedience, clean edges |
| Precise SVG primitives | **Claude (SVG)** | Pixel-exact placement, hand-edit afterwards |
| Icons | **Recraft V3** | Best at solid silhouettes without artefacts |
| Photo-substitutes | None — don't use photo for Saulera | Brand is geometric-illustrative only |

**Tool tips:**
- Always specify **hex values**, not colour names — Midjourney especially listens better
- Generate in batches of 4 with seed control where the tool allows
- Always include the full negative prompt explicitly — every tool defaults to gradients / shadows / decoration if you let it
- For Midjourney, append `--style raw --ar 16:9 --no gradient,shadow,glow,yellow,gold,orange` as flags
- For Ideogram, set "Style: None" or "Style: Vector" — never "Style: 3D" or "Style: Realistic"

---

## 4. The 06:00 vs 12:00 test (apply before approving any output)

Every generated graphic should read as **06:00 (sunrise, quiet, ascending)** not **12:00 (noon, bright, declared)**. If a piece feels too declarative / shouty / energetic, kill it and regenerate. Saulera is always 06:00.

Other approval checks before using a generated graphic:
- [ ] Is the disc above optical centre? (If centred → reject)
- [ ] Are there gradients, glows, or shadows? (If yes → reject — the prompt failed)
- [ ] Does it use any yellow/gold/orange? (If yes → reject)
- [ ] Could this graphic appear on 50 other AI startup sites unchanged? (If yes → push the asymmetry harder, regenerate)
- [ ] Are there more than 4 primitive shapes? (If yes → reject — too busy)
- [ ] Does it have any text other than "saulera"? (If yes → reject)

---

*Working draft — pin to brand sheet sibling location. Update as new surfaces are added.*
