---
title: "Adaptive Routing and Quality Gates"
created: "11-10-26 18-13-52"
updated: "12-10-26 04-24-37"
version: "6.0.0"
status: "proposed"
commit: "docs(codex): document v6 universal orchestration contracts"
---

# Routing & Quality Gates

## Dispatch

| Condition | Preferred execution | Preset/model |
| --- | --- | --- |
| Deterministic calculation, validation or formatting with existing tool | Tool directly; no LLM when viable | none |
| Small, clear request, tightly coupled work | Main | Sol Medium (user may choose Luna main manually) |
| Independent source search / inventory / extraction | Subagent (if net benefit) | `cuo-scout` / Luna High |
| Ambiguous cross-domain reasoning, design alternatives, specs | Main Sol High or `cuo-analyst` | Sol High |
| Bounded write with approved scope, clear DoD | Subagent if independent | `cuo-executor` / Sol Medium |
| Material deliverable review | Independent reviewer | `cuo-reviewer` / Sol High |
| Consequential unresolved decision, high cost of reversal or contradictions | Expert consultation | `cuo-expert` / Astra Low |
| Terra | A/B candidate only | `cuo-terra-candidate` is not installed |

## Necessary preconditions for delegation

At least one: true independence, material context-isolation benefit, parallel wall-time savings, or independent review of meaningful risk. Otherwise do work in main. Strongly prefer fewer better-scoped agents.

## DAG/ownership

- All dependencies explicit; no cycles, no tasks lacking their prerequisite results.
- Concurrent writes to the same files are prohibited. A file-scoped ownership policy is a *soft agent instruction*: actual Codex sandbox and user approvals govern real permission.
- Write scopes apply to local file artifacts only. Shared Figma, Docs, production APIs and other external resources require separate collision controls and authorization; Git worktrees do not isolate them.
- Cross-cutting contracts or source-of-truth changes should be made or approved centrally before dependent execution.
- Separate worktree CLI sessions are optional and require explicit user request/authorization; no automatic merge/deploy/cleanup.

## Gate sequence

G0: Inputs / permission and privacy scope clear. G1: Task-level criteria defined. G2: Dependencies and capabilities resolved. G3: Scope-compliant results or explicit blockers. G4: Domain-appropriate objective verification. G5: Findings resolved / exceptions labeled. G6: Human approvals obtained before irreversible/external changes.

## Routing failure modes

- Model unavailable: surface limitation; use an *available, authorized* alternative only if allowed. Never default to API key or silently weaken privacy conditions.
- Skill unavailable: search via actual Codex catalog; then report missing and propose direct execution or suitable existing alternative. Never invent activation.
- Conflicting agent conclusions: compare evidence and scope. Main resolves; Astra only if consequential uncertainty remains.
- Test/check can't run: mark **not run** with blocker.
- Missing source data: label unknown; do not replace with guesses.
- Subagent runtime permission overrides may differ from profile defaults. Confirm active permission mode before risky steps.

## Model choices

Unspecified subagents default to Sol Medium for safer cross-domain generalization; choosing `cuo-scout` explicitly routes bounded exploratory subtasks to Luna High. This is deliberate: efficiency must not silently downgrade ambiguous work.

`gpt-6.1-sol`, `gpt-6-luna`, `gpt-6-astra`, and optional `gpt-5.6-terra` are **presets, not availability guarantees**. Verify through active Codex `/model` and actual child thread. Optimize successful user outcomes / Pro usage rather than API token price estimates.
