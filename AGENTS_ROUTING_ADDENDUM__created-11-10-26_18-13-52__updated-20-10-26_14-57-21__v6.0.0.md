---
title: "Global Codex Universal Orchestration Addendum"
created: "11-10-26 18-13-52"
updated: "20-10-26 14-57-21"
version: "6.0.0"
status: "proposed"
commit: "docs(cuo): synchronize hook-free routing policy"
---

# Universal Orchestration v6.0 — Codex instructions

> Installer inserts this section into existing active AGENTS.md. Do not override existing repo-specific safety requirements or product-runtime model policies.

## Default behavior

- Handle any kind of user task: research, design, engineering, business, analysis, docs, or hybrid. Never infer a whole execution workflow from domain keywords alone.
- Small, bounded tasks: execute directly; do not construct ceremony or spawn an agent.
- **Main thread only:** apply Adaptive Triage first; for substantial tasks, use `$codex-universal-orchestrate` (v6.0). Spawned subagents must not recursively orchestrate or launch further child agents; they load task-level Skills and execute their bounded handoff. Optimize for completed, verified outcomes per ChatGPT Pro usage.
- Discover and reuse installed Skills. Agent assigned a subtask loads its **own** required Skills; project context and parent-loaded Skills are not necessarily present in child context.
- Select agent presets by task capability: `cuo-scout` Luna, `cuo-analyst` Sol High, `cuo-executor` Sol Medium, `cuo-reviewer` Sol High, `cuo-expert` Astra for consequential uncertainty. Do not use experimental Terra by default.
- Spawn agents only when independence, context isolation or review justifies their overhead. Never run dependent tasks concurrently; avoid any overlap in mutable artifacts. Usually 0–2 subagents; configured cap 5 is not a target.
- Main thread owns integration, evidence review, actual quality gates, and final response. Subject matter/acceptance criteria come from applicable Skills and project docs; don't require Git/tests for noncode tasks.
- Stay within actual permissions. Do not create worktrees or launch separate `codex exec` processes, write Figma/shared systems, merge, deploy or perform irreversible actions without explicit authorization. Never assume subagent `sandbox_mode` is a guaranteed security boundary against live runtime overrides.
- Report unavailable models/Skills, missing evidence, unrun checks and unresolved findings; no silent API fallback.

## Skill handoff rule

For each delegated task: GOAL / INPUTS / DEPENDENCIES / REQUIRED SKILLS (exact names) / OPTIONAL SKILLS / DELIVERABLE / ACCEPTANCE / PERMISSIONS / RETURN (artifact, evidence, skills_used, checks, blockers). No full Skill-body copying into child prompts.

## Verification and observability — v6.0

- For substantive work distinguish process compliance, artifact validity and actual outcome quality. Report missing evidence as `needs_review`, not success.
- Before assigning a required Skill, verify it exists in the active context or explicitly report missing/ambiguous runtime availability.
- Use opt-in non-content Execution Trace only if requested; avoid private data. CUO does not install or require lifecycle hooks.
- Keep policy concise: use `$codex-universal-orchestrate` references for detailed decisions and validator examples.
