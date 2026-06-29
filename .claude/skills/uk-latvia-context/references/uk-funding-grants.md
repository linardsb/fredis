# UK funding & grants — reference pack

A founder-facing cheatsheet for UK and UK-accessible innovation funding. It does
two things: (a) gives a **transferable scoring rubric** for judging whether a
programme is worth chasing — the durable, zero-staleness core; (b) carries a
**dated programme catalogue** with primary-source citations. The rubric is the
part that does not go stale; the catalogue is a snapshot and will.

> **Freshness note (read first).** Funding competitions open, close, pause, and
> rebrand constantly — faster than tax or filing rules. Every figure below is
> dated and cited to the page it came from. **Snapshot date: 2026-06-29.** Treat
> any award range, deadline, or "open / paused" status as stale until you
> re-check it on the cited URL. Two of the programmes the brief originally named
> had already changed by this snapshot (see §Programme catalogue).

---

## Contract — what this pack does and does not do

Same contract as the rest of `uk-latvia-context` ([[citation-and-provenance]]):

- **Reference only.** No API calls, no application submissions, no writes outside
  this skill's own folder. It points; it does not act.
- **Cites primary sources.** Every actionable figure carries a `[SRC-Cn]` marker
  resolving to the Source Register at the foot.
- **Flags the human advisor.** Fredis is **not** an authority on grant
  eligibility. The binding "are you eligible / will this be funded" call belongs
  to a grant consultant, an R&D tax specialist, or an accountant. This pack tells
  Linards *where to look* and *what to verify* — it does not rule on eligibility.

Answers from this pack carry the skill's standard confidence line:

- `confidence: reference` — taken directly from a cited catalogue entry, within
  its freshness window.
- `confidence: inferred` — combines catalogue facts with situational reasoning
  (e.g. scoring a lane against the rubric); verify before acting.
- `confidence: needs advisor` — touches a binding eligibility or tax-position
  judgement. Surface the relevant entry, then route to a human adviser.

Whenever the answer turns on a **specific number** (award range, deadline,
intervention rate), append: *"Verify on the cited page — these change; this
snapshot can go stale."*

---

## The state of play (2026-06-29 snapshot) — read before quoting any programme

The headline a founder needs before spending effort: **the broad,
sector-agnostic UK open grant is not currently available.** Innovate UK paused
its flagship Smart Grants in early 2025 [WEB2-C1], and on this snapshot date no
sector-agnostic open grant had replaced it [WEB3-C1]. What is actually live for a
solo UK software/AI founder:

- **R&D tax relief** — the cleanest near-term **non-dilutive** lever, *if* a
  UK company with qualifying R&D spend exists. It is a **tax relief, not a
  grant** [WEB14-C1].
- **EIC Accelerator (grant-only for UK applicants)** — for a project with EU
  ambition; UK applicants can take the grant but **not** the equity [WEB12-C1].
- **Challenge prizes and sector-specific competitions** — the Manchester Prize
  [WEB7-C1] and Innovate UK's live themed competitions/contracts [WEB3-C1],
  [WEB4-C1] — useful only when a current theme fits the lane.
- **Accelerators** (Tech Nation [WEB15-C1]) — network and visibility, generally
  **not** grant cash.

Everything else below is structure, watch-list, or out-of-fit. This is why the
rubric matters more than the catalogue: it stops effort going into a
well-known-but-closed programme.

---

## The eligibility-scoring rubric (the centrepiece)

