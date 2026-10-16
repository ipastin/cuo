---
title: "Adaptive Triage & Delegation Policy"
created: "12-10-26 04-21-24"
updated: "16-10-26 09-09-10"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): account for context capacity in triage"
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
6. Capacity of the current session's context window for the next bounded stage.

Never use word count as the main complexity signal. Do not call Luna as an external classification API. **High risk is not necessarily multi-agent**, but approval requirements remain binding. When no subagent delivers clear value, do not spawn one. A plan can be revised only for evidence-based blockers or changed constraints.

## Current session or new session

- Use a context-window measurement only when the active Codex runtime explicitly provides it for **this session and model**. Record the named runtime source, units, and observation time. Token usage for one turn, a model's maximum window, transcript length, elapsed time, and context-mode storage statistics are not measurements of remaining capacity.
- If a reliable remaining-capacity value is available, compare it with the estimated context needed for the **next bounded stage**, including tool results, verification, reasoning, and final output. Use a safety margin appropriate to that stage; do not apply a universal percentage threshold. Continue here when there is enough room. Otherwise, prepare a concise, evidence-linked handoff and recommend a new session before starting the stage.
- If the runtime does not expose a reliable value, record capacity as `unknown`; do not invent a percentage or infer one from proxy metrics. Finish short, self-contained work here. Before a substantial new stage, weigh the expected context load, prior compaction, repeated rediscovery, and dependence on earlier decisions. Recommend a new session with a concise handoff when continuity has become unreliable; otherwise continue here and reassess at the next stage boundary.
- Compaction can preserve continuity within one session, but it does not prove that every earlier detail survived. A new session is a recommendation unless the user has explicitly requested its creation. Neither context pressure nor a handoff authorizes a separate CLI session, worktree, or external write.

For nontrivial tasks the parent may create a small JSON triage record. Examples: `examples/triage/*.json`. Run `python3 scripts/triage_check.py <file>` to validate **structure only**; this is not mandatory for every Codex turn and does not select a model automatically.
