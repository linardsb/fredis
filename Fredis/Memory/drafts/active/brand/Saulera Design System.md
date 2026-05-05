# Saulera Design System

**Status:** v1 · May 2026
**Brand:** Saulera — AI-agentic build studio for SMBs
**Metaphor:** Sunrise — a new day starting, a new era beginning

---

## 1. Company & Positioning

**Saulera** turns the daily operations of small and medium businesses into compounding momentum — building AI agents for the work owners actually do, not the work consultants imagine.

**Voice line:** *saulera. the sunrise era of small-business ai.*

**Audience read:** SMB owner waking up to AI's possibility. The brand promises a disciplined start to a real new day, not a hype cycle. **When in doubt, ask: does this read as 06:00 or 12:00? Saulera is always 06:00.**

---

## 2. Colour — Sunrise Palette

The palette draws from Latvian and Argentinean dawn landscapes. Deep Ocean carries the cool weight of pre-dawn water; Amber is the sun the moment it crests the horizon.

| Token | Hex | Name | Role |
|---|---|---|---|
| `--color-anchor` / `--color-deep-ocean` | `#264653` | Deep Ocean | Headers, body text, dark surfaces, wordmark |
| `--color-signature` / `--color-amber` | `#F59E0B` | Amber | Primary CTAs, signal fills, the sun |
| `--color-signature-hov` | `#D98708` | Amber Hover | CTA hover state |
| `--color-signature-act` | `#B97208` | Amber Active | CTA pressed state |
| `--color-counter` / `--color-teal` | `#2A7E8F` | Dawn Teal | Secondary CTAs, counterweight, focus rings |
| `--color-bg` / `--color-stone` | `#EAE6DE` | Warm Stone | Default page background |
| `--color-surface` / `--color-cream` | `#F4F1EA` | Light Cream | Card / panel surface (one layer above bg) |
| `--color-border` / `--color-grey-border` | `#C8C0B0` | Warm Grey | Input borders, dividers, muted edges |
| `--color-mid` / `--color-grey-mid` | `#5A5A5A` | Iron Grey | Captions, secondary text |

### Usage Proportions (modified 60/30/10)

- **60%** Warm Stone or Deep Ocean (ground)
- **30%** the opposite anchor (text on stone, or stone on ocean)
- **10%** combined Amber + Dawn Teal (signal, never decoration)

### WCAG Contrast

| Pair | Ratio | Grade |
|---|---|---|
| Deep Ocean on Warm Stone | 9.2:1 | AAA |
| Deep Ocean on Amber | 6.4:1 | AA — use for CTA labels |
| Teal on Stone / Cream | 4.8–5.0:1 | AA body |
| Iron Grey on Stone | 6.3:1 | AA body |

### No Gradients

Saulera surfaces are **flat**. Six discrete colours — never blend them. No `linear-gradient`, `radial-gradient`, or atmospheric glows. When multiple brand colours coexist, arrange as flat colour bands with hard edges.

---

## 3. Typography

| Role | Family | Weight | Notes |
|---|---|---|---|
| Display / Headlines / Buttons / Labels | **Homizio** | 500 (Medium) | Single weight, sentence case. Letter-spacing 2px on display, 0.08em uppercase on buttons. |
| Body / UI | **Montserrat Ace** | 300 (Light) / 400 / 500 | Medium by default for body; Light for emphasis. |

Both families are self-hosted from `fonts/`.

### Type Scale

| Token | Size | Line | Usage |
|---|---|---|---|
| `--type-display-size` | 56px | 64px | h1, cover titles |
| `--type-h2-size` | 32px | 40px | Section headers |
| `--type-body-size` | 17px | 26px | Paragraphs, UI text |
| `--type-caption-size` | 14px | 22px | Metadata, muted text |

### Rules

- **Lowercase always** for headlines, CTAs, wordmark. References Otl Aicher / 1972 Munich Olympics.
- **Never serifs.** Never title case. Never ALL CAPS except micro-labels (Homizio uppercased with 0.08em letter-spacing).
- **British English** — "colour", "optimise", "realised".

---

## 4. Spacing

8-step scale, 4px base unit.