Adapted from [tractorjuice/arc-kit](https://github.com/tractorjuice/arc-kit)'s
deterministic grants rubric [GH1-C1], reframed from a government project profile
to a **founder/lane profile**, and stripped of its orchestration machinery (no
subagent pipeline, no YAML files, no validator — just a table a human applies by
hand). Same six dimensions and weights; one honesty mechanism added on top.

### Step 0 — Hard gates (pass / fail, before any scoring)

A programme that fails a gate is **Ineligible**, full stop — do not score it, do
not shortlist it. Gates are where most wasted application effort dies.

| Gate | The question | Typical failure |
|------|--------------|-----------------|
| **Entity** | Does the applicant meet the required legal entity? | UK programmes usually need a **UK-registered company** [WEB2-C2]; EIC needs an EU / associated-country SME [WEB12-C2]. A Latvian or not-yet-incorporated entity fails a UK-registration gate. |
| **Size / age** | Within the programme's company size / age limits? | Some are SME-only; some exclude pre-trading; KTP needs **2+ full-time employees** [WEB5-C1], which a true solo founder fails. |
| **Partner** | If a collaborator is mandatory, can you field one? | KTP needs a **UK academic / Catapult lead** [WEB5-C2]; Horizon often needs a multi-country consortium [WEB10-C1]. No partner → out. |
| **Scope** | Is the lane's sector / theme inside the programme's *current* call? | Themed challenges (Manchester Prize round themes [WEB8-C1]; Contracts-for-Innovation challenges [WEB4-C2]) fund only their stated topic. |

### Step 1 — Weighted score (0–100 per criterion), only for programmes that clear every gate

| Criterion | Weight | Scores high when… |
|-----------|:------:|-------------------|
| **Eligibility fit** | 35% | Clears every gate comfortably (not marginally), with strong sector and development-stage overlap. (Innovate UK and EIC frame stage as **TRL** — technology readiness level; EIC Accelerator targets TRL 6–8 [WEB12-C3].) |
| **Funding-size fit** | 20% | The award band matches the lane's actual need — neither too small to justify the effort nor so large the project is too small to win it. |
| **Timing** | 15% | A round is open now or opens soon; rolling / continuous intake scores highest [WEB12-C4]; "closed, no date announced" scores lowest. |
| **Application burden** | 10% | A light application a solo founder can run unaided. Collaborative, consortium, or interview-stage processes lower it. |
| **Odds / track record** | 10% | The programme funds many recipients at a reasonable success rate; one-winner challenge prizes score low here. |
| **Match-funding burden** | 10% | Low or no required co-funding. A 33–50% match [WEB5-C3] is a real constraint for a bootstrapped founder and lowers the score. |

**Banding:** weighted total **≥ 70 = High fit · 40–69 = Medium · < 40 = Low.**
A failed Step-0 gate overrides the band → **Ineligible**.

### What the score is — and is not

The band is a **shortlist signal**: where to spend scarce application effort. It
is **not** an eligibility ruling and **not** a prediction of award. The binding
eligibility call is the programme's own assessors' and a grant adviser's — never
Fredis's. Always present a score as `confidence: inferred` and pair it with the
human-advisor flag.

### Founder / lane profile — the inputs you score against

To run the rubric, capture these first (this is the row the catalogue is scored
*against*; leave a field blank and the gates above cannot be judged):

- **Sector / technology** — what the product is (e.g. MarTech / AI software).
- **Lane stage** — concept / building / near-market / shipping.
- **Entity** — country of registration, company age, employee count. *(The
  single most decisive field — most gates turn on it.)*
- **Funding need** — the £ range that would actually move the lane.
- **Match-funding capacity** — how much co-funding the founder can put in.
- **Timeline** — when the money is needed by.
- **Collaboration reach** — can the founder field an academic / Catapult /
  consortium partner if one is required?

---

## Programme catalogue (dated snapshot — verify before acting)

Concise by design: structure, typical range, current status, the gate that most
often bites, and the source. Specific live deadlines are deliberately *not*
catalogued here — they decay within weeks; pull them from the cited page when an
application is actually on the table.

### UK domestic — Innovate UK / UKRI

**UKRI (the parent body).** UK Research and Innovation is the umbrella: seven
research councils (AHRC, BBSRC, ESRC, EPSRC, MRC, NERC, STFC), **Innovate UK**,
and Research England [WEB1-C1]. For a commercial software founder, **Innovate
UK** is the relevant arm — "the UK's national innovation agency, backing
innovative … businesses" [WEB1-C2]. *Source: `WEB1`.*

**Innovate UK Smart Grants — PAUSED / dormant.** Historically the flagship
*sector-agnostic* open grant. The live guidance page (last updated 2026-02-20)
still carries a pause notice — Smart Grants paused from January 2025 to develop
"tailored support" [WEB2-C1] — and legacy text claiming it is "always open" sits
in conflict on the same page. On the snapshot date **no Smart competition was
open** [WEB3-C1]. Eligibility *when it runs*: UK-registered companies carrying out
the project in the UK, with at least one SME in the project [WEB2-C2]. **Award
range and intervention rate are not stated on the current guidance page** — do
not quote a figure from memory; verify if it reopens. **Watch-list item:** a
broad open-grant successor. *Source: `WEB2`, `WEB3`.*

**Innovate UK Contracts for Innovation (formerly SBRI) — a CONTRACT, not a
grant.** SBRI has been rebranded; the gov.uk SBRI pages are withdrawn and the
live UKRI page titles it "Innovate UK Contracts for Innovation (formerly … the
Small Business Research Initiative or SBRI)" [WEB4-C1]. It is **procurement**: a
public body contracts you to develop a solution to a stated challenge — so it is
non-dilutive cash but **scope-gated** to the live challenge [WEB4-C2]. Open to
organisations of any size, including from the UK / EU / EEA [WEB4-C3]; "no minimum
or maximum" contract size [WEB4-C4]; phased (feasibility → prototype →
demonstrator). Fit only when a current challenge matches the lane. *Source:
`WEB4`.*

