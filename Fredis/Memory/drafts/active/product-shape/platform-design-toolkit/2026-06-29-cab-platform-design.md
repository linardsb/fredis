---
skill: product-shape/platform-design-toolkit
lane: cab
created: 2026-06-29
status: draft
---

# Cab — Platform Design (two-sided marketplace)

Cab is a B2C ride-hailing marketplace, Latvia-first, framed as a Bolt-replacement angle, sharing the
VTV codebase and sequenced after VTV traction [V1-C1]. This draft applies the eight-canvas Platform
Design Toolkit [V3-C1] to shape it as a two-sided market *before* pricing, positioning, and stack
work. It is a shaped artefact for when the lane unlocks — **not** a recommendation to start building.
Cab is currently parked behind VTV, and its own kill trigger fires if VTV has no real B2G
conversations by end of month 4 [V1-C2].

Almost every quantity below is an **assumption to validate**, not a finding — Cab is concept-stage
[V1-C3] and no transaction, cost, or acquisition data exists yet. Figures are written as "what we
would need to see", and the one borrowed competitor benchmark is flagged for verification.

---

## 1. Ecosystem Canvas — the participants

| ID | Entity | Type | Role | Provides | Consumes |
|----|--------|------|------|----------|----------|
| E1 | Drivers | Supply | Carry riders | Vehicle, time, local knowledge | Fares, demand, routing |
| E2 | Riders | Demand | Take rides | Fares, ratings | Transport, ETA, safety |
| E3 | Payment / rails | Supporting | Settle fares | Card/local-rail settlement | Transaction fee |
| E4 | Identity / KYC + insurance | Supporting | Licence, vet, cover drivers | Trust, compliance, cover | Verification load |
| E5 | Regulators / municipality | Supporting | Licence the operation | Legal right to operate | Compliance, tax, data |
| E6 | VTV operator + government relations | Supporting | Distribution base | Channel into LV operators/gov | Shared infra, alignment |
| E7 | Bolt (incumbent) | Adjacent | Sets the default | — | The market we displace |

**Boundary:** Cab operates the match between E1 and E2 inside one constrained LV market at launch.
E3–E5 are external dependencies that must be in place before any ride clears; E6 is the lane's stated
distribution dependency — Cab "rides on VTV's operator + government relationships" and a parallel push
only makes sense if a distinct Cab partner is pulling separately [V1-C4]. E7 is the force every
canvas has to answer.

**Working note:** the supporting entities (E3–E5) are the regulatory/rails risk — LV Road Traffic Law
licensing, municipal licensing, and the EU Mobility Package (VHC/taxi directives) all apply [V1-C5].
None of this is a "feature"; it is precondition.

## 2. Entity Portraits — the two sides

Supply and demand are not symmetric. In ride-hailing cold-start the **scarce side is drivers** —
without cars there are no rides, and drivers carry switching inertia from the incumbent they already
earn on. Drivers decide liquidity. Treat driver acquisition as the binding constraint throughout.

### E1 — Driver (supply, the constraint)

- **Context:** earns today on Bolt (and possibly a taxi licence); a phone, a car, and finite hours;
  income-sensitive.
- **Performance pressures:** every idle minute is lost income; commission erodes take-home; rating
  systems and deactivation risk loom; fuel and vehicle costs are fixed.
- **Goals:** short — fill idle hours with paid trips; medium — steady weekly income above the Bolt
  baseline; long — a platform that does not squeeze the take rate as it grows.
- **Gains sought (each needs a metric):** higher net earnings per hour (€/active hour vs Bolt);
  shorter dead-heading (% paid km); fair, transparent commission (take-rate %); fast payout (days to
  cash).
- **Linkage:** density-aware dispatch → shorter pickups → more paid km; a structurally lower or
  VTV-subsidised take rate → higher net €/hour (the wedge, if it can be funded).

### E2 — Rider (demand)

- **Context:** opens Bolt by default in Riga; price- and time-sensitive; cares about safety and
  reliability.
- **Performance pressures:** wants a car *now*; will not wait on a thin app with long ETAs; one bad
  ride loses them.
- **Goals:** short — get a reliable ride at a fair price; medium — a default app that is consistently
  cheaper or faster on their routes; long — trust.