| Token | Value | Usage |
|---|---|---|
| `--spacing-xs` | 4px | Tight internal padding, micro-spacing |
| `--spacing-sm` | 8px | Button padding, small gaps |
| `--spacing-md` | 16px | Card padding, standard gaps |
| `--spacing-lg` | 24px | Section margins, comfortable spacing |
| `--spacing-xl` | 32px | Large section gaps |
| `--spacing-2xl` | 48px | Major section dividers |
| `--spacing-3xl` | 64px | Hero spacing |
| `--spacing-4xl` | 96px | Maximum breathing room |

---

## 5. Radius — Sharp Architectural Edges

| Token | Value |
|---|---|
| `--radius-sm` | `0` |
| `--radius-md` | `0` |
| `--radius-lg` | `0` |

> **All components use 0px corners.** Cards, CTAs, inputs, surfaces — sharp architectural edges throughout. `border-radius: 50%` is reserved exclusively for true circular elements (status dots, avatars).

---

## 6. Elevation — Subtle, Functional, Never Decorative

| Token | Value | Usage |
|---|---|---|
| `--shadow-sm` | `0 1px 2px rgba(38, 70, 83, 0.06)` | Form inputs, hover states |
| `--shadow-md` | `0 4px 6px rgba(38, 70, 83, 0.09)` | Cards, floating elements |
| `--shadow-lg` | `0 10px 15px rgba(38, 70, 83, 0.12)` | Modals, top-level surfaces |

---

## 7. Motion

**Philosophy:** Subtle, purposeful, never gratuitous. Animations should feel engineered, not playful.

| Token | Value | Usage |
|---|---|---|
| `--duration-fast` | 160ms | Hover, focus, small state changes |
| `--duration-base` | 320ms | Modal, drawer, dropdown |
| `--ease-out-soft` | `cubic-bezier(0.22, 1, 0.36, 1)` | Default ease for state changes |
| `--ease-out-rise` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entry animations (slide-in, fade-up) |

**Rules**
- Fade entry/exit: 200ms with `ease-out-soft`, opacity 0 → 1.
- Slide: 300ms `ease-out-rise`.
- **Avoid scale on buttons / cards.** No bounces, no springs.
- Colour transitions: 150–200ms — never instant flips.

---

## 8. Logo

The logo is a **single solid amber disc** offset above-and-left of the lowercase wordmark "saulera" in Homizio Medium.

### Construction

- Disc diameter: 280 units (any scale)
- Disc positioned **upward by 28 units (10% of diameter)** from the wordmark's optical centre — *never centred*
- Wordmark cap-height: 196 units (70% of disc diameter)
- Disc-to-wordmark gap: 32 units minus 4 units optical overlap (disc visually nudges into the "s")
- Background: Warm Stone (`#EAE6DE`), white, or Deep Ocean (`#264653`)

### The Asymmetric Rule (most important)

Disc offset **upward by 8–12% of diameter** (default 10%). Never offset downward, never centred, never exceed 12%. The upward motion reads as *ascending* — the sun is still rising, not noon-overhead. **This single rule separates Saulera from a generic Bauhaus revival.**

### Files

- `assets/logo_amber.svg` — amber on light backgrounds (Stone / White)
- `assets/logo_amber_white.svg` — amber disc + white wordmark on Deep Ocean

### Forbidden

- Red, vermillion, magenta
- Sun rays, sunbursts, halos, radial lines
- Gradients, glows, drop shadows, 3D effects
- Centred or symmetric placement
- Sans-serif other than Homizio for wordmark
- Title case, ALL CAPS, mixed case (lowercase only)
- Multiple, broken, or partial discs
- Patterns, textures, noise, paper grain

---

## 9. Components

### Buttons

All buttons use Homizio Medium uppercase, 0.08em letter-spacing, **0px border-radius**, no border on primary, 11px × 24px padding.

**Primary** — Amber fill, Deep Ocean text. Hover → `#D98708`. Active → `#B97208`.
**Secondary** — Deep Ocean fill, Stone text. Hover → opacity 0.9.
**Tertiary / Outline** — Transparent fill, 1px Amber border, Amber text. Hover → Amber fill, Deep Ocean text.
**Text Link** — Underline (3px offset), no padding, no border, Amber colour.

### Form Inputs

- 1px `#C8C0B0` border, white background, **0px radius**, 11px × 14px padding.
- Focus: 2px Dawn Teal outline, 2px offset.
- Disabled: 0.5 opacity, Iron Grey text, `not-allowed` cursor.