**Knowledge Transfer Partnerships (KTP) — collaborative, not solo-accessible.**
A three-way partnership: a UK knowledge base (HEI / FE / RTO / Catapult) leads,
partnered with a UK business of any size with **2+ full-time employees** that
**contributes to the cost** [WEB5-C1]. A business **cannot apply alone**
[WEB5-C2]. Package value ~**£80,000–£100,000 per year**, 12–36 months; the grant
covers ~**67% for SMEs (business pays ~33%)** or **50% for larger businesses**
[WEB5-C3]. Runs in fixed rounds (2026–27 Round 2 opened 20 May, closed 24 June
2026 — closed on the snapshot date). **Gate that bites:** the academic-partner
requirement and the 2-FTE floor — a poor fit for a solo, near-market product.
*Source: `WEB5`.*

**Innovate UK Business Growth — advisory support, currently PAUSED to new
clients.** Free, UK-Government-funded *advisory* support (specialists, scaleup
directors), **not grant cash** — only minor elements such as IP Audits attract a
small grant [WEB6-C1]. On the snapshot date new intake was **paused** "as part of
the current planning cycle," with more detail promised spring 2026 [WEB6-C2].
Useful as a relationship/diagnostic once it reopens; not a funding line. *Source:
`WEB6`.*

**Sector-specific Innovate UK competitions.** Beyond the above, Innovate UK runs
a rotating set of themed competitions, loans, and contracts on the Innovation
Funding Service [WEB3-C1]. These are the realistic UK-grant route *when a theme
fits the lane* — they must be checked live, per competition. *Source: `WEB3`.*

### UK domestic — DSIT challenge prizes & state investment

**The Manchester Prize (DSIT) — challenge prize.** A £1,000,000 annual prize for
UK-led AI teams, run by DSIT and delivered by Challenge Works (part of Nesta),
awarded each year for a decade [WEB7-C1]. Round 2 ran on the theme "AI for a
net-zero energy system": ten finalists each received £100,000 seed + up to
£60,000 compute, and the £1M prize was won by BiofuelAi (confirmed mid-2026)
[WEB8-C1]. Non-dilutive, but **theme-gated and lottery-odds** (one winner) — only
worth chasing if a future round's theme squarely fits the lane. No Round 3 theme
announced on the snapshot date. *Source: `WEB7`, `WEB8`.*

**UK Sovereign AI Fund — EQUITY, fenced off here as a different instrument
class.** A £500M state-backed venture fund making **equity** investments of
£1M–£10M in British AI startups (plus compute and contracts) [WEB9-C1]. Listed
for completeness because a founder will hear about it, but it is **dilutive
investment, not a grant or non-dilutive funding** — out of scope for a
non-dilutive search, and growth-skewed. *Source: `WEB9`.*

### EU — Horizon Europe (UK is associated)

**Horizon Europe — UK associated since 1 January 2024.** The UK is an associated
country via a Protocol to the Trade and Cooperation Agreement; UK entities
participate "under similar conditions as EU Member States," can lead consortia,
and are funded directly by the European Commission [WEB11-C1]. Programme budget
€95.5bn, running to 2027 [WEB10-C1]. Mostly collaborative, multi-country R&I
grants — heavy lift; the **consortium requirement** is the usual gate for a solo
founder. *Source: `WEB10`, `WEB11`.*

