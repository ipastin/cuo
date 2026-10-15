---
name: codex-universal-orchestrate
description: Universal Codex orchestration for substantial multi-step or cross-domain tasks; reuse installed Skills, plan dependency DAGs, delegate bounded subtasks across models, verify deliverables. Use on explicit delegation or complex workflows; skip trivial tasks. Applies to Codex work, never product-runtime model routing.
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
commit: "refactor(codex)!: rename orchestrator and ship reliability checks"
---

# Universal Codex Orchestration

This **supersedes the former v4/v5 Skill name**, with an explicit opt-in migration of the previously installed folder. One main orchestrator handles engineering, UX, research, business, writing, analysis and mixed workflows. No domain-specific orchestration skills are created.

## Invocation

Input: user's goal plus applicable project policies, existing context, permissions and acceptance criteria. Output: verified deliverable(s) or explicit blockers. If a task is trivial, execute directly without DAG or subagents.

## Algorithm

0. Before a full plan, apply **Adaptive Triage** from `references/ADAPTIVE_TRIAGE__created-12-10-26_04-21-24__updated-12-10-26_04-24-37__v6.0.0.md`; execute trivial work directly. An additional JSON triage is optional, not mandatory.
1. Identify **intent, deliverables, context, risk and permissions** independently of domain keywords. Read applicable AGENTS/accepted project docs.
2. Discover existing relevant Skills via metadata. Do not invent names, assume availability, or load every skill in the parent. Read `references/SKILL_EXECUTION__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md` for skill handoff.
3. Confirm required Skill eligibility against `references/SKILL_ELIGIBILITY__created-12-10-26_04-21-24__updated-12-10-26_04-24-37__v6.0.0.md`. For meaningful multi-step tasks, define small independently verifiable outputs, prerequisites, source references, acceptance criteria, risk and approvals. Keep a concise Task DAG. See `references/CORE_POLICY__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md`.
4. Keep straightforward or tightly coupled work in main. Parallelize only independent read-heavy subtasks or non-conflicting approved writes; cap is not a target. See `references/ROUTING_AND_GATES__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md`.
5. Route executor to an existing preset by **required capability + outcome risk**, not domain: `cuo-scout` (Luna), `cuo-analyst` (Sol High), `cuo-executor` (Sol Medium), `cuo-reviewer` (Sol High), `cuo-expert` (Astra for escalation). Unavailable presets/models require explicit reporting.
6. Give each child a **bounded task contract with exact mandatory Skill names** (if any). Child loads its own SKILL.md and supporting material, then executes with actual permissions. Optional Skill discovery is allowed only within task scope. Do not paste the entire parent Skill into child context.
7. Wait for prerequisites and all necessary results. Use the Verification Contract and optional minimal Execution Trace in `references/VERIFICATION_TRACE__created-12-10-26_04-21-24__updated-12-10-26_04-24-37__v6.0.0.md`. Validate against **task-specific acceptance criteria** (e.g. source traceability for research, state coverage for UX, lint/tests for code), not generic code checks for every domain.
8. Synthesize in main; resolve conflicting claims using evidence. Astra offers independent advice, not authority or user approval. Report exact checks, skill availability/use, deliverables, unresolved risks and approvals.

## Offramps and controls

- **Main thread only:** if invoked inside a delegated child thread, do not plan new agent workflows or delegate further; execute the existing assigned task-level Skill or return a blocker.

- No mandatory Skill creation, no automatic external services or API key use.
- Never claim a subagent loaded a Skill without inspecting its returned evidence/skills_used (actual adherence remains not guaranteed).
- Parent may itself execute a task-level Skill when no delegation is advantageous.
- Figma and other shared remote assets are **not** isolated by Git worktrees. Write only with appropriate permission and review.
- For independent long-running CLI lanes, read `references/WORKTREE_NOTES__created-11-10-26_18-13-52__updated-12-10-26_04-24-37__v6.0.0.md`; explicit authorization needed before invoking launcher.
- The v5 JSON Plan Contract is an **optional inspectable artifact**, not a native Codex orchestration API; validator checks structural invariants, not model reasoning quality.
