# ISO Safety Standards for Robotics

This file summarises the three regime-defining standards. It is a navigation aid — full text and certification require accredited sources.

## ISO 10218 — Industrial robots

Two parts:

- **Part 1 (ISO 10218-1)** — safety requirements for the *robot manufacturer*. Covers inherent design, protective measures, information for use.
- **Part 2 (ISO 10218-2)** — safety requirements for *robot system integration*. Covers cell layout, guarding, safeguarding, safety functions.

Applies to: caged / fenced industrial robots where operators and the robot occupy separate spaces during normal operation. Entry into the robot envelope triggers safety-rated monitored stop.

Typical protective measures: light curtains, safety-rated interlocked doors, floor mats, safety-rated stop categories (Cat 0/1/2 per IEC 60204-1).

## ISO 13482 — Personal-care robots

Covers three classes:

- **Mobile servant** — travels autonomously in a domestic or personal environment (e.g. home assistant, hospital porter robot).
- **Physical assistant** — worn or physically attached to a person (e.g. exoskeletons).
- **Person carrier** — transports a person (e.g. wheelchair robots, autonomous mobility devices).

Covers: operational envelope, hazards from unstable operation, hazards from incorrect human-robot interaction (HRI), fail-safe behaviour, emergency stop, stability, guarding against pinch/crush, post-fault behaviour.

Does **not** cover medical devices (that's MDR / 60601), toys, military robots, or public-transport autonomy.

## ISO 15066 — Collaborative robots (cobots)

Technical specification supplementing ISO 10218 for robots operating in shared workspace with humans. Defines four collaborative methods:

1. **Safety-rated monitored stop** — robot stops when human enters the shared workspace; resumes when human leaves.
2. **Hand-guiding** — operator physically leads the robot via a hand-guide device; robot operates only while guided.
3. **Speed-and-separation monitoring** — robot tracks human position via safety-rated sensors; speed drops or stops as separation decreases below a computed safety margin.
4. **Power-and-force limiting** — robot is inherently safe by design such that any human contact stays below biomechanical limits; this is the most widespread interpretation in current cobots.

Key numerical tables:
- **Table A.2** — biomechanical limits for transient contact (e.g. upper arm: 140 N, lower leg: 220 N, face/skull: no transient contact permitted).
- **Table A.3** — biomechanical limits for quasi-static contact (held against surface or free in space).

## How to pick

- **Fenced, operator-excluded, industrial setting** → ISO 10218 (+ integrator sign-off under Part 2).
- **Shared-workspace, close-proximity, industrial setting** → ISO 10218-1 + ISO 15066.
- **Domestic / personal / non-industrial** → ISO 13482.
- **Mixed deployment** → apply all that fit; the most restrictive set wins for any given operation mode.

## Certification

Self-declaration is not acceptable for these regimes in most jurisdictions. Notified-body or equivalent accredited testing is required for CE / UKCA. Functional-safety lifecycle per ISO 13849 or IEC 62061 applies to the safety-rated components.
