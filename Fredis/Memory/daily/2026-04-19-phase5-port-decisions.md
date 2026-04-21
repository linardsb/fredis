# Phase 5.1 — Wave 1 Port Decisions (2026-04-19)

Execute-pass of `.agent/plans/phase5-skill-stack.md`. All 4 carry-forward assumptions accepted;
robotics-engineer GO; in-repo `.claude/skills/` location; Archon wiring out of scope.

## Ported from alirezarezvani/claude-skills (MIT)

ceo-advisor ← c-level-advisor/ceo-advisor/
cto-advisor ← c-level-advisor/cto-advisor/
ciso-advisor ← c-level-advisor/ciso-advisor/
scenario-war-room ← c-level-advisor/scenario-war-room/
strategic-alignment ← c-level-advisor/strategic-alignment/
company-os ← c-level-advisor/company-os/
founder-coach ← c-level-advisor/founder-coach/
senior-architect ← engineering-team/senior-architect/
senior-backend ← engineering-team/senior-backend/
ai-security ← engineering-team/ai-security/
senior-data-scientist ← engineering-team/senior-data-scientist/
senior-qa ← engineering-team/senior-qa/
tdd-guide ← engineering-team/tdd-guide/
senior-security ← engineering-team/senior-security/
senior-secops ← engineering-team/senior-secops/
cloud-security ← engineering-team/cloud-security/
security-pen-testing ← engineering-team/security-pen-testing/
statistical-analyst ← engineering/statistical-analyst/
product-strategist ← product-team/product-strategist/
experiment-designer ← product-team/experiment-designer/
product-discovery ← product-team/product-discovery/
product-manager-toolkit ← product-team/product-manager-toolkit/
startup-cto ← agents/personas/startup-cto.md
solo-founder ← agents/personas/solo-founder.md
product-manager ← agents/personas/product-manager.md

## De novo (Fredis-authored)

ip-overhang-guard ← DE NOVO (UK CDPA 1988 s.11(2) + Patents Act 1977 s.39 + clean-room playbook + Merkle letter)
business-cycle-analyst ← DE NOVO (Dalio + Kondratieff + sector rotation + Chris Lori voice)
robotics-engineer ← DE NOVO (ROS2 + ISO 10218/13482/15066 + motion-planning RRT*/MPC)

## Deferred (Wave 2)

playwright-pro — upstream is a full 60+ file plugin with MCP integrations/sub-skills; port
strategy needs a Wave-2 call (vendor tree vs. reference-only skill). Not landed in Wave 1.

## Totals

- Ported: 25
- De novo: 3
- Deferred: 1 (playwright-pro)
- Grand total Wave 1: 28 new skill directories
