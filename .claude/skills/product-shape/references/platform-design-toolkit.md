# Platform Design Toolkit — two-sided / marketplace extension

`product-shape` shapes a single-sided product: price it, position it, pick the stack. A
**two-sided** product breaks that mould. A marketplace has no product until both sides show up at
once, the thing you charge for is a *transaction between other people*, and the moat is the network,
not the feature set. None of `pricing-shaper`, `positioning-sharpener`, or `mvp-architect` thinks in
those terms. This reference is the extension that does.

It ports the eight-canvas **Platform Design Toolkit** (PDT) — ecosystem-first strategy design for
multi-sided markets — into Fredis's neutral voice, product-generic. Run it *before* the other three
references when the product is a marketplace; its outputs become their inputs.

## When this loads

Load this reference when the product is multi-sided — it serves at least two distinct participant
groups whose value to each other the product intermediates. Triggers: "marketplace", "two-sided",
"commission", "take rate", "liquidity", "network effect", "chicken-and-egg", or the **Cab** lane
(B2C ride-hailing — drivers and riders are the two sides).

The test: *if one side vanished overnight, would the other side still get value?* If no, it is
two-sided and the chicken-and-egg problem is real — use this reference. If yes (one side is just a
supplier you could replace), treat it as single-sided and skip to `pricing-shaper`.

## Where it sits in product-shape

For a two-sided product the sequence changes. Platform-design runs **first** and feeds the rest:

| This canvas produces… | …which feeds |
|---|---|
| Take-rate justification (Transactions Board, §4) | `pricing-shaper` B2C-commission canvas — the commission is grounded in transaction-cost reduction, not pulled from a competitor benchmark |
| Two-sided entity portraits (§2) | `positioning-sharpener` — best-fit customer becomes best-fit customer *per side*; you position to each side separately |
| MVP + liquidity strategy (§7) | `mvp-architect` first-commit checklist and `launch-governance/launch-wedge` first-10-users plan |
| Network-effect defensibility (§8) | `launch-governance/bet-review` — the moat claim the monthly review tests |

So this does not replace the existing three references; it front-loads the ecosystem thinking they
assume away, then hands each its grounded input. Do not re-derive pricing maths or positioning
bullets here — produce the *raw material* and cross-reference.

## What it adds — the four gaps

Weight the work here. These are the parts a single-sided shaping pass cannot reach:

1. **Liquidity bootstrapping** (chicken-and-egg). The central marketplace risk: no supply means no
   demand means no supply. Solved in §7, not by "build more features".
2. **Transaction-cost economics** (justifies the take rate). A platform earns its commission by
   removing cost from a transaction the two sides would otherwise bear themselves. Quantified in §4.
3. **Two-sided entity portraits.** Supply and demand have different jobs, pressures, and gains. One
   persona is not enough; §2 portrays each side.
4. **Network-effect defensibility.** Why the second mover cannot just copy the features — same-side,
   cross-side, data, and learning effects compound into a moat. Articulated in §8.

---

## The eight canvases

Each canvas below gives its purpose, the fields to fill, and a Fredis working note. Keep tables
lean — a marketplace draft does not need all of these filled exhaustively; weight toward the four
gaps. Cite every external fact per [[citation-and-provenance]].

### 1. Ecosystem Canvas — map the participants

**Purpose:** name every entity type in the market and the resources flowing between them. 5–15
entities across three classes: **supply** (provides the core value), **demand** (consumes it),
**supporting** (enables the exchange — payments, identity, regulators, complementors).

**Entity Catalog fields:** Entity ID · Name · Type (supply / demand / supporting) · Role · Resources
provided · Resources consumed.

Then describe the **relationships and flows** between them (a simple flow diagram or a flows list)
and the **ecosystem boundary** — who is inside the platform's remit and who is an external force.

**Working note:** the supporting entities are where the regulatory and rails risk hides — payment
licensing, identity/KYC, insurance, the incumbent you are displacing. List them now so they are not
a surprise in §7.

### 2. Entity Portraits — one per side, minimum

**Purpose:** a deep portrait of each key participant type. Minimum three: primary supply-side,
primary demand-side, one supporting entity. This is the two-sided answer to a single product persona.

**Per portrait:**
- **Context** — who they are, their current situation, their constraints.
- **Performance pressures** — the external and internal forces acting on them (what makes their week
  hard).
- **Goals** — short-term (0–6 mo) · medium-term (6–18 mo) · long-term (18+ mo).
- **Gains sought** — the value propositions that would pull them onto the platform, each with a
  metric (the gain only counts if it is measurable).