- **Gains sought:** lower fare (€ vs Bolt on the same route); short ETA (minutes to pickup);
  perceived safety (verified drivers, trip sharing); reliability (completion rate).
- **Linkage:** liquidity in the launch zone → short ETA; lower take rate passed through → lower fare.

### E5 — Regulator / municipality (supporting)

- **Context:** licenses ride-hailing under LV Road Traffic Law + municipal rules [V1-C5]; cares about
  safety, licensed drivers, tax compliance.
- **Goals:** licensed, insured, tax-compliant operation; no informal-economy leakage.
- **Linkage:** KYC/insurance (E4) and transparent settlement (E3) are how Cab stays inside the
  licence. VTV's existing government relationships (E6) may shorten the path [V1-C4].

**Working note:** drivers are the constraint → §7 phase 1 is entirely about acquiring and retaining
the first cohort of drivers, not riders.

## 3. Motivations Matrix — alignment and conflict

| | Driver | Rider | Platform |
|---|---|---|---|
| **Driver** | density helps all drivers (same-side) | aligned: ride happens | **conflict:** driver wants high fare + low take |
| **Rider** | conflict: fare level | network: more riders → more drivers | aligned: low fare, but take funds the platform |
| **Platform** | take rate vs driver net | take rate vs rider price | — |

**Key conflict — the take-rate squeeze.** Driver wants the highest fare and lowest commission; rider
wants the lowest fare; the platform's take sits in the gap and both resent it. This is the central
design tension, and the take-rate work in §4 must *justify* the cut, not hide it. **Key conflict —
growth vs compliance:** moving fast on driver supply collides with licensing/KYC (E4/E5); cutting that
corner is how a ride-hailing launch gets shut down.

**Key synergy — the cross-side loop:** more drivers shorten ETAs, which pulls riders, whose demand
fills driver hours, which retains drivers. That loop is the whole business — §8 turns it into the moat
claim.

## 4. Transactions Board — the engine and the take-rate justification

Core transaction: **a completed ride** (E2 requests → E1 matched → trip → settlement → rating). The
take rate is earned only if the platform collapses more friction-cost out of that transaction than it
charges.

**Transaction-cost reduction across the five dimensions (Coase):**

| Dimension | Cost without a platform | How Cab removes it |
|---|---|---|
| Search | hailing/phoning, no guarantee of a car | instant match against nearby supply |
| Information | is the driver safe? the car real? | KYC, ratings, verified identity (E4) |
| Negotiation | agreeing a fare on the spot | algorithmic, pre-agreed fare |
| Coordination | where/when is pickup | GPS dispatch, live ETA, in-app comms |
| Enforcement | cash, no recourse on a bad trip | in-app settlement, dispute/refund, rating |

**Take-rate justification.** A commission is defensible to the extent it sits *below* the friction it
removes. A take rate in the region of **15–25%** is the working assumption [V2-C1] — but that band is
borrowed from an internal skeleton note with **no verified external source attached** and must be
confirmed against Bolt's actual per-market driver commission before `pricing-shaper` treats it as
fact. Do not assert it as Bolt's rate. The strategic question Cab has to answer: can it sustain a take
rate that leaves drivers visibly better off than the incumbent — possibly funded by VTV-shared infra
reducing Cab's own cost base — without starving the platform? That is the §6 unit-economics hypothesis
and a core Atis-gate flip.

**Working note:** all cost figures here are directional until a real launch produces transaction data.
This canvas is the raw material for `pricing-shaper`'s B2C-commission canvas — it does not set the
final number.

## 5. Learning Engine — the compounding layer

Services that improve with volume (each compounds the moat in §8):

| Service | Inputs | Output | Entity improves | Platform benefit |
|---|---|---|---|---|
| Demand prediction / surge | trip history, time, weather | heat-map, surge signal | drivers position ahead of demand | better match velocity |
| Driver positioning guidance | live supply/demand | "go here" nudges | fewer dead-heading km | shorter ETAs |
| Safety / fraud scoring | ratings, trip telemetry | risk flags | safer rides | trust, fewer incidents |
| Match-quality optimisation | accept/cancel, ETAs | better pairings | faster pickups | retention both sides |