### Cards

- White or `#F4F1EA` Cream surface
- 1px `#C8C0B0` border (optional) **or** `--shadow-sm`
- 24px padding default, 32px on featured cards
- **0px border-radius**
- Hover (interactive cards only): lift via `translateY(-2px)` + `--shadow-md`

### Tags / Badges

- Deep Ocean text on Cream/Stone or Amber/Teal text on white
- 4px × 12px padding, Homizio Medium 11px uppercase 0.08em
- **0px border-radius**

### Navigation

- Sidebar: Deep Ocean background, Stone text at 30% opacity for inactive labels, full opacity for active. 4px Amber dot beside active item.
- Breadcrumbs: Iron Grey text, monospace separators (`→`), Deep Ocean for current page.
- Top bar: Stone or white, 1px bottom border `#C8C0B0`.

### Interaction States

| State | Treatment |
|---|---|
| Hover | Colour shift to darker variant; cards add `--shadow-md` + `translateY(-2px)` |
| Active / Pressed | Colour shift (e.g. Amber → `#B97208`), opacity 0.9, optional inset `--shadow-sm` |
| Focus | 2px Dawn Teal outline, 2px offset, **0px radius** |
| Disabled | 0.5 opacity, Iron Grey, no hover, `cursor: not-allowed` |

---

## 10. Content & Voice

**Register:** Confident, lowercase, no jargon, British English. Quiet morning register.

**Rules**
- **Lowercase.** Headlines, CTAs, wordmark.
- **No jargon.** "Compounding momentum," not "synergistic acceleration."
- **Specificity over platitude.** "Turns ops into momentum" beats "elevates your business."
- **Active voice.** "Saulera builds agents for your workflows."
- **British English.** Colour, optimise, realised.
- **No emoji** on core materials (logo, wordmark, business cards, landing page hero). Acceptable in social captions and blog only.

### Copy Examples

**Landing hero**
> saulera — a new day for small-business operations. ai-agentic builds that turn ops into momentum.

**Mission**
> saulera turns the daily operations of small and medium businesses into compounding momentum — building ai agents for the work owners actually do, not the work consultants imagine.

**Email signature (long)**
> saulera. the sunrise era of small-business ai.
> [name] | [role] | saulera.com

**Social (short)**
> turning small-business ops into compounding momentum — ai agents for the work you actually do, not the work consultants imagine. sunrise era starts now.

### What Copy Should Convey

1. **Sunrise metaphor**, present but not overwrought ("new day", "era", "dawn", "momentum").
2. **Discipline over hype.** Engineered, not vacuous.
3. **SMB-specific.** Every claim targets the business owner.
4. **Outcome-focused.** Compounding momentum is the real outcome — ops that improve the longer agents run.

---

## 11. Imagery & Motifs

- **Page backgrounds:** Warm Stone (`#EAE6DE`) or clean white. Avoid aggressive texture.
- **Photography:** Sunrise/dawn landscapes (Latvian or Argentinean reference). Cool/desaturated grading. **Avoid warm golden-hour imagery — too cliché, not Saulera.**
- **Illustrations:** Geometric, minimal, single-colour fills (Amber / Teal / Deep Ocean). Never gradients, never shadows.
- **Texture:** Avoid. If unavoidable for print, single 1–2% noise layer max.

### When the Asymmetric Disc Appears

- Primary logo (horizontal, stacked, mark-only, wordmark-only)
- Deck dividers & covers (half-disc resting on a horizon line — sunrise explicit, reserved for case studies and large-format social)
- Auseklis (Latvian Morning Star, 8-pointed Bauhaus geometry) — case study covers, large-format only

---

## 12. CSS Token Source

Save as `colors_and_type.css` and import at the top of every page.

