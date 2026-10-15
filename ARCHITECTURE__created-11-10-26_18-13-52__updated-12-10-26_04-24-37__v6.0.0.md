---
title: "Architecture, Decisions and Boundaries"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Architecture — Universal Codex Orchestration v5

## Architecture decision

**One Orchestrator, composable Skills, domain-specific methods only where applicable**. Do not create sub-orchestrators by profession or product. Project `AGENTS.md` and ADRs remain the source of product-specific constraints. The global Codex policy governs only the way **Codex** performs work.

```text
User Goal
  -> Main Codex (Sol; intent/deliverables/context/risk)
       -> Existing Skills catalog: metadata matching
       -> Plan DAG: capabilities, dependencies, gates
       -> Exec choices
            - direct tool / parent execution
            - native child threads (Luna / Sol / Astra presets)
            - optional approved standalone worktree CLI sessions
       -> Actor loads its own required Skills
       -> Evidence/Checks/Handoff artifacts
  -> Main integrates, verifies and reports
```

## Separation of concerns

- **Domain:** contextual knowledge (e.g. UX, education, finance, health, backend). Not a unit of orchestration.
- **Intent:** what the user wants (research/design/build/compare/review/etc.).
- **Deliverable:** accepted observable artifact or decision.
- **Capability:** method needed (evidence analysis, state modeling, implementation, accessibility review).
- **Skill:** repeatable method plus supporting material, selected from actual installed catalog. A skill is neither a model nor an autonomous agent.
- **Model/agent preset:** time/reasoning resources and tool/writing permissions; not a domain knowledge silo.
- **Tools:** CLI, filesystem, Git, Figma, MCP or plugins, gated by actual client capabilities.
- **Quality:** verification rubric picked per deliverable and risk. Deterministic checks where possible.

## Contract hierarchy

Higher priority safety and user/project constraints override generic orchestration recommendations. The JSON Task Contract is optional and serves as an audit artifact; native Codex does not parse the manifest to automatically enforce scheduling. Agents operate from natural-language instructions and native Codex execution controls.

## Specific risks

1. `skills.required` must list *real* names. Local filesystem inventory cannot prove plugin/runtime availability.
2. Parent-activated Skill does not automatically become a child-activated Skill. Child loads its own material.
3. Subagent permissions inherit live parent runtime policies and can override static agent preferences.
4. Git worktrees isolate repo files, **not** cloud collaboration systems or the user's Figma file.
5. Models in presets are subject to actual ChatGPT Pro availability in Codex. No API fallback.
6. Generic AGENTS instructions should stay short: detailed methods live in Skills, references and project specs.

## Upgrade strategy

The breaking naming update supersedes `$codex-hybrid-orchestrate` with `$codex-universal-orchestrate` and `orch_*` with `cuo-*`. Use the explicit migrator (`--upgrade-v5` or `--upgrade-v4`), which backs up previous managed files before removing them. Do not change unrelated user Skills, AGENTS instructions or product sources. The v5 `AGENTS.md` marker format is retained to allow in-place block updates.

## v6.0 Reliability path

```text
Goal → Adaptive Triage (direct | planned | orchestrated)
     → Context and existing Skill eligibility
     → Bounded task plan + agent assignment (if useful)
     → Executor loads task-level Skill
     → Deliverable + evidence
     → Process / Artifact / Outcome verification
     → Optional allowlisted Execution Trace
```

These remain a reusable policy and optional local verification scripts, **not** a custom model router, hosted background scheduler or guarantee of Codex model behavior.
