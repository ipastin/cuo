---
title: "Adaptive Triage & Delegation Policy"
created: "12-10-26 04-21-24"
updated: "20-10-26 15-28-55"
version: "6.0.0"
status: "proposed"
commit: "fix(cuo): prioritize authorized independent stage boundaries"
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

- At each bounded-stage boundary, identify whether the next stage is a substantial, independent deliverable with its own inputs and acceptance criteria. Continue in the current chat for fixes, review, merge checks, or other work tightly coupled to its active PR or decisions.
- Use a context-window measurement only when the active Codex runtime explicitly provides it for **this session and model**. Record the named runtime source, units, and observation time. Token usage for one turn, a model's maximum window, transcript length, elapsed time, and context-mode storage statistics are not measurements of remaining capacity.
- For work that remains in the current chat, compare a reliable remaining-capacity value with the estimated context needed for the **next bounded stage**, including tool results, verification, reasoning, and final output. Use a safety margin appropriate to that stage; do not apply a universal percentage threshold. Continue here when there is enough room. Otherwise, prepare a concise, evidence-linked handoff and recommend a new session before starting the stage.
- If the runtime does not expose a reliable value, record capacity as `unknown`; do not invent a percentage or infer one from proxy metrics. Finish short, self-contained work here. For work that stays in the current chat, weigh expected context load, prior compaction, repeated rediscovery, and dependence on earlier decisions. Recommend a new session when continuity has become unreliable; otherwise reassess at the next stage boundary.
- When the next stage is substantial and independent, and the user has explicitly requested a new chat or already granted standing permission to create one automatically, check existing chats **in the creating turn, before calling `create_thread`**. Search the target project and relevant projectless chats for the same stage; continue a suitable chat instead of creating a duplicate. Follow pagination when available. If the list is incomplete, record what was searched and label global absence `needs_review`; if a duplicate remains plausible, pause creation and ask the user. If no suitable chat exists, create one regardless of whether measured remaining context is sufficient or `unknown`.
- Create one chat in the appropriate saved project with a short handoff covering goal, verified current state, links to authoritative sources, open decisions, acceptance criteria, and binding prohibitions. Link the plan or PR instead of copying its full task and test matrix. After creation, return the new chat's link or identifier; do not also start that stage in the old chat.
- If chat creation or project targeting is unavailable, report the limitation and provide a ready-to-use handoff prompt. Without user authorization, recommend a new chat instead of creating it. Compaction does not prove that every earlier detail survived. Neither context pressure nor a handoff authorizes a separate CLI session, worktree, or external write.

Boundary case: standing permission + substantial independent stage + no suitable chat after the same-turn check + sufficient measured context => create one new chat. A fix tied to the active PR stays in its current chat.

For nontrivial tasks the parent may create a small JSON triage record. Examples: `examples/triage/*.json`. Run `python3 scripts/triage_check.py <file>` to validate **structure only**; this is not mandatory for every Codex turn and does not select a model automatically.