**Working note:** these are the data/learning effects that a fast follower cannot copy on day one
because they require accumulated transaction volume. They are also a potential premium tier later
(driver analytics), but that is post-liquidity — not MVP.

## 6. Platform Experience — journeys and the money

**Driver journey (supply, the hard one):** awareness (referral / Atis's LV network) → sign-up → KYC +
insurance check (E4) → first dispatch → first paid fare → weekly income above baseline → retention.
Friction concentrates at KYC and at the first-week earnings — if the zone is not liquid, the driver's
first hours are empty and they churn back to Bolt.

**Rider journey (demand):** awareness → install → first ride request → short ETA → completed ride →
fair fare → re-open as default. Friction concentrates at the first ETA — a long wait on ride one loses
them.

**Unit economics — hypotheses, not analysis.** No real data exists; these are the numbers Cab would
need to *see*, and each is a validation target, not a claim:

| Quantity | What we would need to see | Risk |
|---|---|---|
| Driver CAC | low enough to beat Bolt switching inertia | **highest risk** |
| Rider CAC | recoverable within N rides | high |
| Rides / rider / month | enough frequency for LTV > CAC | medium |
| Take per ride | covers cost + funds growth at a driver-favourable rate | high |
| LTV:CAC (both sides) | > 3:1 to be viable | unknown until data |

**Working note:** the riskiest number is driver CAC against an entrenched incumbent. `pricing-shaper`
owns the real modelling; this canvas only frames the hypotheses.

## 7. Minimum Viable Platform — liquidity first

The MVP is not feature-minimal; it is **liquidity-minimal** — the smallest platform that clears the
chicken-and-egg in one constrained LV market.

**Critical assumptions:**

| Assumption | Riskiness | Evidence needed | Test |
|---|---|---|---|
| Drivers can be acquired below their Bolt switching inertia | High | first-cohort sign-up + retention at target CAC | concierge recruit ~50–100 Riga drivers |
| Riders will switch from Bolt for a real price/ETA edge in the zone | High | repeat-ride rate in the launch zone | white-glove a seed rider segment |
| VTV distribution actually pulls (operator/gov relationships) | High | a concrete VTV B2G conversation exists | gated on the VTV month-4 trigger [V1-C2] |
| The launch zone can reach match velocity | Medium | rides clearing under target ETA | measure in zone |
| Regulatory/licensing path is clear in Riga | Medium | licence + KYC/insurance in place (E4/E5) | confirm before any ride |

**MVP feature set —**
*in:* driver app (accept, navigate, earnings), rider app (request, track, pay, rate), matching in one
zone, KYC + insurance, in-app payment, ratings.
*out (deferred):* surge pricing, multi-city, scheduled rides, driver analytics tier, the full learning
engine (§5 services come online with volume, not at launch).

**Liquidity bootstrapping — four phases:**
1. **Curate supply (drivers first).** Hand-recruit ~50–100 drivers in one Riga zone — concierge, not
   self-serve — plausibly via Atis / Juris and the LV network [V1-C6]. Constrain hard: one corridor or
   district, not the city.
2. **Seed demand.** White-glove a defined rider segment into that supply — an employer, an airport
   corridor, a campus — and manufacture the first rides if needed (do things that don't scale).
3. **Test transaction velocity.** Can a ride clear reliably under a target ETA in the zone? This — not
   sign-up counts — is the liquidity signal.
4. **Expand.** Only once velocity holds, widen to the next corridor.

**Validation metrics (90-day Go/No-Go, pass / no):** driver retention week 4; rider repeat rate;
median ETA in zone; rides per active driver-hour; driver net €/hour vs Bolt baseline; completion rate;
driver CAC vs target; rider CAC vs target; zone match velocity; one concrete VTV distribution signal.
Ten criteria; the gate is the kill-trigger YAML for `launch-governance/metrics-gate`.

**Working note:** the constraint *is* the strategy. A Cab that launches "Latvia" has liquidity
nowhere. Phase 1 is one zone, drivers first.

## 8. Platform Design Canvas — synthesis and the moat

1. **Ecosystem:** drivers + riders in one LV zone at launch (E1/E2), four supporting entities
   (E3–E6); 1–3 year target deferred until the lane unlocks.
2. **Value creation:** drivers — higher net €/hour + filled idle time; riders — lower fare / shorter
   ETA / safety; ecosystem — a licensed LV-native alternative to a single incumbent.
3. **Value capture:** commission per ride; rate grounded in §4's transaction-cost reduction, not a
   borrowed benchmark; the wedge is a driver-favourable take possibly funded by VTV-shared infra.
4. **Network effects & defensibility:**
   - *same-side* — driver density shortens ETAs, attracting more drivers in the zone;
   - *cross-side* — drivers ↔ riders, the core loop;
   - *data* — surge/match sharpen with volume (§5);
   - *learning* — positioning and safety services improve with use (§5).
   **Honest defensibility read:** none of these effects exist on day one, and Bolt holds a ~decade
   head start with established density [V1-C7]. Cab has **no inherent network moat at launch**. The
   only credible wedge is (a) a segment or corridor Bolt under-serves, plus (b) a structurally
   lower/VTV-subsidised take rate drivers can feel, defended later by the §5 data/learning loops once
   volume accrues. If neither holds, this is a feature-copy of an entrenched incumbent — and that
   belongs in the Atis gate as a *not-yet*.
5. **Transaction engine:** the completed ride; five-dimension cost reduction (§4); velocity target set
   per launch zone.
6. **Learning engine:** the §5 services; no launch revenue, defensibility payoff with volume.

---

## Composing with the rest of product-shape

- Take-rate + transaction-cost analysis (§4) → `pricing-shaper` B2C-commission canvas (it sets the
  real number; verify the 15–25% benchmark first [V2-C1]).
- Two-sided portraits (§2) → `positioning-sharpener` — position to drivers and riders separately;
  the lane's weak default "Bolt replacement in Riga" needs a named under-served segment.
- MVP + liquidity (§7) → `mvp-architect` (the Cab stack template already exists there) and
  `launch-governance/launch-wedge` (first 10 drivers, not first 10 users).
- Network-effect defensibility (§8) → `launch-governance/bet-review` — the moat claim to re-test.

## Atis £1k gate

- **Verdict (Atis would bet £1k?):** **not yet.** Cab is concept-stage [V1-C3], parked behind VTV
  [V1-C1], and its day-one defensibility against an entrenched incumbent is honestly thin (§8).
- **If no / not yet — what would flip him:**
  - VTV showing real B2G traction, proving the distribution base Cab depends on [V1-C2][V1-C4].
  - Evidence the first driver cohort can be acquired and retained *below* their Bolt switching
    inertia at a viable CAC (§7, highest-risk assumption).
  - A named corridor/segment Bolt under-serves — i.e. positioning off the incumbent's strongest
    ground, not onto it.
  - A verified take-rate and cost structure (replace the unsourced 15–25% [V2-C1] with a confirmed
    per-market figure) showing drivers net more than on Bolt while the platform still funds growth.
- **What I'm NOT going to do about it yet (and why):**
  - Not start building Cab — it is correctly parked behind VTV; this draft is the shaped artefact for
    when the lane unlocks, not a green light.
  - Not fetch/verify the Bolt commission figure in this pass — flagged for `pricing-shaper` when Cab
    becomes live, to keep this draft proportionate to a parked lane.

## Source Register

| Source ID | Origin | Retrieved | Description |
|-----------|--------|-----------|-------------|
| `V1` | `.claude/skills/_shared/lanes.md` (Lane 3 — Cab) | 2026-06-29 | Cab lane facts: two-sided, Latvia-first, Bolt-replacement, regulatory layer, distribution dependency on VTV, kill trigger, LV partners |
| `V2` | `.claude/skills/product-shape/references/pricing-shaper.md` | 2026-06-29 | B2C-commission canvas; "Bolt 15–25%" take-rate benchmark — **internal skeleton note, no external source; needs verification** |
| `V3` | `.claude/skills/product-shape/references/platform-design-toolkit.md` | 2026-06-29 | The 8-canvas PDT method applied here |

## Provenance

- **Skill:** product-shape/platform-design-toolkit
- **Model:** claude-opus-4-8
- **Inputs:** V1, V2, V3  (see Source Register)
- **Voice:** neutral
- **Generated:** 2026-06-29
