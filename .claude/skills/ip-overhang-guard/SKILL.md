---
name: ip-overhang-guard
description: Audit employer-IP overhang for tooling built during employment before productising it under UK law. Encodes CDPA 1988 s.11(2) (copyright defaults to the employer), Patents Act 1977 s.39 (employee-invention allocation), clean-room rebuild triggers, and a Merkle-letter template. Use when the user says "IP check", "clean-room", "Merkle letter", "can I ship this", "employer IP", "carve-out", or any Email-Hub-specific product work is about to begin.
---

# IP Overhang Guard

## TL;DR

Audits whether UK employer-IP rules (CDPA 1988 s.11(2); Patents Act 1977 s.39) bite on work the user built during employment before that work can be productised under a personal company. Produces a written audit, a clean-room-vs-carve-out recommendation, and a draft request letter to the employer.

## When to use

- Any time the user considers turning an artefact written during employment into a company product.
- When a product idea overlaps with the current employer's domain (e.g. Email Hub overlapping with Merkle's email-dev stack).
- Before external IP is mentioned publicly, committed to a personal repo, or pitched to prospects.

## Encoded framework

Five moves in order. No step is optional when the audit is advisory-mode.

1. **Inventory** — list every artefact (code, docs, configs, templates, designs) that contributed to the candidate product. For each: where written, on what device, during what hours, and under which contract.
2. **Classify under UK statute** — for each artefact, apply:
   - **CDPA 1988 s.11(2)** — literary/artistic works made *in the course of employment* belong to the employer unless the contract says otherwise.
   - **Patents Act 1977 s.39(1)(a)** — inventions made in the course of normal duties or specifically assigned duties, where an invention might reasonably be expected to result, belong to the employer.
   - **Patents Act 1977 s.39(1)(b)** — inventions where the employee had a special obligation to further the employer's interests (senior / fiduciary) belong to the employer.
   - **Patents Act 1977 s.39(2)** — everything else belongs to the employee.
   - See `references/cdpa-s11.md` and `references/patents-act-s39.md`.
3. **Audit the contract** — read the employment contract's IP clause. Note any clause broader than s.11(2)/s.39 (most UK contracts go broader; some are non-enforceable where they over-reach). Flag anything unclear for solicitor review.
4. **Decide carve-out vs clean-room** — for each artefact that fails the classification:
   - **Carve-out** — negotiate a written assignment back to the employee. Cheap when the employer agrees; leaves a paper trail.
   - **Clean-room rebuild** — redesign from first principles with a chinese-wall-separated implementation team (here: just the user, before/after work hours, on personal hardware, using no employer code or documented design). See `references/clean-room-playbook.md`.
5. **Draft next action** — one of: Merkle letter request (`assets/merkle-ip-letter.md`), clean-room rebuild plan, or "no overhang — safe to ship" memo with the classification evidence.

## Workflow

1. Ask the user to list candidate artefacts. If they don't know what to list, start with `git log --author="<user>" --since="<employment-start>"` on every repo they touched.
2. For each artefact, fill in the 5-row classification table (artefact / origin / contract clause / s.11 or s.39 verdict / confidence).
3. If any artefact classifies as employer-owned or ambiguous: produce the decision matrix (carve-out vs clean-room vs drop-the-feature) with Linards-specific cost/benefit.
4. Draft the output (Merkle letter or clean-room plan or safe-to-ship memo).

## Output

Draft to `Fredis/Memory/drafts/active/ip-overhang-guard/YYYY-MM-DD-<slug>.md`. Never send, post, commit, or push. Linards reviews and sends manually.

## Fredis Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/ip-overhang-guard/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Linards reviews and sends manually from the draft file.

## References

| File | Load when |
|------|-----------|
| `references/cdpa-s11.md` | Any copyright/literary-work classification step |
| `references/patents-act-s39.md` | Any invention/patent-eligible classification step |
| `references/clean-room-playbook.md` | When the recommendation becomes "clean-room rebuild" |
| `assets/merkle-ip-letter.md` | When the recommendation becomes "request written carve-out from employer" |

## Anti-patterns

- **Do not** render a legal verdict. The skill produces an audit and a draft; the user consults a UK IP solicitor before relying on any output.
- **Do not** assume the employer contract is silent where it is not — always demand to read the actual clause before classifying.
- **Do not** recommend publishing or committing any questionable artefact publicly while the audit is in progress.
- **Do not** collapse the clean-room playbook into informal "just rewrite it" advice — clean-room discipline is the whole point.
