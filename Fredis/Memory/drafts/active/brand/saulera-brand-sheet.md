---
title: Saulera — Brand Sheet (executive summary)
status: Draft for Linards review
date: 2026-05-04
service: brand
canonical_design_system: drafts/active/brand/saulera-design-system.md
---

# Saulera — Brand Sheet

> **Editorial summary.** This file holds positioning, mission, voice, and the brand metaphor. For implementation tokens (palette hexes, typography stack, spacing, radius, elevation, motion, components, CSS source), the canonical reference is `saulera-design-system.md` in this folder. Update tokens there, not here.

**Wordmark:** saulera (lowercase always)
**Domain:** saulera.com (acquired 2026-05-01)
**Positioning bet:** AI-agentic build studio for small-and-medium businesses. The "sunrise era" of small-business AI ops — warm, optimistic, disciplined. Differentiated from cold enterprise-blue AI tooling on one side and hand-wavy AI consulting on the other.

---

## 1. Mission

> saulera turns the daily operations of small and medium businesses into compounding momentum — building ai agents for the work owners actually do, not the work consultants imagine.

**Why this line.** Two moves carry the weight: *compounding momentum* names the real outcome (ops that improve the longer agents run, not a one-off automation), and *the work owners actually do, not the work consultants imagine* draws the line between Saulera and generic AI consulting. That second clause is the moat — twelve years of MarTech depth means the agents are built around real workflows, not whiteboard ones.

---

## 2. Voice line

> saulera — a new day for small-business operations. ai-agentic builds that turn ops into momentum.

**Short form (headers, signatures):** *saulera. the sunrise era of small-business ai.*

**Audience read.** SMB owner waking up to AI's possibility. The brand promises a disciplined start to a real new day, not a hype cycle.

**Tone register:** confident, lowercase, no jargon, British English. Quiet morning register.

---

## 3. Brand metaphor — Sunrise Era

*Saulera = a new day starting. A sunrise is upon, and a new era begins.*

The metaphor isn't decorative — it determines every brand decision:

- **Amber disc = the sun, just risen.** Warm and awake, not yet noon-bright.
- **Dawn Teal = the cool side of the sky** before full light. Calm that precedes momentum — counterweight to amber's energy.
- **Deep Ocean anchor** — the cool weight of pre-dawn water; the discipline holding the optimism. Softer than pure black, still serious, still 06:00-coded.
- **Asymmetric disc upward** reads as *ascending* — the sun is still rising, not noon-overhead. Disc offset upward by 8–12% of diameter (default 10%); never centred. *This single rule separates Saulera from a generic Bauhaus revival.*
- **Lowercase always** — quiet morning register, not midday corporate shout.

**When in doubt about a brand decision, ask: *does this read as 06:00 or 12:00?* Saulera is always 06:00.**

---

## 4. Palette — at-a-glance

Full token table, hover/active variants, semantic aliases, and the CSS `:root` source live in `saulera-design-system.md` §2 and §12. Summary for editorial reference:

| Role | Hex | Name | Usage |
|------|-----|------|-------|
| Anchor | `#264653` | Deep Ocean | Headers, body text, dark surfaces, wordmark |
| Signature | `#F59E0B` | Amber | Primary CTAs, signal fills, the sun (fill-only — never type) |
| Counterweight | `#2A7E8F` | Dawn Teal | Secondary CTAs, focus rings, links |
| Background | `#EAE6DE` | Warm Stone | Default page background |
| Surface | `#F4F1EA` | Light Cream | Cards, panels |
| Border | `#C8C0B0` | Warm Grey | Input borders, dividers |
| Secondary text | `#5A5A5A` | Iron Grey | Captions, muted text |

**Renamed from earlier draft:** "Vermillion Rise" → **Amber**. Same hex (`#F59E0B`); name change reflects the design system finalisation.

**Usage proportion (modified 60/30/10):** 60% Warm Stone or Deep Ocean (ground), 30% the opposite anchor, 10% Amber + Dawn Teal combined (signal — never decoration).

**Hard rules:** no gradients (flat colour bands only); Amber is fill-only, never type; 0px border-radius across the entire system except true circular elements.

---

## 5. Typography — at-a-glance

Full type scale, font-face declarations, and CSS rules live in `saulera-design-system.md` §3 and §12. Summary:

| Role | Family | Weight |
|------|--------|--------|
| Display / Headlines / Buttons / Labels | Homizio | 500 (Medium) |
| Body / UI | Montserrat Ace | 300 / 400 / 500 (500 default for body) |

**Rules:** lowercase always for headlines, CTAs, wordmark (Otl Aicher / 1972 Munich Olympics reference). Never serifs. Never title case. Never ALL CAPS except micro-labels (Homizio uppercased with 0.08em letter-spacing). British English only.

---

## 6. Content & voice rules

- **Lowercase** for headlines, CTAs, wordmark.
- **No jargon.** *"Compounding momentum"* not *"synergistic acceleration"*.
- **Specificity over platitude.** *"Turns ops into momentum"* beats *"elevates your business"*.
- **Active voice.** *"Saulera builds agents for your workflows."*
- **British English.** Colour, optimise, realised.
- **No emoji** on core materials (logo, wordmark, business cards, landing page hero). Acceptable in social captions and blog only.

### Copy in the wild

- **Landing hero:** *saulera — a new day for small-business operations. ai-agentic builds that turn ops into momentum.*
- **Email signature (long):** *saulera. the sunrise era of small-business ai.* / [name] | [role] | saulera.com
- **Social (short):** *turning small-business ops into compounding momentum — ai agents for the work you actually do, not the work consultants imagine. sunrise era starts now.*

### What copy should always convey

1. **Sunrise metaphor** present but not overwrought (*new day*, *era*, *dawn*, *momentum*).
2. **Discipline over hype** — engineered, not vacuous.
3. **SMB-specific** — every claim targets the business owner.
4. **Outcome-focused** — compounding momentum is the real outcome.

---

## 7. Imagery direction — at-a-glance

Full imagery rules live in `saulera-design-system.md` §11. Summary:

- **Photography:** sunrise / dawn landscapes (Latvian or Argentinean reference), cool / desaturated grading. **Avoid warm golden-hour imagery — too cliché, not Saulera.**
- **Illustration:** geometric, minimal, single-colour fills (Amber / Teal / Deep Ocean). Never gradients, never shadows.
- **Texture:** avoid. 1–2% noise layer maximum if unavoidable for print.
- **Asymmetric disc motif:** primary logo, deck dividers, half-disc-on-horizon for case studies and large-format social. Auseklis (Latvian Morning Star, 8-pointed Bauhaus geometry) reserved for case-study covers and large-format only.

---

## 8. Cross-references

- **Technical implementation (palette hexes, type, spacing, radius, elevation, motion, components, CSS `:root` source, font-face declarations):** `saulera-design-system.md`
- **Image / logo generation prompts:** `saulera-image-gen-prompts.md`
- **Website implementation plan (page architecture, copy, case studies):** `saulera-website-plan-v1.md`