- **Linkage** — map each goal to the platform feature that serves it and how that feature delivers.

**Working note:** the two sides are rarely symmetric in power. One side is usually scarcer (harder to
acquire) and therefore decides liquidity. Mark which side is the constraint — it drives the whole
bootstrapping plan in §7.

### 3. Motivations Matrix — where the sides align and clash

**Purpose:** an N×N grid of every entity against every other, each cell stating whether their
motivations are **aligned** or in **conflict**, with the reasoning. Then pull out the key synergies
and — more important — the key conflicts.

**Per synergy / conflict:** entities involved · the shared motivation or point of conflict · the
platform's role in amplifying it or resolving it · the success metric.

**Working note:** the conflicts are the design brief. Driver wants the highest fare; rider wants the
lowest; the platform's take sits in the gap and both resent it. Surface that tension explicitly — the
take-rate design in §4 and the pricing canvas downstream have to answer it, not paper over it.

### 4. Transactions Board — the engine, and the take-rate justification

**Purpose:** catalogue the transactions the platform intermediates (aim for the 8–15 that matter,
not an exhaustive list) and quantify how much cost the platform removes from each. **This is where
the commission is justified.**

**Transaction Catalog fields:** Transaction ID · Name · From entity → To entity · Exists today?
(yes/no) · Current channel · Transaction cost *without* the platform · Platform channel · Transaction
cost *with* it · Cost reduction.

**Transaction-cost economics — the five dimensions** (Coase). For each transaction, account for cost
across: **search** (finding a counterparty), **information** (verifying quality/trust),
**negotiation** (agreeing terms/price), **coordination** (timing, logistics, matching), and
**enforcement** (payment, disputes, recourse). The platform's take rate is *earned* to the extent it
collapses these costs below what the two sides would spend transacting on their own.

**Working note:** this is the take-rate argument `pricing-shaper` needs. A 15–20% commission is
defensible only if the platform demonstrably removes more than 15–20% of friction-cost from the deal.
Where there is no real data on current costs (a concept-stage lane), state the figures as
**assumptions to validate**, not findings — see Anti-patterns.

### 5. Learning Engine Canvas — the compounding layer

**Purpose:** design the services that make the platform *better the more it is used* — the data and
learning loops that turn transaction history into improvement for the participants. 3–5 services.

**Per service:** What (description) · Inputs (data sources) · Outputs (what the entity receives) ·
How the entity improves · Platform benefit (why this builds defensibility) · Success metric. Then a
short note on whether any of it is itself monetisable (a premium analytics tier, say).

**Working note:** this is half of the moat in §8 (the data/learning effects). For Cab: surge
prediction, demand heat-maps for drivers, fraud/safety scoring, rider-driver match quality. Each gets
better with volume — that compounding is the thing a fast follower cannot copy on day one.

### 6. Platform Experience Canvas — the journeys and the money

**Purpose:** map the core journeys for each side and attach the business model. Minimum two journeys:
**supply-side onboarding → first transaction** and **demand-side discovery → first purchase**.

**Journey map fields (per stage, ~6–10 stages awareness → retention):** Stage · Entity action ·
Platform service · Transaction (ref §4) · Learning service (ref §5) · Touchpoint · Pain point
addressed.

**Journey metrics:** Metric · Target · Current (without platform) · Improvement.

**Business model:** revenue streams (type · description · projected volume/revenue) · cost structure ·
**unit economics** (per-transaction contribution · per-entity annual value · LTV · CAC · LTV:CAC).

**Working note:** unit economics on a concept-stage marketplace are *hypotheses*, not analysis. Fill
LTV/CAC/take as "what we would need to see for this to work", flag the riskiest number, and hand the
real modelling to `pricing-shaper`. Do not present projected ratios as if measured.

### 7. Minimum Viable Platform Canvas — liquidity first

**Purpose:** the smallest platform that can clear the chicken-and-egg problem in one constrained
market. Not feature-minimal — *liquidity*-minimal.

- **Critical assumptions:** Assumption · Riskiness (high/med/low) · Evidence needed · Test method.
  List 5+; the riskiest is almost always "we can acquire the scarce side cheaply enough".
- **MVP feature set:** an explicit **in** list and **out** (deferred) list — write them as words, not
  ticks.
