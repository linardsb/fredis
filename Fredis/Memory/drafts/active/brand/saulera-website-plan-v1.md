---
title: Saulera — Website Plan v1 (page architecture + draft copy)
status: Draft for Linards review
date: 2026-05-04
service: brand
brand_anchor: drafts/active/brand/saulera-bauhaus-brand-sheet.md
---

# Saulera — Website Plan v1

## TL;DR

- **5 pages** at launch. Not 3, not 8.
- **Single primary CTA** across the site: *"Book a 30-min build review."* Every page funnels here.
- **Positioning angle:** *"AI-agentic operations, built by someone who has actually shipped at scale — not pitched at it."* Differentiates from cold enterprise AI tooling on one side and hand-wavy AI consulting on the other (consistent with brand sheet).
- **One real risk to settle before you ship:** Email Innovation Hub as a case study triggers the UK CDPA 1988 s.11(2) / Patents 1977 s.39 IP overhang. See §5 — **needs `ip-overhang-guard` clearance before it goes public**.
- **One open scope decision:** EN-only at launch vs EN+LV bilingual. Recommendation: EN-only on day one, add LV when the first Riga prospect actually asks for it.

---

## Why 5 pages (and not the alternatives)

| Option | Verdict | Reason |
|--------|---------|--------|
| **1-page (single scroll)** | No | Reads as a side project, not a build studio. Hurts B2B credibility and SEO for SMB-search queries. |
| **5 pages (recommended)** | Yes | Tight enough to ship in days, broad enough to carry the proof + service depth a £5k–£50k engagement decision needs. |
| **6+ pages with blog at launch** | No | Blog cadence isn't proven yet. An empty `/notes` page is worse than no `/notes`. Add it once 4–6 posts exist (LinkedIn/YouTube cross-post candidates already in pipeline per USER.md). |

Pre-revenue + solo means the site is a **closer**, not a content marketing fortress. Five tight pages convert; eight sprawly ones leak attention.

---

## Page architecture

### 1. Home (`/`) — *the promise + the proof*

**Goal:** in 8 seconds, a small-business owner knows what Saulera does, who it's for, and what to do next.

**Sections (top to bottom):**

1. **Hero** — single-screen, vermillion-rise sun motif (per brand sheet) on warm-stone background.
   - **Headline:** *Agentic operations, built for businesses that need them to actually run.*
   - **Subhead:** *Twelve years building marketing systems for global brands. Now building the AI workflows that let small and medium businesses operate at the same level — without the enterprise overhead.*
   - **Primary CTA button:** *Book a 30-min build review*
   - **Secondary link:** *See what we build →* (anchors to §3)
2. **Trust strip** (one line, low-key) — *Built by a senior email developer at Merkle / Dentsu. Clients shipping in the UK and the Baltics.* (Wording adjusts once first paid client is named.)
3. **What we build** — three boxes (full copy in page 2; on home, one sentence each).
4. **Why Saulera** — three short panels:
   - *Built, not just advised.* You get production workflows in your stack — not a 40-page deck.
   - *Right-sized for SMBs.* No enterprise consultancy bloat. One operator who ships.
   - *UK + Baltic reach.* Dual-based in East Grinstead and Riga, with cross-border project experience.
5. **Proof strip** — 3 logos / project tiles (case studies expanded on §4 page).
6. **Closing CTA** — repeats the booking link with a one-line softener: *"30 minutes. No deck. We look at one workflow you'd want agentic, and tell you what it would take to ship."*

**Tone check:** confident, not boastful. No "transform your business" or "leverage cutting-edge". British English throughout.

---

### 2. What we build (`/work`) — *services as outcomes, not feature lists*

**Goal:** prospect reads three blocks and self-identifies which one they want a call about.

**Three service blocks (in this order — most-to-least productised):**

#### Block 1 — Agentic workflows that ship
*Production AI workflows wired into the tools you already use — email, CRM, spreadsheets, dashboards, internal docs. Built, deployed, and documented so your team can run them without us in the room.*

