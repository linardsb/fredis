# Clean-Room Rebuild Playbook (UK context)

Clean-room reimplementation is the practice of rebuilding a piece of software (or documentation, or design) **from a specification only**, without exposure to the original implementation, so that the new work carries no copyright inheritance from the employer version.

## Ten-step discipline

1. **Freeze the old**. Stop touching the employer-owned codebase for anything other than employer work. Delete any local copies from personal devices.
2. **Write the specification from first principles**, not by reading the original code. The spec should describe *what* the system does (interfaces, invariants, data shapes), not *how* it did it in the old code.
3. **Separate the reader from the writer** — in a team clean-room this means two groups; as a solo founder this means a clean time + device boundary: employer work on employer hardware during employer hours; personal rebuild on personal hardware on personal time.
4. **Log everything**. Keep a paper trail: commit timestamps, device used, what reference material was consulted. Contemporaneous notes make the difference if the employer later alleges tainting.
5. **Use only public references** — industry standards, public docs, published research, open-source libraries. No employer Confluence pages, Slack threads, or internal design docs.
6. **Rebuild the interfaces first**, then the implementations. Interfaces are often functional and uncopyrightable anyway; implementations are where copyright lives.
7. **Resist shortcuts**. "I remember exactly how I did it" is tainted memory — write a worse, fresher version first and improve iteratively.
8. **Never copy identifiers**. Variable names, file layouts, table schemas, and comment wording all carry copyright. Rename everything.
9. **Have a third party (solicitor or trusted advisor) sanity-check the artefact list** before commercialising.
10. **Keep a carve-out letter in reserve**. Even after a clean-room rebuild, a written acknowledgement from the employer that they have no claim on the new work closes the loop cheaply.

## When clean-room is the right call

- Employer contract claims ownership and the employer is unlikely to negotiate a carve-out.
- The original artefact is obviously employer-domain (e.g. an email-dev template that maps to Merkle's client playbook).
- The product roadmap can absorb the 20–40% time cost of a fresh implementation.

## When carve-out is the right call

- The employer has an established process for personal-project carve-outs.
- The work is borderline (personal time, tangential to employer domain).
- A written release is cheaper and faster than a rebuild.

---

> Not legal advice. Consult a UK IP solicitor before acting on any output.
