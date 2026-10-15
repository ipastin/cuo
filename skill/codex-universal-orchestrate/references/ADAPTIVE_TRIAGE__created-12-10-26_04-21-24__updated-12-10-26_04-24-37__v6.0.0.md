---
title: "Adaptive Triage & Delegation Policy"
created: "12-10-26 04-21-24"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "feat(codex): formalize adaptive triage"
---

# Adaptive Triage & Delegation Policy

Decide **whether** to orchestrate before creating an agent plan. Default to **DIRECT** for simple work. This is a conceptual policy for the main Codex agent, not a paid classifier or API router.

## Modes

- `direct`: one bounded executor (usually main), no subagents; deterministic tools preferred when suitable.
- `planned`: short ordered tasks; 0–2 subagents only when a concrete benefit exists.
- `orchestrated`: multiple dependent deliverables, checkpoints, scope/permission reviews and an inspectable DAG; worktrees only after explicit approval.

## Decision dimensions

1. Expected deliverable and acceptance evidence (not domain keyword).
2. Dependencies, uncertainty, cost of rework and reversibility.
3. Parallelizable, **independent** scope and actual resource ownership.
4. Expected improvement from delegation: context isolation, independent verification or latency.
5. Tool/Skill availability, actual permissions and model entitlement.

Never use word count as the main complexity signal. Do not call Luna as an external classification API. **High risk is not necessarily multi-agent**, but approval requirements remain binding. When no subagent delivers clear value, do not spawn one. A plan can be revised only for evidence-based blockers or changed constraints.

For nontrivial tasks the parent may create a small JSON triage record. Examples: `examples/triage/*.json`. Run `python3 scripts/triage_check.py <file>` to validate **structure only**; this is not mandatory for every Codex turn and does not select a model automatically.