**EIC Accelerator — UK applicants get GRANT-ONLY.** The European Innovation
Council's instrument for single SMEs. Double-confirmed: a UK applicant "can only
apply for 'grant only'" [WEB12-C1] because UK association excludes the EIC Fund
equity component [WEB11-C2]. Grant: a lump sum **below €2.5M** for TRL 6–8 work
completed in ≤24 months [WEB12-C3]. Short proposals are continuous, batched
monthly; full-proposal cut-offs are published per year [WEB12-C4] — verify the
current dates live. Two-stage, interview-gated — a heavy application, but the
**single most substantial non-dilutive grant a UK SME can realistically target**
for deep-tech innovation. **Gate:** must read as genuine high-risk innovation
with EU-scale ambition. *Source: `WEB11`, `WEB12`.*

**FP10 / next Framework Programme — proposal only, not open.** The successor
(proposed to keep the "Horizon Europe" name, 2028–2034, ~€175bn) was presented by
the Commission on 16 July 2025 and is at proposal stage, to be negotiated
[WEB13-C1]. **UK association to it is not yet decided** [WEB13-C2]. Nothing to
apply for — a watch-list item for 2027+. *Source: `WEB13`.*

### Non-grant non-dilutive (clearly labelled)

**R&D tax relief — a TAX RELIEF, not a grant.** Claimed through Corporation Tax
from HMRC, not applied for as a grant [WEB14-C1]. Two routes for periods
beginning on/after 1 April 2024: the **merged RDEC scheme** — a **20%**
expenditure credit for companies of any size [WEB14-C2]; and **ERIS** (Enhanced
R&D Intensive Support) for **loss-making, R&D-intensive SMEs** where R&D is **≥
30%** of total spend — an extra **86%** deduction (186% total) plus a payable
credit worth **up to 14.5%** of the surrenderable loss [WEB14-C3]. **This is the
cleanest near-term non-dilutive lever for a UK Ltd doing genuine R&D** — but it
turns entirely on having a UK CT-paying company and qualifying spend, which is a
specialist's call. *Source: `WEB14`.*

### Accelerators & foundations (mostly support / equity — not grant cash)

**Tech Nation — relaunched; accelerator and pitch competitions.** Closed in 2023
when it lost government funding; the brand was acquired and relaunched under
Founders Forum Group, and is active in 2026 with stage-based cohorts (incl.
DeepTech and early-stage tracks) and pitch competitions surfacing £500k–£2M
investment opportunities [WEB15-C1]. **Network and visibility, not direct grant
cash**; any money attached is investment via the pitch comps. *Source: `WEB15`.*

**Nesta — Mission Studio — mission-restricted venture builder.** A studio
offering a stipend + build budget then **equity** spin-out investment, but only
for ventures inside Nesta's three missions: early childhood, obesity, and home
carbon emissions [WEB16-C1]. **Not a general AI/software route** — listed so it
is correctly excluded unless a lane squarely fits a mission. *Source: `WEB16`.*

### Instrument-class key — do not conflate these

| Instrument | Non-dilutive? | In this catalogue |
|------------|:-------------:|-------------------|
| **Grant** | Yes | Smart Grants (paused), EIC Accelerator (grant-only), Horizon consortia, KTP (collaborative) |
| **Contract / procurement** | Yes | Contracts for Innovation (ex-SBRI) |
| **Challenge prize** | Yes | Manchester Prize |
| **Tax relief** | Yes | R&D tax relief (RDEC / ERIS) |
| **Equity investment** | **No (dilutive)** | Sovereign AI Fund; Tech Nation pitch-comp investment; Nesta Mission Studio spin-out |
| **Advisory support** | n/a (no cash) | Innovate UK Business Growth (paused) |

---

## When to call a human advisor (the routing rule)

Route to a human — and mark the answer `confidence: needs advisor` — whenever the
question turns on any of:

- **Whether a specific entity is eligible** for a specific programme — that is the
  assessors' and a grant consultant's call, never Fredis's.
- **An R&D tax claim** — scheme choice (RDEC vs ERIS), what spend qualifies, the
  PAYE cap, and the net cash value all need an R&D tax specialist or accountant.
- **A live deadline or current award range** that this snapshot does not hold — go
  to the cited page, not to Fredis's memory.
- **EU consortium or EIC proposal strategy** — heavy, specialist processes.

Fredis's job is to narrow the field with the rubric and hand a short, sourced,
honestly-caveated list to the right human — not to issue a ruling.