- **Typical engagement:** 4–8 weeks, fixed scope.
- **What you get:** the workflow live in your environment, a short runbook, and a 30-day support window.
- **Best fit:** SMBs with a repetitive ops bottleneck — invoicing, lead triage, report generation, content pipelines.

#### Block 2 — Custom apps and platforms
*Web and native applications for the workflows that don't fit off-the-shelf. Built end-to-end from architecture to deployment.*

- **Typical engagement:** 8–16 weeks, milestone-based.
- **What you get:** a working product, source code, and a handover plan.
- **Best fit:** category-specific tooling (mobility, wellbeing, vertical SaaS) where the right software simply doesn't exist yet.

#### Block 3 — MarTech and email infrastructure
*Twelve years of email-developer depth at Merkle / Dentsu. ESP architecture, modular component systems, and AI-assisted email workflows that scale across teams.*

- **Typical engagement:** 2–6 weeks, scoped per audit / build.
- **What you get:** a tightened ESP setup, reusable component library, and a workflow that survives team turnover.
- **Best fit:** mid-market brands with email programmes that have outgrown their template chaos.

**Closing block:** *Not sure which fits? Book a 30-min build review. We'll either point you at the right block — or tell you it isn't us.*

**Push-back note for Linards:** the bundled "marketing / bookkeeping / accounting / sales support" line in USER.md is **deliberately not on the public site v1**. It dilutes the AI-build positioning. Keep it as an offline upsell to existing clients, surface only in the discovery call.

---

### 3. About (`/about`) — *the credibility page*

**Goal:** make the moat legible in under 90 seconds of reading.

**Sections:**

1. **One-line positioning:** *Saulera is an AI-agentic build studio for small and medium businesses. Founded in 2026 by Linards Bērziņš.*
2. **Founder story (3 short paragraphs):**
   - **Twelve years of MarTech depth.** Senior email developer at Merkle / Dentsu — the engineering work behind email and data programmes for global brands. The systems that move money, not the slide decks that promise to.
   - **The agentic shift.** As large language models matured into agentic systems, two things became obvious: most AI consulting wouldn't ship anything real, and most enterprise AI tooling would never reach the businesses that needed it most. Saulera is the bridge — agentic engineering applied to small-and-medium operations.
   - **Dual-based.** Working from East Grinstead, UK and Riga, Latvia. Comfortable with cross-border engagements (UK ↔ Baltic ↔ EU), with project access into Argentina via family network for clients with South American touchpoints.
3. **Working principles** (3–4 short bullets — pulled from SOUL.md voice):
   - We ship working software, not slide decks.
   - We say no to engagements that won't ship.
   - We use British English, weights and measures, and pricing in your local currency (GBP, EUR, ARS as needed).
   - We document what we build so you don't depend on us.
4. **CTA:** booking link.

**Voice note:** keep the founder section in third person ("Saulera was founded by…") for v1 — reads as a studio, not a personal site. Switch to first-person once a second person joins.

---

### 4. Results (`/results`) — *proof, with honesty about what's paid vs built*

**Goal:** prove engineering depth and product instinct without overstating commercial traction.

**Three case study cards, each ~200–300 words:**

