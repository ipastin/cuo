---
title: "Universal Task Contract Template"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Universal Task Contract (human-facing)

This template is domain-neutral. A JSON example and `scripts/validate_plan.py` supply an **optional validation representation**, not native Codex execution semantics.

```yaml
schema_version: "5.0"
goal: "Observable result requested by user"
project_context: ["Project docs / ADR references if applicable"]
constraints: ["Non-negotiable constraints"]
deliverables:
  - id: D1
    kind: report | specification | artifact | code | decision | other
    description: "What will exist at the end"
execution_policy:
  max_parallel_agents: 3  # cap, not goal
  worktrees_enabled: false
  approval_gates: ["before external writes / irreversible operations"]
tasks:
  - id: T1
    goal: "One verifiable outcome"
    depends_on: []
    capabilities: ["research", "evidence_mapping"]
    skills:
      required: []       # actual verified Skill names only
      optional: []       # actual verified Skill names only
      discovery_hint: ["source analysis"]
    executor:
      mode: subagent     # main | subagent | tool_only | worktree
      agent: cuo-scout
      model: gpt-6-luna
      effort: high
    risk: low
    evidence: ["Source references, or empty"]
    write_scopes: []
    permissions:
      external_write: false
      irreversible: false
      human_gate: false
    acceptance_criteria: ["Citable evidence with no invented source"]
```

## Handoff protocol

The parent sends task ID, goal, completed dependencies, available references, verified Skills, actual permissions, expected output and acceptance criteria. The child reports status, artifact references, sources, skill usage, checks, changed files, limitations and blockers.

## When to skip this template

A two-line fix, direct factual question or simple deterministic transformation normally needs no task DAG. Keep overhead proportional to risk and uncertainty.