```css
:root {
  /* Colours — Sunrise palette */
  --color-deep-ocean: #264653;
  --color-amber:      #F59E0B;
  --color-amber-hov:  #D98708;
  --color-amber-act:  #B97208;
  --color-teal:       #2A7E8F;
  --color-stone:      #EAE6DE;
  --color-cream:      #F4F1EA;
  --color-grey-border:#C8C0B0;
  --color-grey-mid:   #5A5A5A;

  /* Semantic aliases */
  --color-fg-primary:    var(--color-deep-ocean);
  --color-fg-secondary:  var(--color-grey-mid);
  --color-fg-muted:      var(--color-grey-border);
  --color-bg-default:    var(--color-stone);
  --color-bg-surface:    var(--color-cream);
  --color-signal-primary:   var(--color-amber);
  --color-signal-secondary: var(--color-teal);
  --color-border:        var(--color-grey-border);

  /* Typography */
  --font-display: "Homizio", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-body:    "Montserrat Ace", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;

  --type-display-size: 56px; --type-display-line: 64px;
  --type-h2-size:      32px; --type-h2-line:      40px;
  --type-body-size:    17px; --type-body-line:    26px;
  --type-caption-size: 14px; --type-caption-line: 22px;

  /* Spacing */
  --spacing-xs:  4px;
  --spacing-sm:  8px;
  --spacing-md:  16px;
  --spacing-lg:  24px;
  --spacing-xl:  32px;
  --spacing-2xl: 48px;
  --spacing-3xl: 64px;
  --spacing-4xl: 96px;

  /* Radius — sharp corners across the system */
  --radius-sm: 0;
  --radius-md: 0;
  --radius-lg: 0;

  /* Elevation */
  --shadow-sm: 0 1px 2px  rgba(38, 70, 83, 0.06);
  --shadow-md: 0 4px 6px  rgba(38, 70, 83, 0.09);
  --shadow-lg: 0 10px 15px rgba(38, 70, 83, 0.12);

  /* Motion */
  --duration-fast: 160ms;
  --duration-base: 320ms;
  --ease-out-soft: cubic-bezier(0.22, 1, 0.36, 1);
  --ease-out-rise: cubic-bezier(0.16, 1, 0.3, 1);
}

/* Global */
html {
  font-family: var(--font-body);
  font-size: 16px;
  line-height: 1.5;
  color: var(--color-fg-primary);
  background-color: var(--color-bg-default);
}
body { margin: 0; padding: 0; }

/* Headings */
h1, .h1 {
  font-family: var(--font-display);
  font-size: var(--type-display-size);
  line-height: var(--type-display-line);
  font-weight: 500;
  margin: 0;
  letter-spacing: 2px;
}
h2, .h2 {
  font-family: var(--font-display);
  font-size: var(--type-h2-size);
  line-height: var(--type-h2-line);
  font-weight: 500;
  margin: 0;
  letter-spacing: 2px;
}

/* Buttons — Homizio Medium uppercase, sharp corners */
button, .btn {
  font-family: var(--font-display);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-radius: 0;
}

p, .body {
  font-family: var(--font-body);
  font-size: var(--type-body-size);
  line-height: var(--type-body-line);
  font-weight: 500;
  margin: 0;
}

.caption {
  font-family: var(--font-body);
  font-size: var(--type-caption-size);
  line-height: var(--type-caption-line);
  font-weight: 500;
  color: var(--color-fg-secondary);
}
```

### Font Faces

```css
@font-face {
  font-family: "Homizio";
  src: url("fonts/Homizio-Medium.ttf") format("truetype");
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Montserrat Ace";
  src: url("fonts/Montserrat-Ace-Light.otf") format("opentype");
  font-weight: 300;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Montserrat Ace";
  src: url("fonts/Montserrat-Ace-Regular.otf") format("opentype");
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Montserrat Ace";
  src: url("fonts/Montserrat-Ace-Medium.otf") format("opentype");
  font-weight: 500;
  font-style: normal;
  font-display: swap;
}
```

---

## 13. Brand Philosophy — Sunrise Metaphor

*Saulera = a new day starting. A sunrise is upon, and a new era begins.*

This metaphor is not decorative — it determines every decision:

- **Amber disc** = the sun, just risen — warm and awake, not yet noon-bright
- **Dawn Teal** = the cool side of the sky before full light; counterweight to amber's energy
- **Asymmetric disc upward** = *ascending* — the sun is still rising, not noon-overhead
- **Lowercase always** = quiet morning register, not midday corporate shout
- **Deep Ocean anchor** = the cool weight of pre-dawn water, discipline holding the optimism

---

**Document version:** 1.0 · May 2026
**Maintainer:** Saulera Design Team
**License:** Internal use only