#### Card 1 — VTV: AI-agentic public-transport optimisation (Riga)
- **What was built:** an AI-agentic system for public-transport route and schedule optimisation, designed for the Latvian municipal context.
- **What shipped:** live prototype with inbound interest from former Latvian Transport Ministers (named only with their permission — defer until you've checked).
- **Why it matters:** demonstrates Saulera's capability to build category-specific agentic systems for civic and mobility clients, not just generic "AI workflows".

#### Card 2 — UGOKI: health & wellbeing iOS / Android app
- **What was built:** end-to-end native mobile MVP for movement and wellbeing tracking.
- **What shipped:** functional MVP on both platforms, with re-engaged investor interest from Walking Ventures (Tim Jackson) in 2026.
- **Why it matters:** end-to-end product capability — design, native build, distribution-readiness — not just web tooling.

#### Card 3 — *(third slot reserved — see §5 below)*

**Honesty principle:** for VTV and UGOKI, write the cards as *built / shipping / interest secured* — not as *paid client engagements*. Overclaiming gets caught in the discovery call and burns trust faster than admitting you're early-stage.

---

## §5 — IP risk to clear before launch

**The problem.** USER.md explicitly flags Email Innovation Hub as carrying a UK CDPA 1988 s.11(2) and Patents Act 1977 s.39 IP overhang — work created during employment at Dentsu / Merkle is presumptively the employer's IP unless cleanly carved out. **Putting Email Hub on a public Saulera case studies page advertises that work as Saulera's commercial output, which is exactly the trigger Dentsu's legal team would react to.**

**Recommendation:**

1. **Do not include Email Innovation Hub on the public site v1.** Not on the homepage, not on the case studies page, not in About. Even oblique references ("our agentic email work for global brands") carry risk.
2. **Use the third Results card for one of:**
   - GERBONI (Latvian heraldry e-commerce) — modest commercial example, your IP, no overhang. Frame as *"built, launched, sold"* — small but real.
   - A **commissioned anonymous build** if any consulting work has already happened (even unpaid friend-of-friend builds — describe the system, not the client).
   - **Defer the third card** entirely until the first paid Saulera engagement closes — two cards is fine for v1.
3. **Run the `ip-overhang-guard` skill before any case study mentioning email, ESP, MarTech, or Merkle / Dentsu work goes live.** Including the About page paragraph mentioning the Merkle / Dentsu role — that's a *biographical* reference, which is generally safe, but the wording should say *"twelve years as an email developer for global brand programmes"* rather than *"twelve years building agentic email systems"* (the latter blurs employer-IP into Saulera's claimed offering).

**Status:** flagged. Do not push the site live with Email Hub on it until this is cleared.

---

### 5. Contact (`/talk`) — *the booking page*

**Goal:** reduce friction to a single 30-min call.

**Sections:**