- **Liquidity bootstrapping strategy — four phases:**
  1. **Curate initial supply** — hand-pick and onboard the scarce side first (concierge, not
     self-serve). Constrain the market hard: one city, one corridor, one segment.
  2. **Seed demand** — white-glove the first buyers into the curated supply; manufacture the first
     transactions if you must (do things that don't scale).
  3. **Test transaction velocity** — can a match clear reliably and fast in the constrained market?
     This is the liquidity signal, not sign-up counts.
  4. **Expand liquidity** — only once velocity holds, widen the constraint (next corridor, next
     segment).
- **Validation metrics:** Metric · Success threshold · Actual · pass/no — a 10+-criterion Go/No-Go
  set for a ~90-day read.
- **Timeline and budget:** rough, category-level.

**Working note:** the constraint is the strategy. A marketplace that launches "everywhere" has
liquidity nowhere. Tie phase 1 to the scarce side identified in §2. This canvas is the direct input
to `launch-governance/launch-wedge` and the kill-trigger gate.

### 8. Platform Design Canvas — synthesis and the moat

**Purpose:** pull the prior seven canvases into six building blocks that state the platform strategy
in one place.

1. **Ecosystem** — participant types and a 1–3 year size target per side.
2. **Value creation** — value for the supply side, the demand side, and the ecosystem overall.
3. **Value capture** — the revenue model and the rationale (grounded in §4).
4. **Network effects** — articulate each that applies and why it defends the position:
   - **same-side** (more drivers attract more drivers via density),
   - **cross-side** (more drivers attract more riders and vice-versa — the core marketplace loop),
   - **data effects** (more transactions sharpen matching/pricing — from §5),
   - **learning effects** (the platform's services improve with use — from §5).
   State the **defensibility**: what a fast follower would have to rebuild, and why the network — not
   the app — is the barrier.
5. **Transaction engine** — the core transactions, their cost reductions, and a velocity target.
6. **Learning engine** — the learning services, any revenue, and the improvement they drive.

**Working note:** block 4 is the answer to "why won't Bolt/an incumbent just do this?". If the honest
answer is "they would and they have a decade's head start", that belongs in the Atis gate as a
*not-yet*, not buried. The moat claim is what `bet-review` will test monthly.

---

## Composing with the rest of product-shape

After this reference produces its canvases, hand off:

- Take-rate + transaction-cost analysis (§4) → `pricing-shaper` (B2C-commission canvas).
- Per-side entity portraits (§2) → `positioning-sharpener` (best-fit customer per side).
- MVP + liquidity plan (§7) → `mvp-architect` (stack + first-commit) and
  `launch-governance/launch-wedge` (first 10 of the scarce side).
- Network-effect defensibility (§8) → `launch-governance/bet-review` (the moat to re-test monthly).

## Grounding, Atis gate, provenance

This is a decision-grade artefact, so it cites per [[citation-and-provenance]]: every external fact
(a competitor's commission, a market size, a regulation) carries an inline marker and a Source
Register row, and unsourced figures are labelled as assumptions. It names its upstream inputs and
STOPs if a depended-on artefact is missing, per [[draft-path-convention]] §Grounding discipline. It
ends with the `## Atis £1k gate` block ([[atis-test]]) and a `## Provenance` block.

## Attribution

The eight-canvas method is the **Platform Design Toolkit** (PDT v2.2.x) by Boundaryless.io
(Simone Cicero et al.), CC-licensed. Borrowed into Fredis via the structure in
[tractorjuice/arc-kit](https://github.com/tractorjuice/arc-kit)'s platform-design command. ArcKit's
UK-government framing (GaaP / Technology Code of Practice / GDS Service Standard / Digital
Marketplace) and its dependencies on ArcKit-specific artefacts (stakeholder/requirement/Wardley/
principle auto-population, traceability registers) are **stripped** — this reference is
product-generic and stands alone. Related plan: `.agent/plans/arckit-borrows.md` (item B1).

## Anti-patterns

- **Counting sign-ups as liquidity.** Registrations are not transactions. The only liquidity signal
  is a match clearing reliably in the constrained market (§7 phase 3).
- **Launching unconstrained.** "The whole country at once" means liquidity nowhere. Constrain to one
  corridor/segment and earn the right to expand.
- **Presenting hypothetical unit economics as analysis.** On a concept-stage marketplace, LTV/CAC/
  take-rate (§6) and cost-reduction percentages (§4) are assumptions to validate. Label them so;
  borrowed competitor benchmarks must be cited to a fetched source, not asserted.
- **Pricing the take rate before §4.** A commission with no transaction-cost-reduction argument
  behind it is a number the two sides will route around the first chance they get.
- **One persona for a two-sided market.** Supply and demand have different jobs; §2 portrays each.
