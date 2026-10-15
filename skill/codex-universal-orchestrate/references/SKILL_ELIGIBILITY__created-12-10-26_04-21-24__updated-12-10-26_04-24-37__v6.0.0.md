---
title: "Skill Eligibility & Runtime Availability"
created: "12-10-26 04-21-24"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "feat(codex): distinguish skill discovery from eligibility"
---

# Skill Eligibility & Runtime Availability

Before assigning a Skill to a child, the **parent** matches capability requirements to Skills using metadata. Avoid inventing Skill IDs or copying full Skill bodies.

For each required Skill verify:
- Exact name and single unambiguous candidate.
- Matching purpose and required inputs; `description` alone is advisory, not proof of methodological suitability.
- Scope/context and tool/permission prerequisites relevant to this task.
- **Runtime availability in the actual Codex session** (built-in/plugin Skills may not be in the filesystem scan).

The **executor** then loads the required Skill instructions in its own context, works within assigned scope, and reports `skills_used` with evidence. A parent-loaded Skill does not transfer its loaded state automatically. Parent independently reviews critical results.

`python3 scripts/skill_eligibility.py examples/plans/research.json --project .` provides a *local inventory-based advisory check*. `--runtime-verified SKILL` annotates what the operator observed in Codex; it does not verify actual loading. Missing or duplicate required Skills are not silently treated as available; return a blocker or request runtime verification. Optional Skills can be omitted with reason.

No new Skill creation by default. New Skills are separate, versioned work and require demonstrable recurring gaps.