1. **Headline:** *Tell us what you'd want to be agentic.*
2. **Sub:** *30 minutes. No deck. We look at one workflow you'd want agentic, and tell you what it would take to ship — or whether it's not us.*
3. **Booking widget:** Cal.com or SavvyCal embed (Linards's choice — Cal.com integrates cleanly with Google Calendar already configured).
4. **Backup form** (3 fields only): name, email, one-line *"what you'd want agentic"*. Submits to Gmail or HubSpot inbound — depending on which integration is wired (HubSpot is primary CRM per USER.md, so route there).
5. **Footer reassurance:** *We reply within one UK working day. If you don't hear back, email linards@saulera.com directly.*

**Push-back:** no "request a quote" form, no multi-page lead magnet funnel, no newsletter signup at launch. One CTA, one path. Add complexity once volume justifies it.

---

## Cross-cutting elements

### Global navigation
`Home · Work · About · Results · Talk` — five items, no dropdowns, no mega-menu.

### Footer
- Three columns: services / company / contact.
- Bottom strip: *© 2026 Saulera · East Grinstead, UK · Riga, LV · linards@saulera.com*
- No social icons until the LinkedIn / YouTube / X cadence is producing weekly (per USER.md content calendar — currently planned, not running).

### Voice and copy rules
- **British English always.** No US spelling. (-ise, -our, -re, etc.)
- **No emoji anywhere.**
- **Headline pattern:** outcome → proof → action. Avoid "transform", "leverage", "harness", "unlock the power of", "synergy". Default to plain verbs: *build, ship, run, scope, deploy*.
- **Sentence length:** mix of short (≤8 words) and medium (≤20). No multi-clause monsters.
- **Pricing:** never on the public site v1. Surface in discovery call. (Pricing model itself is open per USER.md.)

### Visual system
Pulled directly from the existing brand sheet (`drafts/active/brand/saulera-bauhaus-brand-sheet.md`):
- Palette: Deep Ocean / Vermillion Rise / Dawn Teal / Warm Stone / Light Cream / Warm Grey.
- Hero motif: vermillion sun on warm-stone, contemporary AI-era register (Linear / Anthropic / Stripe lineage).
- Typography: TBD in brand sheet — pick one before building.

### Tech stack recommendation
- **Framework:** Next.js (App Router) on Vercel — 12-factor deploys, edge-hosted, free tier covers pre-revenue traffic.
- **CMS:** none at launch. Pages as `.mdx` files in the repo. Add a CMS (Sanity, Payload) only when content-editing volume justifies it.
- **Forms:** HubSpot Forms embed or simple Resend-backed serverless function (latter is lighter; pairs with linards@saulera.com).
- **Analytics:** Plausible or Vercel Analytics — privacy-first, no cookie banner needed for UK / EU compliance.
- **Domain:** saulera.com (acquired). Set up MX records for linards@saulera.com via Google Workspace before launch.

### What's deliberately NOT in v1
- Blog / `/notes` page (add when 4+ posts exist).
- Bilingual EN+LV (add when first Riga prospect requests).
- Pricing page.
- Detailed FAQ page (add 4–6 inline FAQs to `/work` instead if needed).
- Social proof testimonials (add when first paid client gives one).
- Newsletter signup.
- Live chat widget.

Each of these is a "phase 2 if signal supports it" — not a launch blocker.

---

## Open questions for Linards

1. **VTV case study naming.** Šlesers and Krištopans are listed in USER.md as inbound interest. Do you have explicit permission to name them on a public site? If not, frame VTV as "former Latvian transport ministers" without names.
2. **Email Hub IP clearance.** Confirmed not going on the site v1 — agreed?
3. **Bilingual launch.** EN-only on day one, defer LV until requested — agreed? Or do you want LV ready for the Riga lead-gen push from day one?
4. **Booking tool.** Cal.com vs SavvyCal vs HubSpot Meetings? (HubSpot Meetings is free and integrates with the CRM already in use — strongest case unless you have a UX preference.)
5. **Engagement pricing on the site.** Confirmed: no public pricing v1 (pricing model still open per USER.md). Agreed?
6. **Founder voice — third-person studio or first-person personal site?** Recommendation: third-person (reads as a studio). Worth a sense-check.

---

## Build effort estimate

- **Copy refinement (this draft → final):** 1 working day.
- **Design pass against brand sheet (figma or in-code):** 1–2 days.
- **Build (Next.js, 5 pages, forms, analytics):** 2–3 days.
- **Domain + email + analytics setup:** 0.5 day.
- **Total:** ~5–7 working days from sign-off to live.

If pressed for time, a stripped v0 (Home + Work + Talk only, three pages) ships in 2–3 days and earns you a domain that isn't a parked page while the full v1 builds.

---

## Atis £1k gate

- **Verdict (Atis would bet £1k on this site converting?):** *not yet*.
- **What would flip him to yes:**
  - **At least one paid case study card** with a named client and a measurable outcome ("we cut their invoice triage time from 4h/week to 20min/week"). Without it, the Results page is "interesting projects" rather than "proof of commercial delivery".
  - **Booking widget is live and the first 5 bookings are real prospects** (not friends being kind). Vanity calendar bookings collapse the whole funnel.
  - **A pricing anchor somewhere on the site** — even just *"engagements typically £8k–£40k depending on scope"*. Atis would say no-price means no-buyer.
- **What I'm NOT going to do about it yet (and why):**
  - **Force the paid case study before launch** — chicken-and-egg. The site is part of how you generate the first paid engagement. Acceptable to launch with built-but-unpaid case studies, provided the framing is honest (§4 honesty principle).
  - **Push pricing on day one** — pricing model is genuinely undecided per USER.md, and putting a wrong anchor on the site is worse than no anchor. Revisit in v1.1 once first engagement closes.