---

## Source Register

Every figure above traces here. **Retrieved** is the date the page was fetched;
these sources are live and mutable, so re-check before acting.

| Source ID | Origin | Retrieved | Description |
|-----------|--------|-----------|-------------|
| `GH1` | https://github.com/tractorjuice/arc-kit | 2026-06-29 | ArcKit grants command + template — the rubric methodology this pack adapts |
| `WEB1` | https://www.ukri.org/councils/ | 2026-06-29 | UKRI structure; Innovate UK confirmed as a constituent body |
| `WEB2` | https://www.ukri.org/councils/innovate-uk/guidance-for-applicants/guidance-for-specific-funds/smart-innovation-funding-guidance/ | 2026-06-29 | Smart Grants guidance + pause notice; UK-registration eligibility |
| `WEB3` | https://apply-for-innovation-funding.service.gov.uk/competition/search | 2026-06-29 | Innovation Funding Service — live competition list (no open Smart competition on snapshot date) |
| `WEB4` | https://www.ukri.org/what-we-do/browse-our-areas-of-investment-and-support/innovate-uk-contracts-for-innovation/ | 2026-06-29 | Contracts for Innovation (formerly SBRI) — contract instrument, eligibility, sizing |
| `WEB5` | https://www.ukri.org/opportunity/knowledge-transfer-partnership-ktp-2026-to-2027-round-2/ | 2026-06-29 | KTP round 2 — partner requirement, 2-FTE rule, package value, intervention rate |
| `WEB6` | https://www.gov.uk/business-finance-support/innovate-uk-business-growth | 2026-06-29 | Innovate UK Business Growth — advisory support, paused to new clients (cross-checked against the iuk-business-connect FAQ) |
| `WEB7` | https://www.gov.uk/government/publications/manchester-prize | 2026-06-29 | Manchester Prize — £1M annual AI challenge prize, DSIT |
| `WEB8` | https://challengeworks.org/challenge-prizes/manchester-prize-round-2/ | 2026-06-29 | Manchester Prize Round 2 — theme, finalist seed, winner (BiofuelAi, confirmed via University of Surrey release) |
| `WEB9` | https://www.sovereignai.gov.uk/ | 2026-06-29 | UK Sovereign AI Fund — £500M state equity, £1–10M cheques (dilutive) |
| `WEB10` | https://www.ukri.org/apply-for-funding/horizon-europe/ | 2026-06-29 | Horizon Europe for UK applicants — budget, association overview |
| `WEB11` | https://research-and-innovation.ec.europa.eu/strategy/strategy-research-and-innovation/europe-world/international-cooperation/association-horizon-europe/united-kingdom_en | 2026-06-29 | EC UK-association page — associated since 1 Jan 2024; EIC Fund equity excluded |
| `WEB12` | https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en | 2026-06-29 | EIC Accelerator — UK grant-only, <€2.5M grant, TRL 6–8, cut-off cadence |
| `WEB13` | https://european-research-area.ec.europa.eu/news/ec-presents-proposal-next-framework-programme | 2026-06-29 | FP10 proposal — €175bn, 2028–2034, presented 16 Jul 2025, not adopted |
| `WEB14` | https://www.gov.uk/guidance/research-and-development-rd-tax-relief-the-merged-scheme-and-enhanced-rd-intensive-support | 2026-06-29 | R&D tax relief — merged RDEC 20%; ERIS 186% + up to 14.5%; 30% intensity threshold |
| `WEB15` | https://technation.io/ | 2026-06-29 | Tech Nation — relaunched accelerator + pitch competitions |
| `WEB16` | https://missionstudio.vc/ | 2026-06-29 | Nesta Mission Studio — mission-restricted venture builder (cross-checked against nesta.org.uk project page) |

---

## Maintenance

These figures decay faster than the rest of `uk-latvia-context`. Re-verify any
catalogue entry against its cited URL **before acting on it**, and refresh the
whole catalogue if it is used heavily. Anchor a review for **December 2026** (six
months from this snapshot) given the pace of change — sooner if Smart Grants'
successor or a relevant Innovate UK theme reopens. The rubric does not need
refreshing; only the catalogue does.

**Related:** [[citation-and-provenance]] · [[draft-path-convention]] · [[lanes]] · plan `.agent/plans/arckit-borrows.md` (item B4).
