---
name: security-engineering
description: Hands-on application + infrastructure security — STRIDE threat modeling, OWASP Top 10, secure architecture patterns, cryptography (senior-security); SAST/DAST scans, CVE remediation, dependency vulnerability checks, compliance verification for SOC2/PCI-DSS/HIPAA/GDPR (senior-secops); penetration testing + API security + secret detection (pen-testing); cloud posture for AWS/Azure/GCP with IAM escalation-path analysis (cloud-security); AI/ML prompt-injection, jailbreak, model-inversion, data-poisoning assessment with MITRE ATLAS mapping (ai-security). Strategic CISO-level compliance roadmap and board reporting live in the separate `ciso-advisor` skill. Use when user says "threat model", "STRIDE", "OWASP", "SAST", "DAST", "CVE", "pen test", "penetration testing", "secret scan", "API security", "cloud posture", "IAM escalation", "S3 exposure", "IaC security", "prompt injection", "jailbreak", "MITRE ATLAS", "agent security".
---

# security-engineering

TL;DR — all hands-on security engineering lives here. Five layered references: threat modeling, SAST/DAST/CVE, pen testing, cloud posture, AI/ML security. Strategic compliance-roadmap work stays in `ciso-advisor`.

## Routing table

| Trigger | Reference |
|---|---|
| "threat model", "STRIDE", "OWASP", "secure architecture", "cryptography", "secret scan", "security review" | `references/threat-modeling.md` |
| "SAST", "DAST", "CVE", "dependency vulnerability", "compliance check", "secure coding pattern", "SOC2 / PCI-DSS / HIPAA / GDPR", "CI/CD security" | `references/sast-dast-scanning.md` |
| "pen test", "penetration testing", "OWASP Top 10", "API security", "offensive security assessment", "pen-test report" | `references/pen-testing.md` |
| "cloud posture", "AWS security", "Azure security", "GCP security", "IAM escalation", "S3 exposure", "open security group", "IaC gap" | `references/cloud-posture.md` |
| "prompt injection", "jailbreak", "model inversion", "data poisoning", "agent tool abuse", "MITRE ATLAS", "LLM security" | `references/ai-ml-security.md` |

## Hand-off to ciso-advisor

`ciso-advisor` is kept separate on purpose. Route there for:
- SOC 2 / ISO 27001 compliance roadmap design
- Board-level security reporting
- Security budget justification
- Vendor risk programme design
- Incident response leadership (strategic, not technical remediation)

## Shared assets

- `_shared/lanes.md` — lane-specific threat models (Email Hub employer-IP concerns route via `ip-overhang-guard`)
- `_shared/draft-path-convention.md`

## Advisor Mode

Output drafts only. Write to `Fredis/Memory/drafts/active/security-engineering/YYYY-MM-DD-<slug>.md`. Never:
- invoke `slack.postMessage` or `slack send` without `--i-confirm-send`
- invoke `drafts.send` or any send-style API
- POST to GitHub / Monday.com / any external service
- auto-commit or auto-push

Pen-test outputs in particular stay on-disk until Linards explicitly approves sharing — pen-test findings against his own systems are sensitive.

## References

| File | Load when |
|---|---|
| `references/threat-modeling.md` | STRIDE, OWASP review, cryptography design, secret hygiene |
| `references/sast-dast-scanning.md` | Static/dynamic scan, CVE remediation, compliance verification |
| `references/pen-testing.md` | Offensive assessment, OWASP Top 10 coverage, pen-test reports |
| `references/cloud-posture.md` | CSPM, IAM, cloud config assessment |
| `references/ai-ml-security.md` | LLM / agent security, MITRE ATLAS mapping |
| `references/*/scripts/` | Threat modeler, secret scanner, vulnerability assessor, compliance tracker, CSPM scripts |

## Anti-patterns

- Using `security-engineering` for strategic / board security. Route to `ciso-advisor`.
- Pen-testing third-party systems without explicit authorisation. All pen-test work in Fredis is assumed to be against Linards's own systems or authorised CTF/pentest-engagement scope.
- LLM/agent security questions → `ai-ml-security.md` only; don't fold into generic threat-modeling.
