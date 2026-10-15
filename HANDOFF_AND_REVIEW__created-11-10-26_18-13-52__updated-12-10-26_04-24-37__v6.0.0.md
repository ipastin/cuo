---
title: "Executor Handoff and Reviewer Envelope"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Executor handoff & verification

## Handoff to subagent

```text
TASK_ID: T2
GOAL: <measurable subtask>
ALLOWED_SCOPE: <files/context/resources; no broadening>
COMPLETED_DEPENDENCIES: <list with references>
REQUIRED_SKILLS: <exact installed names OR none>
OPTIONAL_SKILLS: <exact installed names OR none>
DISCOVERY_HINTS: <capabilities, not fake Skill names>
DELIVERABLE: <artifact type/location and contents>
PERMISSIONS: <read/write, external actions, approvals>
ACCEPTANCE_CRITERIA: <checkable statements>
RETURN: status, evidence, artifacts, skills_used, skills_unavailable,
        checks_passed/failed/not_run, changes, blockers, residual_risks
```

A human-readable or JSON subagent report is acceptable. The contract is a **reporting convention**, not a machine-enforced host transport.

## Reviewer checklist

- Were accepted user goal and constraints preserved?
- Is the output complete relative to the *requested* deliverable?
- Are claims and external facts grounded with inspectable references?
- Are assumptions and unknowns explicitly separated from verified facts?
- Are quality gates aligned with the artifact rather than generic code checks?
- For writes: are requested approvals explicit, change scope respected and recovery possible?
- Which checks actually ran, and which were not possible?

## Domain examples, not required layers

| Deliverable | Suggested checks |
|---|---|
| UX flow/specification | task coverage, state coverage, edge cases, a11y, Figma alignment when applicable |
| Research brief | source provenance, freshness, citation traceability, counterevidence |
| Product strategy | assumptions, measurable hypotheses, decision trade-offs, business constraints |
| Code | tests, lint, typing, security, diff correctness, integration |
| Document | requested format, completeness, references, language and structure |
| Data analysis | units, transformations, reproducibility, missingness, arithmetic correctness |
